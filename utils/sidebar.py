# utils/sidebar.py
import streamlit as st
import time

def render_sidebar():
    """
    Role-based sidebar navigation for KMFX Empire
    - Client: basic pages
    - Admin: client pages + admin tools
    - Owner: everything
    Includes logout button at the bottom.
    Uses session_state flag to prevent double rendering.
    """
    # Prevent double rendering (very important in multi-page apps)
    if st.session_state.get("_sidebar_rendered", False):
        return
    st.session_state["_sidebar_rendered"] = True

    # Get user info with safe defaults
    role = st.session_state.get("role", "guest").lower().strip()
    full_name = st.session_state.get("full_name", "Guest")

    # ── User Info Header ────────────────────────────────────────────────────
    st.sidebar.markdown(f"**👑 {full_name}**")
    st.sidebar.caption(f"Role: {role.title()}")
    st.sidebar.markdown("### KMFX Empire")
    st.sidebar.markdown("---")

    # ── COMMON PAGES (available to all logged-in users) ─────────────────────
    st.sidebar.page_link("pages/🏠_Dashboard.py", label="Dashboard", icon="🏠")
    st.sidebar.page_link("pages/👤_My_Profile.py", label="My Profile", icon="👤")

    # ── CLIENT + ADMIN + OWNER PAGES ────────────────────────────────────────
    if role in ["client", "admin", "owner"]:
        st.sidebar.page_link("pages/💰_Profit_Sharing.py", label="Profit Sharing", icon="💰")
        st.sidebar.page_link("pages/💳_Withdrawals.py", label="Withdrawals", icon="💳")
        st.sidebar.page_link("pages/🌱_Growth_Fund.py", label="Growth Fund", icon="🌱")
        st.sidebar.page_link("pages/🤖_EA_Versions.py", label="EA Versions", icon="🤖")
        st.sidebar.page_link("pages/🔔_Notifications.py", label="Notifications", icon="🔔")
        st.sidebar.page_link("pages/📸_Testimonials.py", label="Testimonials", icon="📸")

    # ── ADMIN + OWNER ONLY ──────────────────────────────────────────────────
    if role in ["admin", "owner"]:
        st.sidebar.page_link("pages/📊_FTMO_Accounts.py", label="FTMO Accounts", icon="📊")
        st.sidebar.page_link("pages/📜_Audit_Logs.py", label="Audit Logs", icon="📜")
        st.sidebar.page_link("pages/📢_Announcements.py", label="Announcements", icon="📢")
        st.sidebar.page_link("pages/📈_Reports_Export.py", label="Reports Export", icon="📈")
        st.sidebar.page_link("pages/📁_File_Vault.py", label="File Vault", icon="📁")
        st.sidebar.page_link("pages/💬_Messages.py", label="Messages", icon="💬")

    # ── OWNER ONLY ──────────────────────────────────────────────────────────
    if role == "owner":
        st.sidebar.markdown("---")
        st.sidebar.subheader("👑 Owner Tools")
        st.sidebar.page_link("pages/🔑_License_Generator.py", label="License Generator", icon="🔑")
        st.sidebar.page_link("pages/👤_Admin_Management.py", label="Admin Management", icon="👤")
        st.sidebar.page_link("pages/🔮_Simulator.py", label="Simulator", icon="🔮")
    # ── LOGOUT SECTION ──────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Account")

    if st.sidebar.button(
        "🚪 Logout",
        type="primary",
        use_container_width=True,
        key=f"logout_btn_{role}_{st.session_state.get('username', 'anon')}",  # mas stable key
        help="End session and return to login page"
    ):
        # Set flag + clear keys
        st.session_state["logging_out"] = True
        
        keys_to_clear = [
            "authenticated", "username", "full_name", "role",
            "just_logged_in", "theme", "_sidebar_rendered"
        ]
        for key in keys_to_clear:
            st.session_state.pop(key, None)
        
        st.success("Logging out...")  # optional message
        st.rerun()  # importante: trigger full rerun para ma-detect agad