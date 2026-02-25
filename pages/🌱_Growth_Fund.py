# pages/🌱_Growth_Fund.py
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
require_auth(min_role="client")  # clients can view, admin/owner can transact

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

st.header("🌱 Growth Fund Management")
st.markdown("**Empire reinvestment engine** • 100% automatic inflows from profits • Full source transparency with auto-trees • Advanced projections • Manual adjustments • Instant sync across dashboard, profits & balances")

current_role = st.session_state.get("role", "guest").lower()

# ─── ULTRA-REALTIME DATA FETCH (10s TTL) ───
@st.cache_data(ttl=10, show_spinner="Syncing Growth Fund realtime...")
def fetch_gf_full_data():
    try:
        # Instant balance from MV
        gf_resp = supabase.table("mv_growth_fund_balance").select("balance").single().execute()
        gf_balance = gf_resp.data["balance"] if gf_resp.data else 0.0

        # Transactions history
        trans = supabase.table("growth_fund_transactions").select("*").order("date", desc=True).execute().data or []

        # Auto inflows sources
        profits = supabase.table("profits").select("id, account_id, record_date, growth_fund_add").gt("growth_fund_add", 0).execute().data or []
        accounts = supabase.table("ftmo_accounts").select("id, name").execute().data or []
        account_map = {a["id"]: a["name"] for a in accounts}

        auto_sources = {}
        for p in profits:
            acc_name = account_map.get(p["account_id"], "Unknown")
            key = f"{acc_name} ({p['record_date']})"
            auto_sources[key] = auto_sources.get(key, 0) + p["growth_fund_add"]

        # Manual sources / outflows
        manual_sources = {}
        for t in trans:
            if t["type"] == "Out" or t.get("account_source") == "Manual" or not t.get("description", "").startswith("Auto"):
                key = t.get("description") or t.get("account_source") or ("Outflow" if t["type"] == "Out" else "Manual In")
                amount = -t["amount"] if t["type"] == "Out" else t["amount"]
                manual_sources[key] = manual_sources.get(key, 0) + amount

        # Empire stats for projections
        empire = supabase.table("mv_empire_summary").select("total_accounts").single().execute()
        total_accounts = empire.data["total_accounts"] if empire.data else 0

        return trans, gf_balance, auto_sources, manual_sources, total_accounts
    except Exception as e:
        st.error(f"Growth Fund sync error: {str(e)}")
        return [], 0.0, {}, {}, 0

transactions, gf_balance, auto_sources, manual_sources, total_accounts = fetch_gf_full_data()

