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
    Core login function – FIXED for case-insensitive username
    """
    try:
        # Clean input
        clean_username = username.strip()

        # FIX: Use .ilike() for case-insensitive search
        # Also fetch original username to preserve case
        response = supabase.table("users").select(
            "password, full_name, role, username"
        ).ilike("username", clean_username).execute()

        if not response.data:
            st.error("Username not found. Please check spelling (case-insensitive).")
            return False

        # Take the first (and should be only) match
        user = response.data[0]

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            st.error("Invalid password")
            return False

        actual_role = user["role"]

        # Enforce tab-specific role
        if expected_role and actual_role.lower() != expected_role.lower():
            st.error(f"This login tab is for **{expected_role.title()}** accounts only.")
            return False

        # Success: set session state with ORIGINAL username case from DB
        st.session_state.authenticated = True
        st.session_state.username = user["username"]  # preserve original case
        st.session_state.full_name = user["full_name"] or user["username"]
        st.session_state.role = actual_role
        st.session_state.theme = "light"  # auto light mode after login
        st.session_state.just_logged_in = True  # flag for welcome message

        # Log successful login (using original case)
        from utils.helpers import log_action
        log_action("Login Successful", f"User: {user['username']} | Role: {actual_role}")

        # Optional debug (uncomment when testing)
        # st.write(f"Debug: Logged in as {user['username']} (original case preserved)")

        # Force rerun so main.py sees authenticated=True and redirects
        st.rerun()

        return True

    except Exception as e:
        st.error(f"Login error: {str(e)}")
        # Optional debug
        # st.write("Full error:", e)
        return False