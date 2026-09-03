import streamlit as st
import pandas as pd
import requests
from google import genai

# 1. Securely load API Keys
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
FRED_API_KEY = st.secrets["FRED_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Fetch Live Data from FRED
@st.cache_data(ttl=86400)
def get_live_rate():
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=MORTGAGE30US&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
        response = requests.get(url).json()
        return float(response['observations'][0]['value'])
    except Exception:
        return 6.8

live_rate = get_live_rate()

# 3. Fetch Live Market Data from Redfin
@st.cache_data(ttl=604800) # Cache for 7 days (Redfin updates weekly/monthly)
def get_redfin_data():
    # URL for Redfin's public city-level market tracker
    url = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz"
    
    # Load only necessary columns to prevent Streamlit memory crashes
    cols = ['period_end', 'region', 'state_code', 'median_sale_price', 'median_dom', 'months_of_supply']
    df = pd.read_csv(url, compression='gzip', sep='\t', usecols=cols)
    
    # Filter strictly for Texas and drop empty rows
    tx_df = df[df['state_code'] == 'TX'].dropna()
    
    # Sort by date to get the most recent data first
    tx_df['period_end'] = pd.to_datetime(tx_df['period_end'])
    tx_df = tx_df.sort_values(by='period_end', ascending=False)
    return tx_df

# Load the data quietly in the background
with st.spinner("Fetching latest Redfin data..."):
    redfin_df = get_redfin_data()

# 4. Web Page Header & Inputs
st.title("Interactive Market Leverage Sandbox")
st.write("Adjust the parameters below to evaluate local Affordability Friction in real time.")
st.caption(f"📈 Current National 30-Year Fixed Rate: **{live_rate}%**")

# Expand exhaustive markets list
texas_markets = [
    "Tyler", "Longview", "Dallas", "Fort Worth", "Arlington", "Plano", "Garland", 
    "Irving", "McKinney", "Frisco", "Denton", "Richardson", "Rockwall", "Forney", 
    "Terrell", "Crandall", "Kaufman"
]
texas_markets = sorted(list(set(texas_markets)))

sub_market = st.selectbox("Select Target Sub-Market Area", texas_markets)

# Automatically extract the latest Redfin metrics for the chosen city
# Redfin formats city names as "City, TX" in the 'region' column
city_filter = f"{sub_market}, TX"
local_data = redfin_df[redfin_df['region'] == city_filter]

# Set dynamic defaults based on Redfin data if available
if not local_data.empty:
    latest_median_price = int(local_data.iloc[0]['median_sale_price'])
    latest_dom = int(local_data.iloc[0]['median_dom'])
    months_supply = round(local_data.iloc[0]['months_of_supply'], 1)
    st.success(f"✅ Live Redfin Data Synced: Median Price **${latest_median_price:,}** | **{latest_dom}** Days on Market")
else:
    latest_median_price = 309000
    latest_dom = 30
    months_supply = 2.0
    st.warning(f"⚠️ Redfin data pending for {sub_market}. Using default baselines.")

# Sliders
target_price = st.slider("Target Purchase Price ($)", 200000, 1000000, latest_median_price)
interest_rate = st.slider("Mortgage Rate (%)", 3.0, 10.0, live_rate, step=0.1)

income_data = {"Frisco": 145000, "Plano": 105000, "Forney": 98000, "Fort Worth": 72000, "Dallas": 63000, "Tyler": 61000}
median_income = income_data.get(sub_market, 84000)

# 5. Background Calculations
def calc_friction(price, rate, income):
    monthly_payment = (price * (rate / 100)) / 12 
    friction_score = (monthly_payment * 12) / income * 10 
    return round(friction_score, 1)

friction_index = calc_friction(target_price, interest_rate, median_income)

st.divider()
st.metric("Current Affordability Friction Score", f"{friction_index} / 10")
st.divider()

# 6. AI Prompt & Generation
if st.button("Generate Market Report"):
    prompt = f"""
    Act as an expert real estate data analyst specializing in North Texas local markets.
    
    Parameters:
    - Primary Market Area: {sub_market}
    - Redfin Median Sale Price: ${latest_median_price}
    - Redfin Days on Market: {latest_dom}
    - Redfin Months of Supply: {months_supply}
    - Target Purchase Price (Client Slider): ${target_price}
    - Mortgage Rate: {interest_rate}%
    - Affordability Friction Score: {friction_index}/10
    
    Write a localized market intelligence report modeled after 'The Praxis Report' specifically tailored to {sub_market}.
    
    Strictly format your response with these 3 sections. Do NOT merge the table into a single paragraph. Ensure the table uses standard Markdown formatting with new lines for each row:
    
    1. **Applied Dynamics:** Analyze how the {friction_index}/10 Affordability Friction score affects buyer velocity within {sub_market}. Compare the client's Target Price (${target_price}) to the actual Redfin Median Price (${latest_median_price}). Incorporate the current Days on Market ({latest_dom}) and Months of Supply ({months_supply}) into your analysis of leverage.
    
    2. **Sub-Market Heatmap:**
    Create a clean Markdown table comparing 3 specific neighborhoods or micro-pockets surrounding or within {sub_market}. 
    Use exactly these columns and ensure you include the separating header row (---|---|---|---):
    | Neighborhood / Pocket | Leverage Index | Buyer Velocity | Market Phase |
    
    3. **Actionable Playbook:**
    - **For Sellers:** Provide 1 tactical recommendation tailored to the current {sub_market} buyer pool and {months_supply} months of supply.
    - **For Buyers:** Provide 1 tactical leverage point to negotiate effectively given the {friction_index}/10 friction index.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        st.markdown(response.text)
    except Exception as e:
        st.error(f"API Error: {e}")
