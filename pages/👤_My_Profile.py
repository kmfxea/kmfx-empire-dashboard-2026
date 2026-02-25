# pages/👤_My_Profile.py
import streamlit as st
import uuid
import bcrypt
import pandas as pd
from datetime import datetime

from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase
from utils.helpers import (
    log_action,
    generate_qr_image,
    generate_qr_url,
    upload_to_supabase
)

# ────────────────────────────────────────────────
# SIDEBAR + AUTH (must be first)
# ────────────────────────────────────────────────
render_sidebar()
require_auth(min_role="client")

# ────────────────────────────────────────────────
# THEME COLORS (exact match with Dashboard)
# ────────────────────────────────────────────────
accent_primary = "#00ffaa"
accent_gold = "#ffd700"
accent_glow = "#00ffaa40"
accent_hover = "#00ffcc"

# ────────────────────────────────────────────────
# WELCOME + BALLOONS ON FRESH LOGIN
# ────────────────────────────────────────────────
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.success(f"Welcome to your profile, {st.session_state.full_name}! 👑")
    st.session_state.pop("just_logged_in", None)

# ────────────────────────────────────────────────
# SCROLL-TO-TOP (same optimized script as Dashboard)
# ────────────────────────────────────────────────
st.markdown("""
<script>
function forceScrollToTop() {
    window.scrollTo({top: 0, behavior: 'smooth'});
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
    const main = parent.document.querySelector(".main .block-container");
    if (main) main.scrollTop = 0;
}
const observer = new MutationObserver(() => {
    setTimeout(forceScrollToTop, 300);
    setTimeout(forceScrollToTop, 1200);
});
const target = parent.document.querySelector(".main") || document.body;
observer.observe(target, { childList: true, subtree: true, attributes: true });
setTimeout(forceScrollToTop, 800);
setTimeout(forceScrollToTop, 2000);
</script>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# PAGE HEADER
# ────────────────────────────────────────────────
st.header("👤 My Profile")
st.markdown("Your personal empire hub: manage details, security, finances, and preferences securely.")

# ────────────────────────────────────────────────
# FETCH CURRENT USER DATA
# ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_user_data(username: str):
    try:
        resp = supabase.table("users").select("*").eq("username", username.lower()).execute()
        if resp.data:
            return resp.data[0]
        return None
    except Exception as e:
        st.error(f"Could not load profile data: {str(e)}")
        return None

user = get_user_data(st.session_state.username)
if not user:
    st.error("Profile data not found. Please try logging in again.")
    st.stop()

# ────────────────────────────────────────────────
# TABS FOR ADVANCED ORGANIZATION (fixed variable names to avoid NameError)
# ────────────────────────────────────────────────
tab_overview, tab_accounts, tab_security, tab_settings, tab_activity = st.tabs([
    "Overview", "Accounts & Shares", "Security", "Settings", "Activity"
])

# ────────────────────────────────────────────────
# TAB 1: OVERVIEW – Glass Card Grid + Editable Fields
# ────────────────────────────────────────────────
with tab_overview:
    st.subheader("Profile Overview")
    
    metrics = [
        ("Full Name", user.get("full_name", "—"), accent_primary),
        ("Username", user["username"], accent_gold),
        ("Role", user["role"].title(), accent_primary),
        ("Balance", f"${user.get('balance', 0):,.2f}", accent_gold),
        ("Phone", user.get("phone", "Not set"), accent_primary),
        ("Email", user.get("email", "Not set"), accent_gold),
        ("Address", user.get("address", "Not set"), accent_primary),
        ("Date of Birth", user.get("dob", "Not set"), accent_gold),
    ]

    cols = st.columns(4)
    for i, (label, value, color) in enumerate(metrics):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:16px;">
                <h4 style="opacity:0.8; margin:0; font-size:1.1rem;">{label}</h4>
                <h3 style="margin:0.6rem 0 0; font-size:2rem; color:{color};">{value}</h3>
            </div>
            """, unsafe_allow_html=True)

    # Editable personal info form
    with st.form("edit_personal"):
        st.markdown("**Edit Personal Details**")
        full_name_edit = st.text_input("Full Name", value=user.get("full_name", ""))
        phone_edit = st.text_input("Phone Number", value=user.get("phone", ""))
        address_edit = st.text_input("Address", value=user.get("address", ""))
        dob_edit = st.date_input("Date of Birth", value=user.get("dob") if user.get("dob") else None, min_value=datetime(1900, 1, 1))
        email_edit = st.text_input("Email", value=user.get("email", ""))

        if st.form_submit_button("Save Changes", type="primary"):
            updates = {}
            if full_name_edit != user.get("full_name"): updates["full_name"] = full_name_edit
            if phone_edit != user.get("phone"): updates["phone"] = phone_edit
            if address_edit != user.get("address"): updates["address"] = address_edit
            if dob_edit != user.get("dob"): updates["dob"] = str(dob_edit)
            if email_edit != user.get("email"): updates["email"] = email_edit

            if updates:
                supabase.table("users").update(updates).eq("id", user["id"]).execute()
                log_action("Profile Updated", f"User: {user['full_name']} - {updates}")
                st.success("Details updated!")
                st.rerun()
            else:
                st.info("No changes.")

    # Profile Picture
    st.markdown("**Profile Picture**")
    col_pic1, col_pic2 = st.columns([1, 3])
    with col_pic1:
        if user.get("profile_pic"):
            st.image(user["profile_pic"], width=150, caption="Current")
        else:
            st.info("No picture set")

    with col_pic2:
        uploaded = st.file_uploader("Upload new picture", type=["jpg", "jpeg", "png"])
        if uploaded and st.button("Upload & Save", type="primary"):
            with st.spinner("Uploading..."):
                url, _ = upload_to_supabase(uploaded, bucket="profiles", folder="users")
                if url:
                    supabase.table("users").update({"profile_pic": url}).eq("id", user["id"]).execute()
                    log_action("Profile Pic Updated", f"User: {user['full_name']}")
                    st.success("Picture updated!")
                    st.rerun()
                else:
                    st.error("Upload failed.")

