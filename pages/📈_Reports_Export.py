# pages/📈_Reports_&_Export.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="admin")  # stricter — owner/admin only

# ─── THEME (consistent across app) ───
accent_primary = "#00ffaa"
accent_gold    = "#ffd700"
accent_glow    = "#00ffaa40"

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

st.header("📈 Empire Reports & Export")
st.markdown("**Full analytics engine** • Instant realtime reports via materialized views • Professional charts • Detailed breakdowns • Multiple CSV exports • Owner/Admin only")

current_role = st.session_state.get("role", "guest").lower()
if current_role not in ["owner", "admin"]:
    st.error("🔒 Reports & Export is restricted to Owner/Admin only.")
    st.stop()

# ─── ULTRA-REALTIME CACHE (10s TTL) ───
@st.cache_data(ttl=10, show_spinner="Generating realtime empire reports...")
def fetch_reports_full():
    try:
        # Instant MV totals (lightning fast)
        empire = supabase.table("mv_empire_summary").select("*").single().execute().data or {}
        client_mv = supabase.table("mv_client_balances").select("*").single().execute().data or {}
        gf_mv = supabase.table("mv_growth_fund_balance").select("balance").single().execute().data or {}

        total_accounts     = empire.get("total_accounts", 0)
        total_equity       = empire.get("total_equity", 0.0)
        total_withdrawable = empire.get("total_withdrawable", 0.0)
        total_client_bal   = client_mv.get("total_client_balances", 0.0)
        gf_balance         = gf_mv.get("balance", 0.0)

        # Detailed data for charts & tables
        profits       = supabase.table("profits").select("*").order("record_date", desc=True).execute().data or []
        distributions = supabase.table("profit_distributions").select("*").execute().data or []
        clients       = supabase.table("users").select("full_name, balance").eq("role", "client").execute().data or []
        accounts      = supabase.table("ftmo_accounts").select("name, current_phase, current_equity, withdrawable_balance").execute().data or []

        total_gross       = sum(p.get("gross_profit", 0) for p in profits)
        total_distributed = sum(d.get("share_amount", 0) for d in distributions if not d.get("is_growth_fund", False))

        return (
            profits, distributions, clients, accounts,
            total_gross, total_distributed, total_client_bal,
            gf_balance, total_accounts, total_equity, total_withdrawable
        )
    except Exception as e:
        st.error(f"Reports fetch error: {str(e)}")
        return [], [], [], [], 0, 0, 0, 0, 0, 0, 0

(
    profits, distributions, clients, accounts,
    total_gross, total_distributed, total_client_bal,
    gf_balance, total_accounts, total_equity, total_withdrawable
) = fetch_reports_full()

if st.button("🔄 Refresh Reports Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Reports auto-refresh every 10s • Lightning fast via materialized views")

# ─── EMPIRE METRICS GRID ───
st.subheader("Empire Overview (Instant Totals)")
cols = st.columns(6)
cols[0].metric("Active Accounts", total_accounts)
cols[1].metric("Total Equity", f"${total_equity:,.0f}")
cols[2].metric("Withdrawable", f"${total_withdrawable:,.0f}")
cols[3].metric("Gross Profits", f"${total_gross:,.0f}")
cols[4].metric("Distributed", f"${total_distributed:,.0f}")
cols[5].metric("Client Balances", f"${total_client_bal:,.0f}")

st.metric("Growth Fund Balance", f"${gf_balance:,.0f}", delta=None)

# ─── TABBED DETAILED REPORTS ───
tab1, tab2, tab3, tab4 = st.tabs(["Profit Trend", "Distribution Breakdown", "Client Balances", "Accounts Summary"])

