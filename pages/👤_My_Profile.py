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
from utils.helpers import upload_to_supabase, log_action

# ────────────────────────────────────────────────
render_sidebar()
require_auth(min_role="client")

# ────────────────────────────────────────────────
# THEME (match Dashboard)
# ────────────────────────────────────────────────
accent_primary = "#00ffaa"
accent_gold    = "#ffd700"
accent_dark    = "#0a0d14"
text_light     = "#ffffff"
text_dark      = "#0f172a"

# Assume dark theme by default (you can make it dynamic later)
theme = "dark"
front_bg   = "linear-gradient(135deg, #000000, #1f1f1f)"
back_bg    = "linear-gradient(135deg, #1f1f1f, #000000)"
border_col = accent_gold
shadow     = "0 20px 50px rgba(0,255,170,0.25)"
mag_strip  = "#333"

# ────────────────────────────────────────────────
# SCROLL TO TOP + WELCOME
# ────────────────────────────────────────────────
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.success(f"Welcome to your profile, {st.session_state.get('full_name', 'Elite Member')}! 👑")
    st.session_state.pop("just_logged_in", None)

st.markdown("""
<script>
function forceScrollToTop() { window.scrollTo({top: 0, behavior: 'smooth'}); }
const observer = new MutationObserver(() => {
    setTimeout(forceScrollToTop, 300);
    setTimeout(forceScrollToTop, 1200);
});
observer.observe(document.body, { childList: true, subtree: true });
setTimeout(forceScrollToTop, 800);
</script>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
st.header("👤 My Profile")
st.caption("Your KMFX EA Elite Membership • Realtime • Full Transparency")

my_name     = st.session_state.full_name
my_username = st.session_state.username

# ────────────────────────────────────────────────
# CACHE DATA (10s refresh for realtime feel)
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_my_data():
    user_res = supabase.table("users").select("*").eq("username", my_username).single().execute()
    my_user = user_res.data or {}

    acc_res = supabase.table("ftmo_accounts").select("*").execute()
    accounts = acc_res.data or []

    my_accounts = []
    my_id_str = str(my_user.get("id", ""))
    for acc in accounts:
        parts_v2 = acc.get("participants_v2", []) or []
        parts_old = acc.get("participants", []) or []
        if any(
            p.get("display_name") == my_name or 
            str(p.get("user_id")) == my_id_str or 
            p.get("name") == my_name 
            for p in parts_v2 + parts_old
        ):
            my_accounts.append(acc)

    wd_res = supabase.table("withdrawals").select("*").eq("client_name", my_name).order("date_requested", desc=True).execute()
    withdrawals = wd_res.data or []

    files_res = supabase.table("client_files").select("*").eq("assigned_client", my_name).order("upload_date", desc=True).execute()
    proofs = files_res.data or []

    return my_user, my_accounts, withdrawals, proofs

my_user, my_accounts, my_withdrawals, my_proofs = fetch_my_data()

if st.button("🔄 Refresh Profile Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Auto-refreshes every 10 seconds • All data realtime")

# ────────────────────────────────────────────────
# PREMIUM FLIP CARD (almost identical to old one)
# ────────────────────────────────────────────────
my_title   = my_user.get("title", "Member").upper()
card_title = f"{my_title} CARD" if my_title != "NONE" else "MEMBER CARD"
balance    = my_user.get("balance", 0.0)

st.markdown(f"""
<div style="perspective: 1500px; max-width: 600px; margin: 3rem auto; width: 100%;">
  <div class="flip-card">
    <div class="flip-card-inner">
      <!-- Front -->
      <div class="flip-card-front">
        <div style="background: {front_bg}; backdrop-filter: blur(20px); border-radius: 20px; padding: 2rem; min-height: 380px; box-shadow: {shadow}; color: {text_light}; border: 2px solid {border_col}; display: flex; flex-direction: column; justify-content: space-between;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin:0; font-size: clamp(2.2rem, 6vw, 3.2rem); color: {accent_gold}; letter-spacing: 5px; text-shadow: 0 0 15px {accent_gold};">KMFX EA</h2>
            <h3 style="margin:0; font-size: clamp(1.3rem, 4vw, 1.8rem); color: {accent_gold};">{card_title}</h3>
          </div>
          <div style="text-align: center; flex-grow: 1; display: flex; align-items: center; justify-content: center;">
            <h1 style="margin:0; font-size: clamp(2rem, 7vw, 3rem); letter-spacing: 4px;">{my_name.upper()}</h1>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: flex-end;">
            <div style="font-size: clamp(1rem, 3vw, 1.3rem); opacity: 0.9;">Elite Empire Member</div>
            <div style="text-align: right;">
              <p style="margin:0; opacity: 0.9;">Available Balance</p>
              <h2 style="margin:0; color: {accent_primary}; text-shadow: 0 0 20px {accent_primary};">${balance:,.2f}</h2>
            </div>
          </div>
          <p style="text-align:center; margin:1rem 0 0; opacity:0.7; font-size:0.95rem;">Built by Faith • Shared for Generations • 2026 👑</p>
        </div>
      </div>
      <!-- Back -->
      <div class="flip-card-back">
        <div style="background: {back_bg}; backdrop-filter: blur(20px); border-radius: 20px; padding: 2rem; min-height: 380px; box-shadow: {shadow}; color: {text_light}; border: 2px solid {border_col};">
          <h2 style="text-align:center; color: {accent_gold}; margin:0 0 1.2rem;">Membership Details</h2>
          <div style="height:40px; background:#333; border-radius:10px; margin-bottom:1.5rem;"></div>
          <div style="font-size:1.05rem; line-height:1.8;">
            <strong style="color:{accent_gold};">Full Name:</strong> {my_name}<br>
            <strong style="color:{accent_gold};">Title:</strong> {my_title}<br>
            <strong style="color:{accent_gold};">Username:</strong> {my_username}<br>
            <strong style="color:{accent_gold};">Email:</strong> {my_user.get('email','—')}<br>
            <strong style="color:{accent_gold};">Contact:</strong> {my_user.get('contact_no','—') or my_user.get('phone','—')}<br>
            <strong style="color:{accent_gold};">Address:</strong> {my_user.get('address','—')}<br>
            <strong style="color:{accent_gold};">Balance:</strong> <span style="color:{accent_primary}; font-weight:bold;">${balance:,.2f}</span><br>
            <strong style="color:{accent_gold};">Shared Accounts:</strong> {len(my_accounts)} active
          </div>
          <p style="text-align:center; margin-top:1.5rem; opacity:0.7;">KMFX Elite Access • 2026</p>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .flip-card {{ background:transparent; width:100%; height:auto; min-height:380px; perspective:1200px; }}
  .flip-card-inner {{ position:relative; width:100%; height:100%; text-align:center; transition: transform 0.9s cubic-bezier(0.68,-0.55,0.265,1.55); transform-style:preserve-3d; }}
  .flip-card:hover .flip-card-inner {{ transform: rotateY(180deg); }}
  .flip-card-front, .flip-card-back {{ position:absolute; width:100%; height:100%; -webkit-backface-visibility:hidden; backface-visibility:hidden; border-radius:20px; }}
  .flip-card-back {{ transform: rotateY(180deg); }}
  @media (max-width: 768px) {{ .flip-card {{ min-height:340px; }} }}
</style>

<p style="text-align:center; opacity:0.8; margin-top:1rem;">Hover or tap card to flip ↺</p>
""", unsafe_allow_html=True)

# ==================== QR with Regenerate ====================
st.subheader("Quick Login QR Code")

qr_token = my_user.get("qr_token")

if qr_token:
    qr_content = f"https://kmfxeaftmo.streamlit.app/?qr={qr_token}"  # ← your real URL

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00ffaa", back_color="black")

    buf = BytesIO()
    img.save(buf, "PNG")
    qr_bytes = buf.getvalue()

    c1, c2 = st.columns([1,2])
    c1.image(qr_bytes, use_column_width=True)
    with c2:
        st.caption("Scan to login instantly (no password needed)")
        st.download_button("Download QR", qr_bytes, "kmfx_login_qr.png", "image/png")

        st.markdown("---")
        st.warning("**Security Notice**\n\nIf this QR was exposed/shared/lost, regenerate now — old one becomes invalid.")

        if st.button("🔄 Regenerate QR Now", type="primary"):
            if st.session_state.get("confirm_regen", False):
                new_token = str(uuid.uuid4())
                supabase.table("users").update({"qr_token": new_token}).eq("id", my_user["id"]).execute()
                log_action("QR Regenerated", f"User {my_name} - old partial: {qr_token[:8]}...")
                st.session_state.confirm_regen = False
                st.success("New QR generated! Page refreshing...")
                st.rerun()
            else:
                st.session_state.confirm_regen = True
                st.error("Click again to confirm regeneration (old QR will stop working)")
                st.button("Cancel", on_click=lambda: st.session_state.pop("confirm_regen", None))
else:
    st.info("No QR yet.")
    if st.button("Generate First QR"):
        new_token = str(uuid.uuid4())
        supabase.table("users").update({"qr_token": new_token}).eq("id", my_user["id"]).execute()
        st.rerun()

# ────────────────────────────────────────────────
# SHARED ACCOUNTS + TREES
# ────────────────────────────────────────────────
st.subheader(f"Your Shared Accounts ({len(my_accounts)} active)")

if my_accounts:
    for acc in my_accounts:
        parts = acc.get("participants_v2") or acc.get("participants", [])
        my_part = next((p for p in parts if p.get("display_name") == my_name or str(p.get("user_id")) == str(my_user.get("id")) or p.get("name") == my_name), None)
        my_pct = my_part.get("percentage", 0) if my_part else 0
        projected = (acc.get("current_equity", 0) * my_pct / 100)

        with st.expander(f"{acc.get('name')} • Your share: {my_pct:.1f}% • {acc.get('current_phase')}"):
            cols = st.columns(2)
            cols[0].metric("Account Equity", f"${acc.get('current_equity',0):,.0f}")
            cols[0].metric("Your Projected Value", f"${projected:,.2f}")
            cols[1].metric("Withdrawable", f"${acc.get('withdrawable_balance',0):,.0f}")

            # Simple Sankey
            labels = ["Profits"]
            vals = []
            for p in parts:
                name = p.get("display_name") or p.get("name", "—")
                pct = p.get("percentage", 0)
                labels.append(f"{name} ({pct:.1f}%)")
                vals.append(pct)

            if vals:
                fig = go.Figure(go.Sankey(
                    node=dict(pad=15, thickness=20, label=labels, color=[accent_primary] + [accent_gold]*len(vals)),
                    link=dict(source=[0]*len(vals), target=list(range(1,len(labels))), value=vals)
                ))
                fig.update_layout(height=380, margin=dict(t=10,l=0,r=0,b=10))
                st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No shared accounts assigned yet.")

# ────────────────────────────────────────────────
# WITHDRAWALS
# ────────────────────────────────────────────────
st.subheader("💳 Withdrawal History & Requests")

if my_withdrawals:
    for w in my_withdrawals:
        color = {"Pending":"#ffa502", "Approved":accent_primary, "Paid":"#2ed573", "Rejected":"#ff4757"}.get(w["status"], "#666")
        st.markdown(f"""
        <div style="padding:1.4rem; border-left:5px solid {color}; background:rgba(255,255,255,0.05); border-radius:8px; margin-bottom:1rem;">
            <h4 style="margin:0;">${w['amount']:,.0f} — {w['status']}</h4>
            <small>Method: {w['method']} • Requested: {w['date_requested']}</small>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No withdrawal requests yet.")

with st.expander("➕ Request New Withdrawal"):
    if balance <= 0:
        st.info("No available balance to withdraw.")
    else:
        with st.form("wd_request"):
            amt = st.number_input("Amount (USD)", min_value=1.0, max_value=balance, step=50.0)
            method = st.selectbox("Method", ["USDT", "Bank Transfer", "Wise", "PayPal", "GCash", "Other"])
            details = st.text_area("Details (address / account info)")
            proof_file = st.file_uploader("Proof (required)", ["png","jpg","jpeg","pdf"])

            if st.form_submit_button("Submit Request", type="primary"):
                if amt > balance:
                    st.error("Amount exceeds balance")
                elif not proof_file:
                    st.error("Proof document is required")
                else:
                    try:
                        url, path = upload_to_supabase(proof_file, "client_files", "proofs")
                        supabase.table("client_files").insert({
                            "original_name": proof_file.name,
                            "file_url": url,
                            "storage_path": path,
                            "upload_date": datetime.now().date().isoformat(),
                            "sent_by": my_name,
                            "category": "Withdrawal Proof",
                            "assigned_client": my_name
                        }).execute()

                        supabase.table("withdrawals").insert({
                            "client_name": my_name,
                            "client_user_id": my_user["id"],
                            "amount": amt,
                            "method": method,
                            "details": details,
                            "status": "Pending",
                            "date_requested": datetime.now().date().isoformat()
                        }).execute()

                        st.success("Withdrawal request submitted with proof!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Submission failed: {e}")

# ────────────────────────────────────────────────
# PROOFS VAULT
# ────────────────────────────────────────────────
st.subheader("📁 Your Proof Vault (Permanent Storage)")

if my_proofs:
    cols = st.columns(3)
    for i, proof in enumerate(my_proofs):
        with cols[i % 3]:
            file_url = proof.get("file_url")
            if proof.get("storage_path"):
                try:
                    signed = supabase.storage.from_("client_files").create_signed_url(proof["storage_path"], 3600 * 2)
                    file_url = signed.signed_url
                except:
                    pass

            if file_url and proof["original_name"].lower().endswith(('.png','.jpg','.jpeg')):
                st.image(file_url, use_column_width=True, caption=proof["original_name"])
            else:
                st.markdown(f"**{proof['original_name']}**")
                st.caption(f"{proof.get('category','—')} • {proof['upload_date']}")

            if file_url:
                try:
                    resp = requests.get(file_url, timeout=8)
                    if resp.status_code == 200:
                        st.download_button(
                            "⬇ Download",
                            resp.content,
                            file_name=proof["original_name"],
                            use_container_width=True
                        )
                except:
                    st.caption("Download unavailable")
else:
    st.info("No uploaded proofs/documents yet.")

# ────────────────────────────────────────────────
# FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:4rem 1rem; text-align:center; margin:5rem auto; max-width:1000px; border-radius:24px; border:2px solid {accent_primary}30; background:linear-gradient(135deg, rgba(0,255,170,0.06), rgba(0,0,0,0.4)); box-shadow:0 15px 40px rgba(0,255,170,0.12);">
    <h1 style="font-size:2.8rem; background:linear-gradient(90deg,{accent_primary},{accent_gold}); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:1.5rem;">
        Your Empire • Your Rules
    </h1>
    <p style="font-size:1.3rem; opacity:0.9; margin:1.5rem 0;">
        Realtime • Transparent • Motivated Forever
    </p>
    <h2 style="color:{accent_gold}; font-size:2rem;">KMFX Elite • Built by Faith 👑 2026</h2>
</div>
""", unsafe_allow_html=True)