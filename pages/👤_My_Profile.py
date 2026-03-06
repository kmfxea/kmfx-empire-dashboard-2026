# pages/👤_My_Profile.py
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import qrcode
from io import BytesIO
import requests
import uuid

# ────────────────────────────────────────────────
# IMPORTS & INITIAL SETUP
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase, log_action

render_sidebar()
require_auth(min_role="client")

# ─── THEME COLORS ───
accent_primary = "#00ffaa"
accent_gold    = "#ffd700"
accent_glow    = "#00ffaa40"
accent_hover   = "#00ffcc"

# ─── FORCE SCROLL TO TOP ───
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

# ─── WELCOME MESSAGE ON FRESH LOGIN ───
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.success(f"Welcome back, {st.session_state.get('full_name', 'Leader')}! 👑")
    st.session_state.pop("just_logged_in", None)

# ─── HEADER WITH ROLE BADGE ───
role = st.session_state.get("role", "client").lower()
role_emoji = {"client": "👤", "admin": "🛡️", "owner": "👑"}.get(role, "❓")
st.header(f"{role_emoji} My Profile • {role.title()} View")

my_name     = st.session_state.full_name
my_username = st.session_state.username

# Navigation helper
if "navigate_to" not in st.session_state:
    st.session_state.navigate_to = None

# ─── FETCH CURRENT USER DATA ───
@st.cache_data(ttl=60)
def fetch_user_data():
    try:
        resp = supabase.table("users").select("*").eq("username", my_username).maybe_single().execute()
        return resp.data or {}
    except Exception as e:
        st.error(f"User fetch error: {str(e)}")
        return {}

user = fetch_user_data()
balance   = user.get("balance", 0.0)
my_title  = user.get("title", "Member").upper()
qr_token  = user.get("qr_token")
avatar_url = user.get("avatar_url")

# ─── CIRCULAR PROFILE PICTURE WITH UPLOAD ───
st.subheader("Personal Information")

# Default placeholder: first letter of name
default_avatar = f"https://via.placeholder.com/180/111/eee?text={my_name[0].upper()}"

# Circular avatar with hover overlay
st.markdown(
    f"""
    <style>
        .avatar-container {{
            position: relative;
            width: 180px;
            height: 180px;
            margin: 0 auto 1.2rem auto;
        }}
        .avatar-img {{
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid {accent_gold};
            box-shadow: 0 8px 25px rgba(0,255,170,0.3);
            transition: all 0.3s ease;
        }}
        .avatar-img:hover {{
            transform: scale(1.05);
            box-shadow: 0 12px 35px rgba(0,255,170,0.5);
        }}
        .upload-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.55);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease;
            cursor: pointer;
        }}
        .avatar-container:hover .upload-overlay {{
            opacity: 1;
        }}
        .upload-icon {{
            font-size: 3rem;
            color: {accent_gold};
        }}
    </style>

    <div class="avatar-container">
        <img src="{avatar_url or default_avatar}" class="avatar-img" alt="Profile Picture" />
        <label for="avatar-upload-hidden" class="upload-overlay">
            <div class="upload-icon">📷</div>
        </label>
    </div>
    """,
    unsafe_allow_html=True
)

# Hidden uploader (triggered by clicking overlay)
uploaded_file = st.file_uploader(
    "Change Profile Picture",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False,
    label_visibility="collapsed",
    key="avatar_uploader"
)

if uploaded_file is not None:
    if uploaded_file.size > 3 * 1024 * 1024:  # 3MB limit
        st.error("File too large (max 3MB)")
    else:
        with st.spinner("Uploading profile picture..."):
            try:
                # Upload to Supabase
                file_url, storage_path = upload_to_supabase(
                    file=uploaded_file,
                    bucket="client_files",                # ← change if your bucket name is different
                    folder="profiles/avatars",
                    use_signed_url=False             # public URL for easy display
                )

                if file_url:
                    # Update user record
                    supabase.table("users").update({
                        "avatar_url": file_url
                    }).eq("username", my_username).execute()

                    log_action("Profile Picture Updated", f"User: {my_name} | Path: {storage_path}")

                    st.success("Profile picture updated!")
                    st.rerun()
                else:
                    st.error("Upload failed – please try again.")
            except Exception as e:
                st.error(f"Upload error: {str(e)}")

