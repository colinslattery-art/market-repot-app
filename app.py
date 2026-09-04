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

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- FETCH LIVE FRED MORTGAGE RATE ---
@st.cache_data(ttl=86400)
def get_live_rate():
    if not FRED_API_KEY:
        return 6.8
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=MORTGAGE30US&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
        response = requests.get(url, timeout=5).json()
        return float(response['observations'][0]['value'])
    except Exception:
        return 6.8

live_rate = get_live_rate()

# --- LOAD MASTER REDFIN DATABASE ---
@st.cache_data
def load_master_database():
    try:
        df = pd.read_csv("master_redfin_database.csv")
        df['period_end'] = pd.to_datetime(df['period_end'], errors='coerce')
        df = df.sort_values(by='period_end', ascending=False)
        return df
    except Exception as e:
        st.error(f"⚠️ Error loading 'master_redfin_database.csv': {e}")
        return pd.DataFrame()

master_df = load_master_database()

# --- APP HEADER & SUB-MARKET SELECTOR ---
st.title("📈 Praxis Market Intelligence Sandbox")
st.write("Real-time sub-market leverage analysis, capital structure breakdowns, and AI report generation.")

texas_markets = [
    "Aledo", "Allen", "Alvarado", "Anna", "Arlington", "Arp", "Athens", "Atlanta", "Aubrey", "Azle", 
    "Balch Springs", "Bedford", "Benbrook", "Blooming Grove", "Blum", "Boyd", "Bridgeport", "Bullard", 
    "Burleson", "Bynum", "Caddo Mills", "Canton", "Carthage", "Cedar Hill", "Celina", "Center", "Chandler", 
    "Cleburne", "Colleyville", "Commerce", "Coppell", "Corinth", "Corsicana", "Covington", "Crandall", 
    "Crockett", "Crowley", "Dallas", "Decatur", "Denton", "DeSoto", "Duncanville", "Edgewood", "Emory", 
    "Ennis", "Euless", "Farmersville", "Fate", "Ferris", "Flower Mound", "Forney", "Fort Worth", "Frankston", 
    "Frisco", "Frost", "Garland", "Gilmer", "Gladewater", "Glen Rose", "Glenn Heights", "Godley", "Granbury", 
    "Grand Prairie", "Grand Saline", "Grandview", "Grapevine", "Greenville", "Gun Barrel City", "Haltom City", 
    "Haslet", "Henderson", "Highland Village", "Hillsboro", "Hudson Oaks", "Hurst", "Hutchins", "Irving", 
    "Italy", "Itasca", "Jacksonville", "Jefferson", "Josephine", "Joshua", "Kaufman", "Keene", "Keller", 
    "Kemp", "Kilgore", "Krum", "Lake Worth", "Lancaster", "Lavon", "Lewisville", "Lindale", "Little Elm", 
    "Longview", "Lufkin", "Mabank", "Malakoff", "Marshall", "Maypearl", "McKinney", "Melissa", "Mesquite", 
    "Midlothian", "Milford", "Mineola", "Mineral Wells", "Mount Pleasant", "Mount Vernon", "Murphy", 
    "Nacogdoches", "Nevada", "North Richland Hills", "Overton", "Palestine", "Palmer", "Pilot Point", 
    "Pittsburg", "Plano", "Ponder", "Princeton", "Prosper", "Quinlan", "Quitman", "Red Oak", "Richardson", 
    "Rio Vista", "Roanoke", "Rockwall", "Royse City", "Rusk", "Sachse", "Saginaw", "Sanger", "Seagoville", 
    "Southlake", "Springtown", "Stephenville", "Sulphur Springs", "Terrell", "The Colony", "Troup", 
    "Trophy Club", "Tyler", "Venus", "Waxahachie", "Weatherford", "Westlake", "Whitehouse", "Wills Point", 
    "Willow Park", "Wilmer", "Winnsboro", "Wylie"
]

income_data = {
    "Westlake": 250000, "Southlake": 225000, "Trophy Club": 165000, "Prosper": 159000, 
    "Frisco": 145000, "Rockwall": 121000, "Plano": 105000, "Allen": 115000, "Celina": 128000,
    "Forney": 98000, "McKinney": 102000, "Fort Worth": 72000, "Dallas": 63000, "Tyler": 61000, 
    "Longview": 56000, "Denton": 68000, "Weatherford": 75000
}

