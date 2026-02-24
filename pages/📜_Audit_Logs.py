# pages/16_📜_Audit_Logs.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action

require_auth(min_role="owner")  # Strict owner-only for security & compliance

st.header("Empire Audit Logs 📜")
st.markdown("**Full transparency & security: Realtime auto-logged actions from all empire transactions • Advanced search/filter/date range • Daily timeline chart • Action distribution pie • Detailed table • Export filtered CSV**")

current_role = st.session_state.get("role", "guest")

# ────────────────────────────────────────────────
# REALTIME CACHE (30s TTL)
# ────────────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_audit_full():
    try:
        logs_resp = supabase.table("logs").select("*").order("timestamp", desc=True).execute()
        logs = logs_resp.data or []

        total_actions = len(logs)
        unique_users = len(set(l.get("user_name") for l in logs if l.get("user_name")))
        unique_actions = len(set(l.get("action") for l in logs))

        action_counts = pd.Series([l.get("action") for l in logs if l.get("action")]).value_counts()

        return logs, total_actions, unique_users, unique_actions, action_counts
    except Exception as e:
        st.error(f"Audit logs fetch error: {str(e)}")
        return [], 0, 0, 0, pd.Series()

logs, total_actions, unique_users, unique_actions, action_counts = fetch_audit_full()

if st.button("🔄 Refresh Audit Logs Now", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Logs auto-refresh every 30s • Every empire action tracked realtime")

# ────────────────────────────────────────────────
# AUDIT SUMMARY METRICS
# ────────────────────────────────────────────────
col_a1, col_a2, col_a3, col_a4 = st.columns(4)
col_a1.metric("Total Logged Actions", f"{total_actions:,}")
col_a2.metric("Unique Active Users", unique_users)
col_a3.metric("Unique Action Types", unique_actions)
col_a4.metric("Latest Activity", logs[0]["timestamp"][:16].replace("T", " ") if logs else "—")

# ────────────────────────────────────────────────
# ACTION DISTRIBUTION PIE
# ────────────────────────────────────────────────
if not action_counts.empty:
    st.subheader("📊 Action Type Distribution")
    fig_pie = go.Figure(data=[go.Pie(
        labels=action_counts.index,
        values=action_counts.values,
        hole=0.4,
        textinfo="label+percent",
        textposition="outside",
        marker=dict(colors=["#00ffaa", "#ffd700", "#ff6b6b", "#4dabf7", "#a78bfa", "#f472b6"])
    )])
    fig_pie.update_layout(height=450, showlegend=True, legend=dict(orientation="h"))
    st.plotly_chart(fig_pie, use_container_width=True)

# ────────────────────────────────────────────────
# ADVANCED SEARCH & FILTER
# ────────────────────────────────────────────────
st.subheader("🔍 Advanced Search & Filter")
col_f1, col_f2 = st.columns(2)
with col_f1:
    search_log = st.text_input("Search Action / Details / User", placeholder="e.g. Profit, Uploaded, kingminted")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("From Date", value=None if not logs else pd.to_datetime(logs[-1]["timestamp"]).date())
    with col_d2:
        end_date = st.date_input("To Date", value=None if not logs else pd.to_datetime(logs[0]["timestamp"]).date())

with col_f2:
    filter_user = st.selectbox("Filter User", ["All"] + sorted(set(l.get("user_name") for l in logs if l.get("user_name"))))
    filter_action = st.selectbox("Filter Action Type", ["All"] + sorted(set(l.get("action") for l in logs if l.get("action"))))

# Apply filters
filtered_logs = logs
if search_log:
    s = search_log.lower()
    filtered_logs = [
        l for l in filtered_logs
        if s in l.get("action", "").lower()
        or s in l.get("details", "").lower()
        or s in str(l.get("user_name", "")).lower()
    ]

if filter_user != "All":
    filtered_logs = [l for l in filtered_logs if l.get("user_name") == filter_user]

if filter_action != "All":
    filtered_logs = [l for l in filtered_logs if l.get("action") == filter_action]

if start_date or end_date:
    filtered_logs = [
        l for l in filtered_logs
        if (not start_date or pd.to_datetime(l["timestamp"]).date() >= start_date)
        and (not end_date or pd.to_datetime(l["timestamp"]).date() <= end_date)
    ]

# ────────────────────────────────────────────────
# ACTIVITY TIMELINE CHART
# ────────────────────────────────────────────────
st.subheader("📊 Empire Activity Timeline (Filtered)")
if filtered_logs:
    log_df = pd.DataFrame(filtered_logs)
    log_df["timestamp"] = pd.to_datetime(log_df["timestamp"])
    daily_counts = log_df.groupby(log_df["timestamp"].dt.date).size().reset_index(name="Actions")
    daily_counts = daily_counts.sort_values("timestamp")

    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Scatter(
        x=daily_counts["timestamp"],
        y=daily_counts["Actions"],
        mode='lines+markers',
        line=dict(color="#00ffaa", width=4),
        marker=dict(size=8, color="#ffd700", symbol="circle")
    ))
    fig_timeline.update_layout(
        title="Daily Empire Actions (Filtered View)",
        height=450,
        xaxis_title="Date",
        yaxis_title="Number of Actions",
        hovermode="x unified",
        showlegend=False
    )
    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.info("No logs match current filters • Adjust to see activity timeline")

# ────────────────────────────────────────────────
# DETAILED AUDIT TABLE + EXPORT
# ────────────────────────────────────────────────
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

    # Filtered CSV export
    csv_logs = log_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📤 Export Filtered Logs CSV",
        csv_logs,
        f"KMFX_Audit_Logs_{datetime.now().strftime('%Y-%m-%d')}.csv",
        "text/csv",
        use_container_width=True
    )
else:
    st.info("No logs matching current filters • Empire actions are fully tracked")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">
        Complete Audit Transparency
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 2rem auto;">
        Realtime tracking • Date range & advanced filters • Action distribution pie • Daily timeline • Filtered CSV export • Empire fully accountable & secure.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX Audit Logs • Elite Compliance 2026</h2>
</div>
""", unsafe_allow_html=True)