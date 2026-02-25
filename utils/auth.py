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

def send_magic_link(email: str) -> bool:
    """
    Send Supabase magic link (or OTP) – improved version with better feedback & debug
    """
    email = email.strip().lower()
    if not email or "@" not in email:
        st.error("Please enter a valid email address.")
        return False

    try:
        # You can switch to OTP code instead of link by changing template in Supabase dashboard
        # For now we keep magic link, but add better messages
        response = auth.sign_in_with_otp({
            "email": email,
            "options": {
                # IMPORTANT: MUST match EXACTLY one of the allowed redirect URLs in Supabase dashboard
                # Recommended: use the root URL without trailing slash
                "email_redirect_to": "https://kmfxea.streamlit.app",
                
                # Optional but helpful: tell Supabase this is a login (not signup)
                # Helps avoid "confirm signup" confusion for existing users
                "shouldCreateUser": True,           # auto-create if new
            }
        })

        # Supabase returns data with some useful info
        if response.data:
            st.success(f"Magic link sent to **{email}**! Check inbox & spam folder.")
            st.info("→ Click the link in the email to sign in. It should redirect you back here automatically.")
        else:
            st.warning("Message sent, but no confirmation from server. Check your email anyway.")

        # Optional: show last sent time (helps debugging)
        st.session_state["last_magic_email"] = email
        st.session_state["last_magic_time"] = datetime.datetime.now().strftime("%H:%M:%S")

        return True

    except Exception as e:
        error_str = str(e).lower()

        if "rate limit" in error_str or "too many requests" in error_str:
            st.error("Rate limit reached. Please wait 30–60 seconds and try again.")
        elif "invalid" in error_str and "email" in error_str:
            st.error("Invalid email format. Please check and try again.")
        elif "network" in error_str or "timeout" in error_str:
            st.error("Network issue connecting to Supabase. Please check your internet and try again.")
        else:
            st.error(f"Failed to send magic link: {str(e)}")
            # For debugging – show in expander so it's not scary for users
            with st.expander("Technical details (for support)"):
                st.code(str(e))

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