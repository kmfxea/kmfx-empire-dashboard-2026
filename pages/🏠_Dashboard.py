# pages/01_🏠_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action

# Proteksyon: kailangan mag-login muna
require_auth()  # client, admin, owner lahat pwede

# ────────────────────────────────────────────────
#  WELCOME MESSAGE PARA SA FRESH LOGIN
# ────────────────────────────────────────────────
if st.session_state.get("just_logged_in", False):
    st.markdown(
        f"""
        <div class='glass-card' style='text-align:center; padding:2rem;'>
            <h3 style='margin:0; color:#00ffaa;'>Welcome back, {st.session_state.full_name}! 🚀</h3>
            <p style='margin:1rem 0 0; opacity:0.8;'>Scale smarter. Trade bolder. Win bigger.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.balloons()
    st.session_state.just_logged_in = False

# ────────────────────────────────────────────────
#  HEADER + GROWTH FUND METRIC
# ────────────────────────────────────────────────
try:
    gf_resp = supabase.table("mv_growth_fund_balance").select("balance").execute()
    gf_balance = gf_resp.data[0]["balance"] if gf_resp.data else 0.0
except Exception:
    gf_balance = 0.0
    st.caption("⚠️ Growth Fund balance temporarily unavailable")

col1, col2 = st.columns([3, 1])
with col1:
    st.header("🏠 Dashboard")
    st.markdown("**Realtime, fully automatic empire overview**")
with col2:
    st.metric("Growth Fund", f"${gf_balance:,.0f}")

# ────────────────────────────────────────────────
#  OPTIMIZED SCROLL-TO-TOP (mas maikli at matalino)
# ────────────────────────────────────────────────
st.markdown("""
<script>
function scrollToTop() {
    const containers = [
        parent.document.querySelector(".main"),
        parent.document.querySelector(".block-container"),
        parent.document.querySelector(".stApp"),
        document.body,
        document.documentElement
    ];
    containers.forEach(c => { if (c) c.scrollTop = 0; });
    window.scrollTo({top: 0, behavior: 'smooth'});
    window.parent.scrollTo({top: 0, behavior: 'smooth'});
}

// Run on load + after content renders
setTimeout(scrollToTop, 500);
setTimeout(scrollToTop, 1500);
</script>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  FETCH EMPIRE DATA (with fallback)
# ────────────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_empire_summary():
    try:
        # Materialized Views (instant)
        gf_resp = supabase.table("mv_growth_fund_balance").select("balance").execute()
        gf_balance = gf_resp.data[0]["balance"] if gf_resp.data else 0.0

        empire_resp = supabase.table("mv_empire_summary").select("*").execute()
        empire = empire_resp.data[0] if empire_resp.data else {}
        total_accounts = empire.get("total_accounts", 0)
        total_equity = empire.get("total_equity", 0.0)
        total_withdrawable = empire.get("total_withdrawable", 0.0)

        client_resp = supabase.table("mv_client_balances").select("*").execute()
        client_summary = client_resp.data[0] if client_resp.data else {}
        total_client_balances = client_summary.get("total_client_balances", 0.0)

        # Raw data for trees
        accounts_resp = supabase.table("ftmo_accounts").select("*").execute()
        accounts = accounts_resp.data or []

        profits_resp = supabase.table("profits").select("gross_profit").execute()
        total_gross = sum(p.get("gross_profit", 0) for p in profits_resp.data or [])

        dist_resp = supabase.table("profit_distributions").select("share_amount, participant_name, is_growth_fund").execute()
        distributions = dist_resp.data or []
        total_distributed = sum(d.get("share_amount", 0) for d in distributions if not d.get("is_growth_fund", False))

        participant_shares = {}
        for d in distributions:
            if not d.get("is_growth_fund", False):
                name = d["participant_name"]
                participant_shares[name] = participant_shares.get(name, 0) + d["share_amount"]

        total_funded_php = 0
        for acc in accounts:
            contrib = acc.get("contributors_v2") or acc.get("contributors", [])
            for c in contrib:
                units = c.get("units", 0)
                php_per_unit = c.get("php_per_unit", 0) or 0
                total_funded_php += units * php_per_unit

        return (
            accounts, total_accounts, total_equity, total_withdrawable,
            gf_balance, total_gross, total_distributed,
            total_client_balances, participant_shares, total_funded_php
        )
    except Exception as e:
        st.warning("Dashboard data temporarily limited. Showing basic view.")
        return [], 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {}, 0

(
    accounts, total_accounts, total_equity, total_withdrawable,
    gf_balance, total_gross, total_distributed,
    total_client_balances, participant_shares, total_funded_php
) = fetch_empire_summary()

# ────────────────────────────────────────────────
#  METRICS GRID (fixed accent_color → accent_primary)
# ────────────────────────────────────────────────
st.markdown(f"""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.2rem; margin: 1.5rem 0;">
    <div class="glass-card" style="text-align:center; padding:1.5rem;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Active Accounts</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.4rem; color:{accent_primary};">{total_accounts}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Total Equity</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.4rem; color:#00ffaa;">${total_equity:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Withdrawable</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.4rem; color:#ff6b6b;">${total_withdrawable:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Empire Funded (PHP)</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.4rem; color:#ffd700;">₱{total_funded_php:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Gross Profits</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.4rem;">${total_gross:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Distributed Shares</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.4rem; color:#00ffaa;">${total_distributed:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Client Balances</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.4rem; color:#ffd700;">${total_client_balances:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Growth Fund</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.8rem; color:#ffd700;">${gf_balance:,.0f}</h2>
    </div>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  QUICK ACTIONS (multi-page ready)
# ────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("<div class='glass-card' style='padding:2rem; text-align:center; height:100%;'>", unsafe_allow_html=True)
    st.subheader("⚡ Quick Actions")
    current_role = st.session_state.get("role", "guest")
    if current_role in ["owner", "admin"]:
        if st.button("➕ Launch New Account", use_container_width=True, type="primary"):
            st.switch_page("pages/03_📊_FTMO_Accounts.py")
        if st.button("💰 Record Profit", use_container_width=True):
            st.switch_page("pages/04_💰_Profit_Sharing.py")
        if st.button("🌱 Growth Fund Details", use_container_width=True):
            st.switch_page("pages/05_🌱_Growth_Fund.py")
    else:
        st.info("Your earnings & shares update automatically in realtime.")
        if st.button("💳 Request Withdrawal", use_container_width=True, type="primary"):
            st.switch_page("pages/11_💳_Withdrawals.py")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='glass-card' style='padding:2rem; text-align:center; height:100%; display:flex; flex-direction:column; justify-content:center;'>
        <h3>🧠 Empire Insight</h3>
        <p style='font-size:1.2rem; margin-top:1rem;'>
            {"Exponential scaling active • Auto-distributions flowing • Balances updating realtime." if total_distributed > 0 else
             "Foundation built • First profit will activate full automatic flow."}
        </p>
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  EMPIRE FLOW TREES
# ────────────────────────────────────────────────
st.subheader("🌳 Empire Flow Trees (Realtime Auto-Sync)")
tab_emp1, tab_emp2 = st.tabs(["Participant Shares", "Contributor Funding (PHP)"])

with tab_emp1:
    if participant_shares:
        labels = ["Empire Shares"] + list(participant_shares.keys())
        values = [0] + list(participant_shares.values())
        fig = go.Figure(data=[go.Sankey(
            node=dict(pad=20, thickness=30, label=labels, color=["#00ffaa"] + [accent_primary]*len(participant_shares)),
            link=dict(source=[0]*len(participant_shares), target=list(range(1, len(labels))), value=values[1:])
        )])
        fig.update_layout(height=600, title="Total Distributed Shares by Participant")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No distributions yet • Record a profit first")

with tab_emp2:
    funded_by_contributor = {}
    for acc in accounts:
        contributors = acc.get("contributors_v2") or acc.get("contributors", [])
        for c in contributors:
            name = c.get("display_name") or c.get("name", "Unknown")
            units = c.get("units", 0)
            php_per_unit = c.get("php_per_unit", 0) or 0
            funded = units * php_per_unit
            funded_by_contributor[name] = funded_by_contributor.get(name, 0) + funded
    if funded_by_contributor:
        labels = ["Empire Funded (PHP)"] + list(funded_by_contributor.keys())
        values = [0] + list(funded_by_contributor.values())
        fig = go.Figure(data=[go.Sankey(
            node=dict(pad=20, thickness=30, label=labels, color=["#ffd700"] + ["#ff6b6b"]*len(funded_by_contributor)),
            link=dict(source=[0]*len(funded_by_contributor), target=list(range(1, len(labels))), value=values[1:])
        )])
        fig.update_layout(height=600, title="Total Funded by Contributors (PHP)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No contributors yet • Add contributors in FTMO Accounts")

# ────────────────────────────────────────────────
#  LIVE ACCOUNTS WITH MINI-TREES
# ────────────────────────────────────────────────
st.subheader("📊 Live Accounts (Realtime Metrics & Trees)")
if accounts:
    for acc in accounts:
        with st.expander(f"{acc.get('name', 'Unnamed Account')} • {acc.get('current_phase', 'Unknown')}"):
            contributors = acc.get("contributors_v2") or acc.get("contributors", [])
            total_funded_php_acc = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors)
            phase_emoji = {"Challenge P1": "🔴", "Challenge P2": "🟡", "Verification": "🟠", "Funded": "🟢", "Scaled": "💎"}.get(acc.get("current_phase", ""), "⚪")

            cols = st.columns(4)
            cols[0].metric("Equity", f"${acc.get('current_equity', 0):,.0f}")
            cols[1].metric("Withdrawable", f"${acc.get('withdrawable_balance', 0):,.0f}")
            cols[2].metric("Funded (PHP)", f"₱{total_funded_php_acc:,.0f}")
            cols[3].metric("Phase", f"{phase_emoji} {acc.get('current_phase', '—')}")

            tab1, tab2 = st.tabs(["Participants Tree", "Contributors Tree"])
            with tab1:
                participants = acc.get("participants_v2") or acc.get("participants", [])
                if participants:
                    labels = ["Profits"] + [p.get("display_name") or p.get("name", "Unknown") for p in participants]
                    values = [p.get("percentage", 0) for p in participants]
                    fig = go.Figure(data=[go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels),
                        link=dict(source=[0]*len(values), target=list(range(1, len(labels))), value=values)
                    )])
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No participants assigned yet")
            with tab2:
                if contributors:
                    labels = ["Funded (PHP)"] + [c.get("display_name") or c.get("name", "Unknown") for c in contributors]
                    values = [c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors]
                    fig = go.Figure(data=[go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels),
                        link=dict(source=[0]*len(values), target=list(range(1, len(values))), value=values)
                    )])
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No contributors yet")
else:
    st.info("No accounts found • Launch one in FTMO Accounts")

# ────────────────────────────────────────────────
#  CLIENT BALANCES (OWNER/ADMIN ONLY)
# ────────────────────────────────────────────────
if st.session_state.role in ["owner", "admin"]:
    st.subheader("👥 Team Client Balances (Realtime)")
    try:
        clients_resp = supabase.table("users").select("full_name, balance").eq("role", "client").execute()
        clients = clients_resp.data or []
        if clients:
            client_df = pd.DataFrame([{"Client": u["full_name"], "Balance": f"${u.get('balance', 0):,.2f}"} for u in clients])
            st.dataframe(client_df, use_container_width=True, hide_index=True)
        else:
            st.info("No clients registered yet")
    except Exception:
        st.warning("Unable to load client balances right now")

# ────────────────────────────────────────────────
#  MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem; text-align:center; margin:4rem 0; border: 2px solid {accent_primary};'>
    <h1 style="background:linear-gradient(90deg,{accent_primary},#ffd700); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Fully Automatic • Realtime • Exponential Empire
    </h1>
    <p style="font-size:1.4rem; margin:2rem 0; opacity:0.9;">
        Every transaction auto-syncs • Trees update instantly • Balances flow realtime • Empire scales itself.
    </p>
    <h2 style="color:#ffd700;">👑 KMFX Pro • Cloud Edition 2026</h2>
</div>
""", unsafe_allow_html=True)