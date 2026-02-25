# pages/👤_My_Profile.py
import streamlit as st
import bcrypt
from datetime import datetime
import uuid
import qrcode
from io import BytesIO
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase
from utils.helpers import log_action

# ────────────────────────────────────────────────
# SIDEBAR + AUTH (must be first)
# ────────────────────────────────────────────────
render_sidebar()
require_auth(min_role="client")

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
    st.success(f"Welcome to your profile, {st.session_state.get('full_name', 'Trader')}! 👑")
    st.session_state.pop("just_logged_in", None)

# ────────────────────────────────────────────────
# SCROLL-TO-TOP (same script as Dashboard)
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
    setTimeout(forceScrollToTop, 2500);
});
const target = parent.document.querySelector(".main") || document.body;
observer.observe(target, { childList: true, subtree: true, attributes: true });
setTimeout(forceScrollToTop, 800);
setTimeout(forceScrollToTop, 2000);
setTimeout(forceScrollToTop, 4000);
</script>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# HEADER
# ────────────────────────────────────────────────
st.header("👤 My Profile")
st.markdown("**Your personal command center** • Manage details, accounts & security")

# ────────────────────────────────────────────────
# LOAD USER DATA
# ────────────────────────────────────────────────
@st.cache_data(ttl=45)
def get_user(username):
    try:
        res = supabase.table("users").select("*").eq("username", username.lower()).single().execute()
        return res.data if res.data else None
    except:
        return None

user = get_user(st.session_state.username)

if not user:
    st.error("Cannot load profile. Please log out and log in again.")
    st.stop()

# ────────────────────────────────────────────────
# TABS (3 clean sections)
# ────────────────────────────────────────────────
tab_profile, tab_accounts, tab_security = st.tabs([
    "Personal Details",
    "My Accounts & Shares",
    "Security & Password"
])

