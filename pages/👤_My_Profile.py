# pages/👤_My_Profile.py
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import qrcode
from io import BytesIO
import requests
import uuid

from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase

render_sidebar()
require_auth(min_role="client")

st.header("My Profile 👤")
st.markdown("**Your KMFX EA empire membership: Realtime premium flip card, earnings, full details, participation, withdrawals • Full transparency & motivation.**")

my_name = st.session_state.full_name
my_username = st.session_state.username

# FULL REALTIME CACHE (10s for ultra-realtime feel)
@st.cache_data(ttl=10)
def fetch_my_profile_data():
    # My user record
    user_resp = supabase.table("users").select("*").eq("full_name", my_name).single().execute()
    my_user = user_resp.data if user_resp.data else {}
    
    # All accounts (for shared detection)
    accounts_resp = supabase.table("ftmo_accounts").select("*").execute()
    accounts = accounts_resp.data or []
    
    # Detect my accounts (supports BOTH legacy + v2)
    my_accounts = []
    for a in accounts:
        participants_v2 = a.get("participants_v2", [])
        if any(p.get("display_name") == my_name or str(p.get("user_id")) == str(my_user.get("id")) for p in participants_v2):
            my_accounts.append(a)
            continue
        participants = a.get("participants", [])
        if any(p.get("name") == my_name for p in participants):
            my_accounts.append(a)
    
    # My withdrawals
    wd_resp = supabase.table("withdrawals").select("*").eq("client_name", my_name).order("date_requested", desc=True).execute()
    my_withdrawals = wd_resp.data or []
    
    # My proofs (permanent Supabase Storage)
    files_resp = supabase.table("client_files").select("id, original_name, file_url, storage_path, upload_date, category, notes").eq("assigned_client", my_name).order("upload_date", desc=True).execute()
    my_proofs = files_resp.data or []
    
    # All users for title display in trees
    all_users_resp = supabase.table("users").select("id, full_name, title").execute()
    all_users = all_users_resp.data or []
    user_id_to_title = {str(u["id"]): u.get("title") for u in all_users}
    
    return my_user, my_accounts, my_withdrawals, my_proofs, all_users, user_id_to_title

my_user, my_accounts, my_withdrawals, my_proofs, all_users, user_id_to_title = fetch_my_profile_data()

st.caption("🔄 Profile auto-refresh every 10s • Everything realtime & fully synced")

# ====================== PREMIUM RESPONSIVE FLIP CARD ======================
my_title = my_user.get("title", "Member").upper()
card_title = f"{my_title} CARD" if my_title != "NONE" else "MEMBER CARD"
my_balance = my_user.get("balance", 0) or 0

# Theme colors (dark mode assumption)
front_bg = "linear-gradient(135deg, #000000, #1f1f1f)"
back_bg = "linear-gradient(135deg, #1f1f1f, #000000)"
text_color = "#ffffff"
accent_gold = "#ffd700"
accent_green = "#00ffaa"
border_color = "#ffd700"
shadow = "0 20px 50px rgba(0,0,0,0.9)"
mag_strip = "#333"

