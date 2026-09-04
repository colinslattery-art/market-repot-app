import streamlit as st
import pandas as pd
import requests
from google import genai

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Praxis Report - Market Intelligence Sandbox",
    page_icon="📈",
    layout="wide"
)

# --- SECURE API KEYS ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
FRED_API_KEY = st.secrets.get("FRED_API_KEY", "")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- FETCH LIVE FRED MORTGAGE RATE ---
@st.cache_data(ttl=86400)
def get_live_rate():
    if not FRED_API_KEY:
        return 6.8
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=MORTGAGE30US&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
        response = requests.get(url, timeout=1).json()
        return float(response['observations'][0]['value'])
    except Exception:
        return 6.8

live_rate = get_live_rate()

# --- APP HEADER ---
st.title("📈 Praxis Market Intelligence Sandbox")

texas_markets = [
    "Aledo", "Allen", "Celina", "Dallas", "Denton", "Forney", "Fort Worth", "Frisco", 
    "Longview", "McKinney", "Plano", "Prosper", "Rockwall", "Southlake", "Trophy Club", "Tyler", "Weatherford", "Westlake"
]

# Localized Market Data Override
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

col_market, col_rate = st.columns([2, 1])
with col_market:
    sub_market = st.selectbox("Select Target Sub-Market Area", sorted(texas_markets), index=sorted(texas_markets).index("Tyler"))
with col_rate:
    st.metric("FRED 30-Yr Benchmark Rate", f"{live_rate}%")

# Apply Dynamic Selection
market_info = local_market_data.get(sub_market, {"income": 84000, "price": 407000, "dom": 49, "inventory": 450})
median_income = market_info["income"]
latest_median_price = market_info["price"]
latest_dom = market_info["dom"]
active_inventory = market_info["inventory"]

st.divider()

# --- SPECIALIZED ANALYTICS TABS ---
tab1, tab2, tab3 = st.tabs(["🎯 Market Friction & AI Report", "💰 Capital & Financing Structure", "⚠️ Risk & Velocity Signals"])

with tab1:
    st.subheader(f"Interactive Friction Model: {sub_market}")
    
    col_left, col_right = st.columns(2)
    with col_left:
        target_price = st.slider("Target Purchase Price ($)", 100000, 2500000, latest_median_price, step=5000)
        interest_rate = st.slider("Mortgage Rate (%)", 3.0, 10.0, live_rate, step=0.1)

    with col_right:
        def calc_friction(price, rate, income):
            r = (rate / 100) / 12
            n = 360
            monthly_pmt = price * (r * (1 + r)**n) / ((1 + r)**n - 1)
            friction_score = min(round((monthly_pmt * 12 / income) * 20, 1), 10.0)
            return friction_score, round(monthly_pmt, 2)

        friction_index, est_monthly_pmt = calc_friction(target_price, interest_rate, median_income)
        
        st.metric("Affordability Friction Score", f"{friction_index} / 10")
        st.write(f"Estimated Principal & Interest: **${est_monthly_pmt:,.2f} / mo**")
        st.caption(f"Estimated Local Household Income: **${median_income:,}**")

    st.divider()
    if st.button("🚀 Generate AI Report", type="primary"):
        if not client:
            st.error("Please add your GEMINI_API_KEY to secrets.")
        else:
            prompt = f"""
            Act as an expert real estate market strategist specializing in North Texas real estate.
            
            Inputs:
            - Target Sub-Market Area: {sub_market}
            - Baseline Median Price: ${latest_median_price:,} | Client Target Price: ${target_price:,}
            - Interest Rate: {interest_rate}% | Local Household Income: ${median_income:,}
            - Affordability Friction Score: {friction_index} / 10
            - Local Days on Market: {latest_dom} days
            
            Write an executive report formatted strictly into 3 numbered sections:
            1. **Applied Dynamics:** Evaluate buyer velocity and target price tolerance given {friction_index}/10 friction.
            2. **Sub-Market Heatmap:** A markdown table comparing 3 micro-pockets in/around {sub_market} (Neighborhood, Leverage Index, Buyer Velocity, Market Phase).
            3. **Actionable Playbook:** 1 tactical strategy for Sellers and 1 negotiation point for Buyers.
            """
            with st.spinner("Generating intelligence report..."):
                try:
                    response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.subheader(f"Financing Composition ({sub_market})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("All-Cash Buyers", "25.7%")
    c2.metric("Conventional Loans", "78.4%")
    c3.metric("FHA Loan Share", "13.4%")
    c4.metric("Median Down Payment", "$69,250")

with tab3:
    st.subheader(f"Risk & Velocity Signals: {sub_market}")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Local Median Sale Price", f"${latest_median_price:,}")
    r2.metric("Local Days on Market", f"{latest_dom} Days")
    r3.metric("Local Active Listings", f"{active_inventory:,}")
    r4.metric("Nat'l Deal Cancellations", "14.0%")