# ────────────────────────────────
# TAB 1: Personal Details (glass card style)
# ────────────────────────────────
with tab_profile:
    st.subheader("Your Information")

    # Main info card
    st.markdown(f"""
    <div class="glass-card" style="padding:2rem; border-radius:12px; text-align:center; max-width:700px; margin:0 auto 2rem;">
        <h2 style="margin:0 0 1.5rem; color:{accent_primary};">{user.get('full_name', 'Trader')}</h2>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:1.5rem;">
            <div>
                <h4 style="opacity:0.7; margin:0 0 0.4rem;">Username</h4>
                <p style="font-size:1.3rem; margin:0; font-weight:600;">{user['username']}</p>
            </div>
            <div>
                <h4 style="opacity:0.7; margin:0 0 0.4rem;">Role</h4>
                <p style="font-size:1.3rem; margin:0; color:{accent_gold};">{user['role'].title()}</p>
            </div>
            <div>
                <h4 style="opacity:0.7; margin:0 0 0.4rem;">Balance</h4>
                <p style="font-size:1.3rem; margin:0; color:{accent_primary};">${user.get('balance', 0):,.2f}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Editable fields in glass-card form
    with st.form("edit_profile"):
        st.markdown("**Update Personal Information**")
        cols = st.columns(2)
        with cols[0]:
            full_name_new = st.text_input("Full Name", value=user.get("full_name", ""))
            phone_new     = st.text_input("Phone Number", value=user.get("phone", ""))
            email_new     = st.text_input("Email", value=user.get("email", ""))
        with cols[1]:
            address_new   = st.text_input("Address", value=user.get("address", ""))
            dob_new       = st.date_input(
                "Date of Birth",
                value=user.get("dob"),
                min_value=datetime(1950, 1, 1),
                max_value=datetime.now()
            )

        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
            updates = {}
            if full_name_new != user.get("full_name"): updates["full_name"] = full_name_new
            if phone_new     != user.get("phone"):     updates["phone"]     = phone_new
            if email_new     != user.get("email"):     updates["email"]     = email_new
            if address_new   != user.get("address"):   updates["address"]   = address_new
            if str(dob_new)  != str(user.get("dob")):  updates["dob"]       = str(dob_new) if dob_new else None

            if updates:
                try:
                    supabase.table("users").update(updates).eq("id", user["id"]).execute()
                    log_action("Profile Updated", f"{updates}")
                    st.success("Information updated successfully!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Update failed: {ex}")
            else:
                st.info("No changes detected.")

# ────────────────────────────────
# TAB 2: Accounts & Shares
# ────────────────────────────────
with tab_accounts:
    st.subheader("Accounts You Are Involved In")

    try:
        all_acc = supabase.table("ftmo_accounts").select("*").execute().data or []
        my_acc = []
        uname = user["username"]

        for acc in all_acc:
            contrib = acc.get("contributors_v2") or acc.get("contributors", [])
            partic = acc.get("participants_v2") or acc.get("participants", [])
            if any(uname in str(x) for x in contrib + partic):
                my_acc.append(acc)

        if not my_acc:
            st.info("You are not associated with any accounts yet.")
        else:
            for acc in my_acc:
                st.markdown(f"""
                <div class="glass-card" style="padding:1.6rem; margin-bottom:1.2rem; border-radius:12px;">
                    <h3 style="margin:0 0 1rem; color:{accent_primary};">{acc.get('name', 'Unnamed Account')}</h3>
                    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px,1fr)); gap:1rem;">
                        <div><strong>Phase:</strong> {acc.get('current_phase', '—')}</div>
                        <div><strong>Equity:</strong> ${acc.get('current_equity',0):,.2f}</div>
                        <div><strong>Withdrawable:</strong> ${acc.get('withdrawable_balance',0):,.2f}</div>
                        <div><strong>Split:</strong> {acc.get('ftmo_split',80)}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    except Exception as ex:
        st.error(f"Could not load accounts: {ex}")

    # Simple profit share summary
    st.subheader("Profit Share Received")
    try:
        dists = supabase.table("profit_distributions")\
                .select("timestamp, share_amount")\
                .eq("participant_user_id", user["id"])\
                .order("timestamp", desc=True)\
                .limit(10)\
                .execute().data or []

        if dists:
            total = sum(d.get("share_amount", 0) for d in dists)
            st.metric("Total Received", f"${total:,.2f}")
            with st.expander("Last distributions"):
                st.dataframe(
                    [{"Date": d["timestamp"][:10], "Amount": f"${d['share_amount']:,.2f}"} for d in dists],
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No profit distributions received yet.")
    except:
        st.caption("Profit history temporarily unavailable.")

# ────────────────────────────────
# TAB 3: Security
# ────────────────────────────────
with tab_security:
    st.subheader("Security Settings")

    # QR Code Section
    qr_token = user.get("qr_token")
    if not qr_token:
        qr_token = str(uuid.uuid4())
        supabase.table("users").update({"qr_token": qr_token}).eq("id", user["id"]).execute()
        st.rerun()

    qr_content = f"https://kmfxea.streamlit.app/?qr={qr_token}"  # ← update to your real domain!

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")

    col_qr, col_info = st.columns([1, 2])
    with col_qr:
        st.image(buf.getvalue(), use_column_width=True, caption="Quick Login QR")
    with col_info:
        st.markdown("**Scan to log in instantly**")
        st.caption(f"Token (partial): `{qr_token[:8]}…`")
        if st.button("🔄 Regenerate QR Code", type="primary"):
            new_token = str(uuid.uuid4())
            supabase.table("users").update({"qr_token": new_token}).eq("id", user["id"]).execute()
            log_action("QR Regenerated", user.get("full_name", ""))
            st.success("New QR generated → refresh page")
            st.rerun()

    st.divider()

    # Change Password
    st.subheader("Change Password")
    with st.form("change_password"):
        old_pw  = st.text_input("Current Password", type="password")
        new_pw  = st.text_input("New Password", type="password")
        conf_pw = st.text_input("Confirm New Password", type="password")

        if st.form_submit_button("Update Password", type="primary"):
            if not old_pw or not new_pw or not conf_pw:
                st.error("All fields are required.")
            elif new_pw != conf_pw:
                st.error("Passwords do not match.")
            elif len(new_pw) < 8:
                st.error("New password must be at least 8 characters.")
            elif not bcrypt.checkpw(old_pw.encode(), user["password"].encode()):
                st.error("Current password is incorrect.")
            else:
                hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                supabase.table("users").update({"password": hashed}).eq("id", user["id"]).execute()
                log_action("Password Changed", user.get("full_name", ""))
                st.success("Password updated! Logging out for security...")
                for k in ["authenticated", "username", "full_name", "role"]:
                    st.session_state.pop(k, None)
                st.switch_page("pages/01_Login.py")  # ← adjust if login page name is different

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