# pages/🏠_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="client")  # Everyone sees dashboard; owner/admin see extra

# ─── THEME COLORS (consistent across app) ───
accent_primary = "#00ffaa"
accent_gold    = "#ffd700"
accent_glow    = "#00ffaa40"
accent_hover   = "#00ffcc"

# ─── WELCOME + BALLOONS ON FRESH LOGIN ───
if st.session_state.get("just_logged_in", False):
    st.balloons()
    st.success(f"Welcome back, {st.session_state.full_name}! 🚀 Empire scaling mode activated.")
    st.session_state.pop("just_logged_in", None)

# ─── SCROLL-TO-TOP SCRIPT (optimized) ───
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

# ─── HEADER + DESCRIPTION ───
st.header("Elite Empire Command Center 🚀")
st.markdown("**Realtime, fully automatic empire overview** • Every transaction syncs instantly • Trees update live • Empire scales itself")

# ─── OPTIMIZED DATA FETCH (cached 30s) ───
@st.cache_data(ttl=30, show_spinner="Loading empire overview...")
def fetch_empire_summary():
    try:
        # Fast totals from materialized views
        gf_resp = supabase.table("mv_growth_fund_balance").select("balance").execute()
        gf_balance = gf_resp.data[0].get("balance", 0.0) if gf_resp.data else 0.0

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

        total_funded_php = 0
        for acc in accounts:
            contrib = acc.get("contributors_v2") or acc.get("contributors", [])
            for c in contrib:
                total_funded_php += c.get("units", 0) * (c.get("php_per_unit", 0) or 0)

        return (
            accounts, total_accounts, total_equity, total_withdrawable,
            gf_balance, total_gross, total_distributed,
            total_client_balances, participant_shares, total_funded_php
        )
    except Exception as e:
        st.error(f"Dashboard data fetch error: {str(e)}")
        return [], 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {}, 0

(
    accounts, total_accounts, total_equity, total_withdrawable,
    gf_balance, total_gross, total_distributed,
    total_client_balances, participant_shares, total_funded_php
) = fetch_empire_summary()

