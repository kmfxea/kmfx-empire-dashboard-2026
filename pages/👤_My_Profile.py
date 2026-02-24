# pages/02_👤_My_Profile.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import qrcode
from io import BytesIO
import bcrypt
from datetime import datetime

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action, upload_to_supabase

require_auth(min_role="client")  # Client-only page

st.header("My Profile 👤")
st.markdown("**Your KMFX EA elite membership: Realtime premium flip card, earnings, full details, participation, withdrawals • Full transparency & motivation.**")

my_name = st.session_state.full_name
my_username = st.session_state.username
theme = st.session_state.get("theme", "dark")

# ────────────────────────────────────────────────
#  REALTIME CACHE (10s refresh for ultra-fresh feel)
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_my_profile_data():
    try:
        # My user record
        user_resp = supabase.table("users").select("*").eq("username", my_username).single().execute()
        my_user = user_resp.data if user_resp.data else {}

        # All accounts (for shared detection)
        accounts_resp = supabase.table("ftmo_accounts").select("*").execute()
        accounts = accounts_resp.data or []

        # Detect my accounts (v2 + legacy support)
        my_accounts = []
        my_user_id = str(my_user.get("id"))
        for a in accounts:
            participants_v2 = a.get("participants_v2", [])
            if any(
                p.get("display_name") == my_name or
                str(p.get("user_id")) == my_user_id
                for p in participants_v2
            ):
                my_accounts.append(a)
                continue
            # Legacy fallback
            participants = a.get("participants", [])
            if any(p.get("name") == my_name for p in participants):
                my_accounts.append(a)

        # My withdrawals
        wd_resp = supabase.table("withdrawals").select("*").eq("client_name", my_name).order("date_requested", desc=True).execute()
        my_withdrawals = wd_resp.data or []

        # My proofs (permanent)
        files_resp = supabase.table("client_files").select("id, original_name, file_url, storage_path, upload_date, category, notes").eq("assigned_client", my_name).order("upload_date", desc=True).execute()
        my_proofs = files_resp.data or []

        # All users for title display
        all_users_resp = supabase.table("users").select("id, full_name, title").execute()
        all_users = all_users_resp.data or []
        user_id_to_title = {str(u["id"]): u.get("title", "") for u in all_users}

        return my_user, my_accounts, my_withdrawals, my_proofs, user_id_to_title
    except Exception as e:
        st.error(f"Profile load error: {str(e)}")
        return {}, [], [], [], {}

my_user, my_accounts, my_withdrawals, my_proofs, user_id_to_title = fetch_my_profile_data()

st.caption("🔄 Profile auto-refreshes every 10s • Everything realtime & synced")