st.markdown(f"""
<div style="perspective: 1500px; max-width: 600px; width: 100%; margin: 3rem auto;">
  <div class="flip-card">
    <div class="flip-card-inner">
      <!-- Front -->
      <div class="flip-card-front">
        <div style="background: {front_bg}; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-radius: 20px; padding: 2rem; min-height: 380px; box-shadow: {shadow}; color: {text_color}; display: flex; flex-direction: column; justify-content: space-between; border: 2px solid {border_color};">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin: 0; font-size: clamp(2rem, 5vw, 3rem); color: {accent_gold}; letter-spacing: 6px; text-shadow: 0 0 12px {accent_gold};">KMFX EA</h2>
            <h3 style="margin: 0; font-size: clamp(1.2rem, 4vw, 1.6rem); color: {accent_gold}; letter-spacing: 2px;">{card_title}</h3>
          </div>
          <div style="text-align: center; flex-grow: 1; display: flex; align-items: center; justify-content: center;">
            <h1 style="margin: 0; font-size: clamp(1.8rem, 6vw, 2.4rem); letter-spacing: 3px; color: {text_color};">{my_name.upper()}</h1>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: flex-end;">
            <div style="font-size: clamp(1rem, 3vw, 1.4rem); opacity: 0.9;">💳 Elite Empire Member</div>
            <div style="text-align: right;">
              <p style="margin: 0; opacity: 0.9; font-size: clamp(0.9rem, 2.5vw, 1.2rem);">Available Earnings</p>
              <h2 style="margin: 0; font-size: clamp(2rem, 7vw, 3rem); color: {accent_green}; text-shadow: 0 0 18px {accent_green};">${my_balance:,.2f}</h2>
            </div>
          </div>
          <p style="margin: 0; text-align: center; opacity: 0.7; font-size: clamp(0.8rem, 2vw, 1rem); letter-spacing: 1px;">Built by Faith • Shared for Generations • 👑 2026</p>
        </div>
      </div>
      <!-- Back -->
      <div class="flip-card-back">
        <div style="background: {back_bg}; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-radius: 20px; padding: 1.8rem 2rem; min-height: 380px; box-shadow: {shadow}; color: {text_color}; display: flex; flex-direction: column; justify-content: flex-start; border: 2px solid {border_color}; overflow: hidden;">
          <h2 style="margin: 0 0 1rem; text-align: center; color: {accent_gold}; font-size: clamp(1.4rem, 4vw, 1.7rem); letter-spacing: 2px;">Membership Details</h2>
          <div style="height: 35px; background: {mag_strip}; border-radius: 8px; margin-bottom: 1rem;"></div>
          <div style="flex-grow: 1; font-size: clamp(0.9rem, 2.5vw, 1.1rem); line-height: 1.7; overflow-y: auto; padding-right: 0.5rem;">
            <strong style="color: {accent_gold};">Full Name:</strong> {my_name}<br>
            <strong style="color: {accent_gold};">Title:</strong> {my_title}<br>
            <strong style="color: {accent_gold};">Username:</strong> {my_username}<br>
            <strong style="color: {accent_gold};">MT5 Accounts:</strong> {my_user.get('accounts') or 'Not set'}<br>
            <strong style="color: {accent_gold};">Email:</strong> {my_user.get('email') or 'Not set'}<br>
            <strong style="color: {accent_gold};">Contact No.:</strong> {my_user.get('contact_no') or 'Not set'}<br>
            <strong style="color: {accent_gold};">Address:</strong> {my_user.get('address') or 'Not set'}<br>
            <strong style="color: {accent_gold};">Balance:</strong> <span style="color: {accent_green}; font-size: 1.3rem;">${my_balance:,.2f}</span><br>
            <strong style="color: {accent_gold};">Shared Accounts:</strong> {len(my_accounts)} active
          </div>
          <p style="margin: 1rem 0 0; text-align: center; opacity: 0.7; font-size: clamp(0.8rem, 2vw, 0.9rem);">Elite Access • KMFX Empire 👑</p>
        </div>
      </div>
    </div>
  </div>
</div>
<style>
  .flip-card {{ background: transparent; width: 100%; max-width: 600px; height: auto; min-height: 380px; perspective: 1000px; margin: 0 auto; }}
  .flip-card-inner {{ position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.8s cubic-bezier(0.68, -0.55, 0.27, 1.55); transform-style: preserve-3d; }}
  .flip-card:hover .flip-card-inner, .flip-card:focus-within .flip-card-inner {{ transform: rotateY(180deg); }}
  .flip-card-front, .flip-card-back {{ position: absolute; width: 100%; height: 100%; -webkit-backface-visibility: hidden; backface-visibility: hidden; border-radius: 20px; }}
  .flip-card-back {{ transform: rotateY(180deg); }}
  @media (max-width: 768px) {{
    .flip-card {{ min-height: 320px; }}
    .flip-card-front > div, .flip-card-back > div {{ padding: 1.5rem; min-height: 320px; }}
  }}
</style>
<p style="text-align:center; opacity:0.7; margin-top:1rem; font-size:1rem;">
  Hover (desktop) or tap (mobile) the card to flip ↺
</p>
""", unsafe_allow_html=True)

