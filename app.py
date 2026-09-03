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
    Using this data (Affordability Friction: {friction_index}/10, Price: ${target_price}, Rate: {interest_rate}%), 
    generate a real estate market report with exactly 3 sections: 
    1. Applied Dynamics
    2. Sub-Market Heatmap
    3. Actionable Playbook.
    Keep the tone analytical and strictly follow this structure.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    st.markdown(response.text)
