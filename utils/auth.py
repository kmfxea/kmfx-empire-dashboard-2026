"""
Authentication helpers for KMFX Empire (Updated 2026)
Supports both current password login + ready for magic link transition
"""
import streamlit as st
import bcrypt
from utils.supabase_client import supabase, service_supabase, auth

def is_authenticated() -> bool:
    """
    Check if user is logged in via session state.
    """
    return st.session_state.get("authenticated", False)

def require_auth(min_role: str = "client"):
    """
    Protect authenticated pages:
    - Redirect to main.py if not logged in
    - Stop if role is too low
    """
    if not is_authenticated():
        st.switch_page("main.py")
        st.stop()

    current_role = st.session_state.get("role", "guest").lower()
    role_levels = {"guest": 0, "client": 1, "admin": 2, "owner": 3}

    if role_levels.get(current_role, 0) < role_levels.get(min_role.lower(), 1):
        st.error(f"Access denied. Minimum role required: **{min_role.title()}**")
        st.stop()

def login_user(username: str, password: str, expected_role: str = None) -> bool:
    """
    Core login function – case-insensitive username search
    """
    try:
        # Clean input
        clean_username = username.strip()

        # Query with case-insensitive match (.ilike)
        response = supabase.table("users").select(
            "password, full_name, role, username"
        ).ilike("username", clean_username).execute()

        if not response.data:
            st.error("Username not found. Please check spelling (case-insensitive).")
            return False

        if len(response.data) > 1:
            st.warning("Multiple similar usernames found – using first match.")

        user = response.data[0]

        # Debug (uncomment when troubleshooting)
        # st.write("Debug: Found user →", user["username"], user["role"])

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            st.error("Invalid password")
            return False

        actual_role = user["role"]

        # Role tab check
        if expected_role and actual_role.lower() != expected_role.lower():
            st.error(f"This login tab is for **{expected_role.title()}** only.")
            return False

        # Success: set session with original DB case
        st.session_state.authenticated = True
        st.session_state.username = user["username"]  # keep original case
        st.session_state.full_name = user["full_name"] or user["username"]
        st.session_state.role = actual_role
        st.session_state.theme = "light"
        st.session_state.just_logged_in = True

        # Log
        from utils.helpers import log_action
        log_action("Login Successful", f"User: {user['username']} | Role: {actual_role}")

        # Force page reload for redirect + welcome
        st.rerun()
        return True

    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False

# ────────────────────────────────────────────────
# FUTURE MAGIC LINK / OTP SUPPORT (ready for switch)
# ────────────────────────────────────────────────

def send_magic_link(email: str) -> bool:
    """
    Send Supabase magic link (email login) – call when ready to switch
    """
    try:
        auth.sign_in_with_otp({
            "email": email.strip().lower(),
            "options": {
                "email_redirect_to": "https://kmfxea.streamlit.app"
            }
        })
        st.success(f"Magic link sent to {email}! Check inbox/spam.")
        return True
    except Exception as e:
        st.error(f"Failed to send magic link: {str(e)}")
        return False

def handle_auth_callback():
    """
    Call this on every page load (in main.py) to complete magic link login
    """
    try:
        session = auth.get_session()
        if session and session.user:
            user = session.user
            user_id = user.id

            # Check if linked to public.users
            custom = supabase.table("users").select("*").eq("auth_id", user_id).execute()

            if not custom.data:
                # Auto-create on first login
                supabase.table("users").insert({
                    "auth_id": user_id,
                    "email": user.email,
                    "username": user.email.split('@')[0],
                    "full_name": user.user_metadata.get("full_name", user.email.split('@')[0]),
                    "role": "client"  # default – admin can change later
                }).execute()

                custom = supabase.table("users").select("*").eq("auth_id", user_id).execute()

            custom = custom.data[0]

            # Set session
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.session_state.email = user.email
            st.session_state.username = custom["username"]
            st.session_state.full_name = custom["full_name"]
            st.session_state.role = custom["role"]
            st.session_state.just_logged_in = True

            st.rerun()
    except:
        pass  # no session yet