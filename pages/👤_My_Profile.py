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
# THEME COLORS – exact match with Dashboard
# ────────────────────────────────────────────────
accent_primary = "#00ffaa"
accent_gold    = "#ffd700"
accent_glow    = "#00ffaa40"
accent_hover   = "#00ffcc"

# ────────────────────────────────────────────────
# SCROLL-TO-TOP – copied from Dashboard
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
# WELCOME + REFRESH
# ────────────────────────────────────────────────
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.success(f"Welcome to your profile, {st.session_state.get('full_name', 'Elite Member')}! 👑")
    st.session_state.pop("just_logged_in", None)

st.header("👤 My Profile")
st.markdown("Your KMFX EA Elite Membership • Realtime • Full Transparency")

my_name     = st.session_state.full_name
my_username = st.session_state.username

if st.button("🔄 Refresh Profile Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Auto-refreshes every 12 seconds • All data realtime")

# ────────────────────────────────────────────────
# DATA FETCH (same logic as before)
# ────────────────────────────────────────────────
@st.cache_data(ttl=12)
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

# ────────────────────────────────────────────────
# RESTORED PREMIUM FLIP CARD (almost 1:1 from old version)
# ────────────────────────────────────────────────
my_title   = my_user.get("title", "Member").upper()
card_title = f"{my_title} CARD" if my_title != "NONE" else "MEMBER CARD"
balance    = my_user.get("balance", 0.0)

# Dark theme flip card (matches app feel)
front_bg   = "linear-gradient(135deg, #000000, #1f1f1f)"
back_bg    = "linear-gradient(135deg, #1f1f1f, #000000)"
text_color = "#ffffff"
border_col = accent_gold
shadow     = "0 20px 50px rgba(0,255,170,0.25)"