col_market, col_rate = st.columns([2, 1])
with col_market:
    sub_market = st.selectbox("Select Target Sub-Market Area", texas_markets, index=texas_markets.index("Tyler") if "Tyler" in texas_markets else 0)
with col_rate:
    st.metric("FRED 30-Yr Benchmark Rate", f"{live_rate}%")

median_income = income_data.get(sub_market, 84000)

# Extract core values from master database
metric_col = 'dataset_type' if 'dataset_type' in master_df.columns else 'source_metric_type'
latest_median_price = 407730
latest_dom = 49
active_inventory = 1462921

if not master_df.empty:
    housing_rows = master_df[master_df[metric_col].isin(['housing_market', 'housing'])]
    if not housing_rows.empty:
        row = housing_rows.iloc[0]
        p_col = 'median_sale_price_nsa_usd' if 'median_sale_price_nsa_usd' in row and pd.notnull(row['median_sale_price_nsa_usd']) else 'median_sale_price_usd'
        if p_col in row and pd.notnull(row[p_col]):
            latest_median_price = int(row[p_col])
        if 'median_days_on_market_days' in row and pd.notnull(row['median_days_on_market_days']):
            latest_dom = int(row['median_days_on_market_days'])
        if 'active_listings' in row and pd.notnull(row['active_listings']):
            active_inventory = int(row['active_listings'])

st.divider()

# --- SPECIALIZED ANALYTICS TABS ---
tab1, tab2, tab3 = st.tabs([
    "🎯 Market Friction & AI Report", 
    "💰 Capital & Financing Structure", 
    "⚠️ Risk & Velocity Signals"
])

# ==============================================================================
# TAB 1: MARKET FRICTION & AI REPORT
# ==============================================================================
with tab1:
    st.subheader("Interactive Friction Model & AI Intelligence Generation")
    
    col_left, col_right = st.columns(2)
    with col_left:
        target_price = st.slider("Target Purchase Price ($)", 100000, 2000000, latest_median_price, step=5000)
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
        st.caption(f"Estimated Household Income for {sub_market}: **${median_income:,}**")

    st.subheader(f"📈 Price Trend Baseline ({sub_market} Context)")
    if not master_df.empty:
        chart_df = master_df.dropna(subset=['period_end']).copy()
        p_col = 'median_sale_price_nsa_usd' if 'median_sale_price_nsa_usd' in chart_df.columns else 'median_sale_price_usd'
        if p_col in chart_df.columns:
            chart_data = chart_df[['period_end', p_col]].dropna().rename(columns={'period_end': 'Date', p_col: 'Median Sale Price ($)'}).set_index('Date').sort_index()
            st.line_chart(chart_data)

    st.divider()
    st.subheader("🤖 Generate Executive Praxis Intelligence Report")
    
    if st.button("🚀 Generate AI Report", type="primary"):
        if not client:
            st.error("Please add your `GEMINI_API_KEY` to `.streamlit/secrets.toml`.")
        else:
            prompt = f"""
            Act as an expert real estate market strategist specializing in North Texas real estate.
            
            Inputs:
            - Target Sub-Market Area: {sub_market}
            - Baseline Price: ${latest_median_price:,} | Target Price: ${target_price:,}
            - Interest Rate: {interest_rate}% | Local Household Income: ${median_income:,}
            - Affordability Friction Score: {friction_index} / 10
            - Days on Market: {latest_dom} days
            
            Write an executive report formatted strictly into 3 numbered sections:
            1. **Applied Dynamics:** Evaluate buyer velocity and target price tolerance given {friction_index}/10 friction.
            2. **Sub-Market Heatmap:** A markdown table comparing 3 micro-pockets in/around {sub_market} (Neighborhood, Leverage Index, Buyer Velocity, Market Phase).
            3. **Actionable Playbook:** 1 tactical strategy for Sellers and 1 negotiation point for Buyers.
            """
            
            with st.spinner("Generating intelligence report..."):
                try:
                    response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
                    st.markdown(response.text)
                    st.download_button("💾 Download Report (.md)", data=response.text, file_name=f"{sub_market}_Praxis_Report.md")
                except Exception as e:
                    st.error(f"Error: {e}")

