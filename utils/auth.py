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
    Core login function:
    - Verifies username/password with bcrypt
    - Checks role match if expected_role is provided
    - Sets session state on success
    - Logs action
    - Triggers rerun so main.py can handle redirect + welcome message
    """
    try:
        # Fetch user (case-insensitive username)
        response = supabase.table("users").select(
            "password, full_name, role"
        ).eq("username", username.lower()).execute()

        if not response.data:
            st.error("Username not found")
            return False

        user = response.data[0]

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            st.error("Invalid password")
            return False

        actual_role = user["role"]

        # Enforce tab-specific role (owner tab only for owners, etc.)
        if expected_role and actual_role.lower() != expected_role.lower():
            st.error(f"This login tab is for **{expected_role.title()}** accounts only.")
            return False

        # Success: set session state
        st.session_state.authenticated = True
        st.session_state.username = username.lower()
        st.session_state.full_name = user["full_name"] or username
        st.session_state.role = actual_role
        st.session_state.theme = "light"           # auto light mode after login
        st.session_state.just_logged_in = True      # flag for welcome message in main.py

        # Log successful login
        from utils.helpers import log_action
        log_action("Login Successful", f"User: {username} | Role: {actual_role}")

        # IMPORTANT: Force rerun so main.py sees authenticated=True
        # and can show welcome + redirect to dashboard
        st.rerun()

        return True

    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False