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
from utils.helpers import log_action, upload_to_supabase

# ────────────────────────────────────────────────
render_sidebar()
require_auth(min_role="client")

# Theme colors (keep consistent)
ACCENT = "#00ffaa"
GOLD   = "#ffd700"

# ────────────────────────────────────────────────
# Force scroll to top + welcome balloons
# ────────────────────────────────────────────────
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.success(f"Welcome back, {st.session_state.get('full_name', 'Trader')} 👑")
    st.session_state.pop("just_logged_in", None)

st.markdown("""
    <script>
    window.parent.document.querySelector('.main').scrollTop = 0;
    </script>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
st.title("👤 My Profile")
st.caption("Manage your personal details, accounts, security & password")

# ────────────────────────────────────────────────
# Load current user
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
    st.error("Cannot load your profile. Try logging out and back in.")
    st.stop()

# ────────────────────────────────────────────────
# TABS ─ simplified to 3 main sections
# ────────────────────────────────────────────────
tab_profile, tab_accounts, tab_security = st.tabs([
    "Profile & Details",
    "My Accounts & Shares",
    "Security & Password"
])

# ────────────────────────────────
# TAB 1: Profile & Details
# ────────────────────────────────
with tab_profile:

    st.subheader("Personal Information")

    with st.container(border=True):
        col1, col2 = st.columns([1, 3])

        with col1:
            if user.get("profile_pic"):
                st.image(user["profile_pic"], width=140)
            else:
                st.image("https://via.placeholder.com/140?text=No+Photo", width=140)

        with col2:
            st.markdown(f"**Full name**    {user.get('full_name','—')}")
            st.markdown(f"**Username**    **{user['username']}**")
            st.markdown(f"**Role**        {user['role'].title()}")
            st.markdown(f"**Balance**     **${user.get('balance',0):,.2f}**")
            st.markdown(f"**Phone**       {user.get('phone','not set')}")
            st.markdown(f"**Email**       {user.get('email','not set')}")
            st.markdown(f"**Address**     {user.get('address','not set')}")
            st.markdown(f"**Date of Birth** {user.get('dob','not set')}")

    st.subheader("Update Personal Info")
    with st.form("update_profile", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            full_name_new = st.text_input("Full Name",     value=user.get("full_name",""))
            phone_new     = st.text_input("Phone Number",  value=user.get("phone",""))
            email_new     = st.text_input("Email",         value=user.get("email",""))

        with c2:
            address_new   = st.text_input("Address",       value=user.get("address",""))
            dob_new       = st.date_input("Date of Birth", value=user.get("dob"),
                                          min_value=datetime(1950,1,1), max_value=datetime.now())

        uploaded_pic = st.file_uploader("New profile picture (optional)", ["jpg","jpeg","png"])

        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
            updates = {}
            if full_name_new != user.get("full_name"): updates["full_name"] = full_name_new
            if phone_new     != user.get("phone"):     updates["phone"]     = phone_new
            if email_new     != user.get("email"):     updates["email"]     = email_new
            if address_new   != user.get("address"):   updates["address"]   = address_new
            if dob_new       != user.get("dob"):       updates["dob"]       = str(dob_new) if dob_new else None

            pic_url = None
            if uploaded_pic:
                pic_url, _ = upload_to_supabase(uploaded_pic, bucket="profiles", folder="users")
                if pic_url:
                    updates["profile_pic"] = pic_url

            if updates:
                try:
                    supabase.table("users").update(updates).eq("id", user["id"]).execute()
                    log_action("Profile Updated", str(updates))
                    st.success("Profile updated!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Update failed → {ex}")
            else:
                st.info("No changes were made.")

# ────────────────────────────────
# TAB 2: Accounts & Shares
# ────────────────────────────────
with tab_accounts:

    st.subheader("Accounts where you are involved")

    try:
        all_accounts = supabase.table("ftmo_accounts").select("*").execute().data or []

        my_accounts = []
        for acc in all_accounts:
            contrib = acc.get("contributors_v2") or acc.get("contributors", [])
            partic = acc.get("participants_v2") or acc.get("participants", [])

            involved = (
                any(user["username"] in str(x) for x in contrib) or
                any(user["username"] in str(x) for x in partic) or
                user["username"] in str(acc.get("name",""))
            )
            if involved:
                my_accounts.append(acc)

        if not my_accounts:
            st.info("You are not participating in any accounts yet.")
        else:
            for acc in my_accounts:
                with st.container(border=True):
                    st.markdown(f"**{acc.get('name','Unnamed Account')}**")
                    st.caption(acc.get("current_phase","—"))

                    cols = st.columns([2,1,1])
                    with cols[0]:
                        st.metric("Equity", f"${acc.get('current_equity',0):,.2f}")
                    with cols[1]:
                        st.metric("Withdrawable", f"${acc.get('withdrawable_balance',0):,.2f}")
                    with cols[2]:
                        st.metric("Split", f"{acc.get('ftmo_split',80)}%")

    except Exception as ex:
        st.error(f"Could not load accounts → {ex}")

    # Optional mini summary
    st.subheader("Profit Share Received (summary)")
    try:
        dists = supabase.table("profit_distributions") \
                .select("timestamp, share_amount, percentage") \
                .eq("participant_user_id", user["id"]) \
                .order("timestamp", desc=True) \
                .execute().data or []

        if dists:
            total = sum(d["share_amount"] or 0 for d in dists)
            st.metric("Total received", f"${total:,.2f}", delta=None)
            with st.expander("View last records"):
                st.dataframe(dists[:8], use_container_width=True, hide_index=True)
        else:
            st.caption("No profit distributions yet.")
    except:
        st.caption("Could not load profit history.")

# ────────────────────────────────
# TAB 3: Security
# ────────────────────────────────
with tab_security:

    st.subheader("Quick Login QR Code")

    qr_token = user.get("qr_token")
    if not qr_token:
        qr_token = str(uuid.uuid4())
        supabase.table("users").update({"qr_token": qr_token}).eq("id", user["id"]).execute()
        st.rerun()

    qr_content = f"https://kmfxea.streamlit.app/?qr={qr_token}"   # ← update URL!

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    qr_bytes = buf.getvalue()

    col_qr, col_btn = st.columns([2,1])
    with col_qr:
        st.image(qr_bytes, use_column_width=True)
    with col_btn:
        st.caption("Scan to login instantly")
        if st.button("Regenerate QR", type="primary", use_container_width=True):
            new_token = str(uuid.uuid4())
            supabase.table("users").update({"qr_token": new_token}).eq("id", user["id"]).execute()
            log_action("QR Regenerated", user["full_name"])
            st.success("New QR created → refresh page")
            st.rerun()

    st.divider()

    st.subheader("Change Password")
    with st.form("change_pw"):
        old_pw  = st.text_input("Current password", type="password")
        new_pw  = st.text_input("New password",     type="password")
        new_pw2 = st.text_input("Confirm new password", type="password")

        if st.form_submit_button("Update Password", type="primary"):
            if not old_pw or not new_pw:
                st.error("All fields required.")
            elif new_pw != new_pw2:
                st.error("Passwords do not match.")
            elif len(new_pw) < 8:
                st.error("New password must be ≥ 8 characters.")
            elif not bcrypt.checkpw(old_pw.encode(), user["password"].encode()):
                st.error("Current password is incorrect.")
            else:
                hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                supabase.table("users").update({"password": hashed}).eq("id", user["id"]).execute()
                log_action("Password Changed", user["full_name"])
                st.success("Password updated! → Logging out...")
                for k in ["authenticated", "username", "full_name", "role"]:
                    st.session_state.pop(k, None)
                st.switch_page("pages/01_Login.py")   # ← adjust page name if needed

    st.caption("After changing password you will be logged out for security.")

st.markdown("---")
st.caption("Your profile • Your rules • Stay secure 👑")