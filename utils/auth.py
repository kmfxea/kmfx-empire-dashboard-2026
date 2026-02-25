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
    """Check if user is currently logged in"""
    return st.session_state.get("authenticated", False)

def require_auth(min_role: str = "client"):
    """
    Protect pages:
    - Redirect to main.py if not authenticated
    - Show error + stop if role is insufficient
    """
    if not is_authenticated():
        st.switch_page("main.py")
        st.stop()

    current_role = st.session_state.get("role", "guest")
    role_levels = {"guest": 0, "client": 1, "admin": 2, "owner": 3}

    if role_levels.get(current_role, 0) < role_levels.get(min_role, 1):
        st.error(f"Access denied. Minimum role required: **{min_role.title()}**")
        st.stop()

def login_user(username: str, password: str, expected_role: str = None):
    """
    Core login function:
    - Verifies username/password with bcrypt
    - Checks role match if expected_role is provided
    - Sets session state on success
    - Logs action
    - Redirects to dashboard
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
        if expected_role and actual_role != expected_role:
            st.error(f"This login tab is for **{expected_role.title()}** accounts only.")
            return False

        # Success: set session state
        st.session_state.authenticated = True
        st.session_state.username = username.lower()
        st.session_state.full_name = user["full_name"] or username
        st.session_state.role = actual_role
        st.session_state.theme = "light"           # auto light mode after login
        st.session_state.just_logged_in = True     # trigger welcome message

        # Log successful login
        from utils.helpers import log_action
        log_action("Login Successful", f"User: {username} | Role: {actual_role}")

        # Redirect to dashboard (fixed path)
        st.switch_page("pages/🏠_Dashboard.py")

        return True

    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False