# ====================== QUICK LOGIN QR CODE with REGENERATE ======================
st.subheader("🔑 Quick Login QR Code")

current_qr_token = my_user.get("qr_token")
app_url = "https://kmfxea.streamlit.app"

if current_qr_token:
    qr_url = f"{app_url}/?qr={current_qr_token}"
    buf = BytesIO()
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    fill_color = "#00ffaa"
    back_color = "#0a0d14"
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    img.save(buf, format="PNG")
    qr_bytes = buf.getvalue()

    col_qr1, col_qr2 = st.columns([1, 2])
    with col_qr1:
        st.image(qr_bytes, caption="Scan for Instant Login")
    with col_qr2:
        st.code(qr_url, language="text")
        st.download_button(
            "⬇ Download QR PNG",
            qr_bytes,
            f"{my_name.replace(' ', '_')}_QR_Login.png",
            "image/png",
            use_container_width=True
        )
        st.success("Valid on any device • Auto-login straight to your profile")

    # Regenerate QR
    st.markdown("---")
    st.warning("**Palitan ang QR kung na-expose o na-share na ito**\n(luma magiging invalid pag na-regenerate)")
    
    if st.button("🔄 Regenerate QR Code", type="primary", use_container_width=True):
        new_token = str(uuid.uuid4())
        supabase.table("users").update({"qr_token": new_token}).eq("id", my_user["id"]).execute()
        st.success("Bagong QR na nabuo! Refresh page para makita.")
        st.rerun()

else:
    st.info("No QR login token yet • Contact owner to generate one in Admin Management")
    if st.button("🔔 Notify Owner to Generate QR Token"):
        st.info("Owner has been notified (send manual message for now)")

# ====================== YOUR SHARED ACCOUNTS (WITH TREES) ======================
st.subheader(f"Your Shared Accounts ({len(my_accounts)} active)")
if my_accounts:
    for acc in my_accounts:
        participants = acc.get("participants_v2") or acc.get("participants", [])
        my_part = next((p for p in participants if p.get("display_name") == my_name or str(p.get("user_id")) == str(my_user.get("id"))), None)
        my_pct = my_part["percentage"] if my_part else next((p["percentage"] for p in participants if p.get("name") == my_name), 0)
        my_projected = (acc.get("current_equity", 0) * my_pct / 100) if acc.get("current_equity") else 0
        contributors = acc.get("contributors_v2") or acc.get("contributors", [])
        my_funded_php = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors
                            if str(c.get("user_id")) == str(my_user.get("id")))
        if my_funded_php == 0:
            my_funded_php = sum(c["units"] * c["php_per_unit"] for c in contributors if c.get("name") == my_name)
        with st.expander(f"🌟 {acc['name']} • Your Share: {my_pct:.1f}% • Phase: {acc['current_phase']}", expanded=False):
            col_acc1, col_acc2 = st.columns(2)
            with col_acc1:
                st.metric("Account Equity", f"${acc.get('current_equity', 0):,.0f}")
                st.metric("Your Projected Share", f"${my_projected:,.2f}")
            with col_acc2:
                st.metric("Account Withdrawable", f"${acc.get('withdrawable_balance', 0):,.0f}")
                st.metric("Your Funded (PHP)", f"₱{my_funded_php:,.0f}")
            # Sankey tree with titles
            labels = ["Profits"]
            values = []
            for p in participants:
                display = p.get("display_name") or p.get("name", "Unknown")
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
    st.info("No participation yet • Owner will assign you to shared profits")

# ====================== WITHDRAWAL HISTORY & REQUEST ======================
st.subheader("💳 Your Withdrawal Requests & History")
if my_withdrawals:
    for w in my_withdrawals:
        status_color = {"Pending": "#ffa502", "Approved": accent_primary, "Paid": "#2ed573", "Rejected": "#ff4757"}.get(w["status"], "#888")
        st.markdown(f"""
        <div class='glass-card' style='padding:1.5rem; border-left:5px solid {status_color};'>
            <h4>${w['amount']:,.0f} • {w['status']}</h4>
            <small>Method: {w['method']} • Requested: {w['date_requested']}</small>
        </div>
        """, unsafe_allow_html=True)
        if w["details"]:
            with st.expander("Details"):
                st.write(w["details"])
        st.divider()
