# pages/📜_Audit_Logs.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="owner")  # strict — owner only for full audit transparency

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

st.header("📜 Empire Audit Logs")
st.markdown("**Full transparency & security** • Realtime auto-logged actions from all empire transactions (profits, distributions, licenses, withdrawals, uploads, announcements, user changes) • Advanced search/filter/date range • Daily timeline chart • Action distribution pie • Detailed table • Export filtered CSV • Owner-only for compliance & oversight")

current_role = st.session_state.get("role", "guest").lower()
if current_role != "owner":
    st.error("🔒 Audit Logs are **OWNER-ONLY** for empire security & compliance.")
    st.stop()

# ─── FULL REALTIME CACHE (30s TTL) ───
@st.cache_data(ttl=30, show_spinner="Loading realtime audit logs...")
def fetch_audit_full():
    try:
        logs = supabase.table("logs").select("*").order("timestamp", desc=True).execute().data or []

        total_actions   = len(logs)
        unique_users    = len(set(l.get("user_name") for l in logs if l.get("user_name")))
        unique_actions  = len(set(l.get("action") for l in logs))
        action_counts   = pd.Series([l.get("action") for l in logs]).value_counts()

        latest_ts = logs[0]["timestamp"][:16].replace("T", " ") if logs else "—"

        return logs, total_actions, unique_users, unique_actions, action_counts, latest_ts
    except Exception as e:
        st.error(f"Failed to fetch audit logs: {str(e)}")
        return [], 0, 0, 0, pd.Series(), "—"

logs, total_actions, unique_users, unique_actions, action_counts, latest_ts = fetch_audit_full()

if st.button("🔄 Refresh Audit Logs Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Logs auto-refresh every 30s • Every empire action tracked realtime")

# ─── AUDIT SUMMARY METRICS ───
st.subheader("Audit Overview (Instant Stats)")
cols = st.columns(4)
cols[0].metric("Total Logged Actions", f"{total_actions:,}")
cols[1].metric("Unique Active Users", unique_users)
cols[2].metric("Unique Action Types", unique_actions)
cols[3].metric("Latest Activity", latest_ts)

# ─── ACTION DISTRIBUTION PIE ───
if not action_counts.empty:
    st.subheader("📊 Action Type Distribution")
    fig_pie = go.Figure(data=[go.Pie(
        labels=action_counts.index,
        values=action_counts.values,
        hole=0.45,
        textinfo="label+percent",
        textposition="outside",
        marker_colors=[accent_primary, accent_gold, "#ff6b6b", "#00ffcc", "#a67c00", "#ffd700"]
    )])
    fig_pie.update_layout(
        height=420,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ─── ADVANCED SEARCH & FILTER ───
st.subheader("🔍 Advanced Search & Filter")
col_f1, col_f2 = st.columns(2)
with col_f1:
    search_log = st.text_input("Search Action/Details/User", placeholder="e.g. Profit, Uploaded, kingminted")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("From Date", value=None)
    with col_d2:
        end_date = st.date_input("To Date", value=None)

with col_f2:
    filter_user = st.selectbox("Filter User", ["All"] + sorted(set(l.get("user_name") for l in logs if l.get("user_name"))))
    filter_action = st.selectbox("Filter Action Type", ["All"] + sorted(set(l.get("action") for l in logs)))

# Apply filters
filtered_logs = logs
if search_log:
    s = search_log.lower()
    filtered_logs = [l for l in filtered_logs if
                     s in l.get("action", "").lower() or
                     s in l.get("details", "").lower() or
                     s in str(l.get("user_name", "")).lower()]

if filter_user != "All":
    filtered_logs = [l for l in filtered_logs if l.get("user_name") == filter_user]

if filter_action != "All":
    filtered_logs = [l for l in filtered_logs if l.get("action") == filter_action]

if start_date or end_date:
    filtered_logs = [
        l for l in filtered_logs
        if (not start_date or pd.to_datetime(l["timestamp"]).date() >= start_date) and
           (not end_date or pd.to_datetime(l["timestamp"]).date() <= end_date)
    ]

# ─── ACTIVITY TIMELINE CHART ───
st.subheader("📊 Empire Activity Timeline (Filtered View)")
if filtered_logs:
    log_df = pd.DataFrame(filtered_logs)
    log_df["timestamp"] = pd.to_datetime(log_df["timestamp"])
    daily_counts = log_df.groupby(log_df["timestamp"].dt.date).size().reset_index(name="Actions")

    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Scatter(
        x=daily_counts["timestamp"],
        y=daily_counts["Actions"],
        mode='lines+markers',
        line=dict(color=accent_primary, width=5),
        marker=dict(size=8, color=accent_gold),
        name="Daily Actions"
    ))
    fig_timeline.update_layout(
        title="Daily Empire Actions (Filtered)",
        height=450,
        xaxis_title="Date",
        yaxis_title="Number of Actions",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.info("No logs match current filters • Adjust filters to see timeline")

# ─── DETAILED LOG TABLE ───
st.subheader(f"Detailed Audit Logs ({len(filtered_logs):,} entries)")
if filtered_logs:
    log_display = pd.DataFrame(filtered_logs)
    log_display["timestamp"] = pd.to_datetime(log_display["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    log_display = log_display[["timestamp", "user_name", "user_type", "action", "details"]].rename(columns={
        "timestamp": "Time",
        "user_name": "User",
        "user_type": "Role",
        "action": "Action",
        "details": "Details"
    })

    st.dataframe(
        log_display.style.set_properties(**{"text-align": "left"}),
        use_container_width=True,
        hide_index=True
    )

    # Export filtered CSV
    csv_logs = log_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📤 Export Filtered Logs CSV",
        csv_logs,
        f"KMFX_Audit_Logs_{date.today().strftime('%Y-%m-%d')}.csv",
        "text/csv",
        use_container_width=True
    )
else:
    st.info("No logs matching current filters • Empire actions are fully tracked")

# ─── MOTIVATIONAL FOOTER (sync style) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Complete Audit Transparency & Oversight
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Realtime tracking • Date range & advanced filters • Action distribution • Timeline insights • Filtered CSV export • Empire fully accountable
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Secured for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)