with tab1:
    st.subheader("Monthly Profit Trend")
    if profits:
        df = pd.DataFrame(profits)
        df["record_date"] = pd.to_datetime(df["record_date"])
        monthly = df.groupby(df["record_date"].dt.strftime("%Y-%m"))["gross_profit"].sum().reset_index()
        monthly = monthly.sort_values("record_date")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly["record_date"],
            y=monthly["gross_profit"],
            marker_color=accent_primary,
            text=monthly["gross_profit"].apply(lambda x: f"${x:,.0f}"),
            textposition="outside"
        ))
        fig.update_layout(
            height=500,
            title="Monthly Gross Profit (USD)",
            xaxis_title="Month",
            yaxis_title="Gross Profit",
            margin=dict(l=20, r=20, t=60, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No profit records yet")

with tab2:
    st.subheader("All-Time Participant Shares")
    if distributions:
        df = pd.DataFrame(distributions)
        summary = df.groupby("participant_name")["share_amount"].sum().reset_index()
        summary = summary.sort_values("share_amount", ascending=False)
        fig = go.Figure(go.Pie(
            labels=summary["participant_name"],
            values=summary["share_amount"],
            hole=0.5,
            textinfo="label+percent",
            textposition="outside",
            marker_colors=[accent_primary, accent_gold, "#00cc99"]
        ))
        fig.update_layout(height=600, title="Total Distributed Shares (USD)", margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

        summary["share_amount"] = summary["share_amount"].apply(lambda x: f"${x:,.2f}")
        summary = summary.rename(columns={"participant_name": "Participant", "share_amount": "Total Share"})
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.info("No profit distributions yet")

with tab3:
    st.subheader("Client Balances (Realtime)")
    if clients:
        df = pd.DataFrame(clients)
        df["balance"] = df["balance"].apply(lambda x: f"${x:,.2f}")
        df = df.rename(columns={"full_name": "Client", "balance": "Balance"}).sort_values("Balance", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No clients registered yet")

with tab4:
    st.subheader("Active Accounts Summary")
    if accounts:
        df = pd.DataFrame(accounts)
        df["current_equity"] = df["current_equity"].apply(lambda x: f"${x:,.0f}")
        df["withdrawable_balance"] = df["withdrawable_balance"].apply(lambda x: f"${x:,.0f}")
        df = df[["name", "current_phase", "current_equity", "withdrawable_balance"]].rename(columns={
            "name": "Account Name",
            "current_phase": "Phase",
            "current_equity": "Equity",
            "withdrawable_balance": "Withdrawable"
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No FTMO accounts yet")

# ─── CSV EXPORTS ───
st.subheader("📤 Export Reports (CSV)")
col_e1, col_e2 = st.columns(2)
today_str = date.today().strftime("%Y-%m-%d")

with col_e1:
    if profits:
        csv = pd.DataFrame(profits).to_csv(index=False).encode('utf-8')
        st.download_button("📄 Profits Report", csv, f"KMFX_Profits_{today_str}.csv", "text/csv", use_container_width=True)

    if distributions:
        csv = pd.DataFrame(distributions).to_csv(index=False).encode('utf-8')
        st.download_button("📄 Distributions Report", csv, f"KMFX_Distributions_{today_str}.csv", "text/csv", use_container_width=True)

with col_e2:
    if clients:
        client_df = pd.DataFrame([{"Client": c["full_name"], "Balance": c["balance"]} for c in clients])
        csv = client_df.to_csv(index=False).encode('utf-8')
        st.download_button("📄 Client Balances", csv, f"KMFX_Client_Balances_{today_str}.csv", "text/csv", use_container_width=True)

    summary_data = {
        "Metric": ["Gross Profits", "Distributed Shares", "Client Balances", "Growth Fund", "Active Accounts", "Total Equity", "Total Withdrawable"],
        "Value": [total_gross, total_distributed, total_client_bal, gf_balance, total_accounts, total_equity, total_withdrawable]
    }
    csv = pd.DataFrame(summary_data).to_csv(index=False).encode('utf-8')
    st.download_button("📄 Empire Summary", csv, f"KMFX_Empire_Summary_{today_str}.csv", "text/csv", use_container_width=True)

# ─── MOTIVATIONAL FOOTER (sync style) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Lightning Fast Empire Analytics
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Instant MV totals • Tabbed reports • Professional charts • Dated CSV exports • Full transparency
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Mastered for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)