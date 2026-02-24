# utils/sidebar.py
import streamlit as st

def render_sidebar():
    """
    Role-based sidebar navigation para sa KMFX Empire
    - Client: limited pages lang
    - Admin: client pages + admin tools
    - Owner: lahat ng pages
    """
    role = st.session_state.get("role", "guest").lower()

    # Greeting + Role badge (para mas personal)
    st.sidebar.markdown(f"**👑 {st.session_state.get('full_name', 'User')}**")
    st.sidebar.caption(f"Role: {role.title()}")

    st.sidebar.title("KMFX Empire")

    # ── COMMON / CLIENT PAGES (lahat ng roles nakikita 'to) ────────────────
    st.sidebar.page_link("pages/🏠_Dashboard.py", label="Dashboard", icon="🏠")
    st.sidebar.page_link("pages/👤_My_Profile.py", label="My Profile", icon="👤")
    st.sidebar.page_link("pages/💰_Profit_Sharing.py", label="Profit Sharing", icon="💰")
    st.sidebar.page_link("pages/💳_Withdrawals.py", label="Withdrawals", icon="💳")

    # ── EXTENDED CLIENT + ADMIN + OWNER PAGES ──────────────────────────────
    if role in ["client", "admin", "owner"]:
        st.sidebar.page_link("pages/🌱_Growth_Fund.py", label="Growth Fund", icon="🌱")
        st.sidebar.page_link("pages/🤖_EA_Versions.py", label="EA Versions", icon="🤖")
        st.sidebar.page_link("pages/🔔_Notifications.py", label="Notifications", icon="🔔")
        st.sidebar.page_link("pages/📸_Testimonials.py", label="Testimonials", icon="📸")  # optional, kung may ganito

    # ── ADMIN + OWNER ONLY (hindi makikita ng client) ───────────────────────
    if role in ["admin", "owner"]:
        st.sidebar.page_link("pages/📊_FTMO_Accounts.py", label="FTMO Accounts", icon="📊")
        st.sidebar.page_link("pages/📜_Audit_Logs.py", label="Audit Logs", icon="📜")
        st.sidebar.page_link("pages/📢_Announcements.py", label="Announcements", icon="📢")
        st.sidebar.page_link("pages/📈_Reports_Export.py", label="Reports Export", icon="📈")
        st.sidebar.page_link("pages/📁_File_Vault.py", label="File Vault", icon="📁")          # kung may access admin
        st.sidebar.page_link("pages/💬_Messages.py", label="Messages", icon="💬")              # kung admin can manage messages

    # ── OWNER ONLY (hindi makikita ng client at admin) ──────────────────────
    if role == "owner":
        st.sidebar.page_link("pages/🔑_License_Generator.py", label="License Generator", icon="🔑")
        st.sidebar.page_link("pages/👤_Admin_Management.py", label="Admin Management", icon="👤")
        st.sidebar.page_link("pages/🔮_Simulator.py", label="Simulator", icon="🔮")
        # Kung may iba pang owner-exclusive pages, idagdag mo rito

    # ── LOGOUT ──────────────────────────────────────────────────────────────
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout", type="secondary", use_container_width=True):
        # Clear lahat ng auth keys
        auth_keys = ["authenticated", "username", "full_name", "role", "just_logged_in", "theme"]
        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]

        # Optional: total clear (kung walang ibang mahalagang session state)
        # st.session_state.clear()

        st.success("Logged out successfully!")
        import time
        time.sleep(1.2)  # para makita yung success message

        st.switch_page("main.py")