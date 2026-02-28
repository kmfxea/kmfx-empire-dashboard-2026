# =====================================================================
# main.py - OPTIMIZED LIGHTWEIGHT ROUTER (v3.2 - Feb 28, 2026)
# Super fast • Clean • Uses all new modular files
# =====================================================================
import streamlit as st

from utils.helpers import start_keep_alive_if_needed
from utils.auth import is_authenticated
from utils.styles import apply_global_styles
from utils.qr_login import handle_qr_login

# Optional keep-alive para stable ang Supabase
start_keep_alive_if_needed()

# ────────────────────────────────────────────────
# AUTH CHECK + INSTANT REDIRECT (pinakamabilis)
# ────────────────────────────────────────────────
if is_authenticated():
    role = st.session_state.get("role", "client").lower()
    if role in ["owner", "admin"]:
        st.switch_page("pages/👤_Admin_Management.py")
    else:
        st.switch_page("pages/🏠_Dashboard.py")

# ────────────────────────────────────────────────
# PUBLIC PAGE CONFIG (must be FIRST st command)
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="KMFX EA - Elite Empire",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply all premium styles (isang call lang)
apply_global_styles(public=True)

# Hide sidebar completely for public landing
st.markdown("""
<style>
    section[data-testid="stSidebar"], 
    [data-testid="collapsedControl"] {
        display: none !important;
        width: 0 !important;
        min-width: 0 !important;
    }
    .main .block-container {
        max-width: 1300px !important;
        margin: 0 auto !important;
        padding: 2rem 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# QR AUTO-LOGIN
# ────────────────────────────────────────────────
handle_qr_login()

# ────────────────────────────────────────────────
# SHOW FULL PUBLIC LANDING PAGE
# ────────────────────────────────────────────────
from pages.landing import show_public_landing
show_public_landing()

# Logout message handler (kapag nag-logout galing dashboard)
if st.session_state.pop("logging_out", False):
    msg = st.session_state.pop("logout_message", None)
    if msg:
        st.success(msg)

# Final security stop
if not st.session_state.get("authenticated", False):
    st.stop()