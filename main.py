# main.py
# =====================================================================
# KMFX EA - ROOT ENTRY POINT (PUBLIC LANDING + LOGIN REDIRECT)
# Redirects authenticated users → dashboard / admin
# Unauthenticated → landing.py
# =====================================================================

import streamlit as st

# ── IMPORTS (dapat lahat nandito) ────────────────────────────────────
from utils.supabase_client import supabase
from utils.auth import is_authenticated
from utils.helpers import log_action, start_keep_alive_if_needed
from utils.styles import apply_global_styles
from utils.qr_login import handle_qr_login   # ← ETO YUNG KULANG KANINA!

# Keep-alive (optional, para di ma-sleep agad sa free tier)
start_keep_alive_if_needed()

# ────────────────────────────────────────────────
# PAGE CONFIG - MUST BE FIRST STREAMLIT COMMAND
# ────────────────────────────────────────────────
authenticated = is_authenticated()

if authenticated:
    st.set_page_config(
        page_title="KMFX Empire Dashboard",
        page_icon="👑",
        layout="wide",
        initial_sidebar_state="expanded"
    )
else:
    st.set_page_config(
        page_title="KMFX EA - Elite Empire",
        page_icon="👑",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Hide sidebar completely on public/landing
    st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none !important; }
        section[data-testid="stSidebar"] {
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            overflow: hidden !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# APPLY GLOBAL STYLES EARLY
# ────────────────────────────────────────────────
apply_global_styles(is_public=not authenticated)

# ────────────────────────────────────────────────
# QR AUTO-LOGIN (call EARLY, bago mag-redirect o mag-render)
# ────────────────────────────────────────────────
handle_qr_login()   # ← ETO NA ANG TAMANG TAWAG + IMPORT SA TAAS

# ────────────────────────────────────────────────
# AUTHENTICATED → IMMEDIATE REDIRECT
# ────────────────────────────────────────────────
if authenticated:
    role = st.session_state.get("role", "client").lower()
    
    if role in ["owner", "admin"]:
        st.switch_page("pages/👤_Admin_Management.py")
    else:
        st.switch_page("pages/🏠_Dashboard.py")
    
    st.stop()  # Safety net - wag na mag-render ng kahit ano

# ────────────────────────────────────────────────
# NOT AUTHENTICATED → SHOW PUBLIC LANDING
# ────────────────────────────────────────────────
if "logging_out" in st.session_state and st.session_state.logging_out:
    msg = st.session_state.pop("logout_message", "You have been logged out.")
    st.success(msg)
    st.session_state.pop("logging_out", None)

# Redirect to the actual landing page content
st.switch_page("pages/landing.py")