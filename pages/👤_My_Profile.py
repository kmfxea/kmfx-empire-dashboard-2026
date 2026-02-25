# pages/👤_My_Profile.py
import streamlit as st
import uuid
import bcrypt
from io import BytesIO
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
require_auth(min_role="client")  # or higher if needed

# ────────────────────────────────────────────────
# THEME COLORS (exact match with Dashboard)
# ────────────────────────────────────────────────
accent_primary = "#00ffaa"
accent_gold    = "#ffd700"
accent_glow    = "#00ffaa40"
accent_hover   = "#00ffcc"

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
st.markdown("Manage your account details, security, QR login, and personal settings.")

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
# PROFILE OVERVIEW – Glass Card Grid (Dashboard style)
# ────────────────────────────────────────────────
st.subheader("Profile Overview")
metrics = [
    ("Full Name", user.get("full_name", "—"), accent_primary),
    ("Username", user["username"], accent_gold),
    ("Role", user["role"].title(), accent_primary),
    ("Balance", f"${user.get('balance', 0):,.2f}", accent_gold),
]

cols = st.columns(4)
for col, (label, value, color) in zip(cols, metrics):
    with col:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:16px;">
            <h4 style="opacity:0.8; margin:0; font-size:1.1rem;">{label}</h4>
            <h2 style="margin:0.6rem 0 0; font-size:2.4rem; color:{color};">{value}</h2>
        </div>
        """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# QR LOGIN SECTION (with Regenerate)
# ────────────────────────────────────────────────
st.subheader("🔑 Quick Login QR Code")
st.markdown("Scan this on any device to log in instantly. Regenerate if you suspect it's compromised.")

qr_token = user.get("qr_token")
if not qr_token:
    qr_token = uuid.uuid4().hex
    supabase.table("users").update({"qr_token": qr_token}).eq("id", user["id"]).execute()
    log_action("QR Auto-Generated on Profile View", f"User: {user['full_name']}")

qr_url = generate_qr_url("https://kmfxea.streamlit.app", qr_token)   # ← change to your actual deployed URL
qr_bytes = generate_qr_image(qr_url)

col_qr, col_info = st.columns([3, 2])
with col_qr:
    st.image(qr_bytes, use_column_width=True, caption="Scan to login instantly")

with col_info:
    st.markdown(f"**Token (partial):** `{qr_token[:8]}...`")
    st.caption("Never share this token manually – only use the QR.")
    
    if st.button("🔄 Regenerate QR Code", type="primary", use_container_width=True):
        new_token = uuid.uuid4().hex
        supabase.table("users").update({"qr_token": new_token}).eq("id", user["id"]).execute()
        log_action("QR Regenerated by User", f"User: {user['full_name']}")
        st.success("New QR generated! Refreshing...")
        st.rerun()

# ────────────────────────────────────────────────
# CHANGE PASSWORD (secure with bcrypt)
# ────────────────────────────────────────────────
st.subheader("🔒 Change Password")
with st.form("change_password", clear_on_submit=True):
    old_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    
    submitted = st.form_submit_button("Update Password", type="primary", use_container_width=True)

if submitted:
    if not all([old_password, new_password, confirm_password]):
        st.error("All fields are required.")
    elif new_password != confirm_password:
        st.error("New passwords do not match.")
    elif len(new_password) < 8:
        st.error("New password must be at least 8 characters long.")
    else:
        # Verify old password
        if bcrypt.checkpw(old_password.encode('utf-8'), user["password"].encode('utf-8')):
            # Hash new password
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Update
            supabase.table("users").update({"password": hashed}).eq("id", user["id"]).execute()
            log_action("Password Changed Successfully", f"User: {user['full_name']}")
            st.success("Password updated! Logging you out for security...")
            # Force logout
            for key in ["authenticated", "username", "full_name", "role", "theme", "just_logged_in"]:
                st.session_state.pop(key, None)
            st.session_state["logging_out"] = True
            st.switch_page("main.py")
        else:
            st.error("Current password is incorrect.")

# ────────────────────────────────────────────────
# ADDITIONAL PROFILE SETTINGS (email + picture)
# ────────────────────────────────────────────────
st.subheader("⚙️ Account Settings")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Email Address**")
    current_email = user.get("email", "")
    new_email = st.text_input("Update Email", value=current_email, key="email_input")
    
    if st.button("Save Email", use_container_width=True):
        if new_email and new_email != current_email:
            supabase.table("users").update({"email": new_email}).eq("id", user["id"]).execute()
            log_action("Email Updated", f"User: {user['full_name']} → {new_email}")
            st.success("Email updated successfully!")
            st.rerun()
        else:
            st.info("No changes detected.")

with col2:
    st.markdown("**Profile Picture**")
    current_pic = user.get("profile_pic")
    if current_pic:
        st.image(current_pic, caption="Current Profile Picture", width=180)
    
    uploaded_file = st.file_uploader("Upload new picture", type=["jpg", "jpeg", "png"], key="pic_uploader")
    if uploaded_file:
        if st.button("Upload Picture", type="primary"):
            with st.spinner("Uploading..."):
                url, path = upload_to_supabase(
                    uploaded_file,
                    bucket="profiles",
                    folder="users",
                    use_signed_url=False
                )
                if url:
                    supabase.table("users").update({"profile_pic": url}).eq("id", user["id"]).execute()
                    log_action("Profile Picture Updated", f"User: {user['full_name']}")
                    st.success("Profile picture updated!")
                    st.rerun()
                else:
                    st.error("Upload failed. Please try again.")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER (same style as Dashboard)
# ────────────────────────────────────────────────
st.markdown(f"""
<div class="glass-card" style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
            border-radius:24px; border:2px solid {accent_primary}40;
            background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
            box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Your Empire • Your Control
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Secure • Personalized • Always Growing
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith, Shared for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)