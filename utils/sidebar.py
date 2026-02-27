import streamlit as st
from utils.supabase_client import supabase

def render_sidebar():
    """
    Role-based sidebar navigation – UPGRADED FOR LUPETAN
    """
    # Get current user info safely
    role = st.session_state.get("role", "guest").lower().strip()
    full_name = st.session_state.get("full_name", "Guest")
    username = st.session_state.get("username", "")

    with st.sidebar:
        # ─── HEADER & PROFILE ───
        st.markdown(f"### 🚀 Empire Command")
        
        # Profile Section
        st.markdown(f"""
        <div style="background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px;">
            <strong>👑 {full_name}</strong><br>
            <span style="font-size:0.8rem; color:#aaa;">Role: {role.title() if role != 'guest' else 'Visitor'}</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        # ─── NAVIGATION ───
        st.page_link("🏠_Dashboard.py", label="Dashboard", icon="📊")
        st.page_link("pages/👤_My_Profile.py", label="Profile", icon="👤")

        # ─── DYNAMIC LINKS & ANIMATED BELL ───
        unread_count = 0
        if username:
            try:
                # Optimized count query
                unread_data = supabase.table("messages").select("id", count="exact").eq("to_client", username).execute()
                unread_count = unread_data.count
            except:
                unread_count = 0
        
        # Animated Notification Bell Logic
        bell_icon = "🔔"
        if unread_count > 0:
            st.markdown(f"""
            <style>
                @keyframes pulse {{
                    0% {{ box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.4); }}
                    70% {{ box-shadow: 0 0 0 10px rgba(255, 215, 0, 0); }}
                    100% {{ box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }}
                }}
                .gold-pulse {{
                    animation: pulse 1.5s infinite;
                    border-radius: 50%;
                }}
            </style>
            """, unsafe_allow_html=True)
            bell_label = f"Messages ({unread_count})"
        else:
            bell_label = "Messages (0)"
            
        st.page_link("pages/💬_Messages.py", label=bell_label, icon="💬")

        st.markdown("---")
        
        # ─── ROLE BASED MENU ───
        if role == "client":
            st.subheader("Personal Portal")
            st.page_link("pages/💰_Profit_Sharing.py", label="My Earnings", icon="💰")
            st.page_link("pages/💳_Withdrawals.py", label="Withdrawals", icon="💳")
            st.page_link("pages/🌱_Growth_Fund.py", label="Growth Fund", icon="🌱")
            st.page_link("pages/📸_Testimonials.py", label="Testimonials", icon="📸")

        elif role == "admin":
            st.subheader("Operations")
            st.page_link("pages/📊_FTMO_Accounts.py", label="Account Monitoring", icon="📊")
            st.page_link("pages/💰_Profit_Sharing.py", label="Record Profit", icon="💰")
            st.page_link("pages/💳_Withdrawals.py", label="Withdrawals Ops", icon="💳")
            st.page_link("pages/🌱_Growth_Fund.py", label="Fund Management", icon="🌱")
            st.page_link("pages/📁_File_Vault.py", label="File Vault", icon="📁")
            st.page_link("pages/📊_Whitelist_Monitor.py", label="Whitelist Scan", icon="📡")
            st.page_link("pages/📸_Testimonials.py", label="Moderate Views", icon="📸")
            st.page_link("pages/📢_Announcements.py", label="Announcements", icon="📢")

        elif role == "owner":
            st.subheader("Control Panel")
            st.page_link("pages/📊_FTMO_Accounts.py", label="Empire Portfolio", icon="📊")
            st.page_link("pages/💰_Profit_Sharing.py", label="Profit Distribution", icon="💰")
            st.page_link("pages/🌱_Growth_Fund.py", label="Growth Fund Hub", icon="🌱")
            st.page_link("pages/💳_Withdrawals.py", label="Financial Control", icon="💳")
            
            st.subheader("System")
            st.page_link("pages/🤖_EA_Versions.py", label="EA Engine", icon="🤖")
            st.page_link("pages/🔑_License_Generator.py", label="License Key", icon="🔑")
            st.page_link("pages/👤_Admin_Management.py", label="Admin Control", icon="👤")
            st.page_link("pages/📊_Whitelist_Monitor.py", label="Security Scan", icon="📡")
            
            st.subheader("Broadcast")
            st.page_link("pages/📜_Audit_Logs.py", label="Audit Logs", icon="📜")
            st.page_link("pages/📢_Announcements.py", label="Announcements", icon="📢")
            st.page_link("pages/📁_File_Vault.py", label="File Vault", icon="📁")
            
            st.subheader("Analytics")
            st.page_link("pages/🔮_Simulator.py", label="Future Simulator", icon="🔮")
            st.page_link("pages/📈_Reports_Export.py", label="Data Export", icon="📈")

        # ─── LOGOUT ───
        st.markdown("---")
        if st.button("🚪 Logout", type="primary", use_container_width=True):
            # Clear auth-related session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state["logging_out"] = True
            st.switch_page("main.py")