import streamlit as st
import pandas as pd
from google import genai

# 1. Securely load your Google API Key
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Build the Web Page Layout
st.title("Interactive Market Leverage Sandbox")
st.write("Adjust the sliders below to calculate local Affordability Friction in real time.")

# 3. Create Interactive Sliders for the Client
target_price = st.slider("Target Purchase Price ($)", 200000, 800000, 309000)
interest_rate = st.slider("Mortgage Rate (%)", 3.0, 9.0, 6.8)
median_income = 84000 # Example fixed demographic data

# 4. Calculate Proprietary Math in the Background
def calc_friction(price, rate, income):
    monthly_payment = (price * (rate / 100)) / 12 
    friction_score = (monthly_payment * 12) / income * 10 
    return round(friction_score, 1)

friction_index = calc_friction(target_price, interest_rate, median_income)
st.metric("Current Affordability Friction Score", f"{friction_index} / 10")

# 5. Tell the AI what to write when the button is clicked
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
            model='gemini-pro',
            contents=prompt
        )
        st.markdown(response.text)
    except Exception as e:
        st.error(f"API Error: {e}")
