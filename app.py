import streamlit as st
import pandas as pd
import requests
import time
import re
import sqlite3
import hashlib
import json
import uuid
from datetime import datetime
from google import genai
from fpdf import FPDF
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Praxis Report | Colin Slattery", page_icon="🏛️", layout="wide")

# --- ULTRA-LUXURY BRAND CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400&display=swap');
        
        .stApp, .main, .block-container { background-color: #FBFBF9 !important; }
        html, body, p, span, label, li, td, th { font-family: 'Montserrat', sans-serif !important; color: #1A1A1A !important; }
        #MainMenu, footer, header {visibility: hidden;}
        
        h1, h2, h3 { font-family: 'Playfair Display', serif !important; font-weight: 500 !important; color: #0F251A !important; letter-spacing: 0.02em !important; text-align: center; }
        .brand-header { text-align: center; font-family: 'Montserrat', sans-serif; text-transform: uppercase; letter-spacing: 0.25em; font-size: 0.8rem; color: #C5A059 !important; margin-bottom: 2rem; margin-top: 1rem; }
        
        [data-testid="stForm"] { border: none !important; background-color: transparent !important; }
        div[data-baseweb="input"] { background-color: transparent !important; border: none !important; border-bottom: 2px solid #0F251A !important; border-radius: 0 !important; }
        div[data-baseweb="input"] > div { background-color: transparent !important; }
        
        input { font-family: 'Playfair Display', serif !important; font-size: 1.5rem !important; color: #0F251A !important; -webkit-text-fill-color: #0F251A !important; text-align: center !important; padding: 1rem !important; background-color: transparent !important; }
        input::placeholder { color: #A0A0A0 !important; -webkit-text-fill-color: #A0A0A0 !important; font-family: 'Montserrat', sans-serif !important; font-size: 1rem !important; }
        
        .client-card { background-color: #FFFFFF; border: 1px solid #EAEAEA; border-top: 3px solid #0F251A; padding: 1.5rem; text-align: center; transition: 0.3s; margin-bottom: 0.5rem; }
        .client-card:hover { box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-top: 3px solid #C5A059; }
        .client-card h3 { font-size: 1.5rem; margin-bottom: 0.5rem; }
        .client-card p { font-size: 0.8rem; color: #777; text-transform: uppercase; letter-spacing: 0.1em; }
        
        div[data-testid="metric-container"] { background-color: transparent !important; border: none !important; border-left: 2px solid #C5A059 !important; padding: 0.5rem 1.5rem; box-shadow: none !important; }
        div[data-testid="stMetricValue"] { font-family: 'Playfair Display', serif; font-size: 2.2rem !important; font-weight: 500 !important; color: #0F251A !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; font-weight: 600 !important; color: #777777 !important; text-transform: uppercase; letter-spacing: 0.15em; }
        
        .stTabs [data-baseweb="tab-list"] { gap: 3rem; border-bottom: 1px solid #EAEAEA; justify-content: center; }
        .stTabs [data-baseweb="tab"] { height: 4rem; background-color: transparent !important; color: #888 !important; font-weight: 500; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.15em; border-radius: 0; }
        .stTabs [aria-selected="true"] { border-bottom: 2px solid #0F251A !important; color: #0F251A !important; font-weight: 600; }
        
        .stButton>button, .stDownloadButton>button, .stFormSubmitButton>button { background-color: #0F251A !important; color: #FBFBF9 !important; -webkit-text-fill-color: #FBFBF9 !important; border: 1px solid #0F251A !important; border-radius: 0px !important; padding: 0.75rem 2.5rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.15em; transition: 0.4s; }
        .stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover { background-color: #C5A059 !important; border-color: #C5A059 !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
        [data-testid="stFormSubmitButton"] { display: flex; justify-content: center; width: 100%; margin-top: 1.5rem; }
        [data-testid="stFormSubmitButton"] > button { width: 250px !important; }
        [data-testid="stVerticalBlock"] .stButton>button, [data-testid="stVerticalBlock"] .stDownloadButton>button { width: 100%; }
        
        .dataframe { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        .dataframe th { background-color: #0F251A; color: #FBFBF9 !important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; padding: 1rem; letter-spacing: 0.1em; }
        .dataframe td { padding: 1rem; border-bottom: 1px solid #EAEAEA; background-color: #FFFFFF; }
    </style>
""", unsafe_allow_html=True)

# ====================================================================
# SECURE DATABASE ENGINE (SQLITE)
# ====================================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect("praxis_database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS clients 
                 (client_id TEXT PRIMARY KEY, agent_username TEXT, client_name TEXT, market TEXT, 
                  target_price INTEGER, address TEXT, report_type TEXT, payload TEXT)''')
    
    # Ensure Master Admin Exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", hash_password("praxis2026"), "admin"))
    
    conn.commit()
    conn.close()

init_db()

class DatabaseEngine:
    def authenticate(self, username, password):
        conn = sqlite3.connect("praxis_database.db")
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (username.lower(), hash_password(password)))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def add_user(self, username, password, role="agent"):
        conn = sqlite3.connect("praxis_database.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users VALUES (?, ?, ?)", (username.lower(), hash_password(password), role))
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        conn.close()
        return success

    def get_all_users(self):
        conn = sqlite3.connect("praxis_database.db")
        df = pd.read_sql_query("SELECT username, role FROM users", conn)
        conn.close()
        return df

    def check_client_exists(self, agent_username, client_name):
        """Prevents an agent from creating two clients with the exact same name."""
        conn = sqlite3.connect("praxis_database.db")
        c = conn.cursor()
        c.execute("SELECT 1 FROM clients WHERE agent_username=? AND LOWER(client_name)=?", (agent_username.lower(), client_name.lower()))
        exists = c.fetchone()
        conn.close()
        return bool(exists)

    def save_client(self, client_id, agent_username, client_data):
        conn = sqlite3.connect("praxis_database.db")
        c = conn.cursor()
        client_data['agent_owner'] = agent_username.lower() # Tag payload with owner
        payload = json.dumps(client_data)
        c.execute('''INSERT OR REPLACE INTO clients 
                     (client_id, agent_username, client_name, market, target_price, address, report_type, payload) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (client_id, agent_username.lower(), client_data['name'], client_data['market'], 
                   client_data['price'], client_data['address'], client_data['type'], payload))
        conn.commit()
        conn.close()

    def get_agent_clients(self, agent_username):
        conn = sqlite3.connect("praxis_database.db")
        c = conn.cursor()
        c.execute("SELECT client_id, payload FROM clients WHERE agent_username=?", (agent_username.lower(),))
        rows = c.fetchall()
        conn.close()
        return {row[0]: json.loads(row[1]) for row in rows}
        
    def get_all_clients_admin(self):
        """Fetches all clients globally for the God Mode view."""
        conn = sqlite3.connect("praxis_database.db")
        c = conn.cursor()
        c.execute("SELECT client_id, agent_username, payload FROM clients")
        rows = c.fetchall()
        conn.close()
        return [{"client_id": r[0], "agent": r[1], "data": json.loads(r[2])} for r in rows]

    def get_client_by_id(self, client_id):
        """Fetches a specific client regardless of who owns it."""
        conn = sqlite3.connect("praxis_database.db")
        c = conn.cursor()
        c.execute("SELECT payload FROM clients WHERE client_id=?", (client_id,))
        row = c.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None

db = DatabaseEngine()

# --- MARKET DATA ENGINE ---
class MarketDataEngine:
    def __init__(self):
        self.local_fallback = {
            "Westlake": {"income": 250000, "price": 1850000, "dom": 38, "inventory": 145},
            "Southlake": {"income": 225000, "price": 1420000, "dom": 35, "inventory": 210},
            "Frisco": {"income": 145000, "price": 710000, "dom": 39, "inventory": 620},
            "Dallas": {"income": 63000, "price": 435000, "dom": 44, "inventory": 3400},
            "Tyler": {"income": 61000, "price": 315000, "dom": 52, "inventory": 450},
            "Lindale": {"income": 68000, "price": 325000, "dom": 45, "inventory": 110},
        }
    def validate_market(self, city_name):
        city_clean = city_name.title().split(',')[0].strip()
        if city_clean in self.local_fallback: return city_clean
        return None
    def get_market_metrics(self, city_name):
        city = self.validate_market(city_name)
        return self.local_fallback[city] if city else None
    def get_property_details(self, price, address=""):
        tax_rate = 0.022
        hoa_monthly = 0
        if address and address.strip():
            tax_rate = 0.020 + (len(address) % 4) * 0.0015
            hoa_monthly = (len(address) % 5) * 45
        return {"tax_monthly": (price * tax_rate) / 12, "ins_monthly": (price * 0.005) / 12, "hoa_monthly": hoa_monthly, "tax_rate": tax_rate}

engine = MarketDataEngine()
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

@st.cache_data(ttl=86400)
def get_live_rate(): return 6.8
live_rate = get_live_rate()

# --- PDF GENERATOR ---
def sanitize_text_for_pdf(text):
    replacements = {'“': '"', '”': '"', '‘': "'", '’': "'", '—': '--', '–': '-', '…': '...'}
    for k, v in replacements.items(): text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

class PraxisPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(15, 37, 26) 
        self.cell(0, 10, 'THE PRAXIS REPORT | COLIN SLATTERY', 0, 1, 'R')
        self.set_draw_color(197, 160, 89) 
        self.line(10, 20, 200, 20)
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(client_name, market, address, text):
    pdf = PraxisPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font('Helvetica', 'B', 14)
    target_str = address if address else market
    pdf.cell(0, 10, f"Prepared For: {sanitize_text_for_pdf(client_name)}  |  Target: {sanitize_text_for_pdf(target_str)}", 0, 1)
    pdf.ln(5)
    clean_text = sanitize_text_for_pdf(text)
    for line in clean_text.split('\n'):
        if line.strip() == "": pdf.ln(4)
        elif line.startswith('###') or line.startswith('##'):
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(15, 37, 26)
            pdf.multi_cell(0, 8, line.replace('#', '').strip())
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(30, 30, 30)
        else:
            pdf.multi_cell(0, 6, line.replace('**', ''))
    return pdf.output(dest='S').encode('latin-1')

def generate_strategy_memo(client_name, report_type, sub_market, property_address, target_price, interest_rate, friction_score):
    if not client: return "⚠️ Please add your Gemini API Key in Streamlit Secrets."
    target_context = f"Property: {property_address}" if property_address else f"Sub-Market: {sub_market}"
    prompt = f"""
    Act as Colin Slattery, an elite luxury Realtor. Write a highly professional real estate memo.
    Client: {client_name}. Focus: {report_type}. {target_context}. Target Price: ${target_price}. Rate: {interest_rate}%. Friction: {friction_score}/10.
    Tone: Authoritative, polished. DO NOT use emojis.
    Sections: 1. MACRO DYNAMICS. 2. MARKET HEALTH. 3. STRATEGIC PLAYBOOK (1 actionable strategy).
    """
    try: return client.models.generate_content(model='gemini-3.6-flash', contents=prompt).text
    except Exception as e: return f"Error: {e}"

# --- STATE MANAGEMENT ---
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "username": None, "role": None, "view_mode": "login"})
if "active_client_id" not in st.session_state:
    st.session_state.active_client_id = None
if "wizard_step" not in st.session_state:
    st.session_state.update({"wizard_step": 1, "temp_client": {}})

def logout():
    st.session_state.clear()
    st.rerun()

# ====================================================================
# VIEW 0: LOGIN PORTAL
# ====================================================================
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-header'>COLIN SLATTERY | REAL BROKER LLC</div>", unsafe_allow_html=True)
    st.markdown("<h1>Praxis Intelligence Portal</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
            pwd = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            if st.form_submit_button("Authenticate"):
                role = db.authenticate(user, pwd)
                if role:
                    st.session_state.update({"logged_in": True, "username": user.lower(), "role": role, "view_mode": "hub" if role == "agent" else "admin"})
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid credentials.")

# ====================================================================
# VIEW 1: GLOBAL ADMIN DASHBOARD (God Mode)
# ====================================================================
elif st.session_state.role == "admin" and st.session_state.view_mode == "admin":
    st.markdown("<div class='brand-header'>SYSTEM ADMINISTRATOR</div>", unsafe_allow_html=True)
    st.markdown("<h1>Command Center</h1>", unsafe_allow_html=True)
    
    if st.button("Log Out"): logout()
    st.divider()
    
    t1, t2 = st.tabs(["Agent Provisioning", "Global Client Database (God Mode)"])
    
    with t1:
        st.markdown("### Provision New Agent Account")
        c1, c2 = st.columns([1, 1])
        with c1:
            with st.form("new_user"):
                n_user = st.text_input("New Username")
                n_pwd = st.text_input("Initial Password", type="password")
                if st.form_submit_button("Create Account"):
                    if db.add_user(n_user, n_pwd): st.success(f"Account '{n_user}' provisioned. They may now log in.")
                    else: st.error("Username already exists. Usernames must be strictly unique.")
        with c2:
            st.markdown("### Active System Users")
            st.dataframe(db.get_all_users(), hide_index=True, use_container_width=True)
            
    with t2:
        st.markdown("### System-Wide Intelligence Activity")
        global_clients = db.get_all_clients_admin()
        st.metric("Total Intel Briefs Generated", len(global_clients))
        st.divider()
        
        if not global_clients:
            st.info("No client data generated yet by any agents.")
        else:
            col_a, col_b, col_c = st.columns(3)
            cols = [col_a, col_b, col_c]
            
            for idx, c in enumerate(global_clients):
                cdata = c['data']
                cid = c['client_id']
                agent_name = c['agent'].upper()
                
                with cols[idx % 3]:
                    st.markdown(f"<div class='client-card'><h3>{cdata['name']}</h3><p>AGENT: {agent_name}<br>{cdata['market']} | {cdata['type']}</p></div>", unsafe_allow_html=True)
                    if st.button(f"Enter Dashboard ➔", key=f"godmode_{cid}"):
                        st.session_state.active_client_id = cid
                        st.session_state.view_mode = "sandbox"
                        st.rerun()

# ====================================================================
# VIEW 2: AGENT HUB (ROSTER)
# ====================================================================
elif st.session_state.role == "agent" and st.session_state.view_mode == "hub":
    st.markdown("<div style='height: 5vh;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-header'>COLIN SLATTERY | REAL BROKER LLC</div>", unsafe_allow_html=True)
    st.markdown(f"<h1>Agent Hub: {st.session_state.username.title()}</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        c_left, c_right = st.columns(2)
        with c_left:
            if st.button("+ New Client Strategy", use_container_width=True):
                st.session_state.update({"temp_client": {}, "wizard_step": 1, "view_mode": "wizard"})
                st.rerun()
        with c_right:
            if st.button("Log Out", use_container_width=True): logout()
        
        st.divider()
        st.markdown("<h3 style='text-align: left;'>ACTIVE PORTFOLIOS</h3>", unsafe_allow_html=True)
        
        agent_clients = db.get_agent_clients(st.session_state.username)
        if not agent_clients:
            st.info("No active clients. Initialize a new strategy to begin.")
        else:
            for cid, cdata in agent_clients.items():
                st.markdown(f"<div class='client-card'><h3>{cdata['name']}</h3><p>{cdata['market']} | {cdata['type']}</p></div>", unsafe_allow_html=True)
                if st.button(f"Load {cdata['name']}'s Dashboard ➔", key=f"load_{cid}"):
                    st.session_state.update({"active_client_id": cid, "view_mode": "sandbox"})
                    st.rerun()

# ====================================================================
# VIEW 3: DISAPPEARING WIZARD (CREATE NEW CLIENT)
# ====================================================================
elif st.session_state.role == "agent" and st.session_state.view_mode == "wizard":
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-header'>COLIN SLATTERY | REAL BROKER LLC</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.wizard_step == 1:
            st.markdown("<h1>Client Name</h1>", unsafe_allow_html=True)
            with st.form("step1_form"):
                client_input = st.text_input("Client Name", placeholder="e.g., John & Jane Doe", label_visibility="collapsed")
                if st.form_submit_button("Continue") and client_input.strip():
                    clean_name = client_input.title().strip()
                    # UNIQUENESS CHECK
                    if db.check_client_exists(st.session_state.username, clean_name):
                        st.error(f"⚠️ Client '{clean_name}' already exists in your roster. Please use a unique identifier (e.g., '{clean_name} - Buyer').")
                    else:
                        st.session_state.temp_client['name'] = clean_name
                        st.session_state.wizard_step = 2; st.rerun()

        elif st.session_state.wizard_step == 2:
            st.markdown(f"<h1>Which Texas sub-market are we analyzing for {st.session_state.temp_client['name']}?</h1>", unsafe_allow_html=True)
            with st.form("step2_form"):
                market_input = st.text_input("Market Area", placeholder="e.g., Lindale, Richardson, Dallas", label_visibility="collapsed")
                if st.form_submit_button("Verify Data Feed"):
                    market_clean = engine.validate_market(market_input)
                    if market_clean:
                        st.session_state.temp_client['market'] = market_clean
                        st.session_state.wizard_step = 3; st.rerun()
                    else: st.error("⚠️ Data Feed Error: No active coverage for that area.")

        elif st.session_state.wizard_step == 3:
            st.markdown("<h1>Target Price Point</h1>", unsafe_allow_html=True)
            with st.form("step3_form"):
                default_price = engine.get_market_metrics(st.session_state.temp_client['market'])['price']
                price_input = st.text_input("Target Price ($)", value=f"${default_price:,}", label_visibility="collapsed")
                if st.form_submit_button("Lock Price Point"):
                    clean_str = re.sub(r'[^\d.]', '', price_input)
                    if clean_str:
                        st.session_state.temp_client['price'] = int(float(clean_str))
                        st.session_state.wizard_step = 4; st.rerun()

        elif st.session_state.wizard_step == 4:
            st.markdown("<h1>Specific Target Property?</h1>", unsafe_allow_html=True)
            with st.form("step4_form"):
                addr_input = st.text_input("Property Address", placeholder="e.g., 123 Main St (Optional)", label_visibility="collapsed")
                if st.form_submit_button("Continue / Skip"):
                    st.session_state.temp_client['address'] = addr_input.strip()
                    st.session_state.wizard_step = 5; st.rerun()

        elif st.session_state.wizard_step == 5:
            st.markdown("<h1>Strategic Focus</h1>", unsafe_allow_html=True)
            c_buyer, c_seller, c_investor = st.columns(3)
            with c_buyer:
                if st.button("Buyer Advisory"): st.session_state.temp_client['type'] = "Buyer Advisory Brief"; st.session_state.wizard_step = 6; st.rerun()
            with c_seller:
                if st.button("Seller Strategy"): st.session_state.temp_client['type'] = "Seller Disposition Strategy"; st.session_state.wizard_step = 6; st.rerun()
            with c_investor:
                if st.button("Investor Memo"): st.session_state.temp_client['type'] = "Investor Acquisition Memo"; st.session_state.wizard_step = 6; st.rerun()

        elif st.session_state.wizard_step == 6:
            st.session_state.temp_client.update({'base_rate': live_rate, 'tax_rate_override': 2.2, 'hoa_override': 0, 'saved_brief': ""})
            cid = str(uuid.uuid4())
            db.save_client(cid, st.session_state.username, st.session_state.temp_client)
            st.session_state.active_client_id = cid
            st.session_state.view_mode = "sandbox"
            st.rerun()

# ====================================================================
# VIEW 4: THE AGENT SANDBOX (CLIENT DASHBOARD)
# ====================================================================
elif st.session_state.view_mode == "sandbox":
    
    cid = st.session_state.active_client_id
    client_data = db.get_client_by_id(cid)
    
    # Identify who actually owns this client data to save overrides back correctly
    owner_agent = client_data.get('agent_owner', st.session_state.username)
    market_info = engine.get_market_metrics(client_data['market'])
    
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color:#0F251A !important;'>PRAXIS</h2>", unsafe_allow_html=True)
        
        mode_text = "GOD MODE ACTIVE" if st.session_state.role == "admin" else "AGENT SANDBOX"
        st.markdown(f"<div style='text-align: center; color: #C5A059 !important; font-size: 0.75rem; letter-spacing: 0.1em; margin-bottom: 2rem;'>{mode_text}</div>", unsafe_allow_html=True)
        
        if st.button("⬅ Return to Hub"):
            st.session_state.view_mode = "admin" if st.session_state.role == "admin" else "hub"
            st.rerun()
            
        st.divider()
        st.markdown("### Client Overrides")
        new_type = st.selectbox("Strategy Mode", ["Buyer Advisory Brief", "Seller Disposition Strategy", "Investor Acquisition Memo"], index=["Buyer Advisory Brief", "Seller Disposition Strategy", "Investor Acquisition Memo"].index(client_data['type']))
        new_price = st.number_input("Target Price ($)", value=client_data['price'], step=10000)
        new_rate = st.number_input("Base Rate (%)", value=client_data['base_rate'], step=0.125)
        
        st.markdown("### Property Mechanics")
        new_tax = st.number_input("Tax Rate (%)", value=client_data.get('tax_rate_override', 2.2), step=0.1)
        new_hoa = st.number_input("HOA ($/mo)", value=client_data.get('hoa_override', 0), step=10)
        
        # Save overrides 
        if (new_type != client_data['type'] or new_price != client_data['price'] or 
            new_rate != client_data['base_rate'] or new_tax != client_data.get('tax_rate_override') or 
            new_hoa != client_data.get('hoa_override')):
            
            client_data.update({'type': new_type, 'price': new_price, 'base_rate': new_rate, 'tax_rate_override': new_tax, 'hoa_override': new_hoa})
            db.save_client(cid, owner_agent, client_data)
            st.rerun()

    st.markdown("<div class='brand-header'>COLIN SLATTERY | REAL BROKER LLC</div>", unsafe_allow_html=True)
    header_title = client_data['address'] if client_data['address'] else f"{client_data['market']} Market Intelligence"
    st.markdown(f"<h1>{header_title.title()}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #777;'>Prepared for: <strong>{client_data['name']}</strong> | Strategy: <strong>{client_data['type']}</strong></p>", unsafe_allow_html=True)
    st.write("") 

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Target Asset Value", f"${client_data['price']:,}")
    b2.metric("Assigned Tax Rate", f"{client_data.get('tax_rate_override', 2.2):.2f}%")
    b3.metric("Monthly HOA", f"${client_data.get('hoa_override', 0):,.0f}")
    b4.metric("Market Velocity", f"{market_info['dom']} Days")
    st.divider()

    def calc_mortgage(price, rate, dp_pct):
        loan = price * (1 - (dp_pct / 100))
        if loan <= 0: return 0
        r = (rate / 100) / 12
        n = 360
        return loan * (r * (1 + r)**n) / ((1 + r)**n - 1)

    base_pmt = calc_mortgage(client_data['price'], client_data['base_rate'], 20)
    friction_score = min(round((base_pmt * 12 / market_info['income']) * 20, 1), 10.0)

    tab1, tab2, tab3 = st.tabs(["AI Strategy Brief & Export", "Deal Stack Optimizer", "Risk & Capital Matrix"])

    with tab1:
        c_left, c_right = st.columns([1, 1.5])
        with c_left:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = friction_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Affordability Friction", 'font': {'size': 14, 'color': '#C5A059', 'family': 'Montserrat'}},
                gauge = {'axis': {'range': [None, 10], 'tickwidth': 1, 'tickcolor': "darkblue"}, 'bar': {'color': "#0F251A"}, 'bgcolor': "white", 'borderwidth': 2, 'bordercolor': "#EAEAEA", 'steps': [{'range': [0, 4], 'color': '#E5F0EA'}, {'range': [4, 7], 'color': '#FDF3E1'}, {'range': [7, 10], 'color': '#FCE8E8'}]}
            ))
            fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="#FBFBF9")
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

        with c_right:
            if st.button("Generate/Refresh Executive Brief", use_container_width=True):
                with st.spinner("Authoring Advisory Brief..."):
                    brief = generate_strategy_memo(client_data['name'], client_data['type'], client_data['market'], client_data['address'], client_data['price'], client_data['base_rate'], friction_score)
                    client_data['saved_brief'] = brief
                    db.save_client(cid, owner_agent, client_data)
                    st.rerun()
            
            if client_data.get('saved_brief'):
                st.markdown(f"<div style='background-color:transparent; padding: 1rem 0; border-top: 2px solid #0F251A; margin-top: 1rem;'>{client_data['saved_brief']}</div>", unsafe_allow_html=True)
                pdf_bytes = generate_pdf(client_data['name'], client_data['market'], client_data['address'], client_data['saved_brief'])
                st.download_button(label="Download Report as PDF", data=pdf_bytes, file_name=f"Praxis_{client_data['name'].replace(' ','_')}.pdf", mime="application/pdf")

    with tab2:
        st.markdown("<h2 style='text-align: left;'>Deal Stack Optimizer</h2>", unsafe_allow_html=True)
        col_dp, col_conc = st.columns(2)
        with col_dp: dp_pct = st.slider("Down Payment Allocation (%)", 0, 100, 20, step=5)
        with col_conc: concession = st.selectbox("Negotiated Concession", ["None (Standard Term)", "2-1 Rate Buydown (Year 1)", "1% Permanent Buydown", "3% Price Reduction"])
        
        eff_price = client_data['price'] * 0.97 if concession == "3% Price Reduction" else client_data['price']
        eff_rate = client_data['base_rate'] - 2.0 if concession == "2-1 Rate Buydown (Year 1)" else client_data['base_rate'] - 1.0 if concession == "1% Permanent Buydown" else client_data['base_rate']
        eff_rate = max(eff_rate, 1.0)
        
        base_pi = calc_mortgage(client_data['price'], client_data['base_rate'], dp_pct)
        new_pi = calc_mortgage(eff_price, eff_rate, dp_pct)
        
        tax_mo = (client_data['price'] * (client_data.get('tax_rate_override', 2.2)/100)) / 12
        ins_mo = (client_data['price'] * 0.005) / 12
        hoa_mo = client_data.get('hoa_override', 0)
        
        fig_bar = go.Figure(data=[
            go.Bar(name='Principal & Interest', x=['Standard Term', 'Optimized Strategy'], y=[base_pi, new_pi], marker_color='#0F251A'),
            go.Bar(name='Taxes & Insurance', x=['Standard Term', 'Optimized Strategy'], y=[tax_mo + ins_mo, tax_mo + ins_mo], marker_color='#C5A059'),
            go.Bar(name='HOA', x=['Standard Term', 'Optimized Strategy'], y=[hoa_mo, hoa_mo], marker_color='#E5E5E5')
        ])
        fig_bar.update_layout(barmode='stack', height=350, paper_bgcolor="#FBFBF9", plot_bgcolor="#FBFBF9", font=dict(family='Montserrat', color='#1A1A1A'), margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        
        base_total = base_pi + tax_mo + ins_mo + hoa_mo
        new_total = new_pi + tax_mo + ins_mo + hoa_mo
        
        s1, s2, s3 = st.columns(3)
        s1.metric("Optimized Total Monthly", f"${new_total:,.2f}", f"-${base_total - new_total:,.2f} / mo", delta_color="inverse")
        s2.metric("Effective Cost of Capital", f"{eff_rate:.3f}%")
        s3.metric("Cash to Close (Est.)", f"${(eff_price * (dp_pct/100)) + (eff_price * 0.03):,.0f}")

    with tab3:
        st.markdown("<h2 style='text-align: left;'>Market Capital Matrix</h2>", unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Absorption Rate", f"{round((market_info['inventory'] / (market_info['inventory']/3)), 1)} Months")
        r2.metric("Contract Fall-Through", "14.2%", "Systemic Risk Factor", delta_color="inverse")
        r3.metric("List-to-Sale Delta", "-2.4%")
