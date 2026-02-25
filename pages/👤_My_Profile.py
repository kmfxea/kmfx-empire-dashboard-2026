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
# SIDEBAR + AUTH + THEME (first thing)
# ────────────────────────────────────────────────
render_sidebar()
require_auth(min_role="client")

accent_primary = "#00ffaa"
accent_gold = "#ffd700"
accent_glow = "#00ffaa40"
accent_hover = "#00ffcc"

# ────────────────────────────────────────────────
# WELCOME + BALLOONS
# ────────────────────────────────────────────────
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.success(f"Welcome to your profile, {st.session_state.full_name}! 👑")
    st.session_state.pop("just_logged_in", None)

# ────────────────────────────────────────────────
# SCROLL-TO-TOP
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
# HEADER
# ────────────────────────────────────────────────
st.header("👤 My Profile")
st.markdown("Your personal empire hub: manage details, security, finances, and preferences securely.")

# ────────────────────────────────────────────────
# FETCH USER DATA
# ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_user_data(username: str):
    try:
        resp = supabase.table("users").select("*").eq("username", username.lower()).execute()
        if resp.data:
            return resp.data[0]
        return None
    except Exception as e:
        st.error(f"Profile load error: {str(e)}")
        return None

user = get_user_data(st.session_state.username)
if not user:
    st.error("Could not load profile. Log out and back in.")
    st.stop()

# ────────────────────────────────────────────────
# TABS FOR ADVANCED ORGANIZATION
# ────────────────────────────────────────────────
tab_overview, tab_accounts, tab_security, tab_settings, tab_activity = st.tabs([
    "Overview", "Accounts & Shares", "Security", "Settings", "Activity"
])

