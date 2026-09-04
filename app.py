import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from google import genai

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="The Praxis Report - Market Intelligence Sandbox",
    page_icon="📈",
    layout="wide"
)

# --- INJECT THEME-ADAPTIVE CSS ---
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        div[data-testid="metric-container"] {
            background-color: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 600 !important;
            color: var(--text-color) !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            color: var(--text-color) !important;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 1.5rem; }
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            background-color: transparent;
            border-bottom: 2px solid transparent;
            color: var(--text-color);
            opacity: 0.6;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            border-bottom: 2px solid var(--text-color) !important;
            color: var(--text-color) !important;
            opacity: 1.0;
            font-weight: 600;
        }
        h1, h2, h3, p, span, label { color: var(--text-color) !important; }
        .stButton>button {
            background-color: var(--text-color) !important;
            color: var(--background-color) !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 0.6rem 2rem !important;
            font-weight: 600 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- API KEYS & CLIENT ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
FRED_API_KEY = st.secrets.get("FRED_API_KEY", "")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

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

# --- SIDEBAR BRANDING & CLIENT INPUTS ---
with st.sidebar:
    st.markdown("### 📋 Client & Report Settings")
    agent_name = st.text_input("Agent Name", value="Colin Slattery")
    client_name = st.text_input("Client Name", placeholder="e.g., John & Jane Doe")
    property_address = st.text_input("Target Property Address", placeholder="e.g., 123 Main St, Frisco TX")
    report_type = st.selectbox("Report Persona Focus", ["Buyer Advisory Brief", "Seller Listing Strategy", "Investor Acquisition Memo"])
    st.divider()
    st.caption("The Praxis Report v2.5 | Hyper-Local Intelligence")

# --- DATA DICTIONARY (SUB-MARKETS VS DFW BASELINE) ---
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

# --- HEADER SECTION ---
st.title("The Praxis Report")
st.markdown("<p style='font-size: 1.05rem; opacity: 0.8; margin-bottom: 1.5rem;'>Hyper-Local Market Analytics & AI Strategic Advisory</p>", unsafe_allow_html=True)

col_m, col_r = st.columns([2, 1])
with col_m:
    sub_market = st.selectbox("Target Sub-Market Area", sorted(list(local_market_data.keys())), index=sorted(list(local_market_data.keys())).index("Frisco"))
with col_r:
    st.metric("30-Yr Mortgage Rate", f"{live_rate}%")

market_info = local_market_data[sub_market]
median_income = market_info["income"]
latest_median_price = market_info["price"]
latest_dom = market_info["dom"]
active_inventory = market_info["inventory"]

# --- BENCHMARK CARDS WITH COMPARATIVE DELTAS ---
b1, b2, b3, b4 = st.columns(4)
b1.metric("Median Price", f"${latest_median_price:,}", delta=f"{((latest_median_price - dfw_baseline['price']) / dfw_baseline['price']) * 100:+.1f}% vs DFW")
b2.metric("Days on Market", f"{latest_dom} Days", delta=f"{latest_dom - dfw_baseline['dom']:+d} Days vs DFW")
b3.metric("Active Inventory", f"{active_inventory:,}", delta="Local Pool")
b4.metric("Est. Household Income", f"${median_income:,}", delta=f"{((median_income - dfw_baseline['income']) / dfw_baseline['income']) * 100:+.1f}% vs DFW")

st.divider()

# --- ANALYTICS TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Friction Model & AI Advisory", 
    "🧮 Concession & Rate Buydown Simulator", 
    "💰 Capital & Financing Composition", 
    "⚠️ Velocity & Risk Signals"
])

# CALCULATOR HELPER FUNCTION
def calc_monthly_pmt(price, rate):
    r = (rate / 100) / 12
    n = 360
    return price * (r * (1 + r)**n) / ((1 + r)**n - 1)

def calc_friction(price, rate, income):
    pmt = calc_monthly_pmt(price, rate)
    return min(round((pmt * 12 / income) * 20, 1), 10.0), round(pmt, 2)

