# pages/05_🌱_Growth_Fund.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action

require_auth(min_role="admin")  # Owner & Admin lang pwede mag-manage

st.header("Growth Fund Management 🌱")
st.markdown("**Empire reinvestment engine: 100% automatic inflows from profits • Full source transparency • Advanced projections • Manual control • Instant sync**")

current_role = st.session_state.get("role", "guest")

# ────────────────────────────────────────────────
#  ULTRA-REALTIME CACHE (10s refresh)
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_gf_full_data():
    try:
        # Instant balance from MV
        gf_resp = supabase.table("mv_growth_fund_balance").select("balance").single().execute()
        gf_balance = gf_resp.data["balance"] if gf_resp.data else 0.0

        # All transactions
        trans_resp = supabase.table("growth_fund_transactions").select("*").order("date", desc=True).execute()
        transactions = trans_resp.data or []

        # Auto inflows sources
        profits_resp = supabase.table("profits").select("id, account_id, record_date, growth_fund_add").gt("growth_fund_add", 0).execute()
        profits = profits_resp.data or []

        accounts_resp = supabase.table("ftmo_accounts").select("id, name").execute()
        account_map = {a["id"]: a["name"] for a in accounts_resp.data or []}

        auto_sources = {}
        for p in profits:
            acc_name = account_map.get(p["account_id"], "Unknown")
            key = f"{acc_name} ({p['record_date'][:10]})"
            auto_sources[key] = auto_sources.get(key, 0) + p["growth_fund_add"]

        # Manual sources
        manual_sources = {}
        for t in transactions:
            if t["type"] == "Out" or t.get("account_source") == "Manual" or not t.get("description", "").startswith("Auto"):
                key = t.get("description") or t.get("account_source") or ("Manual Out" if t["type"] == "Out" else "Manual In")
                amount = -t["amount"] if t["type"] == "Out" else t["amount"]
                manual_sources[key] = manual_sources.get(key, 0) + amount

        # Empire stats for projections
        empire_resp = supabase.table("mv_empire_summary").select("total_accounts").single().execute()
        total_accounts = empire_resp.data["total_accounts"] if empire_resp.data else 0

        return transactions, gf_balance, auto_sources, manual_sources, total_accounts
    except Exception as e:
        st.error(f"Growth Fund data error: {str(e)}")
        return [], 0.0, {}, {}, 0

transactions, gf_balance, auto_sources, manual_sources, total_accounts = fetch_gf_full_data()

if st.button("🔄 Refresh Growth Fund Now", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

# ────────────────────────────────────────────────
#  KEY METRICS GRID
# ────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Growth Fund (Instant)", f"${gf_balance:,.0f}")
auto_in = sum(auto_sources.values())
col2.metric("Total Auto Inflows", f"${auto_in:,.0f}")
manual_in = sum(v for v in manual_sources.values() if v > 0)
col3.metric("Total Manual In", f"${manual_in:,.0f}")
outflows = sum(abs(v) for v in manual_sources.values() if v < 0)
col4.metric("Total Outflows", f"${outflows:,.0f}")

# ────────────────────────────────────────────────
#  SOURCE FLOW TREE (Auto + Manual)
# ────────────────────────────────────────────────
st.subheader("🌳 Inflow & Outflow Sources Tree (Realtime)")
all_sources = {**auto_sources, **manual_sources}
if all_sources:
    labels = ["Growth Fund"]
    values = []
    colors = []
    source = []
    target = []
    idx = 1
    for key, amount in all_sources.items():
        labels.append(key)
        values.append(abs(amount))
        colors.append("#00ffaa" if amount > 0 else "#ff6b6b")
        source.append(0)
        target.append(idx)
        idx += 1

    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=20, thickness=30, label=labels, color=["#ffd700"] + colors),
        link=dict(source=source, target=target, value=values)
    )])
    fig.update_layout(height=600, title="Complete Flow by Source (Auto + Manual)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Growth Fund is empty • Activates with first profit distribution or manual entry")

