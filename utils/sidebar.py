# utils/sidebar.py
import streamlit as st

def render_sidebar():
    """
    Role-based sidebar – laging fresh, walang caching o flag na magpapasira
    """
    role = st.session_state.get("role", "guest").lower().strip()
    full_name = st.session_state.get("full_name", "Guest")

    # User header
    st.sidebar.markdown(f"**👑 {full_name}**")
    st.sidebar.caption(f"Role: {role.title() if role != 'guest' else 'Not logged in'}")
    st.sidebar.markdown("---")

    # Navigation links based on role
    common_pages = [
        ("🏠 Dashboard", "pages/🏠_Dashboard.py"),
        ("👤 My Profile", "pages/👤_My_Profile.py"),
    ]

    client_admin_owner_pages = [
        ("💰 Profit Sharing", "pages/💰_Profit_Sharing.py"),
        ("💳 Withdrawals", "pages/💳_Withdrawals.py"),
        ("🌱 Growth Fund", "pages/🌱_Growth_Fund.py"),
        ("🤖 EA Versions", "pages/🤖_EA_Versions.py"),
        ("🔔 Notifications", "pages/🔔_Notifications.py"),
        ("📸 Testimonials", "pages/📸_Testimonials.py"),
    ]

    admin_owner_pages = [
        ("📊 FTMO Accounts", "pages/📊_FTMO_Accounts.py"),
        ("📜 Audit Logs", "pages/📜_Audit_Logs.py"),
        ("📢 Announcements", "pages/📢_Announcements.py"),
        ("📈 Reports Export", "pages/📈_Reports_Export.py"),
        ("📁 File Vault", "pages/📁_File_Vault.py"),
        ("💬 Messages", "pages/💬_Messages.py"),
    ]

    owner_only_pages = [
        ("🔑 License Generator", "pages/🔑_License_Generator.py"),
        ("👤 Admin Management", "pages/👤_Admin_Management.py"),
        ("🔮 Simulator", "pages/🔮_Simulator.py"),
    ]

    # Render common pages for all logged-in users
    for label, page in common_pages:
        st.sidebar.page_link(page, label=label, icon=label.split()[0])

    # Client + Admin + Owner
    if role in ["client", "admin", "owner"]:
        for label, page in client_admin_owner_pages:
            st.sidebar.page_link(page, label=label, icon=label.split()[0])

    # Admin + Owner
    if role in ["admin", "owner"]:
        for label, page in admin_owner_pages:
            st.sidebar.page_link(page, label=label, icon=label.split()[0])

    # Owner only
    if role == "owner":
        st.sidebar.markdown("---")
        st.sidebar.subheader("👑 Owner Tools")
        for label, page in owner_only_pages:
            st.sidebar.page_link(page, label=label, icon=label.split()[0])

    # Logout button (simple & reliable)
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", type="primary", use_container_width=True):
        # Clear session
        for key in ["authenticated", "username", "full_name", "role", "theme", "just_logged_in"]:
            st.session_state.pop(key, None)
        st.session_state["logging_out"] = True
        st.switch_page("main.py")