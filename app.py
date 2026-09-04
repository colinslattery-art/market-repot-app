import streamlit as st
import pandas as pd
import requests
import re
import sqlite3
import hashlib
import json
import uuid
from datetime import datetime
from google import genai
from fpdf import FPDF
import plotly.graph_objects as go

# --- CONFIG & CONSTANTS ---
st.set_page_config(page_title="Praxis Terminal", page_icon="🏛️", layout="wide")
DB_NAME = "praxis_saas.db"
THEME_LIGHT = {"primary": "#0F251A", "accent": "#C5A059", "bg": "#FBFBF9", "text": "#1A1A1A", "font_header": "Playfair Display", "font_body": "Montserrat"}
THEME_DARK = {"primary": "#C5A059", "accent": "#FBFBF9", "bg": "#121212", "text": "#EAEAEA", "font_header": "Playfair Display", "font_body": "Montserrat"}

def init_state():
    defaults = {"theme": THEME_LIGHT, "logged_in": False, "username": None, "role": None, "brokerage": None, "team": None, "display_name": None, "view_mode": "login", "wizard_step": 1, "temp_client": {}, "active_client_id": None}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
init_state()

def logout(): st.session_state.clear(); init_state(); st.rerun()

# --- CSS INJECTION ---
def render_css():
    t = st.session_state.theme
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400&display=swap');
            .stApp, .main, .block-container {{ background-color: {t['bg']} !important; }}
            html, body, p, span, label, li, td, th {{ font-family: '{t['font_body']}', sans-serif !important; color: {t['text']} !important; }}
            #MainMenu, footer, header {{visibility: hidden;}}
            h1, h2, h3 {{ font-family: '{t['font_header']}', serif !important; font-weight: 500 !important; color: {t['primary']} !important; letter-spacing: 0.02em !important; text-align: center; }}
            .brand-header {{ text-align: center; font-family: '{t['font_body']}', sans-serif; text-transform: uppercase; letter-spacing: 0.25em; font-size: 0.8rem; color: {t['accent']} !important; margin-bottom: 2rem; margin-top: 1rem; }}
            [data-testid="stForm"] {{ border: none !important; background-color: transparent !important; }}
            div[data-baseweb="input"] {{ background-color: transparent !important; border: none !important; border-bottom: 2px solid {t['primary']} !important; border-radius: 0 !important; }}
            div[data-baseweb="input"] > div {{ background-color: transparent !important; }}
            input {{ font-family: '{t['font_header']}', serif !important; font-size: 1.5rem !important; color: {t['text']} !important; -webkit-text-fill-color: {t['text']} !important; text-align: center !important; padding: 1rem !important; background-color: transparent !important; }}
            input::placeholder {{ color: #A0A0A0 !important; -webkit-text-fill-color: #A0A0A0 !important; font-family: '{t['font_body']}', sans-serif !important; font-size: 1rem !important; }}
            .client-card {{ background-color: transparent; border: 1px solid #EAEAEA; border-top: 3px solid {t['primary']}; padding: 1.5rem; text-align: center; transition: 0.3s; margin-bottom: 0.5rem; }}
            .client-card:hover {{ box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-top: 3px solid {t['accent']}; }}
            .client-card h3 {{ font-size: 1.5rem; margin-bottom: 0.5rem; color: {t['primary']}; }}
            .client-card p {{ font-size: 0.8rem; color: #777; text-transform: uppercase; letter-spacing: 0.1em; }}
            div[data-testid="metric-container"] {{ background-color: transparent !important; border: none !important; border-left: 2px solid {t['accent']} !important; padding: 0.5rem 1.5rem; box-shadow: none !important; }}
            div[data-testid="stMetricValue"] {{ font-family: '{t['font_header']}', serif; font-size: 2.2rem !important; font-weight: 500 !important; color: {t['primary']} !important; }}
            div[data-testid="stMetricLabel"] {{ font-size: 0.75rem !important; font-weight: 600 !important; color: {t['text']} !important; text-transform: uppercase; letter-spacing: 0.15em; opacity: 0.7; }}
            .stTabs [data-baseweb="tab-list"] {{ gap: 3rem; border-bottom: 1px solid #EAEAEA; justify-content: center; }}
            .stTabs [data-baseweb="tab"] {{ height: 4rem; background-color: transparent !important; color: {t['text']} !important; opacity: 0.6; font-weight: 500; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.15em; border-radius: 0; }}
            .stTabs [aria-selected="true"] {{ border-bottom: 2px solid {t['primary']} !important; color: {t['primary']} !important; font-weight: 600; opacity: 1; }}
            .stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {{ background-color: {t['primary']} !important; color: {t['bg']} !important; -webkit-text-fill-color: {t['bg']} !important; border: 1px solid {t['primary']} !important; border-radius: 0px !important; padding: 0.75rem 1.5rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.15em; transition: 0.4s; height: auto !important; min-height: 3rem; }}
            .stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover {{ background-color: {t['accent']} !important; border-color: {t['accent']} !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }}
            [data-testid="stFormSubmitButton"] {{ display: flex; justify-content: center; width: 100%; margin-top: 1.5rem; }}
            [data-testid="stFormSubmitButton"] > button {{ width: 250px !important; }}
            .dataframe {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
            .dataframe th {{ background-color: {t['primary']}; color: {t['bg']} !important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; padding: 1rem; letter-spacing: 0.1em; }}
            .dataframe td {{ padding: 1rem; border-bottom: 1px solid #EAEAEA; background-color: transparent; color: {t['text']} !important; }}
        </style>
    """, unsafe_allow_html=True)
render_css()

# --- DATABASE ENGINE ---
def hash_pw(pwd): return hashlib.sha256(pwd.encode()).hexdigest()
def get_conn(): return sqlite3.connect(DB_NAME)

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, brokerage TEXT, team TEXT, display_name TEXT, login_count INTEGER DEFAULT 0, last_login TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS clients (client_id TEXT PRIMARY KEY, agent_username TEXT, brokerage TEXT, team TEXT, client_name TEXT, market TEXT, target_price INTEGER, address TEXT, report_type TEXT, payload TEXT)''')
        c.execute("SELECT 1 FROM users WHERE username='admin'")
        if not c.fetchone():
            c.execute("INSERT INTO users (username, password, role, brokerage, team, display_name, login_count) VALUES (?, ?, ?, ?, ?, ?, ?)", ("admin", hash_pw("praxis2026"), "sysadmin", "GLOBAL", "GLOBAL", "System Administrator", 0))
        conn.commit()
init_db()

class DatabaseEngine:
    def authenticate(self, user, pwd):
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT role, brokerage, team, display_name FROM users WHERE username=? AND password=?", (user, hash_pw(pwd)))
            res = c.fetchone()
            if res:
                c.execute("UPDATE users SET login_count = login_count + 1, last_login = ? WHERE username = ?", (datetime.now().isoformat(), user))
                conn.commit()
                return {"role": res[0], "brokerage": res[1], "team": res[2], "display_name": res[3]}
        return None

    def add_user(self, user, pwd, role, brokerage, team, display_name):
        try:
            with get_conn() as conn:
                conn.execute("INSERT INTO users (username, password, role, brokerage, team, display_name, login_count) VALUES (?, ?, ?, ?, ?, ?, ?)", (user, hash_pw(pwd), role, brokerage, team, display_name, 0))
                conn.commit()
            return True
        except sqlite3.IntegrityError: return False

    def update_user_credentials(self, old_user, new_user, new_pwd, new_name):
        """Restored: Admin function to edit user login details and cascade updates to their files."""
        try:
            with get_conn() as conn:
                c = conn.cursor()
                if old_user != new_user:
                    c.execute("UPDATE users SET username=?, display_name=? WHERE username=?", (new_user, new_name, old_user))
                    c.execute("UPDATE clients SET agent_username=? WHERE agent_username=?", (new_user, old_user))
                else:
                    c.execute("UPDATE users SET display_name=? WHERE username=?", (new_name, old_user))
                
                if new_pwd and new_pwd.strip():
                    c.execute("UPDATE users SET password=? WHERE username=?", (hash_pw(new_pwd), new_user))
                conn.commit()
            return True
        except sqlite3.IntegrityError: return False

    def delete_user(self, user):
        """Deletes user account and associated client records."""
        with get_conn() as conn:
            conn.execute("DELETE FROM users WHERE username=?", (user,))
            conn.execute("DELETE FROM clients WHERE agent_username=?", (user,))
            conn.commit()

    def get_scoped_users(self, role, brokerage, team):
        with get_conn() as conn:
            if role == "sysadmin": return pd.read_sql_query("SELECT username, display_name, role, brokerage, team, login_count, last_login FROM users", conn)
            if role == "broker": return pd.read_sql_query(f"SELECT username, display_name, role, team, login_count FROM users WHERE brokerage='{brokerage}' AND role!='sysadmin'", conn)
            return pd.read_sql_query(f"SELECT username, display_name, role, login_count FROM users WHERE team='{team}' AND role='agent'", conn)

    def save_client(self, cid, user, brokerage, team, data):
        data['agent_owner'] = user
        with get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO clients (client_id, agent_username, brokerage, team, client_name, market, target_price, address, report_type, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (cid, user, brokerage, team, data['name'], data['market'], data['price'], data['address'], data['type'], json.dumps(data)))
            conn.commit()

    def get_scoped_clients(self, role, user, brokerage, team):
        with get_conn() as conn:
            c = conn.cursor()
            if role == "sysadmin": c.execute("SELECT client_id, agent_username, payload FROM clients")
            elif role == "broker": c.execute("SELECT client_id, agent_username, payload FROM clients WHERE brokerage=?", (brokerage,))
            elif role == "team_admin": c.execute("SELECT client_id, agent_username, payload FROM clients WHERE team=?", (team,))
            else: c.execute("SELECT client_id, agent_username, payload FROM clients WHERE agent_username=?", (user,))
            return [{"client_id": r[0], "agent": r[1], "data": json.loads(r[2])} for r in c.fetchall()]

    def get_client_by_id(self, cid):
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT payload FROM clients WHERE client_id=?", (cid,))
            row = c.fetchone()
            return json.loads(row[0]) if row else None
            
    def get_telemetry(self):
        with get_conn() as conn: return pd.read_sql_query("SELECT * FROM users", conn), pd.read_sql_query("SELECT * FROM clients", conn)

db = DatabaseEngine()

# --- MARKET DATA ENGINE ---
class MarketDataEngine:
    LOCAL = {"Westlake": {"income": 250000, "price": 1850000, "dom": 38, "inventory": 145}, "Southlake": {"income": 225000, "price": 1420000, "dom": 35, "inventory": 210}, "Frisco": {"income": 145000, "price": 710000, "dom": 39, "inventory": 620}, "Dallas": {"income": 63000, "price": 435000, "dom": 44, "inventory": 3400}, "Tyler": {"income": 61000, "price": 315000, "dom": 52, "inventory": 450}, "Lindale": {"income": 68000, "price": 325000, "dom": 45, "inventory": 110}}
    def validate_market(self, city):
        clean = city.title().split(',')[0].strip()
        return clean if clean in self.LOCAL else None
    def get_market_metrics(self, city):
        return self.LOCAL.get(self.validate_market(city))

engine = MarketDataEngine()
client = genai.Client(api_key=st.secrets.get("GEMINI_API_KEY", "")) if st.secrets.get("GEMINI_API_KEY") else None

@st.cache_data(ttl=86400)
def get_live_rate(): return 6.8
live_rate = get_live_rate()

def calc_mortgage(price, rate, dp_pct):
    loan = price * (1 - (dp_pct / 100))
    return loan * ((rate / 100) / 12 * (1 + (rate / 100) / 12)**360) / ((1 + (rate / 100) / 12)**360 - 1) if loan > 0 else 0

# --- PDF & AI LOGIC ---
def sanitize_pdf(text):
    for k, v in {'“':'"', '”':'"', '‘':"'", '’':"'", '—':'--', '–':'-', '…':'...'}.items(): text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

class PraxisPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10); self.set_text_color(15, 37, 26) 
        self.cell(0, 10, f"INTELLIGENCE REPORT | {st.session_state.get('brokerage', 'PRAXIS').upper()}", 0, 1, 'R')
        self.set_draw_color(197, 160, 89); self.line(10, 20, 200, 20); self.ln(10)
    def footer(self):
        self.set_y(-15); self.set_font('Helvetica', 'I', 8); self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(client_name, market, address, text):
    pdf = PraxisPDF(); pdf.add_page(); pdf.set_font('Helvetica', '', 11); pdf.set_text_color(30, 30, 30); pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, f"Prepared For: {sanitize_pdf(client_name)}  |  Target: {sanitize_pdf(address if address else market)}", 0, 1); pdf.ln(5)
    for line in sanitize_pdf(text).split('\n'):
        if not line.strip(): pdf.ln(4)
        elif line.startswith('##'):
            pdf.set_font('Helvetica', 'B', 12); pdf.set_text_color(15, 37, 26)
            pdf.multi_cell(0, 8, line.replace('#', '').strip()); pdf.set_font('Helvetica', '', 11); pdf.set_text_color(30, 30, 30)
        else: pdf.multi_cell(0, 6, line.replace('**', ''))
    return pdf.output(dest='S').encode('latin-1')

def run_ai(prompt, fallback="Error"):
    if not client: return "⚠️ API Key Missing."
    try: return client.models.generate_content(model='gemini-3.6-flash', contents=prompt).text
    except: return fallback

# ====================================================================
# VIEWS ROUTER
# ====================================================================
if not st.session_state.logged_in:
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-header'>SECURE ACCESS</div>", unsafe_allow_html=True)
    st.markdown("<h1>System Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Username", placeholder="Enter Username", label_visibility="collapsed")
            pwd = st.text_input("Password", type="password", placeholder="Enter Password", label_visibility="collapsed")
            if st.form_submit_button("Authenticate"):
                auth = db.authenticate(user, pwd)
                if auth:
                    st.session_state.update({"logged_in": True, "username": user, **auth, "view_mode": "hub" if auth['role'] == "agent" else "admin"})
                    st.rerun()
                else: st.error("Invalid credentials.")

elif st.session_state.role in ["sysadmin", "broker", "team_admin"] and st.session_state.view_mode == "admin":
    st.markdown(f"<div class='brand-header'>{st.session_state.brokerage} | {st.session_state.role.upper()}</div>", unsafe_allow_html=True)
    st.markdown("<h1>Command Center</h1>", unsafe_allow_html=True)
    _, col_out, _ = st.columns([2, 1, 2])
    with col_out: 
        if st.button("Log Out", use_container_width=True): logout()
    st.divider()
    
    t1, t2, t3 = st.tabs(["Agent Management & Provisioning", "Intelligence Portfolios", "System Theming & Analytics"])
    with t1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### Provision Accounts")
            with st.form("new_user"):
                n_user, n_pwd, n_name = st.text_input("Username"), st.text_input("Password", type="password"), st.text_input("Display Name")
                if st.session_state.role == "sysadmin":
                    n_brok, n_team = st.text_input("Brokerage Name", "Real Broker LLC"), st.text_input("Team Name", "Independent")
                    n_role = st.selectbox("Role", ["agent", "team_admin", "broker"])
                else:
                    n_brok, n_team = st.session_state.brokerage, (st.session_state.team if st.session_state.role == "team_admin" else st.text_input("Team Name", "Independent"))
                    n_role = st.selectbox("Role", ["agent", "team_admin"]) if st.session_state.role == "broker" else "agent"
                if st.form_submit_button("Provision Account"):
                    if db.add_user(n_user, n_pwd, n_role, n_brok, n_team, n_name): st.success("Created.")
                    else: st.error("Username exists.")
        with c2:
            st.markdown("### Active Scope Users")
            scoped_users = db.get_scoped_users(st.session_state.role, st.session_state.brokerage, st.session_state.team)
            st.dataframe(scoped_users, hide_index=True, use_container_width=True)

        st.divider()
        st.markdown("### Modify Existing User Credentials")
        user_list = [u for u in scoped_users['username'].tolist() if u != st.session_state.username]
        
        if user_list:
            c3, c4 = st.columns([1.5, 1])
            with c3:
                sel_user = st.selectbox("Select User Account to Modify", user_list)
                # Fetch existing record info
                user_row = scoped_users[scoped_users['username'] == sel_user].iloc[0]
                
                with st.form("edit_user_form"):
                    e_username = st.text_input("Username", value=sel_user)
                    e_display = st.text_input("Display Name", value=user_row['display_name'])
                    e_password = st.text_input("Reset Password", placeholder="Leave blank to keep current password", type="password")
                    
                    if st.form_submit_button("Save Credentials Update"):
                        if db.update_user_credentials(sel_user, e_username, e_password, e_display):
                            st.success(f"Account '{sel_user}' updated.")
                            st.rerun()
                        else:
                            st.error("Failed to update. Username may be taken.")
            with c4:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("Delete User & Purge Data", type="primary", use_container_width=True):
                    db.delete_user(sel_user)
                    st.warning(f"User '{sel_user}' deleted.")
                    st.rerun()
        else:
            st.info("No sub-accounts available to edit in your current scope.")

    with t2:
        st.markdown("### Portfolios")
        clients = db.get_scoped_clients(st.session_state.role, st.session_state.username, st.session_state.brokerage, st.session_state.team)
        if not clients: st.info("No data.")
        else:
            cols = st.columns(3)
            for idx, c in enumerate(clients):
                with cols[idx % 3]:
                    st.markdown(f"<div class='client-card'><h3>{c['data']['name']}</h3><p>AGENT: {c['agent']}<br>{c['data']['market']} | {c['data']['type']}</p></div>", unsafe_allow_html=True)
                    if st.button("Enter Dashboard ➔", key=f"dash_{c['client_id']}", use_container_width=True):
                        st.session_state.update({"active_client_id": c['client_id'], "view_mode": "sandbox"}); st.rerun()

    with t3:
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("### Dynamic UI (AI)")
            if prompt := st.chat_input("Make it ocean blue..."):
                with st.spinner("Rebuilding CSS..."):
                    res = run_ai(f"Respond ONLY with valid JSON (keys: primary, accent, bg, text, font_header, font_body) matching: {prompt}", "")
                    try: st.session_state.theme.update(json.loads(res.replace('```json', '').replace('```', '').strip())); st.rerun()
                    except: st.error("Theming failed.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Revert Default Theme", use_container_width=True): st.session_state.theme = THEME_LIGHT; st.rerun()
        with sc2:
            st.markdown("### Telemetry")
            if st.button("Generate Briefing", use_container_width=True):
                with st.spinner("Analyzing DB..."):
                    df_u, df_c = db.get_telemetry()
                    st.info(run_ai(f"Write a 2-paragraph SaaS admin briefing. Users: {len(df_u)}, Logins: {df_u['login_count'].sum() if not df_u.empty else 0}. Briefs: {len(df_c)}.", "Analytics offline."))

elif st.session_state.role == "agent" and st.session_state.view_mode == "hub":
    st.markdown("<div style='height: 5vh;'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-header'>{st.session_state.display_name.upper()} | {st.session_state.brokerage.upper()}</div>", unsafe_allow_html=True)
    st.markdown("<h1>Client Hub</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        c1, c2 = st.columns(2)
        with c1: 
            if st.button("New Client", use_container_width=True): st.session_state.update({"temp_client": {}, "wizard_step": 1, "view_mode": "wizard"}); st.rerun()
        with c2: 
            if st.button("Log Out", use_container_width=True): logout()
        st.divider(); st.markdown("<h3 style='text-align: center;'>ACTIVE PORTFOLIOS</h3>", unsafe_allow_html=True)
        clients = db.get_scoped_clients("agent", st.session_state.username, None, None)
        if not clients: st.info("No active clients.")
        else:
            for c in clients:
                st.markdown(f"<div class='client-card'><h3>{c['data']['name']}</h3><p>{c['data']['market']} | {c['data']['type']}</p></div>", unsafe_allow_html=True)
                if st.button(f"Load {c['data']['name']} ➔", key=f"ld_{c['client_id']}", use_container_width=True):
                    st.session_state.update({"active_client_id": c['client_id'], "view_mode": "sandbox"}); st.rerun()

elif st.session_state.role == "agent" and st.session_state.view_mode == "wizard":
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-header'>{st.session_state.display_name.upper()} | STRATEGY INTAKE</div>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        if st.session_state.wizard_step == 1:
            st.markdown("<h1>Client Name</h1>", unsafe_allow_html=True)
            with st.form("w1"):
                val = st.text_input("Name", label_visibility="collapsed")
                if st.form_submit_button("Next") and val.strip():
                    st.session_state.temp_client['name'] = val.title().strip()
                    st.session_state.wizard_step = 2; st.rerun()
        elif st.session_state.wizard_step == 2:
            st.markdown("<h1>Market Area</h1>", unsafe_allow_html=True)
            with st.form("w2"):
                val = st.text_input("Market", label_visibility="collapsed")
                if st.form_submit_button("Next"):
                    cln = engine.validate_market(val)
                    if cln: st.session_state.temp_client['market'] = cln; st.session_state.wizard_step = 3; st.rerun()
                    else: st.error("⚠️ Data Feed Error: No coverage.")
        elif st.session_state.wizard_step == 3:
            st.markdown("<h1>Price Point</h1>", unsafe_allow_html=True)
            with st.form("w3"):
                val = st.text_input("Price", value=f"${engine.get_market_metrics(st.session_state.temp_client['market'])['price']:,}", label_visibility="collapsed")
                if st.form_submit_button("Next"):
                    cln = re.sub(r'[^\d.]', '', val)
                    if cln: st.session_state.temp_client['price'] = int(float(cln)); st.session_state.wizard_step = 4; st.rerun()
        elif st.session_state.wizard_step == 4:
            st.markdown("<h1>Specific Target Property?</h1>", unsafe_allow_html=True)
            with st.form("w4"):
                val = st.text_input("Addr", placeholder="(Optional)", label_visibility="collapsed")
                if st.form_submit_button("Next / Skip"): st.session_state.temp_client['address'] = val.strip(); st.session_state.wizard_step = 5; st.rerun()
        elif st.session_state.wizard_step == 5:
            st.markdown("<h1>Strategic Focus</h1>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            for col, lbl, typ in zip([c1, c2, c3], ["Buyer Advisory", "Seller Strategy", "Investor Memo"], ["Buyer Advisory Brief", "Seller Disposition Strategy", "Investor Acquisition Memo"]):
                with col:
                    if st.button(lbl, use_container_width=True): 
                        st.session_state.temp_client.update({'type': typ, 'base_rate': live_rate, 'tax_rate_override': 2.2, 'hoa_override': 0, 'saved_brief': ""})
                        cid = str(uuid.uuid4()); db.save_client(cid, st.session_state.username, st.session_state.brokerage, st.session_state.team, st.session_state.temp_client)
                        st.session_state.update({"active_client_id": cid, "view_mode": "sandbox"}); st.rerun()

elif st.session_state.view_mode == "sandbox":
    cid = st.session_state.active_client_id
    cd = db.get_client_by_id(cid)
    own = cd.get('agent_owner', st.session_state.username)
    mi = engine.get_market_metrics(cd['market'])
    
    with st.sidebar:
        st.markdown(f"<h2 style='text-align: center; color:{st.session_state.theme['primary']} !important;'>PRAXIS</h2>", unsafe_allow_html=True)
        if st.button("⬅ Hub", use_container_width=True): st.session_state.view_mode = "admin" if st.session_state.role != "agent" else "hub"; st.rerun()
        st.divider()
        if st.radio("UI", ["Light", "Dark"], index=0 if st.session_state.theme['bg'] == '#FBFBF9' else 1, horizontal=True) == "Dark" and st.session_state.theme['bg'] != '#121212':
            st.session_state.theme = THEME_DARK; st.rerun()
        elif st.session_state.theme['bg'] != '#FBFBF9' and st.session_state.theme['bg'] != '#121212': pass
        elif st.session_state.theme['bg'] == '#121212': st.session_state.theme = THEME_LIGHT; st.rerun()
            
        st.divider(); st.markdown("### Overrides")
        nt = st.selectbox("Mode", ["Buyer Advisory Brief", "Seller Disposition Strategy", "Investor Acquisition Memo"], index=["Buyer Advisory Brief", "Seller Disposition Strategy", "Investor Acquisition Memo"].index(cd['type']))
        np = st.number_input("Price ($)", value=cd['price'], step=10000)
        nr = st.number_input("Rate (%)", value=cd['base_rate'], step=0.125)
        nx = st.number_input("Tax Rate (%)", value=cd.get('tax_rate_override', 2.2), step=0.1)
        nh = st.number_input("HOA ($/mo)", value=cd.get('hoa_override', 0), step=10)
        
        if any([nt!=cd['type'], np!=cd['price'], nr!=cd['base_rate'], nx!=cd.get('tax_rate_override'), nh!=cd.get('hoa_override')]):
            cd.update({'type': nt, 'price': np, 'base_rate': nr, 'tax_rate_override': nx, 'hoa_override': nh})
            db.save_client(cid, own, st.session_state.brokerage, st.session_state.team, cd); st.rerun()

    st.markdown(f"<div class='brand-header'>{st.session_state.display_name.upper()}</div>", unsafe_allow_html=True)
    st.markdown(f"<h1>{(cd['address'] if cd['address'] else cd['market']).title()}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #777;'>Prepared for: <strong>{cd['name']}</strong> | Strategy: <strong>{cd['type']}</strong></p>", unsafe_allow_html=True)
    
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Asset Value", f"${cd['price']:,}"); b2.metric("Tax Rate", f"{cd.get('tax_rate_override', 2.2):.2f}%")
    b3.metric("Monthly HOA", f"${cd.get('hoa_override', 0):,.0f}"); b4.metric("Velocity", f"{mi['dom']} Days")
    st.divider()

    f_scr = min(round((calc_mortgage(cd['price'], cd['base_rate'], 20) * 12 / mi['income']) * 20, 1), 10.0)

    t1, t2, t3 = st.tabs(["Strategy Brief", "Deal Stack Optimizer", "Capital Matrix"])
    with t1:
        c1, c2 = st.columns([1, 1.5])
        with c1:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=f_scr, title={'text': "Friction", 'font': {'color': st.session_state.theme['accent']}}, gauge={'axis': {'range': [None, 10]}, 'bar': {'color': st.session_state.theme['primary']}, 'bgcolor': "transparent", 'steps': [{'range': [0, 4], 'color': '#E5F0EA'}, {'range': [4, 7], 'color': '#FDF3E1'}, {'range': [7, 10], 'color': '#FCE8E8'}]}))
            fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig, use_container_width=True)
        with c2:
            if st.button("Generate Executive Brief", use_container_width=True):
                with st.spinner("Authoring..."):
                    cd['saved_brief'] = run_ai(f"Act as {st.session_state.display_name}, luxury Realtor. Client: {cd['name']}. Type: {cd['type']}. Target: {cd['address'] or cd['market']}. Price: ${cd['price']}. Rate: {cd['base_rate']}%. Friction: {f_scr}/10. Tone: Polished. No emojis. Sections: MACRO DYNAMICS, MARKET HEALTH, STRATEGIC PLAYBOOK.")
                    db.save_client(cid, own, st.session_state.brokerage, st.session_state.team, cd); st.rerun()
            if cd.get('saved_brief'):
                st.markdown(f"<div style='border-top: 2px solid {st.session_state.theme['primary']}; padding-top:1rem;'>{cd['saved_brief']}</div>", unsafe_allow_html=True)
                st.download_button("Download PDF", generate_pdf(cd['name'], cd['market'], cd['address'], cd['saved_brief']), f"Praxis_{cd['name']}.pdf", "application/pdf")
    with t2:
        col_dp, col_conc = st.columns(2)
        with col_dp: dp = st.slider("Down Payment (%)", 0, 100, 20, step=5)
        with col_conc: conc = st.selectbox("Concession", ["None", "2-1 Rate Buydown", "1% Permanent Buydown", "3% Price Reduction"])
        ep = cd['price'] * 0.97 if "Price" in conc else cd['price']
        er = cd['base_rate'] - 2.0 if "2-1" in conc else cd['base_rate'] - 1.0 if "1%" in conc else cd['base_rate']
        
        bp, np = calc_mortgage(cd['price'], cd['base_rate'], dp), calc_mortgage(ep, max(er, 1.0), dp)
        tm, im, hm = (cd['price'] * (cd.get('tax_rate_override', 2.2)/100))/12, (cd['price']*0.005)/12, cd.get('hoa_override', 0)
        
        f2 = go.Figure(data=[
            go.Bar(name='P&I', x=['Standard', 'Optimized'], y=[bp, np], marker_color=st.session_state.theme['primary']),
            go.Bar(name='Tax/Ins', x=['Standard', 'Optimized'], y=[tm+im, tm+im], marker_color=st.session_state.theme['accent']),
            go.Bar(name='HOA', x=['Standard', 'Optimized'], y=[hm, hm], marker_color='#E5E5E5')
        ])
        f2.update_layout(barmode='stack', height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': st.session_state.theme['text']})
        st.plotly_chart(f2, use_container_width=True)
        s1, s2, s3 = st.columns(3)
        s1.metric("Optimized Monthly", f"${np+tm+im+hm:,.2f}", f"-${(bp+tm+im+hm) - (np+tm+im+hm):,.2f}", "inverse")
        s2.metric("Effective Rate", f"{max(er, 1.0):.3f}%"); s3.metric("Cash to Close", f"${(ep*(dp/100))+(ep*0.03):,.0f}")
    with t3:
        r1, r2, r3 = st.columns(3)
        r1.metric("Absorption Rate", f"{round((mi['inventory'] / (mi['inventory']/3)), 1)} Months")
        r2.metric("Fall-Through", "14.2%", "Risk Factor", "inverse")
        r3.metric("List-to-Sale", "-2.4%")
