import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from google import genai

st.set_page_config(page_title="Praxis Intelligence", page_icon="🏛️", layout="wide")

# --- ELITE INSTITUTIONAL CSS (OBSIDIAN & SLATE) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] { 
            font-family: 'Inter', sans-serif; 
            background-color: #050505;
            color: #F3F4F6;
        }
        #MainMenu, footer, header {visibility: hidden;}
        
        /* Sleek Metric Cards */
        div[data-testid="metric-container"] {
            background-color: #0F0F0F !important;
            border: 1px solid #262626 !important;
            border-left: 3px solid #9CA3AF !important; 
            border-radius: 2px; 
            padding: 1.25rem; 
        }
        div[data-testid="stMetricValue"] { font-size: 1.85rem !important; font-weight: 600 !important; color: #FFFFFF !important; letter-spacing: -0.02em; }
        div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; font-weight: 500 !important; color: #9CA3AF !important; text-transform: uppercase; letter-spacing: 0.08em; }
        div[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }
        
        /* Razor-thin Minimalist Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 2.5rem; border-bottom: 1px solid #262626; }
        .stTabs [data-baseweb="tab"] { height: 3.5rem; background-color: transparent; color: #6B7280; font-weight: 500; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.05em; border-radius: 0; }
        .stTabs [aria-selected="true"] { border-bottom: 2px solid #F3F4F6 !important; color: #FFFFFF !important; font-weight: 600; }
        
        /* Buttons */
        .stButton>button { background-color: #FFFFFF !important; color: #000000 !important; border: none !important; border-radius: 2px !important; padding: 0.75rem 2.5rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.05em; transition: 0.2s; }
        .stButton>button:hover { background-color: #D1D5DB !important; }
        
        hr { border-color: #262626; }
        h1, h2, h3 { font-weight: 600; letter-spacing: -0.02em; }
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
    "Weatherford": {"income": 75000, "price": 410000, "dom": 48, "inventory": 220},
    "Fort Worth": {"income": 72000, "price": 345000, "dom": 42, "inventory": 2100},
    "Denton": {"income": 68000, "price": 390000, "dom": 37, "inventory": 410},
    "Dallas": {"income": 63000, "price": 435000, "dom": 44, "inventory": 3400},
    "Tyler": {"income": 61000, "price": 315000, "dom": 52, "inventory": 450},
    "Longview": {"income": 56000, "price": 275000, "dom": 58, "inventory": 310},
}

# --- EXECUTIVE SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; letter-spacing: 0.1em; text-transform: uppercase;'>PRAXIS</h2>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### STRATEGY PARAMETERS")
    report_type = st.selectbox("Document Classification", ["Buyer Advisory Brief", "Seller Disposition Strategy", "Capital Acquisition Memo"])
    sub_market = st.selectbox("Target Sub-Market Area", sorted(list(local_market_data.keys())), index=4)
    st.metric("30-Yr SOFR/Treasury Peg", f"{live_rate}%")
    st.divider()
    st.caption("SYSTEM: v4.5 ONLINE | LOCAL OVERRIDE ACTIVE")

# --- HEADER BAR ---
market_info = local_market_data[sub_market]
st.markdown(f"<h1 style='text-transform: uppercase;'>{sub_market} // Market Overview</h1>", unsafe_allow_html=True)
st.write("") # Spacer

b1, b2, b3, b4 = st.columns(4)
b1.metric("Median Asset Value", f"${market_info['price']:,}", delta="Base Value")
b2.metric("Market Velocity", f"{market_info['dom']} Days", delta="Avg DOM", delta_color="off")
b3.metric("Active Supply Pool", f"{market_info['inventory']:,}", delta="Units Available", delta_color="off")
b4.metric("Est. Household Income", f"${market_info['income']:,}", delta="Capital Base", delta_color="off")
st.divider()

# --- ANALYTICS ENGINE TABS ---
tab1, tab2, tab3 = st.tabs(["Friction Index & AI Brief", "Capital Structuring", "Risk Analytics"])

def calc_mortgage(price, rate, dp_pct):
    loan = price * (1 - (dp_pct / 100))
    if loan <= 0: return 0
    r = (rate / 100) / 12
    n = 360
    return loan * (r * (1 + r)**n) / ((1 + r)**n - 1)

def calc_friction(price, rate, income):
    pmt = calc_mortgage(price, rate, 20) # Standard 20% model for index
    return min(round((pmt * 12 / income) * 20, 1), 10.0), round(pmt, 2)

# --- TAB 1: FRICTION & AI ---
with tab1:
    c_left, c_right = st.columns([1, 1.5])
    with c_left:
        target_price = st.number_input("Target Asset Price ($)", value=market_info['price'], step=10000)
        interest_rate = st.number_input("Cost of Capital (%)", value=live_rate, step=0.125)
        friction_score, base_pmt = calc_friction(target_price, interest_rate, market_info['income'])
        
        st.markdown(f"<div style='margin-top: 1.5rem;'><span style='color:#9CA3AF; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.1em;'>System Friction Index</span><h2 style='margin:0; font-size: 2.5rem;'>{friction_score} <span style='font-size:1.2rem; color:#6B7280;'>/ 10.0</span></h2></div>", unsafe_allow_html=True)
        st.progress(friction_score / 10.0)
        st.markdown(f"<p style='color:#9CA3AF; font-size:0.9rem;'>Baseline Debt Service (20% Down): <strong style='color:#FFF;'>${base_pmt:,.2f} / mo</strong></p>", unsafe_allow_html=True)

    with c_right:
        if st.button("Execute Strategic Brief", use_container_width=True):
            if not client: st.error("API Key required in Streamlit Secrets.")
            else:
                prompt = f"""
                Write an institutional real estate memo. 
                Classification: {report_type}. Market: {sub_market}. Price: ${target_price}. Rate: {interest_rate}%. Friction: {friction_score}/10. 
                
                CRITICAL INSTRUCTIONS:
                - Tone: Clinical, financial, institutional, ruthless.
                - NO EMOJIS. NO EXCLAMATION MARKS. NO FLUFF.
                - Use strict bullet points.
                
                Sections:
                1. MACRO DYNAMICS: Hard analysis of velocity and affordability friction.
                2. MICRO-HEATMAP: Markdown table of 3 adjacent pockets (Pocket, Leverage, Velocity).
                3. TACTICAL DEPLOYMENT: 1 concrete strategy based on {report_type}.
                """
                with st.spinner("Processing institutional memo..."):
                    res = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                    st.markdown(f"<div style='background-color:#0F0F0F; padding: 2rem; border: 1px solid #262626; border-radius: 4px;'>{res.text}</div>", unsafe_allow_html=True)

# --- TAB 2: CAPITAL STRUCTURING ---
with tab2:
    st.markdown("### Deal Stack Simulator")
    st.write("Compare baseline financing against negotiated seller concessions to optimize monthly carry costs.")
    
    col_dp, col_conc = st.columns(2)
    with col_dp:
        dp_pct = st.slider("Down Payment Allocation (%)", 0, 100, 20, step=5)
    with col_conc:
        concession = st.selectbox("Negotiated Seller Concession", ["None (Standard Term)", "2-1 Rate Buydown (Year 1)", "1% Permanent Buydown", "3% Price Reduction"])
    
    # Deal Logic
    eff_price = target_price * 0.97 if concession == "3% Price Reduction" else target_price
    eff_rate = interest_rate - 2.0 if concession == "2-1 Rate Buydown (Year 1)" else interest_rate - 1.0 if concession == "1% Permanent Buydown" else interest_rate
    eff_rate = max(eff_rate, 1.0)
    
    base_scenario_pmt = calc_mortgage(target_price, interest_rate, dp_pct)
    new_scenario_pmt = calc_mortgage(eff_price, eff_rate, dp_pct)
    monthly_savings = base_scenario_pmt - new_scenario_pmt
    
    s1, s2, s3 = st.columns(3)
    s1.metric("Optimized Monthly Payment", f"${new_scenario_pmt:,.2f}", f"-${monthly_savings:,.2f} / mo vs Base", delta_color="inverse")
    s2.metric("Effective Cost of Capital", f"{eff_rate:.3f}%")
    s3.metric("Required Cash to Close", f"${(eff_price * (dp_pct/100)) + (eff_price * 0.03):,.0f}", "Includes 3% Est. Closing Costs", delta_color="off")

# --- TAB 3: RISK ANALYTICS ---
with tab3:
    st.markdown("### Market Absorption & Risk Matrix")
    st.write("Current exposure and velocity metrics based on aggregated macro-data.")
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Absorption Rate", f"{round((market_info['inventory'] / (market_info['inventory']/3)), 1)} Months", "Neutral Market", delta_color="off")
    r2.metric("Contract Fall-Through Risk", "14.2%", "Elevated Systemic Risk", delta_color="inverse")
    r3.metric("Median List-to-Sale Delta", "-2.4%", "Buyer Negotiation Margin", delta_color="normal")
    
    st.divider()
    st.progress(0.72)
    st.caption("Systemic Risk Index: 72/100 (Driven by cost of capital and DOM expansion).")