else:
    st.info("No requests yet • Earnings auto-accumulate")

# Quick request with permanent proof upload
with st.expander("➕ Request New Withdrawal (from Balance)", expanded=False):
    if my_balance <= 0:
        st.info("No available balance yet • Earnings auto-accumulate from profits")
    else:
        with st.form("my_wd_form", clear_on_submit=True):
            amount = st.number_input("Amount (USD)", min_value=1.0, max_value=my_balance, step=100.0, help=f"Max: ${my_balance:,.2f}")
            method = st.selectbox("Method", ["USDT", "Bank Transfer", "Wise", "PayPal", "GCash", "Other"])
            details = st.text_area("Details (Wallet/Address/Bank Info)")
            proof = st.file_uploader("Upload Proof * (Required - Permanent Storage)", type=["png","jpg","jpeg","pdf"])
            submitted = st.form_submit_button("Submit Request", type="primary")
            if submitted:
                if amount > my_balance:
                    st.error("Exceeds balance")
                elif not proof:
                    st.error("Proof required")
                else:
                    try:
                        url, storage_path = upload_to_supabase(
                            file=proof,
                            bucket="client_files",
                            folder="proofs",
                            use_signed_url=False
                        )
                        supabase.table("client_files").insert({
                            "original_name": proof.name,
                            "file_url": url,
                            "storage_path": storage_path,
                            "upload_date": datetime.date.today().isoformat(),
                            "sent_by": my_name,
                            "category": "Withdrawal Proof",
                            "assigned_client": my_name,
                            "notes": f"Proof for ${amount:,.0f} withdrawal"
                        }).execute()
                        supabase.table("withdrawals").insert({
                            "client_name": my_name,
                            "amount": amount,
                            "method": method,
                            "details": details,
                            "status": "Pending",
                            "date_requested": datetime.date.today().isoformat()
                        }).execute()
                        st.success("Request submitted with permanent proof! Owner will review.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ====================== YOUR PROOFS IN VAULT with DOWNLOAD ======================
st.subheader("📁 Your Proofs in Vault (Permanent)")

if my_proofs:
    cols = st.columns(4)
    for idx, p in enumerate(my_proofs):
        with cols[idx % 4]:
            file_url = p.get("file_url")
            if p.get("storage_path"):
                try:
                    signed_resp = supabase.storage.from_("client_files").create_signed_url(
                        p["storage_path"], 
                        expires_in=7200   # 2 hours
                    )
                    file_url = signed_resp.signed_url
                except:
                    pass  # fallback to original url if signed fails

            if file_url and p["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif')):
                st.image(file_url, use_column_width=True, caption=p["original_name"])
            else:
                st.markdown(f"**{p['original_name']}**")
                st.caption(f"{p.get('category','Other')} • {p['upload_date']}")

            # Download button
            if file_url:
                try:
                    r = requests.get(file_url, timeout=10)
                    if r.status_code == 200:
                        st.download_button(
                            "⬇ Download",
                            r.content,
                            p["original_name"],
                            use_container_width=True,
                            key=f"dl_{p['id']}_{idx}"
                        )
                    else:
                        st.caption("Download unavailable")
                except:
                    st.caption("Cannot download at this time")
else:
    st.info("No proofs uploaded yet")

# ====================== MOTIVATIONAL FOOTER ======================
st.markdown(f"""
<div class='glass-card' style='padding:3rem; text-align:center; margin:3rem 0;'>
    <h1 style="background:linear-gradient(90deg,{accent_primary},#ffd700); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Your Empire Journey
    </h1>
    <p style="font-size:1.3rem; margin:2rem 0;">
        Realtime earnings • Full v2 participation • Permanent proofs • Instant QR • Motivated & aligned forever.
    </p>
    <h2 style="color:#ffd700;">👑 KMFX Pro • Elite Member Portal 2026</h2>
</div>
""", unsafe_allow_html=True)