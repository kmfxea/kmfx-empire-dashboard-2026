# utils/auth.py
"""
Authentication helpers:
- is_authenticated()
- require_auth(min_role)
- login_user() — yung orihinal na logic mo na may bcrypt + role check
"""

import streamlit as st
import bcrypt
from utils.supabase_client import supabase


def is_authenticated() -> bool:
    """Check kung logged in na ba"""
    return st.session_state.get("authenticated", False)


def require_auth(min_role: str = "client"):
    """
    Gatekeeper para sa bawat page
    Kung hindi authenticated → balik sa main.py (login)
    Kung kulang ang role → error + stop
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
    Login logic — diretsong galing sa original code mo
    May bcrypt check + role validation + session setup
    """
    try:
        # Case-insensitive username
        response = supabase.table("users").select(
            "password, full_name, role"
        ).eq("username", username.lower()).execute()

        if response.data:
            user = response.data[0]

            if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                actual_role = user["role"]

                # Role check kung may expected_role (hal. owner tab lang para sa owner)
                if expected_role and actual_role != expected_role:
                    st.error(f"This login tab is for **{expected_role.title()}** accounts only.")
                    return

                # Success — set session
                st.session_state.authenticated = True
                st.session_state.username = username.lower()
                st.session_state.full_name = user["full_name"] or username
                st.session_state.role = actual_role
                st.session_state.theme = "light"          # auto light mode pag logged in
                st.session_state.just_logged_in = True    # para sa welcome message

                # Log successful login
                from utils.helpers import log_action
                log_action("Login Successful", f"User: {username} | Role: {actual_role}")

                # Auto-redirect sa dashboard
                st.switch_page("pages/01_🏠_Dashboard.py")

            else:
                st.error("Invalid password")
        else:
            st.error("Username not found")
    except Exception as e:
        st.error(f"Login error: {str(e)}")