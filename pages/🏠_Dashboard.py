# pages/🏠_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.sidebar import render_sidebar

# ────────────────────────────────────────────────
# PROTECTION + SIDEBAR
# ────────────────────────────────────────────────
require_auth()          # Allows client, admin, owner
render_sidebar()        # Role-aware sidebar + logout

# Accent fallback
accent_primary = st.session_state.get("accent_primary", "#00ffaa")
accent_gold = "#ffd700"

# ────────────────────────────────────────────────
# WELCOME HERO
# ────────────────────────────────────────────────
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.session_state.just_logged_in = False

st.markdown(
    f"""
    <div class='glass-card' style='text-align:center; padding:3rem 2rem; margin-bottom:2.5rem; border:2px solid {accent_primary}40;'>
        <h1 style='margin:0 0 1rem; font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold}); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
            Welcome back, {st.session_state.get('full_name', 'Empire Builder')} 👑
        </h1>
        <p style='font-size:1.3rem; opacity:0.9; margin:0;'>
            Role: <strong>{st.session_state.get('role', 'Client').upper()}</strong> • 
            {datetime.now().strftime('%B %d, %Y • %I:%M %p')}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ────────────────────────────────────────────────
# HEADER + GROWTH FUND
# ────────────────────────────────────────────────
col1, col2 = st.columns([5, 2])
with col1:
    st.header("🏠 Dashboard")
    st.caption("Realtime • Fully Automatic • Exponential Empire Overview")
with col2:
    try:
        gf_resp = supabase.table("mv_growth_fund_balance").select("balance").execute()
        gf_balance = gf_resp.data[0]["balance"] if gf_resp.data else 0.0
        st.metric("Growth Fund Balance", f"${gf_balance:,.0f}")
    except:
        st.metric("Growth Fund Balance", "$0 (loading...)")

# ────────────────────────────────────────────────
# PERSONAL SNAPSHOT – FIXED & ROBUST
# ────────────────────────────────────────────────
st.subheader("Your Empire Snapshot")
try:
    user_query = supabase.table("users").select("balance, funded_amount, share_percentage").eq("username", st.session_state.get("username", "")).execute()
    if user_query.data:
        u = user_query.data[0]
        cols = st.columns(3)
        cols[0].metric("Your Balance", f"${u.get('balance', 0):,.2f}", help="Your current available balance")
        cols[1].metric("Your Funded (PHP)", f"₱{u.get('funded_amount', 0):,.0f}", help="Total PHP contributed/funded")
        cols[2].metric("Your Profit Share", f"{u.get('share_percentage', 0):.2f}%", help="Your share of profit distributions")
    else:
        st.info("Your personal stats will appear here once your profile is fully set up. Contact admin if needed.")
except Exception:
    st.info("Snapshot loading... (this will update shortly)")

# ────────────────────────────────────────────────
# EMPIRE DATA FETCH – ALWAYS RETURNS 11 VALUES
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

        history = []  # placeholder – add real history query later if needed

        return (
            accounts, total_accounts, total_equity, total_withdrawable,
            gf_balance, total_gross, total_distributed,
            total_client_balances, participant_shares, total_funded_php, history
        )
    except Exception as e:
        st.warning(f"Some dashboard data limited: {str(e)}")
        # MUST return EXACTLY 11 values
        return [], 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {}, 0, []

# Unpack safely
data = fetch_empire_summary()
(
    accounts, total_accounts, total_equity, total_withdrawable,
    gf_balance, total_gross, total_distributed,
    total_client_balances, participant_shares, total_funded_php, history
) = data

# ────────────────────────────────────────────────
# QUICK ACTIONS – ROLE-AWARE
# ────────────────────────────────────────────────
st.subheader("⚡ Quick Actions")
role = st.session_state.get("role", "client").lower()
action_cols = st.columns(4)

with action_cols[0]:
    if role in ["admin", "owner"]:
        st.button("➕ Launch New Account", type="primary", use_container_width=True,
                  on_click=lambda: st.switch_page("pages/📊_FTMO_Accounts.py"))
    else:
        st.button("💳 Request Withdrawal", type="primary", use_container_width=True,
                  on_click=lambda: st.switch_page("pages/💳_Withdrawals.py"))

with action_cols[1]:
    if role in ["admin", "owner"]:
        st.button("💰 Record Profit", use_container_width=True,
                  on_click=lambda: st.switch_page("pages/💰_Profit_Sharing.py"))
    else:
        st.button("View My Shares", use_container_width=True, disabled=True)

with action_cols[2]:
    st.button("🌱 Growth Fund", use_container_width=True,
              on_click=lambda: st.switch_page("pages/🌱_Growth_Fund.py"))

with action_cols[3]:
    st.button("🤖 EA Versions", use_container_width=True,
              on_click=lambda: st.switch_page("pages/🤖_EA_Versions.py"))

# ────────────────────────────────────────────────
# RECENT ACTIVITY
# ────────────────────────────────────────────────
st.subheader("Recent Activity")
try:
    logs = supabase.table("audit_logs").select("action, username, created_at").order("created_at", desc=True).limit(5).execute().data or []
    if logs:
        for log in logs:
            ts = log["created_at"][:19].replace("T", " ")
            st.markdown(f"**{ts}** • **{log['action']}** by {log.get('username', 'System')}")
    else:
        st.info("No recent activity recorded yet.")
except:
    st.info("Activity feed temporarily unavailable.")

# ────────────────────────────────────────────────
# EMPIRE FLOW TREES – FIXED VARIABLE ACCESS
# ────────────────────────────────────────────────
st.subheader("🌳 Empire Flow Trees")
tab1, tab2 = st.tabs(["Participant Shares", "Contributor Funding (PHP)"])

with tab1:
    if participant_shares and isinstance(participant_shares, dict):
        labels = ["Empire"] + list(participant_shares.keys())
        values = [0] + list(participant_shares.values())
        fig = go.Figure(go.Sankey(
            node=dict(pad=20, thickness=30, label=labels, color=["#00ffaa"] + [accent_primary]*len(participant_shares)),
            link=dict(source=[0]*len(participant_shares), target=list(range(1, len(labels))), value=values[1:])
        ))
        fig.update_layout(height=600, title="Total Distributed Shares")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No profit distributions recorded yet.")

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
            link=dict(source=[0]*len(funded_by), target=list(range(1, len(labels))), value=values[1:])
        ))
        fig.update_layout(height=600, title="Funding by Contributor (PHP)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No contributors recorded yet.")

# ────────────────────────────────────────────────
# LIVE FTMO ACCOUNTS
# ────────────────────────────────────────────────
st.subheader("📊 Live FTMO Accounts")
if accounts:
    for acc in accounts:
        with st.expander(f"{acc.get('name', 'Unnamed')} • {acc.get('current_phase', '—')}"):
            contrib = acc.get("contributors_v2") or acc.get("contributors", [])
            funded_php = sum(c.get("units", 0) * (c.get("php_per_unit", 0) or 0) for c in contrib)
            phase_map = {"Challenge P1": "🔴", "Challenge P2": "🟡", "Verification": "🟠", "Funded": "🟢", "Scaled": "💎"}
            phase_emoji = phase_map.get(acc.get("current_phase", ""), "⚪")

            cols = st.columns(4)
            cols[0].metric("Equity", f"${acc.get('current_equity', 0):,.0f}")
            cols[1].metric("Withdrawable", f"${acc.get('withdrawable_balance', 0):,.0f}")
            cols[2].metric("Funded (PHP)", f"₱{funded_php:,.0f}")
            cols[3].metric("Phase", f"{phase_emoji} {acc.get('current_phase', '—')}")

            t1, t2 = st.tabs(["Participants Tree", "Contributors Tree"])
            with t1:
                parts = acc.get("participants_v2") or acc.get("participants", [])
                if parts:
                    labels = ["Profits"] + [p.get("display_name") or p.get("name", "?") for p in parts]
                    vals = [p.get("percentage", 0) for p in parts]
                    fig = go.Figure(go.Sankey(node=dict(pad=15, thickness=20, label=labels),
                                              link=dict(source=[0]*len(vals), target=list(range(1,len(labels))), value=vals)))
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No participants assigned yet")
            with t2:
                if contrib:
                    labels = ["Funded"] + [c.get("display_name") or c.get("name", "?") for c in contrib]
                    vals = [c.get("units", 0) * (c.get("php_per_unit", 0) or 0) for c in contrib]
                    fig = go.Figure(go.Sankey(node=dict(pad=15, thickness=20, label=labels),
                                              link=dict(source=[0]*len(vals), target=list(range(1,len(labels))), value=vals)))
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
        st.warning("Client list temporarily unavailable")

# ────────────────────────────────────────────────
# SOLID MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(
    f"""
    <div class='glass-card' style='
        padding:5rem 2rem;
        text-align:center;
        margin:6rem auto 4rem;
        max-width:1100px;
        border-radius:24px;
        border:3px solid {accent_primary}30;
        background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
        box-shadow:0 20px 50px rgba(0,255,170,0.15);
    '>
        <h1 style='
            font-size:3.8rem;
            margin:0 0 1.5rem;
            background:linear-gradient(90deg, {accent_primary}, {accent_gold}, {accent_primary});
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
            letter-spacing:1.5px;
        '>
            Fully Automatic • Realtime • Exponential Empire
        </h1>
        
        <p style='font-size:1.6rem; opacity:0.92; margin:0 0 2.5rem; line-height:1.6;'>
            Every transaction auto-syncs • Trees update instantly • Balances flow realtime • Empire scales itself.
        </p>
        
        <h2 style='
            font-size:2.8rem;
            color:{accent_gold};
            margin:0 0 1rem;
            font-weight:700;
        '>
            Built by Faith, Shared for Generations
        </h2>
        
        <p style='font-size:1.4rem; opacity:0.85; font-style:italic; color:#aaaaaa;'>
            KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Smooth scroll-to-top
st.markdown("""
    <script>
    setTimeout(() => window.scrollTo({top: 0, behavior: 'smooth'}), 1000);
    </script>
""", unsafe_allow_html=True)