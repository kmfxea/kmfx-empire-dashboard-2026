# pages/🏠_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action
from utils.sidebar import render_sidebar

# ────────────────────────────────────────────────
# PROTECTION + SIDEBAR
# ────────────────────────────────────────────────
require_auth()                  # Allows client, admin, owner
render_sidebar()                # Role-aware navigation + logout

# Fallback accent color if not defined elsewhere
accent_primary = st.session_state.get("accent_primary", "#00ffaa")

# ────────────────────────────────────────────────
# WELCOME + PERSONAL SNAPSHOT
# ────────────────────────────────────────────────
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.session_state.just_logged_in = False

st.markdown(
    f"""
    <div class='glass-card' style='text-align:center; padding:2.5rem; margin-bottom:2rem;'>
        <h2 style='margin:0; color:{accent_primary};'>Welcome back, {st.session_state.get('full_name', 'Empire Builder')}! 👑</h2>
        <p style='margin:0.8rem 0 0; opacity:0.9; font-size:1.1rem;'>
            Role: <strong>{st.session_state.get('role', 'Client').upper()}</strong> • 
            Last seen: {datetime.now().strftime('%b %d, %Y %I:%M %p')}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ────────────────────────────────────────────────
# HEADER + GROWTH FUND METRIC
# ────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    st.header("🏠 Dashboard")
    st.caption("Realtime • Fully Automatic • Exponential Empire Overview")
with col2:
    try:
        gf_resp = supabase.table("mv_growth_fund_balance").select("balance").execute()
        gf_balance = gf_resp.data[0]["balance"] if gf_resp.data else 0.0
    except:
        gf_balance = 0.0
    st.metric("Growth Fund Balance", f"${gf_balance:,.0f}")

# ────────────────────────────────────────────────
# PERSONAL SNAPSHOT (user-specific stats)
# ────────────────────────────────────────────────
st.subheader("Your Empire Snapshot")
try:
    user_data = supabase.table("users").select("balance, funded_amount, share_percentage").eq("username", st.session_state.get("username", "")).execute().data
    if user_data:
        user = user_data[0]
        cols = st.columns(3)
        cols[0].metric("Your Balance", f"${user.get('balance', 0):,.2f}")
        cols[1].metric("Your Funded (PHP)", f"₱{user.get('funded_amount', 0):,.0f}")
        cols[2].metric("Your Profit Share %", f"{user.get('share_percentage', 0):.2f}%")
    else:
        st.info("Personal stats not found yet")
except Exception:
    st.info("Loading your snapshot...")

# ────────────────────────────────────────────────
# EMPIRE SUMMARY FETCH (with longer cache)
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_empire_summary():
    try:
        gf_resp = supabase.table("mv_growth_fund_balance").select("balance").execute()
        gf_balance = gf_resp.data[0]["balance"] if gf_resp.data else 0.0

        empire_resp = supabase.table("mv_empire_summary").select("*").execute()
        empire = empire_resp.data[0] if empire_resp.data else {}
        total_accounts = empire.get("total_accounts", 0)
        total_equity = empire.get("total_equity", 0.0)
        total_withdrawable = empire.get("total_withdrawable", 0.0)

        client_resp = supabase.table("mv_client_balances").select("*").execute()
        total_client_balances = client_resp.data[0].get("total_client_balances", 0.0) if client_resp.data else 0.0

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
                total_funded_php += c.get("units", 0) * (c.get("php_per_unit", 0) or 0)

        # Optional: historical data for chart (add table if needed)
        history = []  # replace with real query when you have equity_history table

        return (
            accounts, total_accounts, total_equity, total_withdrawable,
            gf_balance, total_gross, total_distributed,
            total_client_balances, participant_shares, total_funded_php, history
        )
    except Exception as e:
        st.warning("Some data could not be loaded.")
        return [], 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {}, 0, []

data = fetch_empire_summary()
accounts, total_accounts, total_equity, total_withdrawable, gf_balance, total_gross, total_distributed, total_client_balances, participant_shares, total_funded_php, history = data

# ────────────────────────────────────────────────
# GROWTH TREND CHART
# ────────────────────────────────────────────────
st.subheader("Empire Growth Trend")
if history:
    df = pd.DataFrame(history)
    if 'timestamp' in df.columns and 'total_equity' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['total_equity'],
                                 mode='lines+markers', name='Total Equity',
                                 line=dict(color=accent_primary, width=3)))
        fig.update_layout(height=400, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Growth chart data format issue")
else:
    st.info("Growth trend will appear once historical snapshots are available")

# ────────────────────────────────────────────────
# METRICS GRID
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
# QUICK ACTIONS
# ────────────────────────────────────────────────
st.subheader("⚡ Quick Actions")
role = st.session_state.get("role", "client")
action_cols = st.columns(3)

with action_cols[0]:
    if role in ["owner", "admin"]:
        if st.button("➕ Launch New Account", type="primary", use_container_width=True):
            st.switch_page("pages/📊_FTMO_Accounts.py")
    else:
        if st.button("💳 Request Withdrawal", type="primary", use_container_width=True):
            st.switch_page("pages/💳_Withdrawals.py")

with action_cols[1]:
    if role in ["owner", "admin"]:
        if st.button("💰 Record Profit", use_container_width=True):
            st.switch_page("pages/💰_Profit_Sharing.py")
    else:
        st.button("View My Shares", disabled=True, use_container_width=True)

with action_cols[2]:
    if st.button("🌱 Growth Fund Details", use_container_width=True):
        st.switch_page("pages/🌱_Growth_Fund.py")

# ────────────────────────────────────────────────
# RECENT ACTIVITY
# ────────────────────────────────────────────────
st.subheader("Recent Activity")
try:
    logs = supabase.table("audit_logs").select("action, username, created_at").order("created_at", desc=True).limit(5).execute().data or []
    if logs:
        for log in logs:
            ts = log["created_at"][:19].replace("T", " ")
            st.markdown(f"**{ts}** • {log['action']} • by {log.get('username', 'System')}")
    else:
        st.info("No recent activity yet")
except:
    st.info("Activity feed unavailable right now")

# ────────────────────────────────────────────────
# EMPIRE FLOW TREES
# ────────────────────────────────────────────────
st.subheader("🌳 Empire Flow Trees (Realtime)")
tab1, tab2 = st.tabs(["Participant Shares", "Contributor Funding (PHP)"])

with tab1:
    if participant_shares:
        labels = ["Empire"] + list(participant_shares.keys())
        values = [0] + list(participant_shares.values())
        fig = go.Figure(go.Sankey(
            node=dict(pad=20, thickness=30, label=labels, color=["#00ffaa"] + [accent_primary]*len(participant_shares)),
            link=dict(source=[0]*len(participant_shares), target=list(range(1,len(labels))), value=values[1:])
        ))
        fig.update_layout(height=600, title="Total Distributed Shares")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No distributions recorded yet")

with tab2:
    funded_by = {}
    for acc in accounts:
        contrib = acc.get("contributors_v2") or acc.get("contributors", [])
        for c in contrib:
            name = c.get("display_name") or c.get("name", "Unknown")
            funded = c.get("units", 0) * (c.get("php_per_unit", 0) or 0)
            funded_by[name] = funded_by.get(name, 0) + funded
    if funded_by:
        labels = ["Empire Funded"] + list(funded_by.keys())
        values = [0] + list(funded_by.values())
        fig = go.Figure(go.Sankey(
            node=dict(pad=20, thickness=30, label=labels, color=["#ffd700"] + ["#ff6b6b"]*len(funded_by)),
            link=dict(source=[0]*len(funded_by), target=list(range(1,len(labels))), value=values[1:])
        ))
        fig.update_layout(height=600, title="Funding by Contributor (PHP)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No contributors recorded yet")

# ────────────────────────────────────────────────
# LIVE ACCOUNTS SECTION
# ────────────────────────────────────────────────
st.subheader("📊 Live FTMO Accounts")
if accounts:
    for acc in accounts:
        with st.expander(f"{acc.get('name', 'Account')} • {acc.get('current_phase', '—')}"):
            contrib = acc.get("contributors_v2") or acc.get("contributors", [])
            funded_php = sum(c.get("units", 0) * (c.get("php_per_unit", 0) or 0) for c in contrib)
            phase_map = {"Challenge P1": "🔴", "Challenge P2": "🟡", "Verification": "🟠", "Funded": "🟢", "Scaled": "💎"}
            phase_emoji = phase_map.get(acc.get("current_phase", ""), "⚪")

            cols = st.columns(4)
            cols[0].metric("Equity", f"${acc.get('current_equity', 0):,.0f}")
            cols[1].metric("Withdrawable", f"${acc.get('withdrawable_balance', 0):,.0f}")
            cols[2].metric("Funded (PHP)", f"₱{funded_php:,.0f}")
            cols[3].metric("Phase", f"{phase_emoji} {acc.get('current_phase', '—')}")

            t1, t2 = st.tabs(["Participants", "Contributors"])
            with t1:
                parts = acc.get("participants_v2") or acc.get("participants", [])
                if parts:
                    labels = ["Profits"] + [p.get("display_name") or p.get("name", "?") for p in parts]
                    vals = [p.get("percentage", 0) for p in parts]
                    fig = go.Figure(go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels),
                        link=dict(source=[0]*len(vals), target=list(range(1,len(labels))), value=vals)
                    ))
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No participants yet")
            with t2:
                if contrib:
                    labels = ["Funded"] + [c.get("display_name") or c.get("name", "?") for c in contrib]
                    vals = [c.get("units", 0) * (c.get("php_per_unit", 0) or 0) for c in contrib]
                    fig = go.Figure(go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels),
                        link=dict(source=[0]*len(vals), target=list(range(1,len(labels))), value=vals)
                    ))
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No contributors yet")
else:
    st.info("No live accounts yet • Launch one to begin")

# ────────────────────────────────────────────────
# CLIENT BALANCES (ADMIN/OWNER ONLY)
# ────────────────────────────────────────────────
if st.session_state.get("role") in ["admin", "owner"]:
    st.subheader("👥 Client Balances Overview")
    try:
        clients = supabase.table("users").select("full_name, balance").eq("role", "client").execute().data or []
        if clients:
            df = pd.DataFrame([{"Client": c["full_name"], "Balance": f"${c.get('balance', 0):,.2f}"} for c in clients])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No clients registered yet")
    except:
        st.warning("Could not load client list right now")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
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

# Smooth scroll to top after load
st.markdown("""
<script>
setTimeout(() => window.scrollTo({top: 0, behavior: 'smooth'}), 800);
</script>
""", unsafe_allow_html=True)