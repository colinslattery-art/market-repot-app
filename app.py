import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from google import genai

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="The Praxis Report - Market Intelligence Sandbox", page_icon="📈", layout="wide")

# --- INJECT THEME-ADAPTIVE CSS ---
st.markdown("""
    <style>
        html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
        #MainMenu, footer, header {visibility: hidden;}
        div[data-testid="metric-container"] {
            background-color: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            border-radius: 8px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 600 !important; color: var(--text-color) !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.85rem !important; font-weight: 500 !important; color: var(--text-color) !important; opacity: 0.7; text-transform: uppercase; letter-spacing: 0.05em; }
        .stTabs [data-baseweb="tab-list"] { gap: 1.5rem; }
        .stTabs [data-baseweb="tab"] { height: 3rem; background-color: transparent; border-bottom: 2px solid transparent; color: var(--text-color); opacity: 0.6; font-weight: 500; }
        .stTabs [aria-selected="true"] { border-bottom: 2px solid var(--text-color) !important; color: var(--text-color) !important; opacity: 1.0; font-weight: 600; }
        h1, h2, h3, p, span, label { color: var(--text-color) !important; }
        .stButton>button { background-color: var(--text-color) !important; color: var(--background-color) !important; border: none !important; border-radius: 4px !important; padding: 0.6rem 2rem !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

# --- API KEYS ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 📋 Client Settings")
    agent_name = st.text_input("Agent Name", value="Colin Slattery")
    client_name = st.text_input("Client Name", placeholder="e.g., John & Jane Doe")
    property_address = st.text_input("Target Property Address")
    report_type = st.selectbox("Report Persona Focus", ["Buyer Advisory Brief", "Seller Listing Strategy", "Investor Acquisition Memo"])
    
    st.divider()
    st.markdown("### 🏦 Investor Assumptions")
    proj_rent = st.number_input("Projected Monthly Rent ($)", value=3200, step=100)
    down_pmt_pct = st.slider("Down Payment %", 5, 100, 20, step=5)

# --- DATA DICTIONARY ---
dfw_baseline = {"price": 407000, "dom": 49, "inventory": 146000, "income": 84000}
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

# --- HEADER ---
st.title("The Praxis Report")
col_m, col_r = st.columns([2, 1])
with col_m: sub_market = st.selectbox("Target Sub-Market Area", sorted(list(local_market_data.keys())), index=sorted(list(local_market_data.keys())).index("Frisco"))
with col_r: st.metric("30-Yr Mortgage Rate", f"{live_rate}%")

market_info = local_market_data[sub_market]
median_income, latest_median_price, latest_dom, active_inventory = market_info["income"], market_info["price"], market_info["dom"], market_info["inventory"]

b1, b2, b3, b4 = st.columns(4)
b1.metric("Median Price", f"${latest_median_price:,}", f"{((latest_median_price - dfw_baseline['price']) / dfw_baseline['price']) * 100:+.1f}% vs DFW")
b2.metric("Days on Market", f"{latest_dom} Days", f"{latest_dom - dfw_baseline['dom']:+d} Days vs DFW")
b3.metric("Active Inventory", f"{active_inventory:,}", "Local Pool")
b4.metric("Est. Household Income", f"${median_income:,}", f"{((median_income - dfw_baseline['income']) / dfw_baseline['income']) * 100:+.1f}% vs DFW")
st.divider()

# --- ANALYTICS TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Friction & AI Advisory", "🏢 Investor ROI & Yield", "🧮 Concession Simulator", "💰 Capital Structure", "⚠️ Velocity Signals"])

def calc_monthly_pmt(price, rate, dp_pct=0):
    loan_amt = price * (1 - (dp_pct / 100))
    if loan_amt <= 0: return 0
    r = (rate / 100) / 12
    n = 360
    return loan_amt * (r * (1 + r)**n) / ((1 + r)**n - 1)

def calc_friction(price, rate, income):
    pmt = calc_monthly_pmt(price, rate)
    return min(round((pmt * 12 / income) * 20, 1), 10.0), round(pmt, 2)

with tab1:
    c_left, c_right = st.columns(2)
    with c_left:
        target_price = st.slider("Target Purchase Price ($)", 100000, 2500000, latest_median_price, step=5000)
        interest_rate = st.slider("Base Mortgage Rate (%)", 3.0, 10.0, live_rate, step=0.1)
    with c_right:
        friction_score, base_pmt = calc_friction(target_price, interest_rate, median_income)
        st.metric("Affordability Friction Score", f"{friction_score} / 10")
        st.markdown(f"**Monthly Principal & Interest:** `${base_pmt:,.2f}` / mo")
    
    st.divider()
    if st.button("Generate Executive Report", type="primary"):
        if not client: st.error("Add GEMINI_API_KEY to secrets.")
        else:
            prompt = f"Act as an elite real estate strategist. Report Type: {report_type}. Sub-market: {sub_market}. Price: ${target_price}. Rate: {interest_rate}%. Friction: {friction_score}/10. DOM: {latest_dom}. Write 3 numbered sections: 1. Applied Market Dynamics, 2. Sub-Market Micro-Heatmap (Markdown Table), 3. Actionable Strategic Playbook (1 Seller strategy, 1 Buyer strategy)."
            with st.spinner("Compiling strategic report..."):
                res = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                header = f"# THE PRAXIS REPORT\n**Prepared by:** {agent_name} | **Date:** {datetime.now().strftime('%b %d, %Y')}\n**Sub-Market:** {sub_market} | **Friction:** {friction_score}/10\n\n---\n\n"
                full_report = header + res.text
                st.markdown(full_report)
                st.download_button("💾 Download Report (.md)", full_report, f"Praxis_{sub_market}.md")

with tab5:
    st.markdown(f"### Investment Yield Analysis ({sub_market})")
    st.write(f"Based on Target Price: **${target_price:,.2f}** with **{down_pmt_pct}% Down**.")
    
    annual_rent = proj_rent * 12
    taxes = target_price * 0.022  # Est 2.2% Texas Tax Rate
    insurance = target_price * 0.005
    maintenance = annual_rent * 0.08
    noi = annual_rent - (taxes + insurance + maintenance)
    cap_rate = (noi / target_price) * 100
    
    inv_pmt = calc_monthly_pmt(target_price, interest_rate, dp_pct=down_pmt_pct)
    annual_debt = inv_pmt * 12
    cash_flow = noi - annual_debt
    cash_invested = (target_price * (down_pmt_pct / 100)) + (target_price * 0.03) # Down pmt + 3% closing
    coc_return = (cash_flow / cash_invested) * 100 if cash_invested > 0 else 0

    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Net Operating Income (NOI)", f"${noi:,.0f}")
    i2.metric("Cap Rate", f"{cap_rate:.2f}%")
    i3.metric("Annual Cash Flow", f"${cash_flow:,.0f}")
    i4.metric("Cash-on-Cash Return", f"{coc_return:.2f}%")
    
    st.caption("Assumptions: 2.2% Property Tax, 0.5% Insurance, 8% Maintenance/Vacancy reserve, 3% Closing Costs.")

with tab2:
    st.markdown("### Concession Simulator")
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        buydown_type = st.radio("Scenario", ["2-1 Temporary Buydown (Year 1)", "1% Permanent Rate Buydown", "3% Seller Price Reduction"])
        effective_rate = max(interest_rate - 2.0, 1.0) if "2-1" in buydown_type else max(interest_rate - 1.0, 1.0) if "1%" in buydown_type else interest_rate
        adjusted_price = target_price * 0.97 if "3%" in buydown_type else target_price
    with col_sim2:
        new_frict, new_pmt = calc_friction(adjusted_price, effective_rate, median_income)
        st.metric("New Monthly Payment", f"${new_pmt:,.2f}", f"-${base_pmt - new_pmt:,.2f} / mo", "inverse")
        st.metric("Adjusted Friction", f"{new_frict} / 10", f"{new_frict - friction_score:.1f} Points", "inverse")

with tab3:
    st.markdown("### Capital Structure & Financing")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("All-Cash", "25.7%")
    k2.metric("Conventional", "78.4%")
    k3.metric("FHA / VA", "21.6%")
    k4.metric("Median Down", "$69,250")

with tab4:
    st.markdown(f"### Risk & Velocity: {sub_market}")
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Median DOM", f"{latest_dom} Days")
    v2.metric("Deal Cancellations", "14.0%")
    v3.metric("Active Inventory", f"{active_inventory:,}")
    v4.metric("List-to-Sale", "97.8%")