# ─── REFRESH BUTTON ───
if st.button("🔄 Refresh Growth Fund Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ─── KEY METRICS GRID ───
cols = st.columns(4)
cols[0].metric("Current Growth Fund", f"${gf_balance:,.0f}", help="Realtime from materialized view")
cols[1].metric("Total Auto Inflows", f"${sum(auto_sources.values()):,.0f}")
cols[2].metric("Total Manual In", f"${sum(v for v in manual_sources.values() if v > 0):,.0f}")
cols[3].metric("Total Outflows", f"${sum(abs(v) for v in manual_sources.values() if v < 0):,.0f}")

# ─── SOURCE TREE ───
st.subheader("🌳 All Inflow & Outflow Sources (Realtime)")
all_sources = {**auto_sources, **manual_sources}
if all_sources:
    labels = ["Growth Fund"]
    values = []
    colors = []
    source_idx = []
    target_idx = []
    node_id = 1

    for key, amt in all_sources.items():
        labels.append(key)
        values.append(abs(amt))
        colors.append(accent_primary if amt > 0 else "#ff6b6b")
        source_idx.append(0)
        target_idx.append(node_id)
        node_id += 1

    fig = go.Figure(go.Sankey(
        node=dict(pad=20, thickness=30, label=labels, color=["#ffd700"] + colors),
        link=dict(source=source_idx, target=target_idx, value=values)
    ))
    fig.update_layout(height=600, title="Complete Growth Fund Flow by Source", margin=dict(l=0,r=0,t=40,b=40))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Growth Fund is currently empty • It activates automatically with profit distributions")

# ─── MANUAL TRANSACTION (OWNER/ADMIN ONLY) ───
if current_role in ["owner", "admin"]:
    with st.expander("➕ Record Manual Transaction (Scaling / Reinvestment)", expanded=False):
        with st.form("gf_manual", clear_on_submit=True):
            col_t, col_a = st.columns([1, 2])
            with col_t:
                trans_type = st.selectbox("Type", ["In", "Out"])
            with col_a:
                amount = st.number_input("Amount (USD)", min_value=0.01, step=100.0, format="%.2f")

            purpose = st.selectbox("Purpose", [
                "New Challenge Purchase", "Scaling Capital", "EA Development",
                "Team Bonus", "Operational", "Other"
            ])
            desc = st.text_area("Description (optional)")
            trans_date = st.date_input("Transaction Date", value=date.today())

            if st.form_submit_button("Record Transaction", type="primary", use_container_width=True):
                try:
                    supabase.table("growth_fund_transactions").insert({
                        "date": str(trans_date),
                        "type": trans_type,
                        "amount": amount,
                        "description": desc or purpose,
                        "account_source": "Manual",
                        "recorded_by": st.session_state.get("full_name", "Admin")
                    }).execute()
                    st.success("Manual transaction recorded • Growth Fund updated realtime!")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to record: {str(e)}")

# ─── TRANSACTION HISTORY ───
st.subheader("📜 Complete Transaction History")
if transactions:
    df = pd.DataFrame(transactions)
    df["Amount Display"] = df.apply(lambda r: f"+${r['amount']:,.0f}" if r["type"] == "In" else f"-${r['amount']:,.0f}", axis=1)
    df["Type Display"] = df["type"].map({"In": "✅ In", "Out": "❌ Out"})
    df["Source"] = df.apply(lambda r: r["account_source"] if r["account_source"] != "Manual" else (r["description"] or "Manual"), axis=1)

    display_cols = ["date", "Type Display", "Amount Display", "Source", "recorded_by"]
    rename_map = {"date": "Date", "Type Display": "Type", "Amount Display": "Amount", "recorded_by": "By"}
    st.dataframe(df[display_cols].rename(columns=rename_map), use_container_width=True, hide_index=True)
else:
    st.info("No transactions recorded yet • Auto-inflows begin with profit sharing")

# ─── PROJECTIONS ───
st.subheader("🔮 Growth Fund Scaling Projections")
col_p1, col_p2 = st.columns(2)
with col_p1:
    months = st.slider("Projection Period (months)", 6, 72, 36, step=6)
    proj_accounts = st.slider("Projected Active Accounts", total_accounts, total_accounts + 50, total_accounts + 15)
    avg_profit_per_acc = st.number_input("Avg Monthly Gross Profit per Account (USD)", 5000.0, 50000.0, 15000.0, step=1000.0)
    gf_allocation_pct = st.slider("Growth Fund % from Gross Profits", 0.0, 50.0, 20.0, step=1.0)

with col_p2:
    monthly_manual_add = st.number_input("Additional Monthly Manual Injection (USD)", 0.0, 100000.0, 0.0, step=1000.0)

monthly_gross_proj = avg_profit_per_acc * proj_accounts
monthly_gf_add = monthly_gross_proj * (gf_allocation_pct / 100) + monthly_manual_add

proj_dates = [date.today() + timedelta(days=30 * i) for i in range(months + 1)]
proj_balance = [gf_balance]
for _ in range(months):
    proj_balance.append(proj_balance[-1] + monthly_gf_add)

fig_proj = go.Figure()
fig_proj.add_trace(go.Scatter(
    x=proj_dates,
    y=proj_balance,
    mode='lines+markers',
    line=dict(color=accent_primary, width=5),
    name="Projected Balance"
))
fig_proj.add_hline(y=gf_balance * 10, line_dash="dash", line_color=accent_gold, annotation_text="10× Current Goal")
fig_proj.update_layout(
    height=520,
    title=f"Projected Growth Fund (+${monthly_gf_add:,.0f} / month average)",
    xaxis_title="Timeline",
    yaxis_title="Growth Fund Balance (USD)"
)
st.plotly_chart(fig_proj, use_container_width=True)

st.metric("Projected Balance after {} months".format(months), f"${proj_balance[-1]:,.0f}")

if proj_balance[-1] >= gf_balance * 10:
    st.success("🚀 On track for 10× Growth Fund — exponential scaling activated!")
elif proj_balance[-1] >= gf_balance * 5:
    st.success("🔥 Solid trajectory — strong compounding in motion")

# ─── MOTIVATIONAL FOOTER (same as other pages) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Fully Automatic Reinvestment • Realtime Empire Growth
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Profits → Growth Fund → More Accounts → More Profits → Eternal Scaling
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Compounded for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)