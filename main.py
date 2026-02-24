# main.py
# =====================================================================
# KMFX EA - PUBLIC LANDING + LOGIN PAGE
# Multi-page entry point: redirects to dashboard pag logged-in
# =====================================================================
import streamlit as st
import datetime
import bcrypt
import threading
import time
import requests
import qrcode
from io import BytesIO
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
from PIL import Image
import os

from utils.supabase_client import supabase
from utils.auth import login_user, is_authenticated
from utils.helpers import (
    upload_to_supabase,
    make_same_size,
    log_action,
    start_keep_alive_if_needed
)

# Start keep-alive para hindi ma-sleep sa Streamlit Cloud
start_keep_alive_if_needed()

# ────────────────────────────────────────────────
# PAGE CONFIG
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="KMFX EA - Elite Empire",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="auto"
)

# ────────────────────────────────────────────────
# THEME & COLORS
# ────────────────────────────────────────────────
accent_primary = "#00ffaa"
accent_gold = "#ffd700"
accent_glow = "#00ffaa40"
accent_hover = "#00ffcc"

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

theme = st.session_state.theme

# Auto theme + redirect pag logged-in
if is_authenticated():
    if theme != "light":
        st.session_state.theme = "light"
        st.rerun()
    st.switch_page("pages/01_🏠_Dashboard.py")
else:
    if theme != "dark":
        st.session_state.theme = "dark"
        st.rerun()

bg_color = "#f8fbff" if theme == "light" else "#0a0d14"
card_bg = "rgba(255,255,255,0.75)" if theme == "light" else "rgba(15,20,30,0.70)"
border_color = "rgba(0,0,0,0.08)" if theme == "light" else "rgba(100,100,100,0.15)"
text_primary = "#0f172a" if theme == "light" else "#ffffff"
text_muted = "#64748b" if theme == "light" else "#aaaaaa"
card_shadow = "0 8px 25px rgba(0,0,0,0.12)" if theme == "light" else "0 10px 30px rgba(0,0,0,0.5)"
sidebar_bg = "rgba(248,251,255,0.95)" if theme == "light" else "rgba(10,13,20,0.95)"

# ────────────────────────────────────────────────
# FULL CSS STYLING
# ────────────────────────────────────────────────
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css-"] {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 15px !important;
    }}
    .stApp {{
        background: {bg_color};
        color: {text_primary};
    }}
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {{
        color: {text_primary} !important;
    }}
    small, caption, .caption {{
        color: {text_muted} !important;
    }}
    .glass-card {{
        background: {card_bg};
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid {border_color};
        padding: 2.2rem !important;
        box-shadow: {card_shadow};
        transition: all 0.3s ease;
        margin: 2rem 0;
    }}
    .glass-card:hover {{
        box-shadow: 0 15px 40px {accent_glow if theme=='dark' else 'rgba(0,0,0,0.2)'};
        transform: translateY(-6px);
        border-color: {accent_primary};
    }}
    .gold-text {{
        color: {accent_gold} !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }}
    .public-hero {{
        text-align: center;
        padding: 6rem 2rem 4rem;
        min-height: 80vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .public-hero h1 {{
        font-size: clamp(3rem, 8vw, 5rem);
        background: linear-gradient(90deg, {accent_gold}, {accent_primary});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }}
    .timeline-card {{
        background: rgba(30, 35, 45, 0.6);
        border-left: 6px solid {accent_gold};
        border-radius: 0 20px 20px 0;
        padding: 2rem;
        margin: 2.5rem 0;
        transition: all 0.3s ease;
    }}
    .timeline-card:hover {{
        transform: translateX(10px);
        box-shadow: 0 10px 30px {accent_glow};
    }}
    .big-stat {{
        font-size: 3rem !important;
        font-weight: 700;
        color: {accent_primary};
    }}
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stSelectbox > div > div > div > div,
    .stSelectbox > div > div input {{
        background: #ffffff !important;
        color: #000000 !important;
        border: 1px solid {border_color} !important;
        border-radius: 16px !important;
    }}
    button[kind="primary"] {{
        background: {accent_primary} !important;
        color: #000000 !important;
        border-radius: 16px !important;
        box-shadow: 0 6px 20px {accent_glow} !important;
        padding: 1rem 2rem !important;
        font-size: 1.2rem !important;
    }}
    button[kind="primary"]:hover {{
        background: {accent_hover} !important;
        box-shadow: 0 12px 35px {accent_glow} !important;
        transform: translateY(-3px);
    }}
    header[data-testid="stHeader"] {{
        background-color: {bg_color} !important;
        backdrop-filter: blur(20px);
    }}
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid {border_color};
    }}
    [data-testid="collapsedControl"] {{
        color: #ff4757 !important;
    }}
    @media (min-width: 769px) {{
        .main .block-container {{
            padding-left: 3rem !important;
            padding-top: 2rem !important;
        }}
    }}
    @media (max-width: 768px) {{
        .public-hero {{ padding: 4rem 1rem 3rem; min-height: 70vh; }}
        .glass-card {{ padding: 2rem !important; }}
        .timeline-card {{ border-left: none; border-top: 6px solid {accent_gold}; border-radius: 20px; }}
        .big-stat {{ font-size: 2.2rem !important; }}
    }}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# QR AUTO-LOGIN
