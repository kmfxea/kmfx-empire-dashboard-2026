# pages/👤_My_Profile.py
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import qrcode
from io import BytesIO
import requests
import uuid
import pandas as pd
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase  # Assume this is now cached!
from utils.helpers import upload_to_supabase, log_action

render_sidebar()
require_auth(min_role="client")  # Clients see full profile, owner/admin see admin view

# ─── THEME COLORS ───
accent_primary = "#00ffaa"
accent_gold = "#ffd700"
accent_glow = "#00ffaa40"
accent_hover = "#00ffcc"

# ─── SCROLL-TO-TOP (same as Dashboard) ───
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
</script>
""", unsafe_allow_html=True)

# ─── WELCOME + BALLOONS ───
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.success(f"Welcome back, {st.session_state.get('full_name', 'Leader')}! 👑")
    st.session_state.pop("just_logged_in", None)

st.header("👤 My Profile")
my_name = st.session_state.full_name
my_username = st.session_state.username
current_role = st.session_state.get("role", "guest").lower()

# ─── CLIENT PROFILE ───
if current_role == "client":
    st.markdown("**Your KMFX EA Elite Membership** • Realtime flip card, earnings, participation, withdrawals • Full transparency")

    # ─── CACHED + RETRY FETCH ───
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),  # or more specific
        before_sleep=lambda retry_state: st.toast(f"Retrying data fetch... (attempt {retry_state.attempt_number}/3)", icon="🔄")
    )
    @st.cache_data(ttl=60, show_spinner="Loading your profile data...")
    def fetch_client_data():
        try:
            user_resp = supabase.table("users").select("*").eq("username", my_username).single().execute()
            user = user_resp.data or {}

            # Shared accounts
            accs_resp = supabase.table("ftmo_accounts").select("*").execute()
            accounts = accs_resp.data or []
            my_accs = []
            uid = str(user.get("id", ""))
            for a in accounts:
                p_v2 = a.get("participants_v2", []) or []
                p_old = a.get("participants", []) or []
                if any(
                    p.get("display_name") == my_name or
                    str(p.get("user_id")) == uid or
                    p.get("name") == my_name
                    for p in p_v2 + p_old
                ):
                    my_accs.append(a)

            # Withdrawals
            wds = supabase.table("withdrawals").select("*").eq("client_name", my_name).order("date_requested", desc=True).execute().data or []

            # Proofs
            proofs = supabase.table("client_files").select("*").eq("assigned_client", my_name).order("upload_date", desc=True).execute().data or []

            return user, my_accs, wds, proofs

        except Exception as e:
            error_str = str(e)
            if "Resource temporarily unavailable" in error_str or "EAGAIN" in error_str or "pool" in error_str.lower():
                time.sleep(4)  # extra backoff for pool/socket issues
                raise  # retry
            else:
                st.error(f"⚠️ Couldn't load full profile data right now. Showing limited view. ({error_str[:80]}...)")
                return {}, [], [], []

    with st.spinner("Fetching your empire details..."):
        user, my_accounts, my_withdrawals, my_proofs = fetch_client_data()

    # Fallbacks if fetch failed
    if not user:
        user = {"title": "Member", "balance": 0.0, "email": "—", "contact_no": "—", "address": "—"}

    # ─── PREMIUM FLIP CARD (original stable fix - ATM size) ───
    my_title = user.get("title", "Member").upper()
    card_title = f"{my_title} CARD" if my_title != "NONE" else "MEMBER CARD"
    balance = user.get("balance", 0.0)

    st.markdown(f"""
    <div style="perspective: 1800px; max-width: 640px; margin: 2.5rem auto; width: 100%;">
      <div class="flip-card-outer" style="position: relative; width: 100%; aspect-ratio: 85.6 / 53.98; max-height: 85vh;">
        <div class="flip-card">
          <div class="flip-card-inner">
            <div class="flip-card-front">
              <div style="
                background: linear-gradient(135deg, #0a0a0a, #1a1a1a);
                backdrop-filter: blur(16px);
                border-radius: 16px;
                height: 100%;
                padding: 5% 7% 5% 7%;
                box-shadow: 0 18px 48px rgba(0,255,170,0.22);
                color: white;
                border: 1.8px solid {accent_gold};
                display: flex;
                flex-direction: column;
                justify-content: space-between;
              ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4%;">
                  <h2 style="margin:0; font-size: clamp(1.9rem, 7vw, 3.1rem); color: {accent_gold}; letter-spacing: 4px; text-shadow: 0 0 14px {accent_gold};">KMFX EA</h2>
                  <h3 style="margin:0; font-size: clamp(1.1rem, 4vw, 1.7rem); color: {accent_gold};">{card_title}</h3>
                </div>

                <div style="text-align: center; flex-grow: 1; display: flex; align-items: center; justify-content: center; padding: 0 4%;">
                  <h1 style="margin:0; font-size: clamp(1.8rem, 7vw, 3.0rem); letter-spacing: 3px; line-height: 1.15; word-break: break-word; overflow-wrap: break-word;">{my_name.upper()}</h1>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 4%;">
                  <div style="font-size: clamp(0.95rem, 3.2vw, 1.25rem); opacity: 0.9;">Elite Empire Member</div>
                  <div style="text-align: right;">
                    <p style="margin:0 0 0.3rem 0; font-size: clamp(0.9rem, 3vw, 1.1rem); opacity: 0.9;">Available Balance</p>
                    <h2 style="margin:0; color: {accent_primary}; text-shadow: 0 0 18px {accent_primary};">${balance:,.2f}</h2>
                  </div>
                </div>

                <p style="text-align:center; margin:1.4rem 0 0; opacity:0.7; font-size:0.9rem;">Built by Faith • Shared for Generations • 2026 👑</p>
              </div>
            </div>

            <div class="flip-card-back">
              <div style="
                background: linear-gradient(135deg, #1a1a1a, #0a0a0a);
                backdrop-filter: blur(16px);
                border-radius: 16px;
                height: 100%;
                padding: 5% 7%;
                box-shadow: 0 18px 48px rgba(0,255,170,0.22);
                color: white;
                border: 1.8px solid {accent_gold};
              ">
                <h2 style="text-align:center; color: {accent_gold}; margin:0 0 1.2rem; font-size: clamp(1.5rem, 5vw, 2rem);">Membership Details</h2>
                
                <div style="font-size: clamp(0.97rem, 3.4vw, 1.15rem); line-height: 1.85;">
                  <strong style="color:{accent_gold};">Full Name:</strong> {my_name}<br>
                  <strong style="color:{accent_gold};">Title:</strong> {my_title}<br>
                  <strong style="color:{accent_gold};">Username:</strong> {my_username}<br>
                  <strong style="color:{accent_gold};">Email:</strong> {user.get('email','—')}<br>
                  <strong style="color:{accent_gold};">Contact:</strong> {user.get('contact_no') or user.get('phone','—')}<br>
                  <strong style="color:{accent_gold};">Address:</strong> {user.get('address','—')}<br>
                  <strong style="color:{accent_gold};">Balance:</strong> <span style="color:{accent_primary};">${balance:,.2f}</span><br>
                  <strong style="color:{accent_gold};">Shared Accounts:</strong> {len(my_accounts)} active
                </div>

                <p style="text-align:center; margin-top:1.6rem; opacity:0.75; font-size:0.95rem;">KMFX Elite Access • 2026</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <style>
      .flip-card-outer {{ width: 100%; max-width: 640px; margin: 0 auto; }}
      .flip-card {{ width: 100%; height: 100%; perspective: 1800px; }}
      .flip-card-inner {{ 
        position: relative; 
        width: 100%; 
        height: 100%; 
        transition: transform 0.92s cubic-bezier(0.68, -0.55, 0.265, 1.5); 
        transform-style: preserve-3d; 
      }}
      .flip-card:hover .flip-card-inner, .flip-card:active .flip-card-inner {{ transform: rotateY(180deg); }}
      .flip-card-front, .flip-card-back {{ 
        position: absolute; 
        width: 100%; 
        height: 100%; 
        -webkit-backface-visibility: hidden; 
        backface-visibility: hidden; 
        border-radius: 16px; 
      }}
      .flip-card-back {{ transform: rotateY(180deg); }}
      @media (max-width: 576px) {{ 
        .flip-card-outer {{ aspect-ratio: 86 / 54; }} 
      }}
      @media (min-width: 577px) and (max-width: 992px) {{ 
        .flip-card-outer {{ aspect-ratio: 85.6 / 53.98; max-height: 420px; }} 
      }}
    </style>

    <p style="text-align:center; opacity:0.75; margin:1.2rem 0 2.5rem; font-size:0.95rem;">
      Hover or tap card to flip ↺ (ATM-card size feel)
    </p>
    """, unsafe_allow_html=True)

    # ─── QUICK LOGIN QR ───
    st.subheader("🔑 Quick Login QR Code")
    qr_token = user.get("qr_token")
    app_url = "https://kmfxea.streamlit.app"
    if qr_token:
        qr_content = f"{app_url}/?qr={qr_token}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img = qr.make_image(fill_color=accent_primary, back_color="#000000")
        buf = BytesIO()
        img.save(buf, "PNG")
        qr_bytes = buf.getvalue()
        c1, c2 = st.columns([1, 3])
        c1.image(qr_bytes, use_column_width=True, caption="Scan to login instantly")
        with c2:
            st.caption("Scan for instant login – no password needed")
            st.code(qr_content, language=None)
            st.download_button("⬇ Download QR", qr_bytes, f"KMFX_QR_{my_name.replace(' ','_')}.png", "image/png", use_container_width=True)
        st.markdown("---")
        st.warning("**Regenerate if QR is exposed/shared/lost** — old QR will stop working")
        col_regen, col_revoke = st.columns(2)
        with col_regen:
            if st.button("🔄 Regenerate QR Code", type="primary", use_container_width=True):
                new_token = str(uuid.uuid4())
                supabase.table("users").update({"qr_token": new_token}).eq("id", user["id"]).execute()
                log_action("QR Regenerated", f"User: {my_name}")
                st.success("New QR created! Refreshing...")
                st.rerun()
        with col_revoke:
            if st.button("❌ Revoke QR Code", type="secondary", use_container_width=True):
                supabase.table("users").update({"qr_token": None}).eq("id", user["id"]).execute()
                log_action("QR Revoked", f"User: {my_name}")
                st.success("QR revoked • Login code disabled")
                st.rerun()
    else:
        st.info("No Quick Login QR yet. Contact admin/owner to generate one.")

    # ─── SHARED ACCOUNTS ───
    st.subheader(f"Your Shared Accounts ({len(my_accounts)} active)")
    if my_accounts:
        for acc in my_accounts:
            participants = acc.get("participants_v2") or acc.get("participants", [])
            my_part = next((p for p in participants if p.get("display_name") == my_name or str(p.get("user_id")) == str(user.get("id")) or p.get("name") == my_name), None)
            my_pct = my_part.get("percentage", 0) if my_part else 0
            projected = acc.get("current_equity", 0) * my_pct / 100
            with st.expander(f"🌟 {acc.get('name')} • Your share: {my_pct:.1f}% • {acc.get('current_phase')}"):
                cols = st.columns(2)
                cols[0].metric("Equity", f"${acc.get('current_equity',0):,.0f}")
                cols[0].metric("Your Projected", f"${projected:,.2f}")
                cols[1].metric("Withdrawable", f"${acc.get('withdrawable_balance',0):,.0f}")
                labels = ["Profits"]
                vals = []
                for p in participants:
                    name = p.get("display_name") or p.get("name", "—")
                    pct = p.get("percentage", 0)
                    labels.append(f"{name} ({pct:.1f}%)")
                    vals.append(pct)
                if vals:
                    fig = go.Figure(go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels, color=[accent_primary] + [accent_gold]*len(vals)),
                        link=dict(source=[0]*len(vals), target=list(range(1,len(labels))), value=vals)
                    ))
                    fig.update_layout(height=350, margin=dict(t=10))
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No shared accounts yet.")

    # ─── WITHDRAWAL HISTORY & REQUEST ───
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

    with st.expander("➕ Request New Withdrawal", expanded=False):
        if balance <= 0:
            st.info("No available balance yet.")
        else:
            with st.form("wd_request"):
                amt = st.number_input("Amount (USD)", min_value=1.0, max_value=balance, step=50.0, format="%.2f")
                method = st.selectbox("Method", ["USDT", "Bank Transfer", "Wise", "PayPal", "GCash", "Other"])
                details = st.text_area("Details (wallet/address/bank info)")
                proof = st.file_uploader("Proof (required – permanent)", type=["png","jpg","jpeg","pdf","gif"])
                submitted = st.form_submit_button("Submit Request", type="primary")
                if submitted:
                    if amt > balance:
                        st.error("Amount exceeds your balance")
                    elif not proof:
                        st.error("Proof document is required")
                    else:
                        with st.spinner("Submitting withdrawal request..."):
                            try:
                                url, storage_path = upload_to_supabase(
                                    file=proof,
                                    bucket="client_files",
                                    folder="withdrawals"
                                )
                                supabase.table("client_files").insert({
                                    "original_name": proof.name,
                                    "file_url": url,
                                    "storage_path": storage_path,
                                    "upload_date": datetime.now().date().isoformat(),
                                    "sent_by": my_name,
                                    "category": "Withdrawal Proof",
                                    "assigned_client": my_name,
                                    "notes": f"Proof for ${amt:,.2f} withdrawal request"
                                }).execute()
                                supabase.table("withdrawals").insert({
                                    "client_name": my_name,
                                    "client_user_id": user.get("id"),
                                    "amount": amt,
                                    "method": method,
                                    "details": details.strip() or None,
                                    "status": "Pending",
                                    "date_requested": datetime.now().date().isoformat()
                                }).execute()
                                st.success("Withdrawal request submitted! Proof permanently stored.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Submission failed: {str(e)}")

    # ─── PROOF VAULT ───
    st.subheader("📁 Proof Vault")
    if my_proofs:
        proof_cols = st.columns(4)
        for idx, p in enumerate(my_proofs):
            with proof_cols[idx % 4]:
                file_url = p.get("file_url")
                if p.get("storage_path"):
                    try:
                        signed = supabase.storage.from_("client_files").create_signed_url(p["storage_path"], expires_in=7200)
                        file_url = signed.signed_url
                    except:
                        pass
                if file_url:
                    if p["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif')):
                        st.image(file_url, caption=p["original_name"], use_column_width=True)
                    else:
                        st.markdown(f"**{p['original_name']}** • {p.get('upload_date', '—')}")
                        try:
                            r = requests.get(file_url, timeout=10)
                            if r.status_code == 200:
                                st.download_button(
                                    "⬇ Download",
                                    data=r.content,
                                    file_name=p["original_name"],
                                    mime="application/octet-stream",
                                    use_container_width=True,
                                    key=f"dl_proof_{p['id']}"
                                )
                        except:
                            st.caption("Download unavailable")
                else:
                    st.caption("File unavailable")
    else:
        st.info("No proofs uploaded yet")

# ─── OWNER / ADMIN OVERVIEW (unchanged, but add similar caching if needed) ───
else:
    # ... your existing owner/admin code here ...
    pass  # or copy from original if you want full file

# ─── MOTIVATIONAL FOOTER ───
st.markdown(f"""
<div class="glass-card" style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Your Empire • Your Legacy
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Realtime balance • Secure withdrawals • Permanent proofs • Elite access
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith, Shared for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)