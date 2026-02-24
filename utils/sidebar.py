# utils/sidebar.py
import streamlit as st
import time

def render_sidebar():
    """
    Role-based sidebar navigation for KMFX Empire
    - Client: limited pages
    - Admin: client pages + admin tools
    - Owner: everything
    Renders only once per page load even if called multiple times.
    """
    # ── Double-render protection ────────────────────────────────────────────
    if st.session_state.get("_sidebar_rendered", False):
        return
    st.session_state["_sidebar_rendered"] = True

    # ── Get user info safely ────────────────────────────────────────────────
    role = st.session_state.get("role", "guest").lower().strip()
    full_name = st.session_state.get("full_name", "User")

    # ── Header / Greeting ───────────────────────────────────────────────────
    st.sidebar.markdown(f"**👑 {full_name}**")
    st.sidebar.caption(f"Role: {role.title()}")
    st.sidebar.markdown("### KMFX Empire")
    st.sidebar.markdown("---")

    # ── COMMON / CLIENT PAGES ───────────────────────────────────────────────
    # Visible to guest, client, admin, owner
    st.sidebar.page_link("pages/🏠_Dashboard.py", label="Dashboard", icon="🏠")
    st.sidebar.page_link("pages/👤_My_Profile.py", label="My Profile", icon="👤")
    st.sidebar.page_link("pages/💰_Profit_Sharing.py", label="Profit Sharing", icon="💰")
    st.sidebar.page_link("pages/💳_Withdrawals.py", label="Withdrawals", icon="💳")

    # ── EXTENDED PAGES (client + admin + owner) ─────────────────────────────
    if role in ["client", "admin", "owner"]:
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
        st.sidebar.page_link("pages/🔑_License_Generator.py", label="License Generator", icon="🔑")
        st.sidebar.page_link("pages/👤_Admin_Management.py", label="Admin Management", icon="👤")
        st.sidebar.page_link("pages/🔮_Simulator.py", label="Simulator", icon="🔮")

    # ── LOGOUT SECTION ──────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", 
                        type="primary", 
                        use_container_width=True,
                        key="sidebar_logout_button"):   # key para walang conflict
        # Clear authentication & sidebar-related session state
        keys_to_clear = [
            "authenticated", "username", "full_name", "role",
            "just_logged_in", "theme", "_sidebar_rendered"
        ]
        for key in keys_to_clear:
            st.session_state.pop(key, None)

        st.success("Logged out successfully! Redirecting...")
        time.sleep(1.0)
        st.switch_page("main.py")