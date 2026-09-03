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

# --- APP HEADER ---
st.title("📈 Interactive Market Leverage Sandbox")
st.write("Evaluate local Texas sub-market leverage, affordability friction, and national trend benchmarks in real time.")
st.caption(f"🌐 Live National 30-Year Fixed Mortgage Rate (FRED): **{live_rate}%**")

# --- SUB-MARKET SELECTOR & LOCAL INCOME MAPPING ---
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

col_market, col_blank = st.columns([2, 1])
with col_market:
    sub_market = st.selectbox("Select Target Sub-Market Area", texas_markets, index=texas_markets.index("Tyler") if "Tyler" in texas_markets else 0)

median_income = income_data.get(sub_market, 84000)

# --- EXTRACT BENCHMARK METRICS FROM MASTER DATABASE ---
latest_median_price = 407730
latest_dom = 49
active_inventory = 1462921
cash_pct = 25.7
cancellation_pct = 14.0

if not master_df.empty:
    metric_col = 'dataset_type' if 'dataset_type' in master_df.columns else 'source_metric_type'
    
    # Extract housing key metrics
    housing_rows = master_df[master_df[metric_col].isin(['housing_market', 'housing'])]
    if not housing_rows.empty:
        row = housing_rows.iloc[0]
        price_col = 'median_sale_price_nsa_usd' if 'median_sale_price_nsa_usd' in row and pd.notnull(row['median_sale_price_nsa_usd']) else 'median_sale_price_usd'
        if price_col in row and pd.notnull(row[price_col]):
            latest_median_price = int(row[price_col])
        if 'median_days_on_market_days' in row and pd.notnull(row['median_days_on_market_days']):
            latest_dom = int(row['median_days_on_market_days'])
        if 'active_listings' in row and pd.notnull(row['active_listings']):
            active_inventory = int(row['active_listings'])

    # Extract Cash % metric
    cash_rows = master_df[master_df[metric_col].isin(['cash_loan', 'cash'])]
    if not cash_rows.empty and 'percent_all_cash_pct' in cash_rows.columns:
        val = cash_rows.iloc[0]['percent_all_cash_pct']
        if pd.notnull(val):
            cash_pct = round(float(val), 1)

    # Extract Cancellation % metric
    cancel_rows = master_df[master_df[metric_col].isin(['cancellations', 'contract'])]
    if not cancel_rows.empty and 'percent_of_pending_sales_pct' in cancel_rows.columns:
        val = cancel_rows.iloc[0]['percent_of_pending_sales_pct']
        if pd.notnull(val):
            cancellation_pct = round(float(val), 1)

# Display Key Benchmark Metrics
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Median Sale Price", f"${latest_median_price:,}")
m2.metric("Days on Market", f"{latest_dom} Days")
m3.metric("Active Listings", f"{active_inventory:,}")
m4.metric("Cash Buyers Share", f"{cash_pct}%")
m5.metric("Deal Fall-Through Rate", f"{cancellation_pct}%")

st.divider()

# --- INPUT SLIDERS & FRICTION CALCULATOR ---
col_left, col_right = st.columns(2)

with col_left:
    target_price = st.slider("Target Purchase Price ($)", 100000, 2000000, latest_median_price, step=5000)
    interest_rate = st.slider("Mortgage Rate (%)", 3.0, 10.0, live_rate, step=0.1)

with col_right:
    def calc_friction(price, rate, income):
        monthly_interest_rate = (rate / 100) / 12
        num_payments = 360
        monthly_payment = price * (monthly_interest_rate * (1 + monthly_interest_rate)**num_payments) / ((1 + monthly_interest_rate)**num_payments - 1)
        annual_housing_cost = monthly_payment * 12
        debt_to_income = annual_housing_cost / income
        friction_score = min(round(debt_to_income * 20, 1), 10.0)
        return friction_score, round(monthly_payment, 2)

    friction_index, est_monthly_pmt = calc_friction(target_price, interest_rate, median_income)
    
    st.subheader(f"Affordability Friction Score: **{friction_index} / 10**")
    st.write(f"Estimated Principal & Interest: **${est_monthly_pmt:,.2f} / mo**")
    st.caption(f"Estimated Median Household Income for {sub_market}: **${median_income:,}**")

# --- HISTORICAL PRICE TREND CHART ---
st.divider()
st.subheader(f"📈 Historical Benchmark Price Trend ({sub_market} & National Baseline)")

if not master_df.empty:
    chart_df = master_df.dropna(subset=['period_end']).copy()
    
    # Filter for housing records
    price_col = 'median_sale_price_nsa_usd' if 'median_sale_price_nsa_usd' in chart_df.columns else 'median_sale_price_usd'
    if price_col in chart_df.columns:
        chart_data = chart_df[['period_end', price_col]].dropna()
        chart_data = chart_data.rename(columns={'period_end': 'Date', price_col: 'Median Sale Price ($)'})
        chart_data = chart_data.set_index('Date').sort_index()
        st.line_chart(chart_data)
    else:
        st.info("Price trend data preparing...")

# --- GEMINI AI REPORT GENERATOR ---
st.divider()
st.subheader("🤖 Generate Praxis Intelligence Report")

if st.button("🚀 Generate AI Report", type="primary"):
    if not client:
        st.error("Please add your `GEMINI_API_KEY` to `.streamlit/secrets.toml` to generate reports.")
    else:
        prompt = f"""
        Act as an expert real estate data analyst and market strategist specializing in North Texas real estate.
        
        Parameters & Data Inputs:
        - Target Sub-Market Area: {sub_market}
        - Benchmark Median Sale Price: ${latest_median_price:,}
        - Client Target Purchase Price: ${target_price:,}
        - Current Mortgage Rate: {interest_rate}%
        - Local Median Income: ${median_income:,}
        - Calculated Affordability Friction Score: {friction_index} / 10
        - Benchmark Days on Market: {latest_dom} days
        - National All-Cash Share: {cash_pct}%
        - Deal Cancellation Rate: {cancellation_pct}%
        
        Write a localized, executive real estate intelligence report modeled after 'The Praxis Report' specifically tailored for {sub_market}.
        
        Strictly format your response with these exact 3 numbered sections:
        
        1. **Applied Dynamics:** Analyze how the {friction_index}/10 Affordability Friction score impacts buyer velocity and price tolerance in {sub_market}. Compare the client's Target Price (${target_price:,}) against the market median (${latest_median_price:,}). Incorporate the impact of {interest_rate}% interest rates, the {cash_pct}% cash buyer presence, and the {cancellation_pct}% deal cancellation rate on market velocity.
        
        2. **Sub-Market Heatmap:**
        Create a clean Markdown table comparing 3 distinct neighborhoods or micro-pockets within or immediately surrounding {sub_market}.
        Include columns for Neighborhood / Pocket, Leverage Index, Buyer Velocity, and Market Phase:
        | Neighborhood / Pocket | Leverage Index | Buyer Velocity | Market Phase |
        
        3. **Actionable Playbook:**
        - **For Sellers:** Provide 1 specific, tactical pricing or concession strategy to prevent deal cancellation and stand out to buyers given current friction levels.
        - **For Buyers:** Provide 1 specific negotiation leverage point (e.g., rate buydowns, inspection repair credits) to maximize buying power in {sub_market}.
        """
        
        with st.spinner(f"Analyzing market dynamics for {sub_market}..."):
            try:
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt
                )
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Error generating AI report: {e}")