if st.button("🔄 Refresh Now", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

# ────────────────────────────────────────────────
#  PREMIUM RESPONSIVE FLIP CARD (wow factor)
# ────────────────────────────────────────────────
my_title = my_user.get("title", "Member").upper()
card_title = f"{my_title} CARD" if my_title != "NONE" else "MEMBER CARD"
my_balance = my_user.get("balance", 0.0)

# Theme-aware styling
if theme == "dark":
    front_bg = "linear-gradient(135deg, #000000, #1a1a2e)"
    back_bg = "linear-gradient(135deg, #0f0f1a, #000000)"
    text_color = "#e0e0ff"
    accent_gold = "#ffd700"
    accent_green = "#00ffaa"
    border_color = "#ffd70088"
    shadow = "0 25px 60px rgba(0,255,170,0.25)"
    mag_strip = "#222233"
else:
    front_bg = "linear-gradient(135deg, #f8f9ff, #e0e7ff)"
    back_bg = "linear-gradient(135deg, #e0e7ff, #d0e0ff)"
    text_color = "#1a1a3f"
    accent_gold = "#b8860b"
    accent_green = "#006633"
    border_color = "#b8860b88"
    shadow = "0 25px 60px rgba(0,0,0,0.15)"
    mag_strip = "#ccd"

st.markdown(f"""
<div style="perspective: 1800px; max-width: 640px; width: 100%; margin: 3rem auto;">
  <div class="flip-card-inner" style="position: relative; width: 100%; height: 420px; text-align: center; transition: transform 0.9s cubic-bezier(0.68, -0.55, 0.265, 1.55); transform-style: preserve-3d;">
    <!-- Front -->
    <div class="flip-card-front" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; background: {front_bg}; backdrop-filter: blur(20px); border-radius: 24px; padding: 2.5rem; box-shadow: {shadow}; border: 2px solid {border_color}; color: {text_color}; display: flex; flex-direction: column; justify-content: space-between;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <h2 style="margin: 0; font-size: 2.8rem; color: {accent_gold}; letter-spacing: 8px; text-shadow: 0 0 15px {accent_gold};">KMFX EA</h2>
        <h3 style="margin: 0; font-size: 1.8rem; color: {accent_gold};">{card_title}</h3>
      </div>
      <div style="text-align: center; flex-grow: 1; display: flex; align-items: center; justify-content: center;">
        <h1 style="margin: 0; font-size: 3.2rem; letter-spacing: 4px; color: {text_color}; text-shadow: 0 0 10px rgba(255,255,255,0.3);">{my_name.upper()}</h1>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: flex-end;">
        <div style="font-size: 1.3rem; opacity: 0.9;">💳 Elite Empire Member</div>
        <div style="text-align: right;">
          <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">Available Earnings</p>
          <h2 style="margin: 0; font-size: 3.5rem; color: {accent_green}; text-shadow: 0 0 20px {accent_green};">${my_balance:,.2f}</h2>
        </div>
      </div>
      <div style="height: 40px; background: {mag_strip}; border-radius: 10px; margin-top: 1rem;"></div>
    </div>
    <!-- Back -->
    <div class="flip-card-back" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; transform: rotateY(180deg); background: {back_bg}; backdrop-filter: blur(20px); border-radius: 24px; padding: 2rem; box-shadow: {shadow}; border: 2px solid {border_color}; color: {text_color}; overflow-y: auto;">
      <h2 style="margin: 0 0 1.5rem; text-align: center; color: {accent_gold}; font-size: 2rem;">Membership Details</h2>
      <div style="font-size: 1.1rem; line-height: 1.8;">
        <strong style="color: {accent_gold};">Full Name:</strong> {my_name}<br>
        <strong style="color: {accent_gold};">Title:</strong> {my_title}<br>
        <strong style="color: {accent_gold};">Username:</strong> {my_username}<br>
        <strong style="color: {accent_gold};">Email:</strong> {my_user.get('email', 'Not set')}<br>
        <strong style="color: {accent_gold};">Contact:</strong> {my_user.get('contact_no', 'Not set')}<br>
        <strong style="color: {accent_gold};">Address:</strong> {my_user.get('address', 'Not set')}<br>
        <strong style="color: {accent_gold};">Balance:</strong> <span style="color: {accent_green}; font-size: 1.4rem;">${my_balance:,.2f}</span><br>
        <strong style="color: {accent_gold};">Shared Accounts:</strong> {len(my_accounts)} active<br>
        <strong style="color: {accent_gold};">Joined:</strong> {my_user.get('created_at', '—')[:10]}
      </div>
      <p style="margin-top: 2rem; text-align: center; opacity: 0.8; font-size: 1rem;">Elite Access • KMFX Empire 👑 2026</p>
    </div>
  </div>
</div>

<style>
  .flip-card-inner {{ transition: transform 0.9s cubic-bezier(0.68, -0.55, 0.265, 1.55); transform-style: preserve-3d; }}
  .flip-card-front, .flip-card-back {{ backface-visibility: hidden; }}
  .flip-card-inner:hover {{ transform: rotateY(180deg); }}
  @media (max-width: 768px) {{
    .flip-card-inner {{ height: 380px; }}
    .flip-card-front, .flip-card-back {{ padding: 1.5rem; }}
  }}
</style>

<p style="text-align:center; opacity:0.8; margin-top:1rem;">Hover or tap card to flip ↺</p>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  QUICK LOGIN QR CODE + REGENERATE FEATURE
# ────────────────────────────────────────────────
st.subheader("🔑 Quick Login QR Code")
current_qr_token = my_user.get("qr_token")

app_url = "https://kmfxeaftmo.streamlit.app"  # Palitan kung iba ang URL mo

if current_qr_token:
    qr_url = f"{app_url}/?qr={current_qr_token}"
    buf = BytesIO()
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)
    fill_color = "#00ffaa" if theme == "dark" else "#000000"
    back_color = "#0a0d14" if theme == "dark" else "#ffffff"
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    img.save(buf, format="PNG")
    qr_bytes = buf.getvalue()

    col_qr1, col_qr2 = st.columns([1, 3])
    with col_qr1:
        st.image(qr_bytes, caption="Scan for Instant Login", use_column_width=True)
    with col_qr2:
        st.code(qr_url, language="text")
        st.download_button(
            "⬇ Download QR Code",
            qr_bytes,
            file_name=f"{my_name.replace(' ', '_')}_KMFX_QR.png",
            mime="image/png",
            use_container_width=True
        )
        st.success("Valid on any device • Auto-login to your dashboard")
else:
    st.info("No active QR token yet • You can request regeneration below")

if st.button("🔄 Regenerate New QR Code", type="primary", use_container_width=True):
    with st.spinner("Generating new secure QR token..."):
        try:
            new_token = str(uuid.uuid4())
            supabase.table("users").update({"qr_token": new_token}).eq("username", my_username).execute()
            log_action("Regenerated QR Token", f"User: {my_name}")
            st.success("New QR code generated! Refreshing...")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Failed to regenerate QR: {str(e)}")

# ────────────────────────────────────────────────
#  CHANGE PASSWORD (SECURE & VALIDATED)
# ────────────────────────────────────────────────
st.subheader("🔐 Change Password")
with st.form("change_password_form", clear_on_submit=True):
    old_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    if st.form_submit_button("Update Password", type="primary", use_container_width=True):
        if not old_password or not new_password or not confirm_password:
            st.error("All fields required")
        elif new_password != confirm_password:
            st.error("New passwords do not match")
        elif len(new_password) < 8:
            st.error("Password must be at least 8 characters")
        else:
            try:
                user_resp = supabase.table("users").select("password").eq("username", my_username).single().execute()
                stored_hash = user_resp.data["password"].encode('utf-8')
                if bcrypt.checkpw(old_password.encode('utf-8'), stored_hash):
                    new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table("users").update({"password": new_hash}).eq("username", my_username).execute()
                    log_action("Password Changed", f"User: {my_name}")
                    st.success("Password updated successfully! 🔐")
                else:
                    st.error("Current password is incorrect")
            except Exception as e:
                st.error(f"Update failed: {str(e)}")

# ────────────────────────────────────────────────
#  YOUR SHARED ACCOUNTS WITH MINI-TREES
# ────────────────────────────────────────────────
st.subheader(f"Your Shared Accounts ({len(my_accounts)} active)")
if my_accounts:
    for acc in my_accounts:
        participants = acc.get("participants_v2") or acc.get("participants", [])
        my_part = next((p for p in participants if p.get("display_name") == my_name or str(p.get("user_id")) == str(my_user.get("id"))), None)
        my_pct = my_part["percentage"] if my_part else 0.0
        my_projected = (acc.get("current_equity", 0) * my_pct / 100) if acc.get("current_equity") else 0

        contributors = acc.get("contributors_v2") or acc.get("contributors", [])
        my_funded_php = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors if str(c.get("user_id")) == str(my_user.get("id")))

        with st.expander(f"🌟 {acc['name']} • Your Share: {my_pct:.1f}% • Phase: {acc['current_phase']}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Account Equity", f"${acc.get('current_equity', 0):,.0f}")
                st.metric("Your Projected Share", f"${my_projected:,.2f}")
            with col2:
                st.metric("Withdrawable", f"${acc.get('withdrawable_balance', 0):,.0f}")
                st.metric("Your Funded (PHP)", f"₱{my_funded_php:,.0f}")

            # Mini Sankey tree
            labels = ["Profits"]
            values = []
            for p in participants:
                display = p.get("display_name") or "Unknown"
                title = user_id_to_title.get(str(p.get("user_id")), "")
                if title:
                    display += f" ({title})"
                labels.append(f"{display} ({p.get('percentage', 0):.1f}%)")
                values.append(p.get("percentage", 0))

            if values:
                fig = go.Figure(data=[go.Sankey(
                    node=dict(pad=15, thickness=20, label=labels),
                    link=dict(source=[0]*len(values), target=list(range(1, len(labels))), value=values)
                )])
                fig.update_layout(height=350, margin=dict(t=20))
                st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No participation yet • Owner will assign you soon")

# ────────────────────────────────────────────────
#  WITHDRAWAL HISTORY & NEW REQUEST
# ────────────────────────────────────────────────
st.subheader("💳 Withdrawal History & Request")
if my_withdrawals:
    for w in my_withdrawals:
        status_colors = {"Pending": "#ffa502", "Approved": "#00ffaa", "Paid": "#2ed573", "Rejected": "#ff4757"}
        color = status_colors.get(w["status"], "#888")
        st.markdown(f"""
        <div class='glass-card' style='padding:1.5rem; border-left:5px solid {color}; margin-bottom:1rem;'>
            <h4>${w['amount']:,.0f} • {w['status']}</h4>
            <small>Method: {w['method']} • Requested: {w['date_requested']}</small>
        </div>
        """, unsafe_allow_html=True)
        if w.get("details"):
            with st.expander("View Details"):
                st.write(w["details"])
else:
    st.info("No withdrawal requests yet • Earnings auto-accumulate")

with st.expander("➕ Request New Withdrawal", expanded=False):
    if my_balance <= 0:
        st.info("No available balance yet")
    else:
        with st.form("withdrawal_request_form", clear_on_submit=True):
            amount = st.number_input("Amount (USD)", min_value=1.0, max_value=my_balance, step=50.0)
            method = st.selectbox("Withdrawal Method", ["USDT", "Bank Transfer", "Wise", "PayPal", "GCash", "Other"])
            details = st.text_area("Details (Wallet Address / Bank Info / etc.)")
            proof_file = st.file_uploader("Upload Proof (Required)", type=["png", "jpg", "jpeg", "pdf"])

            if st.form_submit_button("Submit Withdrawal Request", type="primary"):
                if amount > my_balance:
                    st.error("Amount exceeds your balance")
                elif not proof_file:
                    st.error("Proof upload is required")
                else:
                    try:
                        url, path = upload_to_supabase(
                            file=proof_file,
                            bucket="client_files",
                            folder="withdrawal_proofs",
                            use_signed_url=False
                        )

                        supabase.table("client_files").insert({
                            "original_name": proof_file.name,
                            "file_url": url,
                            "storage_path": path,
                            "upload_date": datetime.now().isoformat(),
                            "sent_by": my_name,
                            "category": "Withdrawal Proof",
                            "assigned_client": my_name,
                            "notes": f"Proof for ${amount:,.2f} request"
                        }).execute()

                        supabase.table("withdrawals").insert({
                            "client_name": my_name,
                            "amount": amount,
                            "method": method,
                            "details": details,
                            "status": "Pending",
                            "date_requested": datetime.now().isoformat()
                        }).execute()

                        st.success("Withdrawal request submitted! Proof permanently stored • Owner will review soon")
                        log_action("Withdrawal Request", f"Amount: ${amount:,.2f}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Submission failed: {str(e)}")

# ────────────────────────────────────────────────
#  YOUR PROOFS VAULT
# ────────────────────────────────────────────────
st.subheader("📁 Your Proofs Vault (Permanent Storage)")
if my_proofs:
    cols = st.columns(4)
    for idx, proof in enumerate(my_proofs):
        with cols[idx % 4]:
            file_url = proof.get("file_url")
            if proof.get("storage_path"):
                try:
                    signed = supabase.storage.from_("client_files").create_signed_url(proof["storage_path"], 3600 * 24)
                    file_url = signed.get("signedURL") or file_url
                except:
                    pass

            if file_url and proof["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif')):
                st.image(file_url, use_column_width=True, caption=proof["original_name"])
            else:
                st.markdown(f"**{proof['original_name']}**")
                st.caption(f"{proof.get('category', 'Other')} • {proof['upload_date']}")

            if file_url:
                try:
                    import requests
                    r = requests.get(file_url, timeout=8)
                    if r.status_code == 200:
                        st.download_button(
                            "⬇ Download",
                            r.content,
                            file_name=proof["original_name"],
                            use_container_width=True
                        )
                except:
                    st.caption("Download unavailable")
else:
    st.info("No proofs uploaded yet • Add during withdrawals or requests")

# ────────────────────────────────────────────────
#  MOTIVATIONAL EMPIRE FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid {accent_primary}; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, {accent_primary}, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; margin-bottom: 1.5rem;">
        Your Empire Journey Continues 👑
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 800px; margin: 0 auto 2rem;">
        Realtime earnings • Permanent proofs • Instant QR login • Full transparency • Built by faith, powered by discipline.
    </p>
    <h2 style="color: #ffd700; font-size: 2rem;">KMFX Elite • Cloud Edition 2026</h2>
</div>
""", unsafe_allow_html=True)