# TAB 1: FRICTION MODEL & AI ADVISORY
with tab1:
    st.markdown("### Affordability Friction Model")
    c_left, c_right = st.columns(2)
    with c_left:
        target_price = st.slider("Target Purchase Price ($)", 100000, 2500000, latest_median_price, step=5000)
        interest_rate = st.slider("Base Mortgage Rate (%)", 3.0, 10.0, live_rate, step=0.1)

    with c_right:
        friction_score, base_pmt = calc_friction(target_price, interest_rate, median_income)
        st.metric("Affordability Friction Score", f"{friction_score} / 10")
        st.markdown(f"**Monthly Principal & Interest:** `${base_pmt:,.2f}` / mo")
        st.caption(f"Based on {sub_market} median income (${median_income:,})")

    st.divider()
    
    st.markdown(f"### 🤖 Praxis AI Advisory Brief ({report_type})")
    if st.button("Generate Executive Report", type="primary"):
        if not client:
            st.error("Please add your `GEMINI_API_KEY` to `.streamlit/secrets.toml`.")
        else:
            prompt = f"""
            Act as an elite real estate strategist producing 'The Praxis Report'.
            
            Report Parameters:
            - Focus Mode: {report_type}
            - Agent Name: {agent_name}
            - Prepared for Client: {client_name if client_name else 'Valued Client'}
            - Subject Property/Area: {property_address if property_address else sub_market}
            - Sub-Market: {sub_market}
            - Baseline Price: ${latest_median_price:,} | Client Target Price: ${target_price:,}
            - Interest Rate: {interest_rate}% | Local Household Income: ${median_income:,}
            - Affordability Friction Index: {friction_score}/10
            - Days on Market: {latest_dom} days
            
            Format your response strictly into 3 numbered sections:
            
            1. **Applied Market Dynamics:** Analyze buyer velocity, purchasing power, and price sensitivity in {sub_market} given the {friction_score}/10 friction score. Compare target price (${target_price:,}) against local baseline (${latest_median_price:,}).
            
            2. **Sub-Market Micro-Heatmap:** Provide a Markdown table evaluating 3 micro-pockets or neighborhood tiers in/around {sub_market} with columns: | Micro-Pocket | Leverage Index | Buyer Velocity | Market Phase |
            
            3. **Actionable Strategic Playbook:**
            - **Seller Strategy:** 1 high-impact tactical advice regarding pricing, concessions, or staging.
            - **Buyer Strategy:** 1 negotiation leverage point to maximize purchasing power or reduce friction.
            """
            
            with st.spinner("Compiling strategic market report..."):
                try:
                    res = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                    report_text = res.text
                    
                    # Header block for download
                    header_block = f"# THE PRAXIS REPORT\n"
                    header_block += f"**Prepared by:** {agent_name} | **Date:** {datetime.now().strftime('%B %d, %Y')}\n"
                    if client_name: header_block += f"**Prepared for:** {client_name}\n"
                    if property_address: header_block += f"**Target Property:** {property_address}\n"
                    header_block += f"**Sub-Market:** {sub_market} | **Friction Score:** {friction_score}/10\n\n---\n\n"
                    
                    full_report = header_block + report_text
                    
                    st.markdown(full_report)
                    st.download_button("💾 Download Report (.md)", data=full_report, file_name=f"Praxis_Report_{sub_market}_{datetime.now().strftime('%Y%m%d')}.md")
                except Exception as e:
                    st.error(f"Error generating AI advisory: {e}")

# TAB 2: RATE BUYDOWN & CONCESSION SIMULATOR
with tab2:
    st.markdown("### Seller Concession & Rate Buydown Simulator")
    st.write("Model the impact of a 2-1 temporary rate buydown or permanent seller concession on monthly payment and friction.")
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        buydown_type = st.radio("Concession Scenario", ["2-1 Temporary Buydown (Year 1)", "1% Permanent Rate Buydown", "3% Seller Price Reduction"])
        
        if buydown_type == "2-1 Temporary Buydown (Year 1)":
            effective_rate = max(interest_rate - 2.0, 1.0)
            adjusted_price = target_price
        elif buydown_type == "1% Permanent Rate Buydown":
            effective_rate = max(interest_rate - 1.0, 1.0)
            adjusted_price = target_price
        else:
            effective_rate = interest_rate
            adjusted_price = target_price * 0.97

    with col_sim2:
        new_friction, new_pmt = calc_friction(adjusted_price, effective_rate, median_income)
        monthly_savings = base_pmt - new_pmt
        annual_savings = monthly_savings * 12
        
        st.metric("New Monthly Payment", f"${new_pmt:,.2f}", delta=f"-${monthly_savings:,.2f} / mo", delta_color="inverse")
        st.metric("Adjusted Friction Score", f"{new_friction} / 10", delta=f"{new_friction - friction_score:.1f} Points", delta_color="inverse")
        st.success(f"💰 Total First-Year Cash Savings: **${annual_savings:,.2f}**")

# TAB 3: CAPITAL & FINANCING COMPOSITION
with tab3:
    st.markdown(f"### Capital Structure & Financing Breakdown ({sub_market})")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("All-Cash Buyers", "25.7%", delta="National Baseline")
    k2.metric("Conventional Financing", "78.4%", delta="Primary Vehicle")
    k3.metric("FHA / VA Financing", "21.6%", delta="Entry Buyer Share")
    k4.metric("Median Down Payment", "$69,250", delta="~16.3% Average")
    
    st.divider()
    st.markdown("#### Capital Distribution Summary")
    cap_data = pd.DataFrame({
        "Financing Type": ["Conventional", "All-Cash", "FHA Loan", "VA Loan"],
        "Share (%)": [58.2, 25.7, 11.2, 4.9]
    }).set_index("Financing Type")
    st.bar_chart(cap_data)

# TAB 4: VELOCITY & RISK SIGNALS
with tab4:
    st.markdown(f"### Risk & Velocity Signals: {sub_market}")
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Local Median DOM", f"{latest_dom} Days", delta="Speed of Sale")
    v2.metric("Pending Deal Cancellations", "14.0%", delta="National Risk Index")
    v3.metric("Active Sub-Market Inventory", f"{active_inventory:,}", delta="Available Supply")
    v4.metric("List-to-Sale Price Ratio", "97.8%", delta="-2.2% Negotiation Margin")
