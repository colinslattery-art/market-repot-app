import streamlit as st
import pandas as pd
import requests
from google import genai

# 1. Securely load your API Keys
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
FRED_API_KEY = st.secrets["FRED_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Fetch Live Data from FRED
@st.cache_data(ttl=86400) # Caches the data for 24 hours to save API calls
def get_live_rate():
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=MORTGAGE30US&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
        response = requests.get(url).json()
        return float(response['observations'][0]['value'])
    except Exception:
        return 6.8 # Fallback if FRED is temporarily down

live_rate = get_live_rate()

# 3. Build the Web Page Layout
st.title("Interactive Market Leverage Sandbox")
st.write("Adjust the sliders below to calculate local Affordability Friction in real time.")
st.caption(f"📈 Current National 30-Year Fixed Rate: **{live_rate}%**")

# 4. Create Interactive Sliders for the Client
target_price = st.slider("Target Purchase Price ($)", 200000, 800000, 309000)
interest_rate = st.slider("Mortgage Rate (%)", 3.0, 10.0, live_rate, step=0.1)
median_income = 84000 # Example fixed demographic data

# 5. Calculate Proprietary Math in the Background
def calc_friction(price, rate, income):
    monthly_payment = (price * (rate / 100)) / 12 
    friction_score = (monthly_payment * 12) / income * 10 
    return round(friction_score, 1)

friction_index = calc_friction(target_price, interest_rate, median_income)
st.metric("Current Affordability Friction Score", f"{friction_index} / 10")

# 6. Tell the AI what to write when the button is clicked
if st.button("Generate Market Report"):
    prompt = f"""
    Act as an expert real estate data analyst. 
    Using the following interactive metrics:
    - Target Purchase Price: ${target_price}
    - Mortgage Rate: {interest_rate}%
    - Affordability Friction Score: {friction_index}/10
    
    Write a market report modeled after 'The Praxis Report' for a local county. 
    You MUST output exactly these 3 sections:
    
    1. **Applied Dynamics:** Explain how the {friction_index}/10 Affordability Friction is stalling buyer velocity based on the {interest_rate}% rate.
    2. **Sub-Market Heatmap:** Create a Markdown table comparing 3 local cities. Include columns for Leverage Index, Buyer Velocity, and Market Phase.
    3. **Actionable Playbook:** Provide one tactical bullet point for sellers and one for buyers based on the metrics.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        st.markdown(response.text)
    except Exception as e:
        st.error(f"API Error: {e}")