st.markdown(f"""
<div style="perspective: 1500px; max-width: 620px; margin: 2.5rem auto; width: 100%;">
  <div class="flip-card">
    <div class="flip-card-inner">
      <!-- Front -->
      <div class="flip-card-front">
        <div style="background: {front_bg}; backdrop-filter: blur(20px); border-radius: 20px; padding: 2.2rem; min-height: 380px; box-shadow: {shadow}; color: {text_color}; border: 2px solid {border_col}; display: flex; flex-direction: column; justify-content: space-between;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin:0; font-size: clamp(2.4rem, 6vw, 3.4rem); color: {accent_gold}; letter-spacing: 6px; text-shadow: 0 0 16px {accent_gold};">KMFX EA</h2>
            <h3 style="margin:0; font-size: clamp(1.4rem, 4vw, 1.9rem); color: {accent_gold};">{card_title}</h3>
          </div>
          <div style="text-align: center; flex-grow: 1; display: flex; align-items: center; justify-content: center;">
            <h1 style="margin:0; font-size: clamp(2.2rem, 7vw, 3.2rem); letter-spacing: 4px;">{my_name.upper()}</h1>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: flex-end;">
            <div style="font-size: clamp(1.1rem, 3vw, 1.4rem); opacity: 0.9;">Elite Empire Member</div>
            <div style="text-align: right;">
              <p style="margin:0; opacity: 0.9; font-size: 1.1rem;">Available Balance</p>
              <h2 style="margin:0; color: {accent_primary}; text-shadow: 0 0 20px {accent_primary};">${balance:,.2f}</h2>
            </div>
          </div>
          <p style="text-align:center; margin:1.2rem 0 0; opacity:0.75; font-size:0.95rem;">Built by Faith • Shared for Generations • 2026 👑</p>
        </div>
      </div>
      <!-- Back -->
      <div class="flip-card-back">
        <div style="background: {back_bg}; backdrop-filter: blur(20px); border-radius: 20px; padding: 2.2rem; min-height: 380px; box-shadow: {shadow}; color: {text_color}; border: 2px solid {border_col};">
          <h2 style="text-align:center; color: {accent_gold}; margin:0 0 1.4rem; font-size:1.8rem;">Membership Details</h2>
          <div style="height:40px; background:#333; border-radius:10px; margin-bottom:1.6rem;"></div>
          <div style="font-size:1.05rem; line-height:1.9;">
            <strong style="color:{accent_gold};">Full Name:</strong> {my_name}<br>
            <strong style="color:{accent_gold};">Title:</strong> {my_title}<br>
            <strong style="color:{accent_gold};">Username:</strong> {my_username}<br>
            <strong style="color:{accent_gold};">Email:</strong> {my_user.get('email','—')}<br>
            <strong style="color:{accent_gold};">Contact:</strong> {my_user.get('contact_no') or my_user.get('phone','—')}<br>
            <strong style="color:{accent_gold};">Address:</strong> {my_user.get('address','—')}<br>
            <strong style="color:{accent_gold};">Balance:</strong> <span style="color:{accent_primary};">${balance:,.2f}</span><br>
            <strong style="color:{accent_gold};">Shared Accounts:</strong> {len(my_accounts)} active
          </div>
          <p style="text-align:center; margin-top:1.8rem; opacity:0.75;">KMFX Elite Access • 2026</p>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .flip-card { background:transparent; width:100%; min-height:380px; perspective:1200px; }
  .flip-card-inner { position:relative; width:100%; height:100%; transition: transform 0.9s cubic-bezier(0.68,-0.55,0.265,1.55); transform-style:preserve-3d; }
  .flip-card:hover .flip-card-inner { transform: rotateY(180deg); }
  .flip-card-front, .flip-card-back { position:absolute; width:100%; height:100%; -webkit-backface-visibility:hidden; backface-visibility:hidden; border-radius:20px; }
  .flip-card-back { transform: rotateY(180deg); }
  @media (max-width: 768px) { .flip-card { min-height:340px; } }
</style>

<p style="text-align:center; opacity:0.8; margin:1rem 0 2.5rem;">Hover or tap to flip the card ↺</p>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# QR with safe regeneration – Dashboard-style warning
# ────────────────────────────────────────────────
st.markdown('<div class="glass-card" style="padding:1.8rem; border-radius:12px;">', unsafe_allow_html=True)
st.subheader("🔑 Quick Login QR Code")

qr_token = my_user.get("qr_token")
APP_URL = "https://kmfxea.streamlit.app"

if qr_token:
    qr_content = f"{APP_URL}/?qr={qr_token}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color=accent_primary, back_color="#000000")

    buf = BytesIO()
    img.save(buf, "PNG")
    qr_bytes = buf.getvalue()

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(qr_bytes, use_column_width=True)

    with col2:
        st.caption("Scan to login instantly – no password needed")
        st.code(qr_content, language=None)

        st.download_button(
            "⬇ Download QR PNG",
            qr_bytes,
            f"KMFX_{my_name.replace(' ','_')}_QR.png",
            "image/png",
            use_container_width=True
        )

        st.markdown("---")
        st.warning("**Important Security Step**\n\nIf this QR code has been shared, exposed, or your device is lost → regenerate now. The old QR will become invalid immediately.")

        if st.button("🔄 Regenerate QR Code", type="primary", use_container_width=True):
            new_token = str(uuid.uuid4())
            supabase.table("users").update({"qr_token": new_token}).eq("id", my_user["id"]).execute()
            log_action("QR Regenerated", f"User: {my_name} | Old partial: {qr_token[:8]}...")
            st.success("New QR generated! Refreshing page...")
            st.rerun()
else:
    st.info("No Quick Login QR yet.")
    if st.button("Generate QR Code", type="primary"):
        new_token = str(uuid.uuid4())
        supabase.table("users").update({"qr_token": new_token}).eq("id", my_user["id"]).execute()
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Shared Accounts – Dashboard-like glass cards
# ────────────────────────────────────────────────
st.markdown('<div class="glass-card" style="padding:1.8rem; border-radius:12px; margin-top:2rem;">', unsafe_allow_html=True)
st.subheader(f"Your Shared Accounts ({len(my_accounts)})")

if my_accounts:
    for acc in my_accounts:
        parts = acc.get("participants_v2") or acc.get("participants", [])
        my_part = next((p for p in parts if p.get("display_name") == my_name or str(p.get("user_id")) == str(my_user.get("id")) or p.get("name") == my_name), None)
        my_pct = my_part.get("percentage", 0) if my_part else 0
        projected = acc.get("current_equity", 0) * my_pct / 100

        st.markdown(f"""
        <div style="padding:1.4rem; background:rgba(0,255,170,0.04); border-radius:10px; margin-bottom:1.2rem;">
            <h4 style="margin:0 0 1rem; color:{accent_primary};">{acc.get('name')} • Your share: {my_pct:.1f}%</h4>
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1rem;">
                <div><strong>Phase:</strong> {acc.get('current_phase','—')}</div>
                <div><strong>Equity:</strong> ${acc.get('current_equity',0):,.0f}</div>
                <div><strong>Withdrawable:</strong> ${acc.get('withdrawable_balance',0):,.0f}</div>
                <div><strong>Your Projected:</strong> ${projected:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No shared accounts assigned yet.")
st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Motivational Footer – exact Dashboard style
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