# ─── METRICS GRID (responsive glass cards) ───
st.markdown(f"""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.2rem; margin: 2rem 0;">
    <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:12px;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Active Accounts</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.6rem; color:{accent_primary};">{total_accounts}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:12px;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Total Equity</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.6rem; color:#00ffaa;">${total_equity:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:12px;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Withdrawable</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.6rem; color:#ff6b6b;">${total_withdrawable:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:12px;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Empire Funded (PHP)</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.6rem; color:{accent_gold};">₱{total_funded_php:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:12px;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Gross Profits</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.6rem;">${total_gross:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:12px;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Distributed Shares</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.6rem; color:#00ffaa;">${total_distributed:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:12px;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Client Balances</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.6rem; color:{accent_gold};">${total_client_balances:,.0f}</h2>
    </div>
    <div class="glass-card" style="text-align:center; padding:1.5rem; border-radius:12px;">
        <h4 style="opacity:0.8; margin:0; font-size:1rem;">Growth Fund</h4>
        <h2 style="margin:0.5rem 0 0; font-size:2.8rem; color:{accent_gold};">${gf_balance:,.0f}</h2>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── QUICK ACTIONS (role-aware) ───
st.subheader("⚡ Quick Actions")
action_cols = st.columns(3)
current_role = st.session_state.get("role", "client").lower()

with action_cols[0]:
    if current_role in ["owner", "admin"]:
        if st.button("➕ Launch New Account", type="primary", use_container_width=True):
            st.switch_page("pages/📊_FTMO_Accounts.py")
    else:
        st.button("View My Shares", disabled=True, use_container_width=True)

with action_cols[1]:
    if current_role in ["owner", "admin"]:
        if st.button("💰 Record Profit", type="primary", use_container_width=True):
            st.switch_page("pages/💰_Profit_Sharing.py")
    else:
        if st.button("💳 Request Withdrawal", type="primary", use_container_width=True):
            st.switch_page("pages/💳_Withdrawals.py")

with action_cols[2]:
    if st.button("🌱 Growth Fund Details", type="primary", use_container_width=True):
        st.switch_page("pages/🌱_Growth_Fund.py")

# ─── EMPIRE FLOW TREES ───
st.subheader("🌳 Empire Flow Trees (Realtime Auto-Sync)")
tab_part, tab_contrib = st.tabs(["Participant Shares Distribution", "Contributor Funding Flow (PHP)"])

with tab_part:
    if participant_shares:
        labels = ["Empire Shares"] + list(participant_shares.keys())
        values = [0] + list(participant_shares.values())
        fig_part = go.Figure(go.Sankey(
            node=dict(
                pad=20,
                thickness=30,
                label=labels,
                color=["#00ffaa"] + [accent_primary] * len(participant_shares)
            ),
            link=dict(
                source=[0] * len(participant_shares),
                target=list(range(1, len(labels))),
                value=values[1:]
            )
        ))
        fig_part.update_layout(height=600, title="Total Distributed Shares by Participant")
        st.plotly_chart(fig_part, use_container_width=True)
    else:
        st.info("No profit distributions yet • Record one in Profit Sharing page")

with tab_contrib:
    funded_by = {}
    for acc in accounts:
        contrib = acc.get("contributors_v2") or acc.get("contributors", [])
        for c in contrib:
            name = c.get("display_name") or c.get("name", "Unknown")
            funded = c.get("units", 0) * (c.get("php_per_unit", 0) or 0)
            funded_by[name] = funded_by.get(name, 0) + funded

    if funded_by:
        labels = ["Empire Funded (PHP)"] + list(funded_by.keys())
        values = [0] + list(funded_by.values())
        fig_contrib = go.Figure(go.Sankey(
            node=dict(
                pad=20,
                thickness=30,
                label=labels,
                color=["#ffd700"] + ["#ff6b6b"] * len(funded_by)
            ),
            link=dict(
                source=[0] * len(funded_by),
                target=list(range(1, len(labels))),
                value=values[1:]
            )
        ))
        fig_contrib.update_layout(height=600, title="Total Funded by Contributors (PHP)")
        st.plotly_chart(fig_contrib, use_container_width=True)
    else:
        st.info("No contributors yet • Add in FTMO Accounts page")

# ─── LIVE ACCOUNTS GRID + MINI TREES ───
st.subheader("📊 Live Accounts (Realtime Metrics & Trees)")
if accounts:
    for acc in accounts:
        contrib = acc.get("contributors_v2") or acc.get("contributors", [])
        funded_php_acc = sum(c.get("units", 0) * (c.get("php_per_unit", 0) or 0) for c in contrib)
        phase_emoji = {
            "Challenge P1": "🔴", "Challenge P2": "🟡",
            "Verification": "🟠", "Funded": "🟢", "Scaled": "💎"
        }.get(acc.get("current_phase", ""), "⚪")

        st.markdown(f"""
        <div class="glass-card" style="padding:1.8rem; margin-bottom:1.5rem; border-radius:12px;">
            <h3>{phase_emoji} {acc.get('name', 'Unnamed Account')}</h3>
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1rem; margin:1rem 0;">
                <div><strong>Phase:</strong> {acc.get('current_phase', '—')}</div>
                <div><strong>Equity:</strong> ${acc.get('current_equity', 0):,.0f}</div>
                <div><strong>Withdrawable:</strong> ${acc.get('withdrawable_balance', 0):,.0f}</div>
                <div><strong>Funded PHP:</strong> ₱{funded_php_acc:,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_p, tab_c = st.tabs(["Participants Tree", "Contributors Tree"])
        with tab_p:
            parts = acc.get("participants_v2") or acc.get("participants", [])
            if parts:
                labels = ["Profits"] + [p.get("display_name") or p.get("name", "?") for p in parts]
                vals = [p.get("percentage", 0) for p in parts]
                fig_p = go.Figure(go.Sankey(
                    node=dict(pad=15, thickness=20, label=labels),
                    link=dict(source=[0]*len(vals), target=list(range(1,len(labels))), value=vals)
                ))
                fig_p.update_layout(height=350, title="Participants Share Flow")
                st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.info("No participants assigned yet")

        with tab_c:
            if contrib:
                labels = ["Funded"] + [c.get("display_name") or c.get("name", "?") for c in contrib]
                vals = [c.get("units", 0) * (c.get("php_per_unit", 0) or 0) for c in contrib]
                fig_c = go.Figure(go.Sankey(
                    node=dict(pad=15, thickness=20, label=labels),
                    link=dict(source=[0]*len(vals), target=list(range(1,len(labels))), value=vals)
                ))
                fig_c.update_layout(height=350, title="Contributors Funding Flow (PHP)")
                st.plotly_chart(fig_c, use_container_width=True)
            else:
                st.info("No contributors yet")
else:
    st.info("No live accounts yet • Launch one in FTMO Accounts page")

# ─── CLIENT BALANCES (OWNER/ADMIN ONLY) ───
if st.session_state.get("role", "").lower() in ["owner", "admin"]:
    st.subheader("👥 Client Balances (Realtime)")
    try:
        clients = supabase.table("users").select("full_name, balance").eq("role", "client").execute().data or []
        if clients:
            df = pd.DataFrame([
                {"Client": c["full_name"], "Balance": f"${c.get('balance', 0):,.2f}"}
                for c in clients
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No clients registered yet")
    except Exception as e:
        st.warning(f"Client list temporarily unavailable: {str(e)}")

# ─── MOTIVATIONAL FOOTER ───
st.markdown(f"""
<div class="glass-card" style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Fully Automatic • Realtime • Exponential Empire
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Every transaction auto-syncs • Trees update instantly • Empire scales itself.
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith, Shared for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)