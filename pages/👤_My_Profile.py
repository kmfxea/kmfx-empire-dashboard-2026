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
# Theme & constants
# ────────────────────────────────────────────────
PRIMARY   = "#00ffaa"
GOLD      = "#ffd700"
BG_DARK   = "#0f172a"
TEXT      = "#e2e8f0"
ACCENT_BG = "rgba(0, 255, 170, 0.08)"

st.markdown(f"""
    <style>
        .profile-header {{ font-size: 2.4rem; font-weight: 700; color: {PRIMARY}; margin-bottom: 0.5rem; }}
        .profile-sub   {{ font-size: 1.1rem; color: {TEXT}; opacity: 0.85; margin-bottom: 2rem; }}
        .card {{ 
            background: linear-gradient(145deg, {BG_DARK}, #1e293b);
            border-radius: 16px;
            padding: 1.8rem;
            border: 1px solid rgba(0,255,170,0.18);
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            margin-bottom: 1.6rem;
        }}
        .section-title {{ 
            font-size: 1.5rem; 
            color: {GOLD}; 
            margin: 2.2rem 0 1.2rem;
            border-left: 5px solid {PRIMARY};
            padding-left: 1rem;
        }}
        .qr-container {{ background: #000; border-radius: 12px; padding: 1.2rem; text-align: center; }}
        .download-btn {{ margin-top: 1rem; }}
        .proof-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1.2rem; }}
        .proof-item {{ background: rgba(30,41,59,0.6); border-radius: 10px; overflow: hidden; }}
        .proof-img {{ width: 100%; height: auto; display: block; }}
        .small-caption {{ font-size: 0.85rem; color: #94a3b8; text-align: center; padding: 0.6rem; }}
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
st.markdown('<div class="profile-header">My Profile</div>', unsafe_allow_html=True)
st.markdown('<div class="profile-sub">Your KMFX Elite Membership • Realtime • Secure</div>', unsafe_allow_html=True)

my_name     = st.session_state.full_name
my_username = st.session_state.username

# ────────────────────────────────────────────────
# Data fetch
# ────────────────────────────────────────────────
@st.cache_data(ttl=12)
def get_profile_data():
    user = supabase.table("users").select("*").eq("username", my_username).single().execute().data or {}
    
    accs = supabase.table("ftmo_accounts").select("*").execute().data or []
    my_accs = []
    uid = str(user.get("id", ""))
    for a in accs:
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

    return user, my_accs, wds, proofs

user, my_accounts, withdrawals, proofs = get_profile_data()

if st.button("↻ Refresh Now", type="tertiary"):
    st.cache_data.clear()
    st.rerun()

# ────────────────────────────────────────────────
# Flip Card (kept but slimmed down + better contrast)
# ────────────────────────────────────────────────
balance = user.get("balance", 0.0)
title   = user.get("title", "Member").upper()

st.markdown(f"""
<div class="card" style="text-align:center; padding:2.5rem 1.5rem;">
    <div style="font-size:2.8rem; font-weight:800; color:{GOLD}; letter-spacing:3px; margin-bottom:1.2rem;">
        KMFX EA {title if title != 'NONE' else 'MEMBER'} CARD
    </div>
    <div style="font-size:2.1rem; color:{TEXT}; margin:1.8rem 0;">
        {my_name.upper()}
    </div>
    <div style="font-size:1.9rem; color:{PRIMARY}; font-weight:700; margin:1.5rem 0;">
        ${balance:,.2f}
    </div>
    <div style="font-size:1rem; opacity:0.7; margin-top:1.5rem;">
        Elite Empire Member • Built by Faith • 2026 👑
    </div>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# QR Code – with easy & safe regeneration
# ────────────────────────────────────────────────
st.markdown('<div class="section-title">Quick Login QR Code</div>', unsafe_allow_html=True)

qr_token = user.get("qr_token")
APP_URL = "https://kmfxea.streamlit.app"

if qr_token:
    qr_data = f"{APP_URL}/?qr={qr_token}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=PRIMARY, back_color="black")

    buf = BytesIO()
    img.save(buf, "PNG")
    qr_bytes = buf.getvalue()

    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown('<div class="qr-container">', unsafe_allow_html=True)
        st.image(qr_bytes, use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.caption("Scan to login instantly – no password needed")
        st.code(qr_data, language=None)
        
        st.download_button(
            "⬇ Download QR Code",
            qr_bytes,
            file_name=f"KMFX_{my_name.replace(' ','_')}_QR.png",
            mime="image/png",
            use_container_width=True,
            type="primary"
        )

        st.markdown("---")
        st.warning("**Security Action**\n\nIf this QR was shared, exposed, or your device is compromised → regenerate now. The old QR will immediately stop working.")

        if "qr_confirm" not in st.session_state:
            st.session_state.qr_confirm = False

        if st.button("🔄 Regenerate QR Code", type="primary", use_container_width=True):
            if st.session_state.qr_confirm:
                new_token = str(uuid.uuid4())
                supabase.table("users").update({"qr_token": new_token}).eq("id", user["id"]).execute()
                log_action("QR Regenerated", f"{my_name} | old partial: {qr_token[:8]}...")
                st.session_state.qr_confirm = False
                st.success("New QR generated successfully!")
                st.rerun()
            else:
                st.session_state.qr_confirm = True
                st.error("Click AGAIN to confirm. Old QR will be invalidated permanently.")
        
        if st.session_state.qr_confirm:
            if st.button("Cancel Regeneration", use_container_width=True):
                st.session_state.qr_confirm = False
                st.rerun()
else:
    st.info("No Quick Login QR yet.")
    if st.button("Generate My QR Code", type="primary"):
        new_token = str(uuid.uuid4())
        supabase.table("users").update({"qr_token": new_token}).eq("id", user["id"]).execute()
        st.success("QR created!")
        st.rerun()

# ────────────────────────────────────────────────
# Proof Vault – improved grid + reliable download
# ────────────────────────────────────────────────
st.markdown('<div class="section-title">Your Proof Vault</div>', unsafe_allow_html=True)

if proofs:
    st.markdown('<div class="proof-grid">', unsafe_allow_html=True)
    
    for proof in proofs:
        file_url = proof.get("file_url")
        path = proof.get("storage_path")
        
        # Try to get fresh signed URL if path exists
        if path:
            try:
                signed = supabase.storage.from_("client_files").create_signed_url(path, expires_in=7200)
                file_url = signed.signed_url
            except:
                pass

        st.markdown('<div class="proof-item">', unsafe_allow_html=True)
        
        if file_url and proof["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif')):
            st.image(file_url, use_column_width=True)
        else:
            st.markdown(f"<div style='padding:2rem; text-align:center; color:#94a3b8;'>{proof['original_name']}</div>", unsafe_allow_html=True)
        
        st.markdown(f'<div class="small-caption">{proof.get("category","—")} • {proof["upload_date"]}</div>', unsafe_allow_html=True)

        if file_url:
            try:
                r = requests.get(file_url, timeout=10)
                if r.status_code == 200:
                    st.download_button(
                        "⬇ Download",
                        r.content,
                        file_name=proof["original_name"],
                        mime="application/octet-stream",
                        use_container_width=True,
                        key=f"dl_{proof['id']}"
                    )
            except:
                st.caption("Download unavailable right now")

        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No documents/proofs uploaded yet.")

# ────────────────────────────────────────────────
# Simple footer
# ────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding:3rem 1rem; color:#64748b; font-size:0.95rem; margin-top:4rem;">
    KMFX Elite Portal • Your Empire • Built by Faith 👑 2026
</div>
""", unsafe_allow_html=True)