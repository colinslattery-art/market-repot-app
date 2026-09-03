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

# 3. Web Page Header & Inputs
st.title("Interactive Market Leverage Sandbox")
st.write("Adjust the parameters below to evaluate local Affordability Friction in real time.")
st.caption(f"📈 Current National 30-Year Fixed Rate: **{live_rate}%**")

# Define expanded exhaustive markets list
texas_markets = [
    # Tyler & East Texas
    "Tyler", "Longview", "Marshall", "Kilgore", "Jacksonville", "Palestine", "Athens", 
    "Henderson", "Lindale", "Whitehouse", "Bullard", "Chandler", "Canton", "Mineola", 
    "Quitman", "Winnsboro", "Gilmer", "Gladewater", "Troup", "Arp", "Overton", "Rusk", 
    "Crockett", "Nacogdoches", "Lufkin", "Mount Pleasant", "Pittsburg", "Sulphur Springs", 
    "Grand Saline", "Edgewood", "Wills Point", "Emory", "Jefferson", "Mabank", "Gun Barrel City",
    "Kemp", "Malakoff", "Frankston", "Mount Vernon", "Atlanta", "Carthage", "Center",
    # DFW Core & Surrounding Commuter Towns
    "Dallas", "Fort Worth", "Arlington", "Plano", "Garland", "Irving", "McKinney", "Frisco", 
    "Denton", "Richardson", "Grand Prairie", "Mesquite", "Carrollton", "Lewisville", "Allen", 
    "Flower Mound", "North Richland Hills", "Euless", "Bedford", "Hurst", "Coppell", "Grapevine", 
    "Haltom City", "Keller", "Rockwall", "Burleson", "Cleburne", "Weatherford", "Waxahachie", 
    "Midlothian", "Corsicana", "Ennis", "Lancaster", "DeSoto", "Cedar Hill", "Duncanville", 
    "Balch Springs", "Seagoville", "Forney", "Terrell", "Crandall", "Kaufman", "Royse City", 
    "Fate", "Wylie", "Sachse", "Murphy", "Prosper", "Celina", "Anna", "Melissa", "Princeton", 
    "Farmersville", "Greenville", "Commerce", "Quinlan", "Caddo Mills", "Josephine", "Nevada", 
    "Lavon", "Little Elm", "The Colony", "Corinth", "Highland Village", "Argyle", "Roanoke", 
    "Justin", "Ponder", "Krum", "Sanger", "Pilot Point", "Aubrey", "Saginaw", "Lake Worth", 
    "Azle", "Springtown", "Aledo", "Benbrook", "Crowley", "Joshua", "Alvarado", "Venus", 
    "Maypearl", "Italy", "Palmer", "Red Oak", "Glenn Heights", "Ovilla", "Hutchins", "Wilmer", 
    "Ferris", "Southlake", "Colleyville", "Trophy Club", "Westlake", "Haslet", "Rhome", "Decatur", 
    "Bridgeport", "Boyd", "Willow Park", "Hudson Oaks", "Mineral Wells", "Granbury",
    "Stephenville", "Glen Rose", "Keene", "Godley", "Grandview", "Rio Vista", 
    "Blum", "Hillsboro", "Milford", "Frost", "Blooming Grove", "Bynum", "Itasca", "Covington"
]
# Eliminate any accidental duplicates and alphabetize
texas_markets = sorted(list(set(texas_markets)))

# Dropdown for Target Sub-Markets
sub_market = st.selectbox(
    "Select Target Sub-Market Area",
    texas_markets
)

# Sliders
target_price = st.slider("Target Purchase Price ($)", 200000, 800000, 309000)
interest_rate = st.slider("Mortgage Rate (%)", 3.0, 10.0, live_rate, step=0.1)
median_income = 84000 

# 4. Background Calculations
def calc_friction(price, rate, income):
    monthly_payment = (price * (rate / 100)) / 12 
    friction_score = (monthly_payment * 12) / income * 10 
    return round(friction_score, 1)

friction_index = calc_friction(target_price, interest_rate, median_income)

st.divider()
st.metric("Current Affordability Friction Score", f"{friction_index} / 10")
st.divider()

# 5. AI Prompt & Generation
if st.button("Generate Market Report"):
    prompt = f"""
    Act as an expert real estate data analyst specializing in North Texas local markets.
    
    Parameters:
    - Primary Market Area: {sub_market}
    - Target Purchase Price: ${target_price}
    - Mortgage Rate: {interest_rate}%
    - Affordability Friction Score: {friction_index}/10
    
    Write a localized market intelligence report modeled after 'The Praxis Report' specifically tailored to {sub_market}.
    
    Strictly format your response with these 3 sections. Do NOT merge the table into a single paragraph. Ensure the table uses standard Markdown formatting with new lines for each row:
    
    1. **Applied Dynamics:** Analyze how the {friction_index}/10 Affordability Friction score affects buyer velocity specifically within {sub_market} at a ${target_price} price point and {interest_rate}% interest rate.
    
    2. **Sub-Market Heatmap:**
    Create a clean Markdown table comparing 3 specific neighborhoods or micro-pockets surrounding or within {sub_market}. 
    Use exactly these columns and ensure you include the separating header row (---|---|---|---):
    | Neighborhood / Pocket | Leverage Index | Buyer Velocity | Market Phase |
    
    3. **Actionable Playbook:**
    - **For Sellers:** Provide 1 tactical recommendation tailored to the current {sub_market} buyer pool.
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
