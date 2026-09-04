import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from google import genai

st.set_page_config(page_title="Praxis Intelligence", page_icon="🏛️", layout="wide")

# --- PREMIUM INSTITUTIONAL CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] { 
            font-family: 'Inter', sans-serif; 
            background-color: #0A0A0A;
            color: #EDEDED;
        }
        #MainMenu, footer, header {visibility: hidden;}
        
        /* Metric Box Containers */
        div[data-testid="metric-container"] {
            background-color: #121212 !important;
            border: 1px solid #2A2A2A !important;
            border-left: 4px solid #D4AF37 !important; /* Gold accent */
            border-radius: 4px; 
            padding: 1.2rem; 
        }
        div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; color: #FFFFFF !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; font-weight: 600 !important; color: #888888 !important; text-transform: uppercase; letter-spacing: 0.1em; }
        
        /* Minimalist Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 2rem; border-bottom: 1px solid #2A2A2A; }
        .stTabs [data-baseweb="tab"] { height: 3.5rem; background-color: transparent; color: #888888; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.05em; }
        .stTabs [aria-selected="true"] { border-bottom: 2px solid #D4AF37 !important; color: #FFFFFF !important; }
        
        /* Buttons */
        .stButton>button { background-color: #FFFFFF !important; color: #000000 !important; border-radius: 2px !important; padding: 0.75rem 2.5rem !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.05em; }
        .stButton>button:hover { background-color: #D4AF37 !important; color: #000000 !important; }
    </style>
""", unsafe_allow_html=True)

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

# --- BRANDING & HEADER ---
st.image("https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=2000&q=80", use_container_width=True)
st.markdown("<h1 style='text-align: center; font-weight: 700; letter-spacing: -0.02em; text-transform: uppercase;'>The Praxis Report</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888888; letter-spacing: 0.1em; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 3rem;'>Institutional Market Intelligence & Capital Strategy</p>", unsafe_allow_html=True)

local_market_data = {
    "Westlake": {"income": 250000, "price": 1850000, "dom": 38, "inventory": 145},
    "Frisco": {"income": 145000, "price": 710000, "dom": 39, "inventory": 620},
    "Dallas": {"income": 63000, "price": 435000, "dom": 44, "inventory": 3400},
}

with st.sidebar:
    st.image("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=500&q=80", use_container_width=True)
    st.markdown("### Executive Setup")
    report_type = st.selectbox("Document Classification", ["Buyer Advisory Brief", "Seller Disposition Strategy", "Capital Acquisition Memo"])
    sub_market = st.selectbox("Target Sub-Market Area", sorted(list(local_market_data.keys())))
    st.metric("30-Yr SOFR/Treasury Peg", f"{live_rate}%")

market_info = local_market_data.get(sub_market, {"income": 100000, "price": 500000, "dom": 40, "inventory": 500})

b1, b2, b3, b4 = st.columns(4)
b1.metric("Median Asset Value", f"${market_info['price']:,}")
b2.metric("Market Velocity (DOM)", f"{market_info['dom']} Days")
b3.metric("Active Supply", f"{market_info['inventory']:,}")
b4.metric("Est. Household Income", f"${market_info['income']:,}")
st.divider()

tab1, tab2, tab3 = st.tabs(["Friction Index & AI Brief", "Capital Structuring", "Market Signals"])

def calc_friction(price, rate, income):
    r = (rate / 100) / 12
    n = 360
    pmt = price * (r * (1 + r)**n) / ((1 + r)**n - 1)
    return min(round((pmt * 12 / income) * 20, 1), 10.0), round(pmt, 2)

with tab1:
    c_left, c_right = st.columns([1, 1.5])
    with c_left:
        target_price = st.number_input("Target Asset Price ($)", value=market_info['price'], step=10000)
        interest_rate = st.number_input("Cost of Capital (%)", value=live_rate, step=0.125)
        friction_score, base_pmt = calc_friction(target_price, interest_rate, market_info['income'])
        
        st.markdown(f"<div style='margin-top: 2rem;'><span style='color:#888; text-transform:uppercase; font-size:0.8rem;'>Friction Index</span><h2 style='margin:0;'>{friction_score} / 10.0</h2></div>", unsafe_allow_html=True)
        st.progress(friction_score / 10.0)
        st.markdown(f"**Debt Service:** `${base_pmt:,.2f}` / mo")

    with c_right:
        if st.button("Generate Executive Brief", use_container_width=True):
            if not client: st.error("API Key required.")
            else:
                prompt = f"""
                Write an institutional real estate memo. 
                Classification: {report_type}. Market: {sub_market}. Price: ${target_price}. Rate: {interest_rate}%. Friction: {friction_score}/10. 
                
                CRITICAL INSTRUCTIONS:
                - Tone: Clinical, financial, institutional, ruthless.
                - NO EMOJIS. NO EXCLAMATION MARKS. NO FLUFF.
                - Use strict bullet points.
                
                Sections:
                1. MACRO DYNAMICS: Hard analysis of velocity and friction.
                2. MICRO-HEATMAP: Markdown table of 3 adjacent pockets (Pocket, Leverage, Velocity).
                3. TACTICAL DEPLOYMENT: 1 concrete strategy based on {report_type}.
                """
                with st.spinner("Compiling institutional memo..."):
                    res = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                    st.markdown(res.text)

with tab2:
    st.markdown("### Deal Structuring Simulator")
    st.info("Additional capital and concession metrics module active.")
with tab3:
    st.markdown("### Risk Analytics")
    st.info("Velocity and supply curve module active.")
