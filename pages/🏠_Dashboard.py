import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

# Set page config for maximum width and title
st.set_page_config(page_title="Empire Command Center", page_icon="🚀", layout="wide")

# ─── THEME COLORS ───
accent_primary = "#00ffaa"
accent_gold    = "#ffd700"
accent_danger  = "#ff6b6b"
accent_bg      = "#101010"

# Render sidebar at the very top to detect messages
render_sidebar()
require_auth(min_role="client")

# ─── CSS CUSTOM STYLING (THE "LUPET" VERSION) ───
st.markdown(f"""
<style>
    /* Animated Gradient Background */
    .stApp {{
        background: linear-gradient(135deg, #101010 0%, #1a1a1a 100%);
    }}

    /* Global Card Style */
    .glass-card {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }}
    .glass-card:hover {{
        border: 1px solid {accent_primary}60;
        box-shadow: 0 4px 15px {accent_primary}20;
    }}
    
    /* Metrics Styling */
    .metric-container {{
        text-align: center;
        padding: 1rem;
    }}
    .metric-title {{
        color: rgba(255,255,255,0.7);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }}
    .metric-value {{
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        font-family: 'Courier New', monospace; /* Monospace for numbers */
    }}
    
    /* Live Count Animation */
    @keyframes countUp {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .animate-number {{
        animation: countUp 0.5s ease-out;
    }}

    /* Account Status Badges */
    .status-badge {{
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# ─── WELCOME + BALLOONS ───
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.success(f"Welcome back, **{st.session_state.full_name}**! 🚀 Empire scaling mode activated.")
    st.session_state.pop("just_logged_in", None)

# ─── HEADER ───
st.title("Elite Empire Command Center 🚀")
st.markdown("Realtime, fully automatic empire overview • Every transaction syncs instantly • Empire scales itself")
st.markdown("---")

# ─── OPTIMIZED DATA FETCH ───
@st.cache_data(ttl=15, show_spinner="Syncing Empire Data...") # Reduced TTL for faster perception
def fetch_empire_summary():
    try:
        # Fast totals from materialized views
        gf_resp = supabase.table("mv_growth_fund_balance").select("balance, target_amount").execute()
        gf_data = gf_resp.data[0] if gf_resp.data else {"balance": 0.0, "target_amount": 100000.0}
        
        gf_balance = gf_data.get("balance", 0.0)
        gf_target = gf_data.get("target_amount", 100000.0)

        empire_resp = supabase.table("mv_empire_summary").select("*").execute()
        empire = empire_resp.data[0] if empire_resp.data else {}
        total_accounts = empire.get("total_accounts", 0)
        total_equity = empire.get("total_equity", 0.0)
        total_withdrawable = empire.get("total_withdrawable", 0.0)

        client_resp = supabase.table("mv_client_balances").select("*").execute()
        total_client_balances = client_resp.data[0].get("total_client_balances", 0.0) if client_resp.data else 0.0

        # Lightweight raw data
        accounts = supabase.table("ftmo_accounts").select("*").execute().data or []
        profits = supabase.table("profits").select("gross_profit").execute().data or []
        distributions = supabase.table("profit_distributions").select("share_amount, participant_name, is_growth_fund").execute().data or []

        total_gross = sum(p.get("gross_profit", 0) for p in profits)
        total_distributed = sum(d.get("share_amount", 0) for d in distributions if not d.get("is_growth_fund", False))

        participant_shares = {}
        for d in distributions:
            if not d.get("is_growth_fund", False):
                name = d.get("participant_name", "Unknown")
                participant_shares[name] = participant_shares.get(name, 0) + d.get("share_amount", 0)

        # Resolve contributor names
        all_users = supabase.table("users").select("id, full_name").execute().data or []
        user_map = {u["id"]: u["full_name"] for u in all_users}

        total_funded_php = 0
        for acc in accounts:
            contrib = acc.get("contributors_v2") or acc.get("contributors", [])
            for c in contrib:
                funded = c.get("units", 0) * (c.get("php_per_unit", 0) or 0)
                total_funded_php += funded

        return (
            accounts, total_accounts, total_equity, total_withdrawable,
            gf_balance, gf_target, total_gross, total_distributed,
            total_client_balances, participant_shares, total_funded_php
        )
    except Exception as e:
        st.error(f"Dashboard data fetch error: {str(e)}")
        return [], 0, 0.0, 0.0, 0.0, 100000.0, 0.0, 0.0, 0.0, {}, 0

(
    accounts, total_accounts, total_equity, total_withdrawable,
    gf_balance, gf_target, total_gross, total_distributed,
    total_client_balances, participant_shares, total_funded_php
) = fetch_empire_summary()

# ─── METRICS GRID ───
st.subheader("📊 Executive Overview")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

def styled_metric(label, value, color="#FFFFFF", prefix=""):
    return f"""
    <div class="glass-card metric-container">
        <div class="metric-title">{label}</div>
        <div class="metric-value animate-number" style="color:{color};">{prefix}{value:,.0f}</div>
    </div>
    """

with m_col1:
    st.markdown(styled_metric("Active Accounts", total_accounts, accent_primary), unsafe_allow_html=True)
with m_col2:
    st.markdown(styled_metric("Total Equity", total_equity, "#FFFFFF", "$"), unsafe_allow_html=True)
with m_col3:
    st.markdown(styled_metric("Withdrawable", total_withdrawable, accent_danger, "$"), unsafe_allow_html=True)
with m_col4:
    st.markdown(styled_metric("Empire Funded (PHP)", total_funded_php, accent_gold, "₱"), unsafe_allow_html=True)

st.write("##") 

m_col5, m_col6, m_col7, m_col8 = st.columns(4)
with m_col5:
    st.markdown(styled_metric("Gross Profits", total_gross, "#FFFFFF", "$"), unsafe_allow_html=True)
with m_col6:
    st.markdown(styled_metric("Distributed Shares", total_distributed, accent_primary, "$"), unsafe_allow_html=True)
with m_col7:
    st.markdown(styled_metric("Client Balances", total_client_balances, accent_gold, "$"), unsafe_allow_html=True)
with m_col8:
    st.markdown(styled_metric("Growth Fund", gf_balance, accent_gold, "$"), unsafe_allow_html=True)

# ─── GROWTH FUND PROGRESS BAR ───
st.write("##")
st.subheader("📈 Growth Fund Progress")
with st.container():
    st.markdown(f"""
    <div class="glass-card" style="padding: 1rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; color: rgba(255,255,255,0.7);">
            <span>Current: <strong style="color:white;">${gf_balance:,.0f}</strong></span>
            <span>Target: <strong style="color:{accent_gold};">${gf_target:,.0f}</strong></span>
        </div>
    """, unsafe_allow_html=True)
    
    progress = min(gf_balance / gf_target, 1.0) if gf_target > 0 else 0
    st.progress(progress)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ─── QUICK ACTIONS ───
st.subheader("⚡ Quick Actions")
action_cols = st.columns(3)
current_role = st.session_state.get("role", "client").lower()

with action_cols[0]:
    if current_role in ["owner", "admin"]:
        if st.button("➕ Launch New Account", use_container_width=True):
            st.switch_page("pages/📊_FTMO_Accounts.py")
    else:
        st.button("View My Shares", disabled=True, use_container_width=True)

with action_cols[1]:
    if current_role in ["owner", "admin"]:
        if st.button("💰 Record Profit", use_container_width=True):
            st.switch_page("pages/💰_Profit_Sharing.py")
    else:
        if st.button("💳 Request Withdrawal", use_container_width=True):
            st.switch_page("pages/💳_Withdrawals.py")

with action_cols[2]:
    if st.button("🌱 Growth Fund Details", use_container_width=True):
        st.switch_page("pages/🌱_Growth_Fund.py")

st.markdown("---")

# ─── EMPIRE FLOW TREES ───
st.subheader("🌳 Empire Flow Trees (Realtime Auto-Sync)")
tab_part, tab_contrib = st.tabs(["Participant Shares Distribution", "Contributor Funding Flow (PHP)"])

with tab_part:
    if participant_shares:
        labels = ["Empire Shares"] + list(participant_shares.keys())
        values = list(participant_shares.values())
        
        fig_part = go.Figure(go.Sankey(
            node=dict(
                pad=20, thickness=20, line=dict(color="black", width=0.5),
                label=labels, color=accent_primary
            ),
            link=dict(
                source=[0] * len(participant_shares),
                target=list(range(1, len(labels))),
                value=values,
                color="rgba(0,255,170,0.15)"
            )
        ))
        fig_part.update_layout(height=500, margin=dict(l=0, r=0, t=20, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_part, use_container_width=True)
    else:
        st.info("No profit distributions yet")

with tab_contrib:
    funded_by = {}
    for acc in accounts:
        contrib = acc.get("contributors_v2") or acc.get("contributors", [])
        for c in contrib:
            name = c.get("display_name") or c.get("name") or "Anonymous"
            funded = c.get("units", 0) * (c.get("php_per_unit", 0) or 0)
            funded_by[name] = funded_by.get(name, 0) + funded

    if funded_by:
        labels = ["Total Funded (PHP)"] + list(funded_by.keys())
        values = list(funded_by.values())
        
        fig_contrib = go.Figure(go.Sankey(
            node=dict(
                pad=20, thickness=20, line=dict(color="black", width=0.5),
                label=labels, color=accent_gold
            ),
            link=dict(
                source=[0] * len(funded_by),
                target=list(range(1, len(labels))),
                value=values,
                color="rgba(255,215,0,0.1)"
            )
        ))
        fig_contrib.update_layout(height=500, margin=dict(l=0, r=0, t=20, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_contrib, use_container_width=True)
    else:
        st.info("No contributors yet")

# ─── LIVE ACCOUNTS GRID ───
st.subheader("📊 Live Accounts Status")
if accounts:
    for acc in accounts:
        contrib = acc.get("contributors_v2") or acc.get("contributors", [])
        funded_php_acc = sum(c.get("units", 0) * (c.get("php_per_unit", 0) or 0) for c in contrib)
        phase_map = {
            "Challenge P1": "🔴 Challenge P1", "Challenge P2": "🟡 Challenge P2",
            "Verification": "🟠 Verification", "Funded": "🟢 Funded", "Scaled": "💎 Scaled"
        }
        phase_display = phase_map.get(acc.get("current_phase"), "⚪ Unknown")
        
        # Account Card
        with st.container():
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: white;">{acc.get('name', 'Unnamed Account')}</h3>
                    <span class="status-badge" style="background: rgba(255,255,255,0.05); color: #ccc;">{phase_display}</span>
                </div>
                <hr style="margin: 0.7rem 0; border: 1px solid rgba(255,255,255,0.05);">
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:0.5rem; color: #ddd;">
                    <div>Equity: <strong style="color:white;">${acc.get('current_equity', 0):,.0f}</strong></div>
                    <div>Withdrawable: <strong style="color:{accent_danger};">${acc.get('withdrawable_balance', 0):,.0f}</strong></div>
                    <div>Funded: <strong style="color:{accent_gold};">₱{funded_php_acc:,.0f}</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No live accounts yet")

# ─── LATEST UPDATES SECTION ───
st.markdown("---")
st.subheader("🔔 Latest Updates")
up_col1, up_col2 = st.columns([1, 1])

with up_col1:
    latest_ann = supabase.table("announcements").select("title, message, date").order("date", desc=True).limit(3).execute().data or []
    if latest_ann:
        st.markdown("#### 📢 Announcements")
        for a in latest_ann:
            with st.expander(f"{a['title']} - {a.get('date', '—')}"):
                st.write(a['message'])
    else:
        st.info("No recent announcements")

with up_col2:
    my_username = st.session_state.get("username", "")
    unread_data = supabase.table("messages").select("id").eq("to_client", my_username).execute()
    unread_count = len(unread_data.data)

    if unread_count > 0:
        st.markdown(f"#### 💬 Messages ({unread_count} unread)")
        if st.button("Open Inbox", type="primary", use_container_width=True):
            st.switch_page("pages/💬_Messages.py")
    else:
        st.markdown("#### 💬 Messages")
        st.info("Inbox clear")

# ─── CLIENT BALANCES (OWNER/ADMIN ONLY) ───
if st.session_state.get("role", "").lower() in ["owner", "admin"]:
    st.markdown("---")
    st.subheader("👥 Client Balances (Realtime)")
    try:
        clients = supabase.table("users").select("full_name, balance").eq("role", "client").execute().data or []
        if clients:
            df = pd.DataFrame(clients)
            df.columns = ["Client Name", "Balance"]
            df["Balance"] = df["Balance"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No clients registered")
    except Exception as e:
        st.warning(f"Client list unavailable: {str(e)}")

# ─── MOTIVATIONAL FOOTER ───
st.markdown(f"""
<div style="padding:3rem 2rem; text-align:center; margin:3rem auto; max-width:1000px;
    border-radius:24px; border:1px solid {accent_primary}20;
    background: rgba(255, 255, 255, 0.01);">
    <h1 style="font-size:2.5rem; color:white; margin-bottom:0.5rem;">
        Fully Automatic • Realtime • Exponential Empire
    </h1>
    <p style="font-size:1.2rem; opacity:0.8; margin:0.5rem 0;">
        Built by Faith, Shared for Generations 👑
    </p>
    <p style="opacity:0.6; font-style:italic; margin-top:1rem;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)