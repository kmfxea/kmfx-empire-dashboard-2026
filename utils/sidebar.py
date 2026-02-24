# utils/sidebar.py
import streamlit as st

def render_sidebar():
    """
    Role-based sidebar navigation for KMFX Empire
    """
    # ── Force reset sidebar flag right after login (prevents empty sidebar bug) ──
    if st.session_state.get("just_logged_in", False):
        st.session_state.pop("_sidebar_rendered", None)
        st.session_state["just_logged_in"] = False  # consume the flag

    # ── Read role & name EARLY ───────────────────────────────────────────────
    role = st.session_state.get("role", "guest").lower().strip()
    full_name = st.session_state.get("full_name", "Guest")

    # ── Double-render prevention ─────────────────────────────────────────────
    if st.session_state.get("_sidebar_rendered", False):
        return

    st.session_state["_sidebar_rendered"] = True

    # ── User Info Header ─────────────────────────────────────────────────────
    st.sidebar.markdown(f"**👑 {full_name}**")
    st.sidebar.caption(f"Role: {role.title() if role != 'guest' else 'Not logged in'}")

    if role == "guest":
        st.sidebar.warning("No role detected – please log in again")
        return  # Early exit if something is wrong

    st.sidebar.markdown("### KMFX Empire")
    st.sidebar.markdown("---")

    # ── COMMON PAGES (all logged-in users) ───────────────────────────────────
    st.sidebar.page_link("pages/🏠_Dashboard.py", label="Dashboard", icon="🏠")
    st.sidebar.page_link("pages/👤_My_Profile.py", label="My Profile", icon="👤")

    # ── CLIENT + ADMIN + OWNER ───────────────────────────────────────────────
    if role in ["client", "admin", "owner"]:
        st.sidebar.page_link("pages/💰_Profit_Sharing.py", label="Profit Sharing", icon="💰")
        st.sidebar.page_link("pages/💳_Withdrawals.py", label="Withdrawals", icon="💳")
        st.sidebar.page_link("pages/🌱_Growth_Fund.py", label="Growth Fund", icon="🌱")
        st.sidebar.page_link("pages/🤖_EA_Versions.py", label="EA Versions", icon="🤖")
        st.sidebar.page_link("pages/🔔_Notifications.py", label="Notifications", icon="🔔")
        st.sidebar.page_link("pages/📸_Testimonials.py", label="Testimonials", icon="📸")

    # ── ADMIN + OWNER ONLY ───────────────────────────────────────────────────
    if role in ["admin", "owner"]:
        st.sidebar.page_link("pages/📊_FTMO_Accounts.py", label="FTMO Accounts", icon="📊")
        st.sidebar.page_link("pages/📜_Audit_Logs.py", label="Audit Logs", icon="📜")
        st.sidebar.page_link("pages/📢_Announcements.py", label="Announcements", icon="📢")
        st.sidebar.page_link("pages/📈_Reports_Export.py", label="Reports Export", icon="📈")
        st.sidebar.page_link("pages/📁_File_Vault.py", label="File Vault", icon="📁")
        st.sidebar.page_link("pages/💬_Messages.py", label="Messages", icon="💬")

    # ── OWNER ONLY ───────────────────────────────────────────────────────────
    if role == "owner":
        st.sidebar.markdown("---")
        st.sidebar.subheader("👑 Owner Tools")
        st.sidebar.page_link("pages/🔑_License_Generator.py", label="License Generator", icon="🔑")
        st.sidebar.page_link("pages/👤_Admin_Management.py", label="Admin Management", icon="👤")
        st.sidebar.page_link("pages/🔮_Simulator.py", label="Simulator", icon="🔮")

    # ── LOGOUT SECTION ───────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Account")

    if st.sidebar.button(
        "🚪 Logout",
        type="primary",
        use_container_width=True,
        key="logout_button",  # stable key is fine now
        help="End session and return to public page"
    ):
        # Clear session
        keys_to_clear = [
            "authenticated", "username", "full_name", "role",
            "just_logged_in", "theme", "_sidebar_rendered"
        ]
        for k in keys_to_clear:
            st.session_state.pop(k, None)

        st.session_state["logging_out"] = True
        st.session_state["logout_message"] = "Logged out successfully. See you again! 👋"

        st.switch_page("main.py")