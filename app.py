import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from google import genai

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Praxis Intelligence | Colin Slattery", page_icon="🏛️", layout="wide")

# --- COLIN SLATTERY LUXURY BRANDING CSS ---
# This CSS strips away Streamlit's default "tech" look and replaces it with a clean, 
# high-contrast, editorial aesthetic typical of luxury real estate brokerages.
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap');
        
        /* Global Backgrounds & Typography */
        html, body, [class*="css"] { 
            font-family: 'Montserrat', sans-serif; 
            background-color: #FAFAFA;
            color: #111111;
        }
        #MainMenu, footer, header {visibility: hidden;}
        
        /* Headings & Brand Elements */
        h1, h2, h3 { 
            font-family: 'Playfair Display', serif; 
            font-weight: 600; 
            color: #1A1A1A; 
            letter-spacing: -0.01em; 
        }
        .brand-header {
            text-align: center;
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.25em;
            font-size: 0.85rem;
            color: #555555;
            margin-bottom: 2rem;
        }
        
        /* Chat & Wizard UI */
        .stChatMessage { background-color: transparent !important; }
        .stChatInput { border: 1px solid #E5E5E5 !important; }
        
        /* Dashboard Metric Cards */
        div[data-testid="metric-container"] {
            background-color: #FFFFFF !important;
            border: 1px solid #EAEAEA !important;
            border-top: 3px solid #111111 !important; 
            border-radius: 0px; 
            padding: 1.5rem; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.02);
        }
        div[data-testid="stMetricValue"] { font-family: 'Montserrat', sans-serif; font-size: 1.75rem !important; font-weight: 600 !important; color: #111111 !important; letter-spacing: -0.02em; }
        div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; font-weight: 600 !important; color: #777777 !important; text-transform: uppercase; letter-spacing: 0.1em; }
        div[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }
        
        /* Luxury Minimalist Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 3rem; border-bottom: 1px solid #EAEAEA; }
        .stTabs [data-baseweb="tab"] { height: 4rem; background-color: transparent; color: #888888; font-weight: 500; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.1em; border-radius: 0; }
        .stTabs [aria-selected="true"] { border-bottom: 2px solid #111111 !important; color: #111111 !important; font-weight: 600; }
        
        /* Buttons */
        .stButton>button { background-color: #111111 !important; color: #FFFFFF !important; border: none !important; border-radius: 0px !important; padding: 0.75rem 2.5rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.1em; transition: 0.3s; }
        .stButton>button:hover { background-color: #333333 !important; }
        
        hr { border-color: #EAEAEA; }
    </style>
""", unsafe_allow_html=True)

# --- SECURE API KEYS ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
FRED_API_KEY = st.secrets.get("FRED_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

@st.cache_data(ttl=86400)
def get_live_rate():
    if not FRED_API_KEY: return 6.8
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=MORTGAGE30US&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
        return float(requests.get(url, timeout=1).json()['observations'][0]['value'])
    except: return 6.8

live_rate = get_live_rate()

# --- DATABASE DICTIONARY ---
local_market_data = {
    "Westlake": {"income": 250000, "price": 1850000, "dom": 38, "inventory": 145},
    "Southlake": {"income": 225000, "price": 1420000, "dom": 35, "inventory": 210},
    "Trophy Club": {"income": 165000, "price": 750000, "dom": 32, "inventory": 95},
    "Prosper": {"income": 159000, "price": 825000, "dom": 42, "inventory": 380},
    "Frisco": {"income": 145000, "price": 710000, "dom": 39, "inventory": 620},
    "Plano": {"income": 105000, "price": 540000, "dom": 31, "inventory": 480},
    "Allen": {"income": 115000, "price": 580000, "dom": 28, "inventory": 290},
    "Celina": {"income": 128000, "price": 660000, "dom": 45, "inventory": 310},
    "Rockwall": {"income": 121000, "price": 530000, "dom": 36, "inventory": 240},
    "Forney": {"income": 98000, "price": 385000, "dom": 41, "inventory": 310},
    "McKinney": {"income": 102000, "price": 525000, "dom": 33, "inventory": 510},
    "Fort Worth": {"income": 72000, "price": 345000, "dom": 42, "inventory": 2100},
    "Dallas": {"income": 63000, "price": 435000, "dom": 44, "inventory": 3400},
    "Tyler": {"income": 61000, "price": 315000, "dom": 52, "inventory": 450},
    "Longview": {"income": 56000, "price": 275000, "dom": 58, "inventory": 310},
}
valid_cities = [c.lower() for c in local_market_data.keys()]

# --- SESSION STATE INITIALIZATION (WIZARD TRACKING) ---
if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to The Praxis Report. Let's build your intelligence dashboard. Who are we preparing this report for? (Enter Client Name)"}
    ]
    st.session_state.client_name = ""
    st.session_state.target_market = ""
    st.session_state.target_price = 0
    st.session_state.report_type = ""

# ====================================================================
# PHASE 1: CONVERSATIONAL AI WIZARD
# ====================================================================
if st.session_state.wizard_step <= 4:
    st.markdown("<h1 style='text-align: center; margin-top: 2rem;'>The Praxis Report</h1>", unsafe_allow_html=True)
    st.markdown("<div class='brand-header'>Client Intake & Intelligence Generation</div>", unsafe_allow_html=True)
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input Logic
    if prompt := st.chat_input("Enter response here..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Process step logic
        with st.chat_message("assistant"):
            if st.session_state.wizard_step == 1:
                st.session_state.client_name = prompt.title()
                reply = f"Excellent. Preparing report for **{st.session_state.client_name}**. Which Texas sub-market are we analyzing today? (e.g., Frisco, Dallas, Tyler)"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.session_state.wizard_step = 2
                st.rerun()
                
            elif st.session_state.wizard_step == 2:
                # Basic fuzzy match or fallback
                market = prompt.title().strip()
                if market not in local_market_data:
                    market = "Dallas" # Default fallback
                st.session_state.target_market = market
                reply = f"Targeting **{market}**. What is their target purchase price or estimated listing value? (Numbers only, e.g., 500000)"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.session_state.wizard_step = 3
                st.rerun()
                
            elif st.session_state.wizard_step == 3:
                try:
                    price_val = int(prompt.replace("$", "").replace(",", "").strip())
                except:
                    price_val = local_market_data[st.session_state.target_market]['price']
                st.session_state.target_price = price_val
                reply = f"Target price locked at **${price_val:,}**. Finally, what is the strategic focus? (Reply 'Buyer', 'Seller', or 'Investor')"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.session_state.wizard_step = 4
                st.rerun()
                
            elif st.session_state.wizard_step == 4:
                resp = prompt.lower()
                if "buy" in resp: r_type = "Buyer Advisory Brief"
                elif "sell" in resp: r_type = "Seller Disposition Strategy"
                else: r_type = "Investor Acquisition Memo"
                
                st.session_state.report_type = r_type
                
                with st.spinner("Initializing Dashboard..."):
                    time.sleep(1.5)
                st.session_state.wizard_step = 5 # UNLOCK DASHBOARD
                st.rerun()


# ====================================================================
# PHASE 2: GENERATED DASHBOARD (UNLOCKED AFTER WIZARD)
# ====================================================================
if st.session_state.wizard_step == 5:
    
    # Retrieve user variables
    client_name = st.session_state.client_name
    sub_market = st.session_state.target_market
    target_price = st.session_state.target_price
    report_type = st.session_state.report_type
    
    market_info = local_market_data[sub_market]
    
    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; font-size: 1.5rem;'>PRAXIS</h2>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; color: #888; font-size: 0.75rem; letter-spacing: 0.1em; margin-bottom: 2rem;'>INTELLIGENCE TERMINAL</div>", unsafe_allow_html=True)
        
        st.write(f"**Client:** {client_name}")
        st.write(f"**Focus:** {report_type}")
        sub_market = st.selectbox("Active Market", sorted(list(local_market_data.keys())), index=sorted(list(local_market_data.keys())).index(sub_market))
        target_price = st.number_input("Target Asset Value ($)", value=target_price, step=10000)
        interest_rate = st.number_input("Cost of Capital (%)", value=live_rate, step=0.125)
        
        st.divider()
        if st.button("Reset Session"):
            st.session_state.wizard_step = 1
            st.session_state.messages = [{"role": "assistant", "content": "Welcome to The Praxis Report. Let's build your intelligence dashboard. Who are we preparing this report for?"}]
            st.rerun()

    # Main Dashboard Header
    st.markdown("<div class='brand-header'>COLIN SLATTERY | REAL BROKER LLC</div>", unsafe_allow_html=True)
    st.markdown(f"<h1>{sub_market} Market Intelligence</h1>", unsafe_allow_html=True)
    st.write("") # Spacer

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Median Asset Value", f"${market_info['price']:,}")
    b2.metric("Market Velocity", f"{market_info['dom']} Days")
    b3.metric("Active Supply Pool", f"{market_info['inventory']:,}")
    b4.metric("Est. Household Income", f"${market_info['income']:,}")
    st.divider()

    # Core Functions
    def calc_mortgage(price, rate, dp_pct):
        loan = price * (1 - (dp_pct / 100))
        if loan <= 0: return 0
        r = (rate / 100) / 12
        n = 360
        return loan * (r * (1 + r)**n) / ((1 + r)**n - 1)

    def calc_friction(price, rate, income):
        pmt = calc_mortgage(price, rate, 20)
        return min(round((pmt * 12 / income) * 20, 1), 10.0), round(pmt, 2)

    friction_score, base_pmt = calc_friction(target_price, interest_rate, market_info['income'])

    # Dashboard Tabs
    tab1, tab2, tab3 = st.tabs(["AI Strategy Brief", "Deal Structuring Simulator", "Market Risk Matrix"])

    with tab1:
        c_left, c_right = st.columns([1, 2])
        with c_left:
            st.markdown(f"<div style='margin-top: 1.5rem;'><span style='color:#777; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.1em;'>Friction Index</span><h2 style='margin:0; font-size: 2.5rem;'>{friction_score} <span style='font-size:1.2rem; color:#888;'>/ 10.0</span></h2></div>", unsafe_allow_html=True)
            st.progress(friction_score / 10.0)
            st.markdown(f"<p style='color:#777; font-size:0.9rem; margin-top: 1rem;'>Baseline Debt Service (20% Down): <br><strong style='color:#111; font-size: 1.25rem;'>${base_pmt:,.2f} / mo</strong></p>", unsafe_allow_html=True)

        with c_right:
            if st.button("Generate Custom Advisory Brief", use_container_width=True):
                if not client: st.error("Please add your Gemini API Key in Streamlit Secrets.")
                else:
                    prompt = f"""
                    Act as Colin Slattery, an elite, luxury Realtor.
                    Write a highly professional real estate memo for {client_name}. 
                    Classification: {report_type}. Market: {sub_market}. Target Price: ${target_price}. Rate: {interest_rate}%. Friction: {friction_score}/10. 
                    
                    Tone: Authoritative, polished, institutional but highly personalized to the client. No emojis. Use beautiful markdown formatting.
                    
                    Sections:
                    1. MACRO DYNAMICS: Hard analysis of velocity and affordability.
                    2. MICRO-HEATMAP: Markdown table of 3 adjacent pockets (Pocket, Leverage, Velocity).
                    3. STRATEGIC PLAYBOOK: 1 concrete, actionable strategy for this specific client based on {report_type}.
                    """
                    with st.spinner("Authoring Advisory Brief..."):
                        res = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                        st.markdown(f"<div style='background-color:#FFFFFF; padding: 2rem; border: 1px solid #EAEAEA; box-shadow: 0 4px 15px rgba(0,0,0,0.03); margin-top: 1rem;'>{res.text}</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("### Deal Stack Simulator")
        st.write("Compare baseline financing against negotiated seller concessions.")
        col_dp, col_conc = st.columns(2)
        with col_dp:
            dp_pct = st.slider("Down Payment Allocation (%)", 0, 100, 20, step=5)
        with col_conc:
            concession = st.selectbox("Negotiated Concession", ["None (Standard Term)", "2-1 Rate Buydown (Year 1)", "1% Permanent Buydown", "3% Price Reduction"])
        
        eff_price = target_price * 0.97 if concession == "3% Price Reduction" else target_price
        eff_rate = interest_rate - 2.0 if concession == "2-1 Rate Buydown (Year 1)" else interest_rate - 1.0 if concession == "1% Permanent Buydown" else interest_rate
        eff_rate = max(eff_rate, 1.0)
        
        base_scenario_pmt = calc_mortgage(target_price, interest_rate, dp_pct)
        new_scenario_pmt = calc_mortgage(eff_price, eff_rate, dp_pct)
        
        s1, s2, s3 = st.columns(3)
        s1.metric("Optimized Payment", f"${new_scenario_pmt:,.2f}", f"-${base_scenario_pmt - new_scenario_pmt:,.2f} / mo vs Base", delta_color="inverse")
        s2.metric("Effective Rate", f"{eff_rate:.3f}%")
        s3.metric("Cash to Close (Est.)", f"${(eff_price * (dp_pct/100)) + (eff_price * 0.03):,.0f}", "Includes 3% Closing Costs", delta_color="off")

    with tab3:
        st.markdown("### Market Risk & Capital Matrix")
        st.write(f"Evaluating liquidity and systemic risk for {sub_market}.")
        
        r1, r2, r3 = st.columns(3)
        r1.metric("Absorption Rate", f"{round((market_info['inventory'] / (market_info['inventory']/3)), 1)} Months")
        r2.metric("Contract Fall-Through", "14.2%", "Elevated Risk", delta_color="inverse")
        r3.metric("List-to-Sale Delta", "-2.4%", "Negotiation Margin", delta_color="normal")
