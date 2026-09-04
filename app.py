import streamlit as st
import pandas as pd
import requests
import re
import sqlite3
import hashlib
import json
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
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
    defaults = {
        "theme": THEME_LIGHT, 
        "logged_in": False, 
        "username": None, 
        "role": None, 
        "brokerage": None, 
        "team": None, 
        "display_name": None, 
        "email": None,
        "view_mode": "login", 
        "wizard_step": 1, 
        "temp_client": {}, 
        "active_client_id": None,
        "return_to": "hub"
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
init_state()

def logout(): 
    st.session_state.clear()
    init_state()
    st.rerun()

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
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     username TEXT PRIMARY KEY, password TEXT, role TEXT, brokerage TEXT, 
                     team TEXT, display_name TEXT, login_count INTEGER DEFAULT 0, last_login TEXT,
                     email TEXT, smtp_server TEXT, smtp_port INTEGER, smtp_user TEXT, smtp_pass TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS clients (
                     client_id TEXT PRIMARY KEY, agent_username TEXT, brokerage TEXT, team TEXT, 
                     client_name TEXT, market TEXT, target_price INTEGER, address TEXT, report_type TEXT, 
                     share_token TEXT, payload TEXT)''')
        
        try:
            c.execute("ALTER TABLE users ADD COLUMN email TEXT")
            c.execute("ALTER TABLE users ADD COLUMN smtp_server TEXT")
            c.execute("ALTER TABLE users ADD COLUMN smtp_port INTEGER")
            c.execute("ALTER TABLE users ADD COLUMN smtp_user TEXT")
            c.execute("ALTER TABLE users ADD COLUMN smtp_pass TEXT")
        except sqlite3.OperationalError: pass

        c.execute("SELECT 1 FROM users WHERE username='admin'")
        if not c.fetchone():
            c.execute("INSERT INTO users (username, password, role, brokerage, team, display_name, login_count) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      ("admin", hash_pw("praxis2026"), "sysadmin", "GLOBAL", "GLOBAL", "System Administrator", 0))
        conn.commit()
init_db()

class DatabaseEngine:
    def authenticate(self, user, pwd):
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT role, brokerage, team, display_name, email FROM users WHERE username=? AND password=?", (user, hash_pw(pwd)))
            res = c.fetchone()
            if res:
                c.execute("UPDATE users SET login_count = login_count + 1, last_login = ? WHERE username = ?", (datetime.now().isoformat(), user))
                conn.commit()
                return {"role": res[0], "brokerage": res[1], "team": res[2], "display_name": res[3], "email": res[4]}
        return None

    def add_user(self, user, pwd, role, brokerage, team, display_name, email=None):
        try:
            with get_conn() as conn:
                conn.execute("INSERT INTO users (username, password, role, brokerage, team, display_name, email, login_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                             (user, hash_pw(pwd), role, brokerage, team, display_name, email, 0))
                conn.commit()
            return True
        except sqlite3.IntegrityError: return False

    def update_user_credentials(self, old_user, new_user, new_pwd, new_name):
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

    def update_agent_email_settings(self, username, email, smtp_server, smtp_port, smtp_user, smtp_pass):
        with get_conn() as conn:
            conn.execute("UPDATE users SET email=?, smtp_server=?, smtp_port=?, smtp_user=?, smtp_pass=? WHERE username=?", 
                      (email, smtp_server, smtp_port, smtp_user, smtp_pass, username))
            conn.commit()

    def get_user_email_settings(self, username):
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT display_name, email, brokerage, smtp_server, smtp_port, smtp_user, smtp_pass FROM users WHERE username=?", (username,))
            res = c.fetchone()
            if res:
                return {"display_name": res[0], "email": res[1], "brokerage": res[2], "smtp_server": res[3], "smtp_port": res[4], "smtp_user": res[5], "smtp_pass": res[6]}
            return {}

    def delete_user(self, user):
        with get_conn() as conn:
            conn.execute("DELETE FROM users WHERE username=?", (user,))
            conn.execute("DELETE FROM clients WHERE agent_username=?", (user,))
            conn.commit()

    def get_scoped_users(self, role, brokerage, team):
        with get_conn() as conn:
            if role == "sysadmin": return pd.read_sql_query("SELECT username, display_name, email, role, brokerage, team, login_count, last_login FROM users", conn)
            if role == "broker": return pd.read_sql_query(f"SELECT username, display_name, email, role, team, login_count FROM users WHERE brokerage='{brokerage}' AND role!='sysadmin'", conn)
            return pd.read_sql_query(f"SELECT username, display_name, email, role, login_count FROM users WHERE team='{team}' AND role='agent'", conn)

    def save_client(self, cid, user, brokerage, team, data):
        data['agent_owner'] = user
        if 'share_token' not in data or not data['share_token']:
            data['share_token'] = str(uuid.uuid4())[:8]
        with get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO clients (client_id, agent_username, brokerage, team, client_name, market, target_price, address, report_type, share_token, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                         (cid, user, brokerage, team, data['name'], data['market'], data['price'], data['address'], data['type'], data['share_token'], json.dumps(data)))
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

    def get_client_by_token(self, token):
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT payload, brokerage FROM clients WHERE share_token=?", (token,))
            row = c.fetchone()
            if row:
                d = json.loads(row[0])
                d['brokerage_header'] = row[1]
                return d
            return None
            
    def get_telemetry(self):
        with get_conn() as conn: return pd.read_sql_query("SELECT * FROM users", conn), pd.read_sql_query("SELECT * FROM clients", conn)

db = DatabaseEngine()

# --- DYNAMIC EMAIL ENGINE ---
def send_report_email(agent_username, recipient_email, client_name, share_link, pdf_bytes):
    agent_info = db.get_user_email_settings(agent_username)
    agent_display_name = agent_info.get("display_name", agent_username)
    agent_email = agent_info.get("email", None)
    brokerage = agent_info.get("brokerage", "PRAXIS TERMINAL")

    if agent_info.get("smtp_server") and agent_info.get("smtp_user") and agent_info.get("smtp_pass"):
        smtp_server = agent_info["smtp_server"]
        smtp_port = agent_info.get("smtp_port") or 587
        smtp_user = agent_info["smtp_user"]
        smtp_pass = agent_info["smtp_pass"]
        sender_header = f"{agent_display_name} <{agent_email or smtp_user}>"
        reply_to_email = agent_email or smtp_user
    else:
        smtp_server = st.secrets.get("SMTP_SERVER", None)
        smtp_port = st.secrets.get("SMTP_PORT", 587)
        smtp_user = st.secrets.get("SMTP_USERNAME", None)
        smtp_pass = st.secrets.get("SMTP_PASSWORD", None)
        sender_header = f"{agent_display_name} via Praxis <{smtp_user}>"
        reply_to_email = agent_email or smtp_user

    if not all([smtp_server, smtp_user, smtp_pass]): return False, "SMTP delivery server is not configured."

    msg = MIMEMultipart()
    msg['From'] = sender_header
    msg['To'] = recipient_email
    if reply_to_email: msg['Reply-To'] = reply_to_email
    msg['Subject'] = f"Executive Advisory Brief | {client_name}"

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1A1A1A; line-height: 1.6;">
        <div style="background-color: #0F251A; padding: 20px; text-align: center; color: #C5A059;">
            <h2 style="margin: 0; font-family: Georgia, serif;">{brokerage.upper()}</h2>
            <p style="margin: 5px 0 0 0; font-size: 12px; letter-spacing: 2px;">REAL ESTATE ADVISORY</p>
        </div>
        <div style="padding: 30px; background-color: #FBFBF9;">
            <p>Dear {client_name},</p>
            <p>Your customized real estate strategy brief and market analysis is complete.</p>
            <p>You may download the attached PDF or access your interactive portal using the link below:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{share_link}" style="background-color: #0F251A; color: #FBFBF9; padding: 12px 25px; text-decoration: none; font-weight: bold;">VIEW INTERACTIVE PORTAL</a>
            </p>
            <p>Best regards,<br><strong>{agent_display_name}</strong><br>{brokerage}</p>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))
    pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_attachment.add_header('Content-Disposition', 'attachment', filename=f"Praxis_{client_name.replace(' ', '_')}.pdf")
    msg.attach(pdf_attachment)

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True, f"Brief successfully sent to {recipient_email}."
    except Exception as e: return False, f"SMTP Delivery Error: {e}"

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
    pdf = PraxisPDF(); pdf.add_page(); pdf.set_font('Helvetica', '', 10); pdf.set_text_color(30, 30, 30)
    pdf.set_fill_color(245, 245, 240); pdf.rect(10, 25, 190, 28, 'F')
    
    pdf.set_xy(14, 28); pdf.set_font('Helvetica', 'B', 10); pdf.set_text_color(15, 37, 26)
    pdf.cell(90, 6, f"PREPARED FOR: {sanitize_pdf(client_name).upper()}", 0, 0)
    pdf.cell(90, 6, f"LOCATION: {sanitize_pdf(address if address else market).upper()}", 0, 1)
    
    pdf.set_x(14); pdf.set_font('Helvetica', '', 9); pdf.set_text_color(100, 100, 100)
    pdf.cell(90, 6, f"DATE: {datetime.now().strftime('%B %d, %Y').upper()}", 0, 0)
    pdf.cell(90, 6, f"CLASSIFICATION: CONFIDENTIAL ADVISORY", 0, 1)
    pdf.ln(12)

    clean_text = sanitize_pdf(text)
    for line in clean_text.split('\n'):
        line_str = line.strip()
        if not line_str: pdf.ln(3)
        elif line_str.startswith('##'):
            pdf.ln(4); pdf.set_font('Helvetica', 'B', 12); pdf.set_text_color(15, 37, 26)
            pdf.cell(0, 8, line_str.replace('#', '').strip().upper(), 0, 1)
            pdf.set_draw_color(197, 160, 89); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(4)
            pdf.set_font('Helvetica', '', 10); pdf.set_text_color(40, 40, 40)
        elif line_str.startswith('*') or line_str.startswith('-'):
            pdf.set_font('Helvetica', '', 10); pdf.set_text_color(40, 40, 40)
            clean_bullet = line_str.lstrip('*- ').replace('**', '')
            pdf.multi_cell(0, 5, f"   * {clean_bullet}"); pdf.ln(2)
        else:
            pdf.set_font('Helvetica', '', 10); pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 5, line_str.replace('**', '')); pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1')

def generate_strategy_memo(agent_name, client_name, report_type, sub_market, property_address, target_price, interest_rate, friction_score):
    if not client: return "⚠️ API Key Missing."
    target_context = f"Property: {property_address}" if property_address else f"Sub-Market: {sub_market}"
    prompt = f"""
    You are {agent_name}, an elite luxury real estate strategist and advisor.
    Write a clean, highly polished executive advisory memo based strictly on this data:
    - Client Name: {client_name}
    - Strategic Focus: {report_type}
    - Location: {target_context}
    - Asset Value / Price Point: ${target_price:,}
    - Cost of Capital (Rate): {interest_rate}%
    - Market Friction Score: {friction_score}/10

    STRICT FORMATTING RULES:
    1. Do NOT write a run-on block of text. Use double returns between paragraphs.
    2. Format all major section titles using Markdown H2 tags (e.g., `## MACRO DYNAMICS`).
    3. Use bold bullet points for key takeaways and tactical phases.
    4. Tone: Institutional, authoritative, analytical, and highly professional. DO NOT use emojis.

    REQUIRED SECTIONS:
    ## EXECUTIVE OVERVIEW
    ## MACRO DYNAMICS
    ## MARKET HEALTH & FRICTION ANALYSIS
    ## STRATEGIC PLAYBOOK
    """
    try: return client.models.generate_content(model='gemini-3.6-flash', contents=prompt).text
    except Exception as e: return f"Error authoring strategy brief: {e}"

def run_ai(prompt, fallback="Error"):
    if not client: return "⚠️ API Key Missing."
    try: return client.models.generate_content(model='gemini-3.6-flash', contents=prompt).text
    except: return fallback

def clean_json_res(raw_text): return raw_text.replace("```json", "").replace("```", "").strip()

# ====================================================================
# VIEWS ROUTER
# ====================================================================

# PUBLIC READ-ONLY TOKEN ROUTING
query_params = st.query_params
if "token" in query_params:
    public_token = query_params["token"]
    client_public_data = db.get_client_by_token(public_token)
    if client_public_data:
        st.markdown(f"<div class='brand-header'>{client_public_data.get('brokerage_header', 'PRAXIS TERMINAL')} | EXECUTIVE BRIEF</div>", unsafe_allow_html=True)
        st.markdown(f"<h1>{(client_public_data['address'] if client_public_data['address'] else client_public_data['market']).title()}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #777;'>Prepared for: <strong>{client_public_data['name']}</strong> | Strategy: <strong>{client_public_data['type']}</strong></p>", unsafe_allow_html=True)
        st.divider()
        
        mi = engine.get_market_metrics(client_public_data['market'])
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Asset Value", f"${client_public_data['price']:,}"); b2.metric("Tax Rate", f"{client_public_data.get('tax_rate_override', 2.2):.2f}%")
        b3.metric("Monthly HOA", f"${client_public_data.get('hoa_override', 0):,.0f}"); b4.metric("Velocity", f"{mi['dom']} Days")
        st.divider()

        st.markdown("### Strategy Memo")
        if client_public_data.get('saved_brief'):
            st.markdown(f"<div style='border-top: 2px solid #0F251A; padding-top:1rem;'>{client_public_data['saved_brief']}</div>", unsafe_allow_html=True)
            pdf_b = generate_pdf(client_public_data['name'], client_public_data['market'], client_public_data['address'], client_public_data['saved_brief'])
            st.download_button("Download Official PDF", pdf_b, f"Praxis_{client_public_data['name']}.pdf", "application/pdf")
        else: st.info("The advisory memo for this portfolio is currently being authored.")
        st.stop()
    else:
        st.error("Invalid or expired share token."); st.stop()

# AUTHENTICATED PORTAL ROUTING
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
    c_hdr1, c_hdr2, c_hdr3 = st.columns([4, 1.5, 1])
    with c_hdr1: st.markdown(f"<div class='brand-header' style='text-align:left;'>{st.session_state.brokerage} | {st.session_state.role.upper()}</div>", unsafe_allow_html=True)
    with c_hdr2:
        if st.button("My Personal Hub", use_container_width=True): st.session_state.view_mode = "hub"; st.rerun()
    with c_hdr3:
        if st.button("Log Out", key="admin_top_logout", use_container_width=True): logout()
            
    st.markdown("<h1>Command Center</h1>", unsafe_allow_html=True)
    st.divider()
    
    t1, t2, t3 = st.tabs(["Agent Management & Provisioning", "Intelligence Portfolios", "System Theming & Analytics"])
    with t1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### Provision Accounts")
            with st.form("new_user"):
                n_user, n_pwd, n_name = st.text_input("Username"), st.text_input("Password", type="password"), st.text_input("Display Name")
                n_email = st.text_input("Agent Email", placeholder="agent@realbroker.com")
                if st.session_state.role == "sysadmin":
                    n_brok, n_team = st.text_input("Brokerage Name", "Real Broker LLC"), st.text_input("Team Name", "Independent")
                    n_role = st.selectbox("Role", ["agent", "team_admin", "broker"])
                else:
                    n_brok, n_team = st.session_state.brokerage, (st.session_state.team if st.session_state.role == "team_admin" else st.text_input("Team Name", "Independent"))
                    n_role = st.selectbox("Role", ["agent", "team_admin"]) if st.session_state.role == "broker" else "agent"
                if st.form_submit_button("Provision Account"):
                    if db.add_user(n_user, n_pwd, n_role, n_brok, n_team, n_name, n_email): st.success("Created.")
                    else: st.error("Username exists.")
        with c2:
            st.markdown("### Active Scope Users")
            scoped_users = db.get_scoped_users(st.session_state.role, st.session_state.brokerage, st.session_state.team)
            st.dataframe(scoped_users, hide_index=True, use_container_width=True)

        st.divider(); st.markdown("### Modify Existing User Credentials")
        user_list = [u for u in scoped_users['username'].tolist() if u != st.session_state.username]
        if user_list:
            c3, c4 = st.columns([1.5, 1])
            with c3:
                sel_user = st.selectbox("Select User Account to Modify", user_list)
                user_row = scoped_users[scoped_users['username'] == sel_user].iloc[0]
                with st.form("edit_user_form"):
                    e_username, e_display = st.text_input("Username", value=sel_user), st.text_input("Display Name", value=user_row['display_name'])
                    e_password = st.text_input("Reset Password", placeholder="Leave blank to keep current password", type="password")
                    if st.form_submit_button("Save Credentials Update"):
                        if db.update_user_credentials(sel_user, e_username, e_password, e_display): st.success("Updated."); st.rerun()
                        else: st.error("Failed. Username taken.")
            with c4:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("Delete User & Purge Data", type="primary", use_container_width=True): db.delete_user(sel_user); st.warning("Deleted."); st.rerun()
        else: st.info("No sub-accounts available.")

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
                        st.session_state.update({"active_client_id": c['client_id'], "view_mode": "sandbox", "return_to": "admin"}); st.rerun()

    with t3:
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("### Dynamic UI (AI)")
            if prompt := st.chat_input("Make it ocean blue..."):
                with st.spinner("Rebuilding CSS..."):
                    res = run_ai(f"Respond ONLY with valid JSON (keys: primary, accent, bg, text, font_header, font_body) matching: {prompt}", "")
                    try: st.session_state.theme.update(json.loads(clean_json_res(res))); st.rerun()
                    except: st.error("Theming failed.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Revert Default Theme", use_container_width=True): st.session_state.theme = THEME_LIGHT; st.rerun()
        with sc2:
            st.markdown("### Telemetry")
            if st.button("Generate Briefing", use_container_width=True):
                with st.spinner("Analyzing DB..."):
                    df_u, df_c = db.get_telemetry()
                    st.info(run_ai(f"Write a 2-paragraph SaaS admin briefing. Users: {len(df_u)}, Logins: {df_u['login_count'].sum() if not df_u.empty else 0}. Briefs: {len(df_c)}.", "Analytics offline."))

elif st.session_state.role in ["agent", "sysadmin", "broker", "team_admin"] and st.session_state.view_mode == "hub":
    if st.session_state.role != "agent":
        c_hdr1, c_hdr2, c_hdr3 = st.columns([4, 1.5, 1])
        with c_hdr1: st.markdown(f"<div class='brand-header' style='text-align:left;'>{st.session_state.display_name.upper()} | {st.session_state.brokerage.upper()}</div>", unsafe_allow_html=True)
        with c_hdr2:
            if st.button("Command Center", use_container_width=True): st.session_state.view_mode = "admin"; st.rerun()
        with c_hdr3:
            if st.button("Log Out", key="agent_top_logout", use_container_width=True): logout()
    else:
        c_hdr1, c_hdr2 = st.columns([5, 1])
        with c_hdr1: st.markdown(f"<div class='brand-header' style='text-align:left;'>{st.session_state.display_name.upper()} | {st.session_state.brokerage.upper()}</div>", unsafe_allow_html=True)
        with c_hdr2:
            if st.button("Log Out", key="agent_top_logout", use_container_width=True): logout()

    st.markdown("<h1>Client Hub</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown(f"<h2 style='text-align: center; color:{st.session_state.theme['primary']} !important;'>PRAXIS</h2>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; color: {st.session_state.theme['accent']} !important; font-size: 0.75rem; letter-spacing: 0.1em; margin-bottom: 1rem;'>AGENT PROFILE</div>", unsafe_allow_html=True)
        
        agent_cfg = db.get_user_email_settings(st.session_state.username)
        with st.expander("Email & Custom SMTP Settings"):
            with st.form("agent_smtp_form"):
                cfg_email = st.text_input("Contact Email", value=agent_cfg.get("email") or "")
                cfg_server = st.text_input("Custom SMTP Host", value=agent_cfg.get("smtp_server") or "", placeholder="e.g. smtp.gmail.com")
                cfg_port = st.number_input("SMTP Port", value=int(agent_cfg.get("smtp_port") or 587))
                cfg_user = st.text_input("SMTP Username", value=agent_cfg.get("smtp_user") or "")
                cfg_pass = st.text_input("SMTP Password", value=agent_cfg.get("smtp_pass") or "", type="password")
                if st.form_submit_button("Save Email Settings"):
                    db.update_agent_email_settings(st.session_state.username, cfg_email, cfg_server, cfg_port, cfg_user, cfg_pass)
                    st.session_state.email = cfg_email; st.success("Updated."); st.rerun()

    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        if st.button("+ New Client", use_container_width=True): st.session_state.update({"temp_client": {}, "wizard_step": 1, "view_mode": "wizard"}); st.rerun()
        st.divider(); st.markdown("<h3 style='text-align: center;'>ACTIVE PORTFOLIOS</h3>", unsafe_allow_html=True)
        
        # Uses standard "agent" role fetch to ONLY pull their personally created files
        clients = db.get_scoped_clients("agent", st.session_state.username, None, None)
        if not clients: st.info("No active clients.")
        else:
            for c in clients:
                st.markdown(f"<div class='client-card'><h3>{c['data']['name']}</h3><p>{c['data']['market']} | {c['data']['type']}</p></div>", unsafe_allow_html=True)
                if st.button(f"Load {c['data']['name']} ➔", key=f"ld_{c['client_id']}", use_container_width=True):
                    st.session_state.update({"active_client_id": c['client_id'], "view_mode": "sandbox", "return_to": "hub"}); st.rerun()

elif st.session_state.view_mode == "wizard":
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-header'>{st.session_state.display_name.upper()} | STRATEGY INTAKE</div>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        if st.session_state.wizard_step == 1:
            st.markdown("<h1>Client Name</h1>", unsafe_allow_html=True)
            with st.form("w1"):
                val = st.text_input("Name", label_visibility="collapsed")
                if st.form_submit_button("Next") and val.strip():
                    st.session_state.temp_client['name'] = val.title().strip(); st.session_state.wizard_step = 2; st.rerun()
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
                        st.session_state.temp_client.update({'type': typ, 'base_rate': live_rate, 'tax_rate_override': 2.2, 'hoa_override': 0, 'saved_brief': "", 'share_token': str(uuid.uuid4())[:8]})
                        cid = str(uuid.uuid4()); db.save_client(cid, st.session_state.username, st.session_state.brokerage, st.session_state.team, st.session_state.temp_client)
                        st.session_state.update({"active_client_id": cid, "view_mode": "sandbox", "return_to": "hub"}); st.rerun()

elif st.session_state.view_mode == "sandbox":
    cid = st.session_state.active_client_id
    cd = db.get_client_by_id(cid)
    own = cd.get('agent_owner', st.session_state.username)
    mi = engine.get_market_metrics(cd['market'])
    
    with st.sidebar:
        st.markdown(f"<h2 style='text-align: center; color:{st.session_state.theme['primary']} !important;'>PRAXIS</h2>", unsafe_allow_html=True)
        if st.button("⬅ Return", use_container_width=True): 
            st.session_state.view_mode = st.session_state.get("return_to", "hub")
            st.rerun()
            
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
            
        st.divider()
        if st.button("Log Out", key="sandbox_sidebar_logout", use_container_width=True): logout()

    st.markdown(f"<div class='brand-header'>{st.session_state.display_name.upper()}</div>", unsafe_allow_html=True)
    st.markdown(f"<h1>{(cd['address'] if cd['address'] else cd['market']).title()}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #777;'>Prepared for: <strong>{cd['name']}</strong> | Strategy: <strong>{cd['type']}</strong></p>", unsafe_allow_html=True)
    
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Asset Value", f"${cd['price']:,}"); b2.metric("Tax Rate", f"{cd.get('tax_rate_override', 2.2):.2f}%")
    b3.metric("Monthly HOA", f"${cd.get('hoa_override', 0):,.0f}"); b4.metric("Velocity", f"{mi['dom']} Days")
    st.divider()

    f_scr = min(round((calc_mortgage(cd['price'], cd['base_rate'], 20) * 12 / mi['income']) * 20, 1), 10.0)

    t1, t2, t3, t4 = st.tabs(["Strategy Brief", "Deal Stack Optimizer", "Capital Matrix", "Lead Distribution"])
    
    with t1:
        c1, c2 = st.columns([1, 1.5])
        with c1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=f_scr, title={'text': "Friction", 'font': {'color': st.session_state.theme['accent']}}, 
                gauge={'axis': {'range': [0, 10]}, 'bar': {'color': st.session_state.theme['primary']}, 'bgcolor': "rgba(0,0,0,0)", 'steps': [{'range': [0, 4], 'color': '#E5F0EA'}, {'range': [4, 7], 'color': '#FDF3E1'}, {'range': [7, 10], 'color': '#FCE8E8'}]}
            ))
            fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig, use_container_width=True)
        with c2:
            if st.button("Generate Executive Brief", use_container_width=True):
                with st.spinner("Authoring..."):
                    cd['saved_brief'] = generate_strategy_memo(st.session_state.display_name, cd['name'], cd['type'], cd['market'], cd['address'], cd['price'], cd['base_rate'], f_scr)
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

    with t4:
        st.markdown("### Client Delivery & Tokenized Share")
        base_app_url = st.secrets.get("BASE_URL", "https://your-app.streamlit.app")
        token = cd.get("share_token", "default")
        share_url = f"{base_app_url}/?token={token}"
        
        st.text_input("Read-Only Client Access URL", value=share_url)
        st.divider()
        
        st.markdown("### Email Advisory Brief Directly")
        with st.form("email_delivery_form"):
            recipient = st.text_input("Client Email Address", placeholder="client@example.com")
            if st.form_submit_button("Send PDF & Portal Link via Email"):
                if recipient and cd.get('saved_brief'):
                    pdf_bytes = generate_pdf(cd['name'], cd['market'], cd['address'], cd['saved_brief'])
                    with st.spinner("Dispatching email..."):
                        ok, status_msg = send_report_email(own, recipient, cd['name'], share_url, pdf_bytes)
                        if ok: st.success(status_msg)
                        else: st.error(status_msg)
                elif not cd.get('saved_brief'): st.error("Please generate the Executive Brief in Tab 1 before sending.")
                else: st.error("Please enter a valid email address.")
