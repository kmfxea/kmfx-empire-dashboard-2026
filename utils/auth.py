"""
Authentication helpers for KMFX Empire:
- is_authenticated()
- require_auth(min_role)
- login_user(username, password, expected_role)
"""
import streamlit as st
import bcrypt
from utils.supabase_client import supabase

def is_authenticated() -> bool:
    """
    Check if user is currently logged in via session state.
    Returns True if authenticated, False otherwise.
    """
    return st.session_state.get("authenticated", False)

def require_auth(min_role: str = "client"):
    """
    Protect authenticated pages:
    - Redirect to main.py if not logged in
    - Stop execution if current role is below required level
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
            "password, full_name, role, username"  # include username to preserve original case
        ).ilike("username", clean_username).execute()

        if not response.data:
            st.error("Username not found. Please check spelling (case-insensitive).")
            return False

        # If multiple matches (shouldn't happen with UNIQUE constraint), take first
        if len(response.data) > 1:
            st.warning("Multiple users found with similar username – using first match.")
        
        user = response.data[0]

        # Debug: Show what Supabase actually returned (uncomment when testing)
        # st.write("Debug: Found user →", user["username"], user["role"])

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            st.error("Invalid password")
            return False

        actual_role = user["role"]

        # Enforce tab-specific role check
        if expected_role and actual_role.lower() != expected_role.lower():
            st.error(f"This login tab is for **{expected_role.title()}** accounts only.")
            return False

        # Success: set session with ORIGINAL case from DB
        st.session_state.authenticated = True
        st.session_state.username = user["username"]           # preserve original case
        st.session_state.full_name = user["full_name"] or user["username"]
        st.session_state.role = actual_role
        st.session_state.theme = "light"
        st.session_state.just_logged_in = True

        # Log with original username
        from utils.helpers import log_action
        log_action("Login Successful", f"User: {user['username']} | Role: {actual_role}")

        # Force rerun so main.py can redirect + show welcome
        st.rerun()
        return True

    except Exception as e:
        st.error(f"Login error: {str(e)}")
        # Debug: show full error (uncomment when troubleshooting)
        # st.write("Full error details:", e)
        return False