# ==============================================================================
# TAB 2: CAPITAL & FINANCING STRUCTURE
# ==============================================================================
with tab2:
    st.subheader("Financing Composition & Cash Buyer Penetration")
    
    cash_rows = master_df[master_df[metric_col].isin(['cash_loan', 'cash'])] if not master_df.empty else pd.DataFrame()
    
    cash_pct = 25.7
    fha_pct = 13.4
    va_pct = 8.2
    conv_pct = 78.4
    median_dp = 69250
    
    if not cash_rows.empty:
        r = cash_rows.iloc[0]
        cash_pct = float(r.get('percent_all_cash_pct', cash_pct)) if pd.notnull(r.get('percent_all_cash_pct')) else cash_pct
        fha_pct = float(r.get('percent_fha_loan_pct', fha_pct)) if pd.notnull(r.get('percent_fha_loan_pct')) else fha_pct
        va_pct = float(r.get('percent_va_loan_pct', va_pct)) if pd.notnull(r.get('percent_va_loan_pct')) else va_pct
        conv_pct = float(r.get('percent_conventional_loan_pct', conv_pct)) if pd.notnull(r.get('percent_conventional_loan_pct')) else conv_pct
        median_dp = int(r.get('median_down_payment_usd', median_dp)) if pd.notnull(r.get('median_down_payment_usd')) else median_dp

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("All-Cash Buyers", f"{cash_pct}%")
    c2.metric("Conventional Loans", f"{conv_pct}%")
    c3.metric("FHA Loan Share", f"{fha_pct}%")
    c4.metric("VA Loan Share", f"{va_pct}%")
    c5.metric("Median Down Payment", f"${median_dp:,}")

    st.divider()
    st.subheader("📈 Capital Trend (Cash vs Financed Buyers)")
    if not cash_rows.empty and 'period_end' in cash_rows.columns:
        cols = [c for c in ['percent_all_cash_pct', 'percent_conventional_loan_pct', 'percent_fha_loan_pct'] if c in cash_rows.columns]
        c_chart = cash_rows[['period_end'] + cols].dropna().set_index('period_end').sort_index()
        st.line_chart(c_chart)

# ==============================================================================
# TAB 3: RISK & VELOCITY SIGNALS
# ==============================================================================
with tab3:
    st.subheader("Market Friction & Fall-Through Metrics")
    
    cancel_rows = master_df[master_df[metric_col].isin(['cancellations', 'contract'])] if not master_df.empty else pd.DataFrame()
    delist_rows = master_df[master_df[metric_col].isin(['delistings', 'delistings_relistings'])] if not master_df.empty else pd.DataFrame()
    
    cancel_pct = 14.0
    total_delistings = 83587
    
    if not cancel_rows.empty and 'percent_of_pending_sales_pct' in cancel_rows.columns:
        val = cancel_rows.iloc[0]['percent_of_pending_sales_pct']
        if pd.notnull(val): cancel_pct = float(val)
        
    if not delist_rows.empty and 'total_delistings' in delist_rows.columns:
        val = delist_rows.iloc[0]['total_delistings']
        if pd.notnull(val): total_delistings = int(val)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Pending Deal Cancellations", f"{cancel_pct}%")
    r2.metric("Total Stale Delistings", f"{total_delistings:,}")
    r3.metric("Median Days on Market", f"{latest_dom} Days")
    r4.metric("Active Inventory Pool", f"{active_inventory:,}")

    st.divider()
    st.subheader("📈 Contract Cancellation Rate Trend (%)")
    if not cancel_rows.empty and 'percent_of_pending_sales_pct' in cancel_rows.columns:
        cancel_chart = cancel_rows[['period_end', 'percent_of_pending_sales_pct']].dropna().rename(columns={'percent_of_pending_sales_pct': 'Cancellation Rate (%)'}).set_index('period_end').sort_index()
        st.line_chart(cancel_chart)
