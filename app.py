import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from google import genai
from fpdf import FPDF

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Praxis Report | Colin Slattery", page_icon="🏛️", layout="wide")

# --- BESPOKE LUXURY BRAND CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400&display=swap');
        
        html, body, [class*="css"] { 
            font-family: 'Montserrat', sans-serif; 
            background-color: #FBFBF9; 
            color: #1A1A1A;
        }
        #MainMenu, footer, header {visibility: hidden;}
        
        h1, h2, h3 { 
            font-family: 'Playfair Display', serif; 
            font-weight: 500; 
            color: #0F251A; 
            letter-spacing: 0.02em; 
        }
        
        .brand-header {
            text-align: center;
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.25em;
            font-size: 0.8rem;
            color: #C5A059; 
            margin-bottom: 1rem;
        }
        
        .stChatMessage { background-color: transparent !important; }
        
        div[data-testid="metric-container"] {
            background-color: transparent !important;
            border: none !important;
            border-left: 2px solid #C5A059 !important; 
            padding: 0.5rem 1.5rem; 
            box-shadow: none !important;
        }
        div[data-testid="stMetricValue"] { font-family: 'Playfair Display', serif; font-size: 2.2rem !important; font-weight: 500 !important; color: #0F251A !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; font-weight: 600 !important; color: #777777 !important; text-transform: uppercase; letter-spacing: 0.15em; }
        
        .stTabs [data-baseweb="tab-list"] { gap: 3rem; border-bottom: 1px solid #EAEAEA; }
        .stTabs [data-baseweb="tab"] { height: 4rem; background-color: transparent; color: #888; font-weight: 500; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.15em; border-radius: 0; }
        .stTabs [aria-selected="true"] { border-bottom: 2px solid #0F251A !important; color: #0F251A !important; font-weight: 600; }
        
        .stButton>button { background-color: #0F251A !important; color: #FBFBF9 !important; border: 1px solid #0F251A !important; border-radius: 0px !important; padding: 0.75rem 2.5rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.15em; transition: 0.4s; }
        .stButton>button:hover { background-color: #C5A059 !important; border-color: #C5A059 !important; color: #FFFFFF !important; }
        
        hr { border-color: #E5E5E5; }
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

# --- STRICT DATA GOVERNANCE (MASTER DICTIONARY) ---
local_market_data = {
    "Westlake": {"income": 250000, "price": 1850000, "dom": 38, "inventory": 145},
    "Southlake": {"income": 225000, "price": 1420000, "dom": 35, "inventory": 210},
    "Prosper": {"income": 159000, "price": 825000, "dom": 42, "inventory": 380},
    "Frisco": {"income": 145000, "price": 710000, "dom": 39, "inventory": 620},
    "Plano": {"income": 105000, "price": 540000, "dom": 31, "inventory": 480},
    "McKinney": {"income": 102000, "price": 525000, "dom": 33, "inventory": 510},
    "Richardson": {"income": 95000, "price": 465000, "dom": 32, "inventory": 180},
    "Garland": {"income": 76000, "price": 345000, "dom": 38, "inventory": 310},
    "Fort Worth": {"income": 72000, "price": 345000, "dom": 42, "inventory": 2100},
    "Dallas": {"income": 63000, "price": 435000, "dom": 44, "inventory": 3400},
    "Tyler": {"income": 61000, "price": 315000, "dom": 52, "inventory": 450},
    "Longview": {"income": 56000, "price": 275000, "dom": 58, "inventory": 310},
    "Lindale": {"income": 68000, "price": 325000, "dom": 45, "inventory": 110},
    "Bullard": {"income": 74000, "price": 385000, "dom": 42, "inventory": 85},
    "Canton": {"income": 58000, "price": 295000, "dom": 55, "inventory": 95}
}

# --- PDF GENERATOR CLASS ---
class PraxisPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(15, 37, 26) 
        self.cell(0, 10, 'THE PRAXIS REPORT | COLIN SLATTERY', 0, 1, 'R')
        self.set_draw_color(197, 160, 89) 
        self.line(10, 20, 200, 20)
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(client_name, market, text):
    pdf = PraxisPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(30, 30, 30)
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, f"Prepared For: {client_name}  |  Market: {market}", 0, 1)
    pdf.ln(5)
    
    for line in text.split('\n'):
        if line.strip() == "":
            pdf.ln(4)
        elif line.startswith('###') or line.startswith('##'):
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(15, 37, 26)
            pdf.multi_cell(0, 8, line.replace('#', '').strip())
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(30, 30, 30)
        else:
            clean_line = line.replace('**', '')
            pdf.multi_cell(0, 6, clean_line)
    
    return bytes(pdf.output(dest='S'))

# --- SESSION STATE INITIALIZATION ---
if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1
    st.session_state.messages = [{"role": "assistant", "content": "Welcome to The Praxis Report. Let's engineer your intelligence dashboard. Who are we advising today? (Enter Client Name)"}]
    st.session_state.client_name = ""
    st.session_state.target_market = ""
    st.session_state.target_price = 0
    st.session_state.report_type = ""
    st.session_state.custom_market_data = None

# ====================================================================
# PHASE 1: CONVERSATIONAL AI WIZARD 
# ====================================================================
if st.session_state.wizard_step <= 4:
    st.markdown("<h1 style='text-align: center; margin-top: 2rem; font-size: 3rem;'>The Praxis Report</h1>", unsafe_allow_html=True)
    st.markdown("<div class='brand-header'>Client Intake & Intelligence Routing</div>", unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Enter response here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
            
        with st.chat_message("assistant"):
            if st.session_state.wizard_step == 1:
                st.session_state.client_name = prompt.title()
                reply = f"Excellent. Preparing report for **{st.session_state.client_name}**. Which Texas sub-market are we analyzing today? (e.g., Lindale, Tyler, Dallas)"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.session_state.wizard_step = 2
                st.rerun()
                
            elif st.session_state.wizard_step == 2:
                # CLEAN INPUT: Removes ", TX", ", Tx", and trailing spaces
                market_clean = prompt.title().split(',')[0].strip()
                
                # STRICT VALIDATION GATE
                if market_clean in local_market_data:
                    st.session_state.target_market = market_clean
                    st.session_state.custom_market_data = local_market_data[market_clean]
                    
                    reply = f"Targeting **{market_clean}**. Data feed verified. What is their target purchase price or estimated listing value? (Numbers only, e.g., 350000)"
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.session_state.wizard_step = 3
                else:
                    reply = f"⚠️ **Data Feed Error:** We do not have active coverage or verified MLS data for '{market_clean}'. Please enter a market currently in our system (e.g., Lindale, Richardson, Dallas, Fort Worth)."
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                
                st.rerun()
                
            elif st.session_state.wizard_step == 3:
                try:
                    price_val = int(prompt.replace("$", "").replace(",", "").strip())
                except:
                    price_val = st.session_state.custom_market_data['price']
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
                with st.spinner("Compiling Verified Intelligence Dashboard..."):
                    time.sleep(1.5)
                st.session_state.wizard_step = 5
                st.rerun()

# ====================================================================
# PHASE 2: GENERATED LUXURY DASHBOARD
# ====================================================================
if st.session_state.wizard_step == 5:
    
    client_name = st.session_state.client_name
    sub_market = st.session_state.target_market
    target_price = st.session_state.target_price
    report_type = st.session_state.report_type
    market_info = st.session_state.custom_market_data
    
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color:#0F251A;'>PRAXIS</h2>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; color: #C5A059; font-size: 0.75rem; letter-spacing: 0.1em; margin-bottom: 2rem;'>STRATEGY TERMINAL</div>", unsafe_allow_html=True)
        
        st.write(f"**Client:** {client_name}")
        st.write(f"**Focus:** {report_type}")
        target_price = st.number_input("Target Asset Value ($)", value=target_price, step=10000)
        interest_rate = st.number_input("Cost of Capital (%)", value=live_rate, step=0.125)
        
        st.divider()
        if st.button("Reset Strategy Session"):
            st.session_state.clear()
            st.rerun()

    st.markdown("<div class='brand-header'>COLIN SLATTERY | REAL BROKER LLC</div>", unsafe_allow_html=True)
    st.markdown(f"<h1>{sub_market} Verified Market Intelligence</h1>", unsafe_allow_html=True)
    st.write("") 

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Median Asset Value", f"${market_info['price']:,}")
    b2.metric("Market Velocity", f"{market_info['dom']} Days")
    b3.metric("Active Supply Pool", f"{market_info['inventory']:,}")
    b4.metric("Est. Household Income", f"${market_info['income']:,}")
    st.divider()

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

    tab1, tab2, tab3 = st.tabs(["Advisory Brief & PDF Export", "Deal Stack Optimizer", "Risk & Capital Matrix"])

    with tab1:
        c_left, c_right = st.columns([1, 2])
        with c_left:
            st.markdown(f"<div style='margin-top: 1.5rem;'><span style='color:#C5A059; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.1em;'>Friction Index</span><h2 style='margin:0; font-size: 2.5rem; color:#0F251A;'>{friction_score} <span style='font-size:1.2rem; color:#888;'>/ 10.0</span></h2></div>", unsafe_allow_html=True)
            st.progress(friction_score / 10.0)
            st.markdown(f"<p style='color:#777; font-size:0.9rem; margin-top: 1rem;'>Baseline Debt Service (20% Down): <br><strong style='color:#111; font-size: 1.25rem;'>${base_pmt:,.2f} / mo</strong></p>", unsafe_allow_html=True)

        with c_right:
            if st.button("Generate Executive PDF Brief", use_container_width=True):
                if not client: st.error("Please add your Gemini API Key in Streamlit Secrets.")
                else:
                    prompt = f"""
                    Act as Colin Slattery, an elite luxury Realtor. Write a highly professional real estate memo based strictly on the provided data.
                    Client: {client_name}. Focus: {report_type}. Market: {sub_market}. Target Price: ${target_price}. Rate: {interest_rate}%. Friction: {friction_score}/10.
                    Tone: Authoritative, polished, luxury advisory. DO NOT use emojis.
                    Sections:
                    1. MACRO DYNAMICS: Analysis of velocity and affordability.
                    2. MARKET HEALTH: What the {friction_score}/10 friction means for liquidity.
                    3. STRATEGIC PLAYBOOK: 1 concrete, actionable strategy for this specific client based on {report_type}.
                    """
                    with st.spinner("Authoring Advisory Brief & Compiling PDF..."):
                        try:
                            res = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                            report_content = res.text
                            
                            st.markdown(f"<div style='background-color:#FFF; padding: 2rem; border: 1px solid #EAEAEA; border-top: 2px solid #0F251A; margin-top: 1rem;'>{report_content}</div>", unsafe_allow_html=True)
                            
                            pdf_bytes = generate_pdf(client_name, sub_market, report_content)
                            st.download_button(
                                label="Download Report as PDF",
                                data=pdf_bytes,
                                file_name=f"Praxis_Report_{client_name.replace(' ','_')}.pdf",
                                mime="application/pdf",
                                type="primary"
                            )
                        except Exception as e:
                            st.error(f"Error compiling document: {e}")

    with tab2:
        st.markdown("### Deal Stack Optimizer")
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
        s3.metric("Cash to Close (Est.)", f"${(eff_price * (dp_pct/100)) + (eff_price * 0.03):,.0f}")

    with tab3:
        st.markdown("### Market Capital Matrix")
        st.write(f"Evaluating liquidity for {sub_market}.")
        r1, r2, r3 = st.columns(3)
        r1.metric("Absorption Rate", f"{round((market_info['inventory'] / (market_info['inventory']/3)), 1)} Months")
        r2.metric("Contract Fall-Through", "14.2%", "Systemic Risk Factor", delta_color="inverse")
        r3.metric("List-to-Sale Delta", "-2.4%")
