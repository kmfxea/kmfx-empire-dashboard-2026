# utils/qr_login.py
# =====================================================================
# KMFX EA - QR AUTO-LOGIN HANDLER (v2.1 – Feb 2026)
# Secure, idempotent, with better error handling & audit trail
# =====================================================================
import streamlit as st
from utils.auth import is_authenticated
from utils.supabase_client import supabase
from utils.helpers import log_action

def handle_qr_login(redirect_page: str = "pages/🏠_Dashboard.py"):
    """
    Handles QR code login via ?qr=TOKEN in the URL.
    
    Features:
    - Skips if already authenticated
    - Uses maybe_single() for safer query
    - Optional is_active check
    - Detailed logging (partial token + IP if available)
    - Always clears param to prevent replay
    - Flexible redirect (default: client dashboard)
    """
    if is_authenticated():
        return  # Already logged in → no action needed

    params = st.query_params
    qr_token = params.get("qr", [None])[0]

    if not qr_token:
        return  # No QR parameter → nothing to do

    try:
        # Safer query: expect 0 or 1 row only
        response = supabase.table("users") \
            .select("id, username, full_name, role, qr_token, is_active") \
            .eq("qr_token", qr_token) \
            .maybe_single() \
            .execute()

        if not response.data:
            st.error("❌ Invalid or expired QR code.")
            st.query_params.clear()
            return

        user = response.data

        # Optional: prevent login if account is deactivated
        if user.get("is_active") is False:
            st.error("❌ This account has been deactivated.")
            st.query_params.clear()
            return

        # ── Successful QR login ────────────────────────────────────────
        st.session_state.authenticated   = True
        st.session_state.username         = user["username"].lower()
        st.session_state.full_name        = user.get("full_name") or user["username"]
        st.session_state.role             = user["role"].lower()
        st.session_state.theme            = "light"  # common after QR/mobile login
        st.session_state.just_logged_in   = True

        # Enhanced logging
        ip_approx = st.context.headers.get("X-Forwarded-For", "unknown")
        log_action(
            "QR Login Success",
            f"User: {user.get('full_name', user['username'])} | "
            f"Username: {user['username']} | Role: {user['role']} | "
            f"QR Token (partial): {qr_token[:8]}... | IP approx: {ip_approx}"
        )

        # Clear QR param immediately (security + UX)
        st.query_params.clear()

        # Redirect
        st.switch_page(redirect_page)

    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ QR login failed: {error_msg}")

        # Log failure too (helps detect abuse or bugs)
        log_action(
            "QR Login Failed",
            f"Token (partial): {qr_token[:8]}... | Error: {error_msg[:120]}"
        )

        # Still clear param even on error
        st.query_params.clear()