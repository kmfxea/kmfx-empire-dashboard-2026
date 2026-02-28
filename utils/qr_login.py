# utils/qr_login.py
# =====================================================================
# KMFX EA - QR AUTO-LOGIN HANDLER
# Fully optimized, clean, and integrated with your existing utils
# =====================================================================
import streamlit as st
from utils.auth import is_authenticated
from utils.supabase_client import supabase
from utils.helpers import log_action

def handle_qr_login():
    """
    Handles QR code login from URL parameter ?qr=TOKEN
    Automatically logs in the user and redirects to dashboard.
    """
    # Get query parameter
    params = st.query_params
    qr_token = params.get("qr", [None])[0]

    if not qr_token or is_authenticated():
        return  # Walang QR o naka-login na

    try:
        # Query user by qr_token
        resp = supabase.table("users").select("*").eq("qr_token", qr_token).execute()

        if resp.data:
            user = resp.data[0]

            # Set session state
            st.session_state.authenticated = True
            st.session_state.username = user["username"].lower()
            st.session_state.full_name = user.get("full_name") or user["username"]
            st.session_state.role = user["role"]
            st.session_state.theme = "light"
            st.session_state.just_logged_in = True

            # Log the action (using your existing helper)
            log_action("QR Login Success", f"User: {user.get('full_name', user['username'])} | Role: {user['role']}")

            # Clear QR param from URL
            st.query_params.clear()

            # Instant redirect
            st.switch_page("pages/🏠_Dashboard.py")

        else:
            st.error("❌ Invalid or expired QR code")
            st.query_params.clear()

    except Exception as e:
        st.error(f"❌ QR login failed: {str(e)}")
        st.query_params.clear()