# ────────────────────────────────────────────────
# TAB 2: ACCOUNTS & SHARES
# ────────────────────────────────────────────────
with tab_accounts:
    st.subheader("Associated FTMO Accounts")
    try:
        accounts = supabase.table("ftmo_accounts").select("*").execute().data or []
        user_accounts = []
        for acc in accounts:
            contrib = acc.get("contributors_v2", []) or acc.get("contributors", [])
            parts = acc.get("participants_v2", []) or acc.get("participants", [])
            if any(user["username"] in str(item) for item in contrib + parts):
                user_accounts.append(acc)

        if user_accounts:
            for acc in user_accounts:
                st.markdown(f"""
                <div class="glass-card" style="padding:1.5rem; margin-bottom:1rem;">
                    <h3>{acc.get('name', 'Unnamed Account')} ({acc.get('current_phase', '—')})</h3>
                    <p><strong>Equity:</strong> ${acc.get('current_equity', 0):,.2f}</p>
                    <p><strong>Your Role:</strong> Contributor/Participant</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("You are not associated with any FTMO accounts yet.")
    except Exception as e:
        st.error(f"Accounts error: {str(e)}")

    st.subheader("Profit Share Summary")
    try:
        dists = supabase.table("profit_distributions").select("*").eq("participant_user_id", user["id"]).execute().data or []
        if dists:
            df = pd.DataFrame(dists)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            st.dataframe(df[["timestamp", "share_amount", "percentage"]], use_container_width=True)
            total = df["share_amount"].sum()
            st.metric("Total Profit Share Received", f"${total:,.2f}")
        else:
            st.info("No profit distributions received yet.")
    except Exception as e:
        st.error(f"Profit share error: {str(e)}")

# ────────────────────────────────────────────────
# TAB 3: SECURITY
# ────────────────────────────────────────────────
with tab_security:
    st.subheader("🔑 Quick Login QR Code")
    qr_token = user.get("qr_token")
    if not qr_token:
        qr_token = str(uuid.uuid4())
        supabase.table("users").update({"qr_token": qr_token}).eq("id", user["id"]).execute()
        log_action("QR Auto-Generated", f"User: {user['full_name']}")

    qr_url = generate_qr_url("https://kmfxea.streamlit.app", qr_token)  # CHANGE TO YOUR ACTUAL APP URL
    qr_bytes = generate_qr_image(qr_url)

    col_qr, col_info = st.columns([3, 2])
    with col_qr:
        st.image(qr_bytes, use_column_width=True, caption="Scan to login instantly")
    with col_info:
        st.markdown(f"**Token (partial):** `{qr_token[:8]}...`")
        st.caption("Never share this token manually – only use the QR.")
        if st.button("🔄 Regenerate QR Code", type="primary", use_container_width=True):
            new_token = str(uuid.uuid4())
            supabase.table("users").update({"qr_token": new_token}).eq("id", user["id"]).execute()
            log_action("QR Regenerated", f"User: {user['full_name']}")
            st.success("New QR generated! Refreshing...")
            st.rerun()

    st.subheader("🔒 Change Password")
    with st.form("change_password", clear_on_submit=True):
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Update Password", type="primary")

    if submitted:
        if not all([old_password, new_password, confirm_password]):
            st.error("All fields are required.")
        elif new_password != confirm_password:
            st.error("New passwords do not match.")
        elif len(new_password) < 8:
            st.error("New password must be at least 8 characters long.")
        else:
            if bcrypt.checkpw(old_password.encode('utf-8'), user["password"].encode('utf-8')):
                hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                supabase.table("users").update({"password": hashed}).eq("id", user["id"]).execute()
                log_action("Password Changed Successfully", f"User: {user['full_name']}")
                st.success("Password updated! Logging you out for security...")
                for key in ["authenticated", "username", "full_name", "role", "theme", "just_logged_in"]:
                    st.session_state.pop(key, None)
                st.session_state["logging_out"] = True
                st.switch_page("main.py")
            else:
                st.error("Current password is incorrect.")

# ────────────────────────────────────────────────
# TAB 4: SETTINGS
# ────────────────────────────────────────────────
with tab_settings:
    st.subheader("Notification Preferences")
    prefs = user.get("prefs", {})
    profit_notif = st.checkbox("Notify on Profit Share", value=prefs.get("profit_share", True))
    wd_notif = st.checkbox("Notify on Withdrawal Status", value=prefs.get("withdrawal_status", True))
    acc_notif = st.checkbox("Notify on Account Updates", value=prefs.get("account_updates", True))
    ann_notif = st.checkbox("Notify on Announcements", value=prefs.get("announcements", True))

    if st.button("Save Preferences"):
        new_prefs = {
            "profit_share": profit_notif,
            "withdrawal_status": wd_notif,
            "account_updates": acc_notif,
            "announcements": ann_notif
        }
        supabase.table("users").update({"prefs": new_prefs}).eq("id", user["id"]).execute()
        log_action("Preferences Updated", f"User: {user['full_name']}")
        st.success("Preferences saved!")
        st.rerun()

# ────────────────────────────────────────────────
# TAB 5: ACTIVITY
# ────────────────────────────────────────────────
with tab_activity:
    st.subheader("Recent Activity")
    try:
        activities = supabase.table("logs").select("*").eq("user_name", user["full_name"]).order("timestamp", desc=True).limit(10).execute().data or []
        if activities:
            df = pd.DataFrame(activities)
            st.dataframe(df[["timestamp", "action", "details"]], use_container_width=True)
        else:
            st.info("No recent activity.")
    except Exception as e:
        st.error(f"Activity load error: {str(e)}")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class="glass-card" style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
            border-radius:24px; border:2px solid {accent_primary}40;
            background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
            box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Your Profile • Your Empire
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Secure • Personalized • Always Growing
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith, Shared for Generations 👑
    </h2>
</div>
""", unsafe_allow_html=True)