# utils/sidebar.py
import streamlit as st

def render_sidebar():
    # Get current role safely (fallback to guest/client)
    role = st.session_state.get("role", "client")

    st.sidebar.title("KMFX Empire")

    # ── COMMON PAGES (all roles) ────────────────────────────────
    st.sidebar.page_link("pages/🏠_Dashboard.py", label="Dashboard", icon="🏠")
    st.sidebar.page_link("pages/👤_My_Profile.py", label="My Profile", icon="👤")
    st.sidebar.page_link("pages/💰_Profit_Sharing.py", label="Profit Sharing", icon="💰")
    st.sidebar.page_link("pages/💳_Withdrawals.py", label="Withdrawals", icon="💳")

    # ── EXTENDED ACCESS (client + admin + owner) ────────────────
    if role in ["client", "admin", "owner"]:
        st.sidebar.page_link("pages/🌱_Growth_Fund.py", label="Growth Fund", icon="🌱")
        st.sidebar.page_link("pages/🤖_EA_Versions.py", label="EA Versions", icon="🤖")
        st.sidebar.page_link("pages/🔔_Notifications.py", label="Notifications", icon="🔔")     # added if useful

    # ── ADMIN + OWNER ONLY ──────────────────────────────────────
    if role in ["admin", "owner"]:
        st.sidebar.page_link("pages/📊_FTMO_Accounts.py", label="FTMO Accounts", icon="📊")
        st.sidebar.page_link("pages/📜_Audit_Logs.py", label="Audit Logs", icon="📜")
        st.sidebar.page_link("pages/📢_Announcements.py", label="Announcements", icon="📢")
        st.sidebar.page_link("pages/📈_Reports_Export.py", label="Reports Export", icon="📈")   # useful for admins

    # ── OWNER ONLY ──────────────────────────────────────────────
    if role == "owner":
        st.sidebar.page_link("pages/🔑_License_Generator.py", label="License Generator", icon="🔑")
        st.sidebar.page_link("pages/👤_Admin_Management.py", label="Admin Management", icon="👤")
        st.sidebar.page_link("pages/🔮_Simulator.py", label="Simulator", icon="🔮")            # if owner-only

    # ── LOGOUT SECTION ──────────────────────────────────────────
    st.sidebar.divider()
    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Logout", type="secondary", use_container_width=True):
        # Clear all auth-related session keys
        for key in list(st.session_state.keys()):
            if key in ["authenticated", "username", "full_name", "role", "just_logged_in"]:
                del st.session_state[key]
        
        # Optional: clear other temp keys if you have them
        st.session_state.clear()  # nuclear option — use only if no other important state

        st.success("Logged out successfully!")
        # Small delay to show message
        import time
        time.sleep(1.2)
        
        # Redirect to public landing
        st.switch_page("main.py")  # assuming main.py is your login/landing page