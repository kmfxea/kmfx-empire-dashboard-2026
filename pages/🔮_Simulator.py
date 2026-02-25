# pages/🔮_Simulator.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="client")  # everyone can simulate, but data is empire-wide

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

st.header("🔮 Empire Growth Simulator")
st.markdown("**Advanced scaling forecaster** • Auto-loaded from current empire (accounts, equity, GF balance, avg profits per account, actual Growth Fund %, unit value) via materialized views + realtime data • Simulate scenarios • Projected equity, distributions, growth fund, units • Realtime multi-line charts • Sankey flow previews • Professional planning tool")

# ─── FULL INSTANT CACHE — MATERIALIZED VIEWS + REALTIME CALCS FOR ACCURATE DEFAULTS ───
@st.cache_data(ttl=60, show_spinner="Loading current empire stats for simulation...")
def fetch_simulator_data():
    try:
        # Instant core stats from materialized views
        empire = supabase.table("mv_empire_summary").select("total_accounts, total_equity").single().execute().data or {}
        gf_mv  = supabase.table("mv_growth_fund_balance").select("balance").single().execute().data or {}

        total_accounts = empire.get("total_accounts", 0)
        total_equity   = empire.get("total_equity", 0.0)
        gf_balance     = gf_mv.get("balance", 0.0)

        # Accurate averages from lightweight tables
        accounts = supabase.table("ftmo_accounts").select("unit_value, participants_v2").execute().data or []
        profits  = supabase.table("profits").select("gross_profit, record_date").execute().data or []

        # Avg monthly gross PER ACCOUNT (historical mean)
        avg_per_acc = 15000.0  # sensible fallback
        if profits:
            df = pd.DataFrame(profits)
            df["record_date"] = pd.to_datetime(df["record_date"])
            monthly_sums = df.groupby(df["record_date"].dt.to_period("M"))["gross_profit"].sum()
            avg_monthly_total = monthly_sums.mean() if len(monthly_sums) > 0 else 0.0
            if total_accounts > 0:
                avg_per_acc = avg_monthly_total / total_accounts
            if avg_per_acc < 1000:
                avg_per_acc = 15000.0

        # True avg Growth Fund % from actual participant rows
        gf_pcts = []
        for a in accounts:
            gf_acc = 0.0
            parts = a.get("participants_v2", []) or a.get("participants", [])
            for p in parts:
                display = p.get("display_name") or p.get("name", "")
                if "growth fund" in display.lower():
                    gf_acc += p.get("percentage", 0.0)
            gf_pcts.append(gf_acc)
        avg_gf_pct = sum(gf_pcts) / len(gf_pcts) if gf_pcts else 10.0
        if avg_gf_pct == 0:
            avg_gf_pct = 10.0  # reasonable default

        # Avg unit value
        unit_values = [a.get("unit_value", 3000.0) for a in accounts if a.get("unit_value", 0) > 0]
        avg_unit_value = sum(unit_values) / len(unit_values) if unit_values else 3000.0

        return (
            total_equity, total_accounts, float(avg_per_acc),
            float(avg_gf_pct), float(avg_unit_value), gf_balance
        )
    except Exception as e:
        st.error(f"Simulator data fetch error: {str(e)}")
        return 0.0, 0, 15000.0, 10.0, 3000.0, 0.0

(
    total_equity, total_accounts, avg_per_acc,
    avg_gf_pct, avg_unit_value, gf_balance
) = fetch_simulator_data()

st.info(f"**Instant Auto-Loaded Empire Stats:** {total_accounts} accounts • Total Equity **${total_equity:,.0f}** • Avg Monthly Gross per Account **${avg_per_acc:,.0f}** • Avg Growth Fund % **{avg_gf_pct:.1f}%** • Avg Unit Value **${avg_unit_value:,.0f}** • Current GF **${gf_balance:,.0f}**")

# ─── SIMULATION INPUTS (ACCURATE DEFAULTS) ───
st.subheader("Configure Simulation Scenarios")
col_sim1, col_sim2 = st.columns(2)
with col_sim1:
    months = st.slider("Projection Months", 6, 72, 36, step=6)
    projected_accounts = st.slider("Projected Active Accounts", total_accounts, total_accounts + 100, total_accounts + 20)
    monthly_gross_per_acc = st.number_input(
        "Avg Monthly Gross Profit per Account (USD)",
        value=avg_per_acc,
        min_value=0.0,
        step=1000.0,
        help="Auto-loaded from historical average per account (fallback $15,000 if no data)"
    )
    gf_percentage = st.slider(
        "Growth Fund Allocation % (from Profits)",
        0.0, 50.0, avg_gf_pct,
        step=0.5,
        help="Auto-loaded from actual 'Growth Fund' participant rows across all accounts"
    )