# ────────────────────────────────────────────────
# TAB 1: OVERVIEW – Glass Card Grid + Editable Fields
# ────────────────────────────────────────────────
with tab_overview:
    st.subheader("Profile Overview")
    
    # Grid metrics
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

    # Editable personal info
    with st.form("edit_personal"):
        st.markdown("**Edit Personal Details**")
        full_name = st.text_input("Full Name", value=user.get("full_name", ""))
        phone = st.text_input("Phone Number", value=user.get("phone", ""))
        address = st.text_input("Address", value=user.get("address", ""))
        dob = st.date_input("Date of Birth", value=user.get("dob"), min_value=datetime(1900, 1, 1))
        email = st.text_input("Email", value=user.get("email", ""))

        if st.form_submit_button("Save Changes", type="primary"):
            updates = {}
            if full_name != user.get("full_name"): updates["full_name"] = full_name
            if phone != user.get("phone"): updates["phone"] = phone
            if address != user.get("address"): updates["address"] = address
            if dob != user.get("dob"): updates["dob"] = str(dob)
            if email != user.get("email"): updates["email"] = email

            if updates:
                supabase.table("users").update(updates).eq("id", user["id"]).execute()
                log_action("Profile Updated", f"User: {user['full_name']} - {updates}")
                st.success("Personal details updated!")
                st.rerun()
            else:
                st.info("No changes detected.")

    # Profile Picture
    st.markdown("**Profile Picture**")
    col1, col2 = st.columns([1, 3])
    with col1:
        if user.get("profile_pic"):
            st.image(user["profile_pic"], width=150, caption="Current")
        else:
            st.info("No picture")

    with col2:
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
            if any(user["username"] in str(c) for c in contrib + parts):
                user_accounts.append(acc)

        if user_accounts:
            for acc in user_accounts:
                phase = acc.get('current_phase', '—')
                equity = acc.get('current_equity', 0)
                st.markdown(f"""
                <div class="glass-card" style="padding:1.5rem; margin-bottom:1rem;">
                    <h3>{acc.get('name', 'Unnamed')} ({phase})</h3>
                    <p><strong>Equity:</strong> ${equity:,.2f}</p>
                    <p><strong>Your Role:</strong> Contributor/Participant</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No associated FTMO accounts yet.")
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
            st.metric("Total Received", f"${total:,.2f}")
        else:
            st.info("No profit shares received yet.")
    except Exception as e:
        st.error(f"Profit share error: {str(e)}")

# ────────────────────────────────────────────────
# TAB 3: SECURITY
# ────────────────────────────────────────────────
with tab3:
    st.subheader("QR Login Code")
    qr_token = user.get("qr_token")
    if not qr_token:
        qr_token = str(uuid.uuid4())
        supabase.table("users").update({"qr_token": qr_token}).eq("id", user["id"]).execute()
        log_action("QR Generated", f"User: {user['full_name']}")

    qr_url = generate_qr_url("https://kmfxea.streamlit.app", qr_token)  # ← YOUR APP URL HERE
    qr_bytes = generate_qr_image(qr_url)

    col_qr, col_info = st.columns([2, 1])
    with col_qr:
        st.image(qr_bytes, use_column_width=True, caption="Scan to login")
    with col_info:
        st.markdown(f"**Token (partial):** `{qr_token[:8]}...`")
        if st.button("🔄 Regenerate QR", type="primary"):
            new_token = str(uuid.uuid4())
            supabase.table("users").update({"qr_token": new_token}).eq("id", user["id"]).execute()
            log_action("QR Regenerated", f"User: {user['full_name']}")
            st.success("New QR! Refreshing...")
            st.rerun()

    st.subheader("Change Password")
    with st.form("change_pass"):
        old_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New", type="password")
        submitted = st.form_submit_button("Update", type="primary")

    if submitted:
        if not old_pass or not new_pass or not confirm_pass:
            st.error("All fields required.")
        elif new_pass != confirm_pass:
            st.error("Passwords do not match.")
        elif len(new_pass) < 8:
            st.error("New password must be 8+ characters.")
        elif bcrypt.checkpw(old_pass.encode('utf-8'), user["password"].encode('utf-8')):
            hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            supabase.table("users").update({"password": hashed}).eq("id", user["id"]).execute()
            log_action("Password Changed", f"User: {user['full_name']}")
            st.success("Updated! Logging out...")
            for key in ["authenticated", "username", "full_name", "role", "theme", "just_logged_in"]:
                st.session_state.pop(key, None)
            st.session_state["logging_out"] = True
            st.switch_page("main.py")
        else:
            st.error("Current password incorrect.")

# ────────────────────────────────────────────────
# TAB 4: SETTINGS
# ────────────────────────────────────────────────
with tab4:
    st.subheader("Notification Preferences")
    prefs = user.get("prefs", {})
    profit_n = st.checkbox("Profit Share Alerts", value=prefs.get("profit_share", True))
    wd_n = st.checkbox("Withdrawal Status", value=prefs.get("withdrawal_status", True))
    acc_n = st.checkbox("Account Updates", value=prefs.get("account_updates", True))
    ann_n = st.checkbox("Announcements", value=prefs.get("announcements", True))

    if st.button("Save Preferences"):
        new_prefs = {"profit_share": profit_n, "withdrawal_status": wd_n, "account_updates": acc_n, "announcements": ann_n}
        supabase.table("users").update({"prefs": new_prefs}).eq("id", user["id"]).execute()
        log_action("Prefs Updated", f"User: {user['full_name']}")
        st.success("Saved!")
        st.rerun()

# ────────────────────────────────────────────────
# TAB 5: ACTIVITY
# ────────────────────────────────────────────────
with tab5:
    st.subheader("Recent Activity")
    try:
        logs = supabase.table("logs").select("*").eq("user_name", user["full_name"]).order("timestamp", desc=True).limit(10).execute().data or []
        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(df[["timestamp", "action", "details"]], use_container_width=True)
        else:
            st.info("No recent activity.")
    except Exception as e:
        st.error(f"Activity error: {str(e)}")

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