# ────────────────────────────────────────────────
#  MANUAL TRANSACTION (OWNER/ADMIN ONLY)
# ────────────────────────────────────────────────
if current_role in ["owner", "admin"]:
    with st.expander("➕ Manual Transaction (Reinvestment / Scaling)", expanded=False):
        with st.form("gf_manual_form", clear_on_submit=True):
            col_t1, col_t2 = st.columns([1, 2])
            with col_t1:
                trans_type = st.selectbox("Type", ["In (Add)", "Out (Withdraw)"])
            with col_t2:
                amount = st.number_input("Amount (USD)", min_value=0.01, step=100.0, format="%.2f")

            purpose = st.selectbox("Purpose", [
                "New FTMO Challenge Purchase",
                "Account Scaling Capital",
                "EA Development / Upgrade",
                "Team / Pioneer Bonus",
                "Operational Expenses",
                "Other (Specify below)"
            ])
            desc = st.text_area("Description / Notes (Optional)")
            trans_date = st.date_input("Transaction Date", value=date.today())

            if st.form_submit_button("Record Transaction", type="primary", use_container_width=True):
                try:
                    supabase.table("growth_fund_transactions").insert({
                        "date": str(trans_date),
                        "type": "In" if trans_type == "In (Add)" else "Out",
                        "amount": amount if trans_type == "In (Add)" else -amount,
                        "description": desc or purpose,
                        "account_source": "Manual",
                        "recorded_by": st.session_state.full_name
                    }).execute()

                    log_action("Manual GF Transaction", f"{trans_type} ${amount:,.2f} - {purpose}")
                    st.success(f"Transaction recorded! Growth Fund updated realtime.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to record: {str(e)}")

# ────────────────────────────────────────────────
#  TRANSACTION HISTORY TABLE
# ────────────────────────────────────────────────
st.subheader("📜 Complete Transaction History")
if transactions:
    df = pd.DataFrame(transactions)
    df["Amount"] = df.apply(lambda r: f"+${r['amount']:,.2f}" if r["type"] == "In" else f"-${r['amount']:,.2f}", axis=1)
    df["Type"] = df["type"].map({"In": "✅ In", "Out": "❌ Out"})
    df["Source"] = df.apply(lambda r: r["account_source"] if r["account_source"] != "Manual" else (r["description"] or "Manual"), axis=1)

    display_df = df[["date", "Type", "Amount", "Source", "recorded_by"]].rename(columns={
        "date": "Date", "Source": "Source / Description", "recorded_by": "Recorded By"
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("No transactions recorded yet • Auto-inflows start with profit distributions")

# ────────────────────────────────────────────────
#  ADVANCED SCALING PROJECTIONS
# ────────────────────────────────────────────────
st.subheader("🔮 Advanced Growth Fund Projections")
col_p1, col_p2 = st.columns(2)
with col_p1:
    months = st.slider("Projection Period (Months)", 6, 72, 36, step=6)
    projected_accounts = st.slider("Projected Active Accounts", total_accounts, total_accounts + 50, total_accounts + 15)
    avg_monthly_profit = st.number_input("Avg Monthly Gross Profit per Account (USD)", value=15000.0, step=1000.0, format="%.0f")
    gf_pct = st.slider("Growth Fund % from Gross Profits", 0.0, 50.0, 20.0, step=0.5)

with col_p2:
    monthly_manual = st.number_input("Additional Monthly Manual In (USD)", value=0.0, step=500.0, format="%.0f")

projected_monthly_gross = avg_monthly_profit * projected_accounts
projected_monthly_gf = projected_monthly_gross * (gf_pct / 100) + monthly_manual

dates = [date.today() + timedelta(days=30 * i) for i in range(months + 1)]
gf_proj = [gf_balance]
for _ in range(months):
    gf_proj.append(gf_proj[-1] + projected_monthly_gf)

fig_proj = go.Figure()
fig_proj.add_trace(go.Scatter(
    x=dates, y=gf_proj,
    mode='lines+markers',
    line=dict(color='#00ffaa', width=4),
    marker=dict(size=8, color='#ffd700'),
    name="Projected Balance"
))
fig_proj.add_hline(y=gf_balance * 10, line_dash="dash", line_color="#ffd700", annotation_text="10x Current Target")
fig_proj.update_layout(
    height=550,
    title=f"Projected Growth Fund Growth (+${projected_monthly_gf:,.0f}/month)",
    xaxis_title="Timeline",
    yaxis_title="Growth Fund Balance (USD)"
)
st.plotly_chart(fig_proj, use_container_width=True)

st.metric("Projected Balance in {} Months".format(months), f"${gf_proj[-1]:,.0f}", delta=f"+${gf_proj[-1] - gf_balance:,.0f}")

if gf_proj[-1] >= gf_balance * 10:
    st.success("🚀 On track for 10x Growth Fund! Empire scaling strong.")
elif gf_proj[-1] >= gf_balance * 5:
    st.success("🔥 Solid growth trajectory • Keep compounding!")
else:
    st.info("Growth projection active • Increase accounts/profits for faster scaling")

# ────────────────────────────────────────────────
#  MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.2rem; margin-bottom: 1.5rem;">
        Automatic Reinvestment Engine 🌱
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 0 auto 2rem;">
        Instant materialized balance • Realtime inflow/outflow trees • Manual control for scaling • Projections auto-loaded from empire stats • Empire compounds itself forever.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX Growth Fund • Fully Automatic • 2026 Edition</h2>
</div>
""", unsafe_allow_html=True)