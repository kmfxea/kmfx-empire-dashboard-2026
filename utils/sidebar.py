# utils/sidebar.py
import streamlit as st

def render_sidebar():
    """
    Role-based sidebar navigation – clean, no double icons, emojis only in labels
    Always renders fresh – no flags or caching tricks
    """
    # Get current user info safely
    role = st.session_state.get("role", "guest").lower().strip()
    full_name = st.session_state.get("full_name", "Guest")

    # User header
    st.sidebar.markdown(f"**👑 {full_name}**")
    st.sidebar.caption(f"Role: {role.title() if role != 'guest' else 'Not logged in'}")
    st.sidebar.markdown("---")

    # ── COMMON PAGES (available to all logged-in users) ───────────────────────
    st.sidebar.page_link("pages/🏠_Dashboard.py", label="🏠 Dashboard")
    st.sidebar.page_link("pages/👤_My_Profile.py", label="👤 My Profile")

    # ── CLIENT + ADMIN + OWNER PAGES ──────────────────────────────────────────
    if role in ["client", "admin", "owner"]:
        st.sidebar.page_link("pages/💰_Profit_Sharing.py", label="💰 Profit Sharing")
        st.sidebar.page_link("pages/💳_Withdrawals.py", label="💳 Withdrawals")
        st.sidebar.page_link("pages/🌱_Growth_Fund.py", label="🌱 Growth Fund")
        st.sidebar.page_link("pages/🤖_EA_Versions.py", label="🤖 EA Versions")
        st.sidebar.page_link("pages/🔔_Notifications.py", label="🔔 Notifications")
        st.sidebar.page_link("pages/📸_Testimonials.py", label="📸 Testimonials")

    # ── ADMIN + OWNER ONLY PAGES ──────────────────────────────────────────────
    if role in ["admin", "owner"]:
        st.sidebar.page_link("pages/📊_FTMO_Accounts.py", label="📊 FTMO Accounts")
        st.sidebar.page_link("pages/📜_Audit_Logs.py", label="📜 Audit Logs")
        st.sidebar.page_link("pages/📢_Announcements.py", label="📢 Announcements")
        st.sidebar.page_link("pages/📈_Reports_Export.py", label="📈 Reports Export")
        st.sidebar.page_link("pages/📁_File_Vault.py", label="📁 File Vault")
        st.sidebar.page_link("pages/💬_Messages.py", label="💬 Messages")

    # ── OWNER ONLY TOOLS ──────────────────────────────────────────────────────
    if role == "owner":
        st.sidebar.markdown("---")
        st.sidebar.subheader("👑 Owner Tools")
        st.sidebar.page_link("pages/🔑_License_Generator.py", label="🔑 License Generator")
        st.sidebar.page_link("pages/👤_Admin_Management.py", label="👤 Admin Management")
        st.sidebar.page_link("pages/🔮_Simulator.py", label="🔮 Simulator")

    # ── LOGOUT SECTION ────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", type="primary", use_container_width=True):
        # Clear ALL auth-related session state keys
        keys_to_clear = [
            "authenticated", "username", "full_name", "role",
            "theme", "just_logged_in", "_sidebar_rendered"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

        # Set flag for success message in main.py
        st.session_state["logging_out"] = True

        # Force redirect to public landing
        st.switch_page("main.py")
        st.rerun()  # Extra force refresh to ensure clean state