with col_sim2:
    unit_value_proj = st.number_input(
        "Profit Unit Value (USD)",
        value=avg_unit_value,
        min_value=100.0,
        step=500.0,
        help="Auto-loaded average unit value from FTMO accounts"
    )
    monthly_manual_in = st.number_input("Additional Monthly Manual In to GF (USD)", value=0.0, step=1000.0)
    scenario_name = st.text_input("Scenario Name", value="Elite Scaling Plan 2026")

# Auto-calculated monthly totals
monthly_gross_total = monthly_gross_per_acc * projected_accounts
monthly_gf_add      = monthly_gross_total * (gf_percentage / 100) + monthly_manual_in
monthly_distributed = monthly_gross_total - monthly_gf_add
monthly_units       = monthly_gross_total / unit_value_proj if unit_value_proj > 0 else 0

col_calc1, col_calc2, col_calc3, col_calc4 = st.columns(4)
col_calc1.metric("Projected Monthly Gross (Total)", f"${monthly_gross_total:,.0f}")
col_calc2.metric("Monthly GF Add", f"${monthly_gf_add:,.0f}")
col_calc3.metric("Monthly Distributed", f"${monthly_distributed:,.0f}")
col_calc4.metric("Monthly Units Generated", f"{monthly_units:.2f}")

# ─── RUN SIMULATION ───
if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
    with st.spinner("Running empire growth simulation..."):
        # Starting points
        start_equity = total_equity
        start_gf     = gf_balance
        dates        = [date.today() + timedelta(days=30 * i) for i in range(months + 1)]

        # Projections
        equity_proj      = [start_equity]
        gf_proj          = [start_gf]
        distributed_proj = [0.0]
        units_proj       = [0.0]

        for _ in range(months):
            gross       = monthly_gross_total
            gf_add      = monthly_gf_add
            distributed = monthly_distributed
            units       = monthly_units

            new_equity = equity_proj[-1] + gross
            new_gf     = gf_proj[-1] + gf_add

            equity_proj.append(new_equity)
            gf_proj.append(new_gf)
            distributed_proj.append(distributed_proj[-1] + distributed)
            units_proj.append(units_proj[-1] + units)

        # Multi-line projection chart
        fig_multi = go.Figure()
        fig_multi.add_trace(go.Scatter(x=dates, y=equity_proj,      name="Total Equity",      line=dict(color=accent_primary, width=6)))
        fig_multi.add_trace(go.Scatter(x=dates, y=gf_proj,          name="Growth Fund",        line=dict(color=accent_gold,    width=6)))
        fig_multi.add_trace(go.Scatter(x=dates, y=distributed_proj, name="Distributed Shares", line=dict(color="#00ffcc",       width=5)))
        fig_multi.add_trace(go.Scatter(x=dates, y=units_proj,       name="Cumulative Units",   line=dict(color="#ff6b6b",      width=5, dash="dot")))

        fig_multi.update_layout(
            title=f"{scenario_name} — Empire Growth Trajectory ({months} months)",
            height=620,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="Timeline",
            yaxis_title="Value (USD / Units)",
            margin=dict(l=40, r=40, t=80, b=40)
        )
        st.plotly_chart(fig_multi, use_container_width=True)

        # Final key metrics
        col_final1, col_final2, col_final3, col_final4 = st.columns(4)
        col_final1.metric("Final Total Equity", f"${equity_proj[-1]:,.0f}")
        col_final2.metric("Final Growth Fund", f"${gf_proj[-1]:,.0f}")
        col_final3.metric("Total Distributed Shares", f"${distributed_proj[-1]:,.0f}")
        col_final4.metric("Total Units Generated", f"{units_proj[-1]:.2f}")

        # Average monthly Sankey flow preview
        st.subheader("Projected Average Monthly Flow")
        if monthly_gross_total > 0:
            labels = ["Monthly Gross Profit"]
            values = []
            source = []
            target = []
            idx = 1

            labels.append("Distributed Shares")
            values.append(monthly_distributed)
            source.append(0)
            target.append(idx)
            idx += 1

            labels.append("Growth Fund")
            values.append(monthly_gf_add)
            source.append(0)
            target.append(idx)

            fig_avg = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=20,
                    thickness=30,
                    label=labels,
                    color=["#00ffaa", "#00ffcc", "#ffd700"]
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=values,
                    color=["#00ffcc80", "#ffd70080"]
                )
            )])
            fig_avg.update_layout(
                height=500,
                title=f"Avg Monthly Flow — ${monthly_gross_total:,.0f} Gross Profit",
                margin=dict(l=20, r=20, t=60, b=20)
            )
            st.plotly_chart(fig_avg, use_container_width=True)
        else:
            st.info("No gross profit projected in this scenario")

# ─── MOTIVATIONAL FOOTER (sync style) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Predictive Empire Scaling Simulator
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Accurate auto-loads • Realtime MV stats • Multi-scenario projections • Sankey flows • Elite planning tool
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Exponential for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)