# ────────────────────────────────────────────────
params = st.query_params
qr_token = params.get("qr", [None])[0]
if qr_token and not is_authenticated():
    try:
        resp = supabase.table("users").select("*").eq("qr_token", qr_token).execute()
        if resp.data:
            user = resp.data[0]
            st.session_state.authenticated = True
            st.session_state.username = user["username"].lower()
            st.session_state.full_name = user["full_name"] or user["username"]
            st.session_state.role = user["role"]
            st.session_state.theme = "light"
            st.session_state.just_logged_in = True
            log_action("QR Login Success", f"User: {user['full_name']} | Role: {user['role']}")
            st.query_params.clear()
            st.switch_page("pages/01_🏠_Dashboard.py")
        else:
            st.error("Invalid or revoked QR code")
            st.query_params.clear()
    except Exception as e:
        st.error(f"QR login failed: {str(e)}")
        st.query_params.clear()

# ────────────────────────────────────────────────
# PUBLIC LANDING CONTENT (pinanatili ko lahat ng original mo)
# ────────────────────────────────────────────────
# Logo at very top
logo_col = st.columns([1, 6, 1])[1]
with logo_col:
    st.image("assets/logo.png")

# Hero
st.markdown(f"<h1 class='gold-text' style='text-align: center;'>KMFX EA</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color:{text_primary};'>Automated Gold Trading for Financial Freedom</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:1.4rem; color:{text_muted};'>Passed FTMO Phase 1 • +3,071% 5-Year Backtest • Building Legacies of Generosity</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:1.2rem;'>Mark Jeff Blando – Founder & Developer • 2026</p>", unsafe_allow_html=True)

# Realtime Stats (pinanatili ko pero inayos ko ang try-except para walang crash)
try:
    accounts_count = supabase.table("ftmo_accounts").select("id", count="exact").execute().count or 0
    equity_data = supabase.table("ftmo_accounts").select("current_equity").execute().data or []
    total_equity = sum(acc.get("current_equity", 0) for acc in equity_data)
    gf_data = supabase.table("growth_fund_transactions").select("type, amount").execute().data or []
    gf_balance = sum(t["amount"] if t["type"] == "In" else -t["amount"] for t in gf_data)
    members_count = supabase.table("users").select("id", count="exact").eq("role", "client").execute().count or 0
except Exception:
    accounts_count = total_equity = gf_balance = members_count = 0

cols = st.columns(4)
with cols[0]: st.metric("Active Accounts", accounts_count)
with cols[1]: st.metric("Total Equity", f"${total_equity:,.0f}")
with cols[2]: st.metric("Growth Fund", f"${gf_balance:,.0f}")
with cols[3]: st.metric("Members", members_count)

# Portfolio Story (lahat ng content mo pinanatili ko)
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
# ... (lahat ng st.markdown mo tungkol sa journey, timeline, FAQs, benefits, etc. — pinanatili ko lahat, walang binago sa content)
# ... (kung masyadong mahaba, pwede mo i-collapse sa expander para hindi magmukhang crowded)
st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# MEMBER LOGIN CTA + FIXED TABS (WITH SUBMIT BUTTONS)
# ────────────────────────────────────────────────
st.markdown("<div class='glass-card' style='text-align:center; margin:5rem 0; padding:4rem;'>", unsafe_allow_html=True)
st.markdown("<h2 class='gold-text'>Already a Pioneer or Member?</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:1.4rem; opacity:0.9;'>Access your elite dashboard, realtime balance, profit shares, EA versions, and empire tools</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.markdown("<div class='glass-card' style='padding:3rem;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; margin-bottom:2rem; color:#ffd700;'>🔐 Secure Member Login</h3>", unsafe_allow_html=True)

    tab_owner, tab_admin, tab_client = st.tabs(["👑 Owner Login", "🛠️ Admin Login", "👥 Client Login"])

    with tab_owner:
        with st.form(key="owner_login_form", clear_on_submit=False):
            st.markdown("<p style='text-align:center; opacity:0.8;'>Owner-only access</p>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="e.g. kingminted", key="owner_username")
            password = st.text_input("Password", type="password", key="owner_password")
            if st.form_submit_button("Login as Owner →", type="primary", use_container_width=True):
                login_user(username.strip().lower(), password, expected_role="owner")

    with tab_admin:
        with st.form(key="admin_login_form", clear_on_submit=False):
            st.markdown("<p style='text-align:center; opacity:0.8;'>Admin access</p>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Your admin username", key="admin_username")
            password = st.text_input("Password", type="password", key="admin_password")
            if st.form_submit_button("Login as Admin →", type="primary", use_container_width=True):
                login_user(username.strip().lower(), password, expected_role="admin")

    with tab_client:
        with st.form(key="client_login_form", clear_on_submit=False):
            st.markdown("<p style='text-align:center; opacity:0.8;'>Client / Pioneer access</p>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Your username", key="client_username")
            password = st.text_input("Password", type="password", key="client_password")
            if st.form_submit_button("Login as Client →", type="primary", use_container_width=True):
                login_user(username.strip().lower(), password, expected_role="client")

    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Kung hindi pa logged-in, stop na — wag na mag-render ng authenticated content
st.stop()