# Personal details below avatar
cols = st.columns([2, 5])
with cols[0]:
    st.markdown("**Name**")
    st.markdown("**Username**")
    st.markdown("**Title**")
    st.markdown("**Email**")
    st.markdown("**Contact**")
    st.markdown("**Address**")
with cols[1]:
    st.markdown(f"{my_name}")
    st.markdown(f"@{my_username}")
    st.markdown(f"{my_title}")
    st.markdown(f"{user.get('email', '—')}")
    st.markdown(f"{user.get('contact_no') or user.get('phone', '—')}")
    st.markdown(f"{user.get('address', '—')}")

st.metric("Available Balance", f"${balance:,.2f}")
st.markdown("---")

# ─── ROLE-SPECIFIC CONTENT ───
if role == "client":
    # ── CLIENT VIEW ────────────────────────────────────────────────

    # Premium Flip Card
    st.subheader("Your KMFX EA Elite Membership Card")
    card_title = f"{my_title} CARD" if my_title != "NONE" else "MEMBER CARD"

    st.markdown(f"""
    <div style="perspective: 1500px; max-width: 620px; margin: 2.5rem auto; width: 100%;">
      <div class="flip-card">
        <div class="flip-card-inner">
          <div class="flip-card-front">
            <div style="background: linear-gradient(135deg, #000000, #1f1f1f); backdrop-filter: blur(20px); border-radius: 20px; padding: 2.2rem; min-height: 380px; box-shadow: 0 20px 50px rgba(0,255,170,0.25); color: white; border: 2px solid {accent_gold}; display: flex; flex-direction: column; justify-content: space-between;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin:0; font-size: clamp(2.4rem, 6vw, 3.4rem); color: {accent_gold}; letter-spacing: 5px; text-shadow: 0 0 16px {accent_gold};">KMFX EA</h2>
                <h3 style="margin:0; font-size: clamp(1.4rem, 4vw, 1.9rem); color: {accent_gold};">{card_title}</h3>
              </div>
              <div style="text-align: center; flex-grow: 1; display: flex; align-items: center; justify-content: center;">
                <h1 style="margin:0; font-size: clamp(2.2rem, 7vw, 3.2rem); letter-spacing: 4px;">{my_name.upper()}</h1>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                <div style="font-size: clamp(1.1rem, 3vw, 1.4rem); opacity: 0.9;">Elite Empire Member</div>
                <div style="text-align: right;">
                  <p style="margin:0; opacity: 0.9;">Available Balance</p>
                  <h2 style="margin:0; color: {accent_primary}; text-shadow: 0 0 20px {accent_primary};">${balance:,.2f}</h2>
                </div>
              </div>
              <p style="text-align:center; margin:1.2rem 0 0; opacity:0.75; font-size:0.95rem;">Built by Faith • Shared for Generations • 2026 👑</p>
            </div>
          </div>
          <div class="flip-card-back">
            <div style="background: linear-gradient(135deg, #1f1f1f, #000000); backdrop-filter: blur(20px); border-radius: 20px; padding: 2.2rem; min-height: 380px; box-shadow: 0 20px 50px rgba(0,255,170,0.25); color: white; border: 2px solid {accent_gold};">
              <h2 style="text-align:center; color: {accent_gold}; margin:0 0 1.4rem; font-size:1.8rem;">Membership Details</h2>
              <div style="height:40px; background:#333; border-radius:10px; margin-bottom:1.6rem;"></div>
              <div style="font-size:1.05rem; line-height:1.9;">
                <strong style="color:{accent_gold};">Full Name:</strong> {my_name}<br>
                <strong style="color:{accent_gold};">Title:</strong> {my_title}<br>
                <strong style="color:{accent_gold};">Username:</strong> {my_username}<br>
                <strong style="color:{accent_gold};">Email:</strong> {user.get('email','—')}<br>
                <strong style="color:{accent_gold};">Contact:</strong> {user.get('contact_no') or user.get('phone','—')}<br>
                <strong style="color:{accent_gold};">Address:</strong> {user.get('address','—')}<br>
                <strong style="color:{accent_gold};">Balance:</strong> <span style="color:{accent_primary};">${balance:,.2f}</span><br>
              </div>
              <p style="text-align:center; margin-top:1.8rem; opacity:0.75;">KMFX Elite Access • 2026</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    <style>
      .flip-card {{ background:transparent; width:100%; min-height:380px; perspective:1200px; }}
      .flip-card-inner {{ position:relative; width:100%; height:100%; transition: transform 0.9s cubic-bezier(0.68,-0.55,0.265,1.55); transform-style:preserve-3d; }}
      .flip-card:hover .flip-card-inner {{ transform: rotateY(180deg); }}
      .flip-card-front, .flip-card-back {{ position:absolute; width:100%; height:100%; -webkit-backface-visibility:hidden; backface-visibility:hidden; border-radius:20px; }}
      .flip-card-back {{ transform: rotateY(180deg); }}
      @media (max-width: 768px) {{ .flip-card {{ min-height:340px; }} }}
    </style>
    <p style="text-align:center; opacity:0.8; margin-top:1rem;">Hover or tap card to flip ↺</p>
    """, unsafe_allow_html=True)

    # Quick Login QR
    st.subheader("🔑 Quick Login QR Code")
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
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Regenerate QR Code", type="primary", use_container_width=True):
                new_token = str(uuid.uuid4())
                supabase.table("users").update({"qr_token": new_token}).eq("username", my_username).execute()
                log_action("QR Regenerated", f"User: {my_name}")
                st.success("New QR created! Refreshing...")
                st.rerun()
        with col2:
            if st.button("❌ Revoke QR Code", type="secondary", use_container_width=True):
                supabase.table("users").update({"qr_token": None}).eq("username", my_username).execute()
                log_action("QR Revoked", f"User: {my_name}")
                st.success("QR revoked • Login code disabled")
                st.rerun()
    else:
        st.info("No Quick Login QR yet. Contact admin/owner to generate one.")

    # Shared Accounts + Withdrawals + Proofs (same as before)
    @st.cache_data(ttl=30)
    def fetch_client_data():
        try:
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
            wds = supabase.table("withdrawals").select("*").eq("client_name", my_name).order("date_requested", desc=True).execute().data or []
            proofs = supabase.table("client_files").select("*").eq("assigned_client", my_name).order("upload_date", desc=True).execute().data or []
            return my_accs, wds, proofs
        except Exception as e:
            st.error(f"Client data fetch error: {str(e)}")
            return [], [], []

    my_accounts, my_withdrawals, my_proofs = fetch_client_data()

    st.subheader(f"Your Shared Accounts ({len(my_accounts)} active)")
    if my_accounts:
        for acc in my_accounts:
            participants = acc.get("participants_v2") or acc.get("participants", [])
            my_part = next((p for p in participants if p.get("display_name") == my_name or str(p.get("user_id")) == str(user.get("id")) or p.get("name") == my_name), None)
            my_pct = my_part.get("percentage", 0) if my_part else 0
            projected = acc.get("current_equity", 0) * my_pct / 100
            with st.expander(f"🌟 {acc.get('name')} • Your share: {my_pct:.1f}% • {acc.get('current_phase')}"):
                c1, c2 = st.columns(2)
                c1.metric("Equity", f"${acc.get('current_equity',0):,.0f}")
                c1.metric("Your Projected", f"${projected:,.2f}")
                c2.metric("Withdrawable", f"${acc.get('withdrawable_balance',0):,.0f}")
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

    st.subheader("💳 Withdrawal History & Requests")
    if my_withdrawals:
        for w in my_withdrawals:
            color = {"Pending":"#ffa502", "Approved":accent_primary, "Paid":"#2ed573", "Rejected":"#ff4757"}.get(w.get("status","Pending"), "#666")
            st.markdown(f"""
            <div style="padding:1.4rem; border-left:5px solid {color}; background:rgba(255,255,255,0.05); border-radius:8px; margin-bottom:1rem;">
                <h4 style="margin:0;">${w.get('amount',0):,.0f} — {w.get('status','Pending')}</h4>
                <small>Method: {w.get('method','—')} • Requested: {w.get('date_requested','—')}</small>
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
                        with st.spinner("Submitting..."):
                            try:
                                url, path = upload_to_supabase(proof, "client_files", "withdrawals")
                                supabase.table("client_files").insert({
                                    "original_name": proof.name,
                                    "file_url": url,
                                    "storage_path": path,
                                    "upload_date": datetime.now().date().isoformat(),
                                    "sent_by": my_name,
                                    "category": "Withdrawal Proof",
                                    "assigned_client": my_name,
                                    "notes": f"Proof for ${amt:,.2f} withdrawal"
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
                                st.success("Request submitted! Proof stored permanently.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Submission failed: {str(e)}")

    st.subheader("📁 Proof Vault")
    if my_proofs:
        cols = st.columns(4)
        for i, p in enumerate(my_proofs):
            with cols[i % 4]:
                file_url = p.get("file_url")
                if p.get("storage_path"):
                    try:
                        signed = supabase.storage.from_("client_files").create_signed_url(p["storage_path"], 7200)
                        file_url = signed.get("signedURL")
                    except:
                        pass
                if file_url:
                    if p["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif')):
                        st.image(file_url, caption=p["original_name"], use_column_width=True)
                    else:
                        st.markdown(f"**{p['original_name']}** • {p.get('upload_date','—')}")
                        try:
                            r = requests.get(file_url, timeout=10)
                            if r.status_code == 200:
                                st.download_button("⬇ Download", r.content, p["original_name"], use_container_width=True, key=f"dl_{p['id']}")
                        except:
                            st.caption("Download unavailable")
    else:
        st.info("No proofs uploaded yet.")

elif role in ("admin", "owner"):
    # ── ADMIN & OWNER VIEW ─────────────────────────────────────────

    st.subheader("Empire Overview & Quick Controls")

    @st.cache_data(ttl=30)
    def fetch_empire_overview():
        try:
            gf = supabase.table("mv_growth_fund_balance").select("balance").execute().data
            gf_balance = gf[0]["balance"] if gf else 0.0

            emp = supabase.table("mv_empire_summary").select("*").execute().data
            emp_data = emp[0] if emp else {"total_accounts":0, "total_equity":0, "total_withdrawable":0}

            cl = supabase.table("mv_client_balances").select("*").execute().data
            cl_data = cl[0] if cl else {"total_client_balances":0, "total_clients":0}

            recent = supabase.table("profits").select("gross_profit, record_date").order("record_date", desc=True).limit(5).execute().data or []

            return gf_balance, emp_data, cl_data, recent
        except Exception as e:
            st.error(f"Overview fetch error: {str(e)}")
            return 0.0, {}, {}, []

    gf_balance, empire, clients, recent_profits = fetch_empire_overview()

    cols = st.columns(4)
    cols[0].metric("Active Accounts", empire.get("total_accounts", 0))
    cols[1].metric("Total Equity", f"${empire.get('total_equity', 0):,.0f}")
    cols[2].metric("Withdrawable", f"${empire.get('total_withdrawable', 0):,.0f}")
    cols[3].metric("Growth Fund", f"${gf_balance:,.0f}")

    if role == "owner":
        extra = st.columns(2)
        extra[0].metric("Total Clients", clients.get("total_clients", 0))
        extra[1].metric("Client Balances", f"${clients.get('total_client_balances', 0):,.0f}")

    st.subheader("Recent Profits (Last 5)")
    if recent_profits:
        for p in recent_profits:
            st.markdown(f"**{p.get('record_date', '—')}** — Gross Profit: **${p.get('gross_profit', 0):,.2f}**")
    else:
        st.info("No recent profit records.")

    st.subheader("⚡ Quick Actions")
    cols = st.columns(3 if role == "admin" else 4)

    cols[0].button(
        "Manage FTMO Accounts",
        type="primary",
        use_container_width=True,
        on_click=lambda: st.session_state.update({"navigate_to": "pages/📊_FTMO_Accounts.py"})
    )
    cols[1].button(
        "Record Profit",
        type="primary",
        use_container_width=True,
        on_click=lambda: st.session_state.update({"navigate_to": "pages/💰_Profit_Sharing.py"})
    )
    cols[2].button(
        "Growth Fund",
        type="primary",
        use_container_width=True,
        on_click=lambda: st.session_state.update({"navigate_to": "pages/🌱_Growth_Fund.py"})
    )

    if role == "owner":
        cols[3].button(
            "Admin Management",
            type="primary",
            use_container_width=True,
            on_click=lambda: st.session_state.update({"navigate_to": "pages/👤_Admin_Management.py"})
        )

    if st.session_state.navigate_to:
        target = st.session_state.navigate_to
        st.session_state.navigate_to = None
        st.switch_page(target)

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