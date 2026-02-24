# utils/sidebar.py
import streamlit as st

def show_custom_sidebar():
    """
    Custom sidebar na role-based, may user info sa itaas,
    grouped sections, at Logout button sa baba.
    """
    st.sidebar.title("KMFX Empire")

    # ── User Info Section ────────────────────────────────────────
    if "authenticated" in st.session_state and st.session_state.authenticated:
        full_name = st.session_state.get("full_name", "User")
        role = st.session_state.get("role", "unknown").capitalize()

        st.sidebar.markdown(
            f"""
            **👑 {full_name}**  
            Role: **{role}**
            """,
            unsafe_allow_html=True
        )
    else:
        st.sidebar.info("Not logged in")

    st.sidebar.markdown("---")

    # ── Navigation Links ─────────────────────────────────────────
    role = st.session_state.get("role", "").lower()

    # Everyone (logged-in)
    st.sidebar.page_link("pages/🏠_Dashboard.py", label="🏠 Dashboard")
    st.sidebar.page_link("pages/👤_My_Profile.py", label="👤 My Profile")

    # Client + Admin + Owner
    if role in ["client", "admin", "owner"]:
        st.sidebar.page_link("pages/💰_Profit_Sharing.py", label="💰 Profit Sharing")
        st.sidebar.page_link("pages/💳_Withdrawals.py", label="💳 Withdrawals")
        st.sidebar.page_link("pages/🌱_Growth_Fund.py", label="🌱 Growth Fund")
        st.sidebar.page_link("pages/🤖_EA_Versions.py", label="🤖 EA Versions")
        st.sidebar.page_link("pages/🔔_Notifications.py", label="🔔 Notifications")
        st.sidebar.page_link("pages/📸_Testimonials.py", label="📸 Testimonials")

    # Admin + Owner
    if role in ["admin", "owner"]:
        st.sidebar.page_link("pages/📊_FTMO_Accounts.py", label="📊 FTMO Accounts")
        st.sidebar.page_link("pages/📜_Audit_Logs.py", label="📜 Audit Logs")
        st.sidebar.page_link("pages/📢_Announcements.py", label="📢 Announcements")
        st.sidebar.page_link("pages/📈_Reports_Export.py", label="📈 Reports Export")
        st.sidebar.page_link("pages/📁_File_Vault.py", label="📁 File Vault")
        st.sidebar.page_link("pages/💬_Messages.py", label="💬 Messages")

    # Owner Only
    if role == "owner":
        st.sidebar.markdown("---")
        st.sidebar.subheader("👑 Owner Tools")
        st.sidebar.page_link("pages/🔑_License_Generator.py", label="🔑 License Generator")
        st.sidebar.page_link("pages/👤_Admin_Management.py", label="👤 Admin Management")
        st.sidebar.page_link("pages/🔮_Simulator.py", label="🔮 Simulator")
        # ← idagdag mo rito kung may iba pang owner-only pages

    # ── Footer / Logout ──────────────────────────────────────────
    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Logout", type="primary", use_container_width=True):
        # Clear lahat ng session state keys
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Balik sa main login page
        st.switch_page("main.py")   # siguraduhin na tama ang path (kung nasa root si main.py)
        # Alternatibo: st.rerun() kung gusto mo lang i-refresh pero mas safe ang switch_page dito