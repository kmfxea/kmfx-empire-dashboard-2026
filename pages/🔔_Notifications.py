# pages/10_🔔_Notifications.py
import streamlit as st
import pandas as pd
from datetime import datetime

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action

require_auth()  # Lahat authenticated, pero role-based visibility

st.header("Empire Notifications 🔔")
st.markdown("**Realtime alert system: Auto-push on profits, withdrawals, licenses, milestones • Unread badges • Search & filters • Mark read • Instant sync**")

current_role = st.session_state.get("role", "guest")
my_name = st.session_state.full_name

# ────────────────────────────────────────────────
# REALTIME CACHE (10s TTL)
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_notifications_full():
    try:
        notif_resp = supabase.table("notifications").select("*").order("date", desc=True).execute()
        notifications = notif_resp.data or []

        users_resp = supabase.table("users").select("id, full_name, balance, role").execute()
        all_users = users_resp.data or []

        user_map = {u["full_name"]: {"balance": u["balance"] or 0.0} for u in all_users}
        client_names = sorted([u["full_name"] for u in all_users if u["role"] == "client"])

        return notifications, user_map, client_names
    except Exception as e:
        st.error(f"Notifications load error: {str(e)}")
        return [], {}, []

notifications, user_map, client_names = fetch_notifications_full()

if st.button("🔄 Refresh Notifications Now", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Notifications auto-refresh every 10s • Auto-push on key events")

# ────────────────────────────────────────────────
# CLIENT VIEW: Sariling notifications + unread
# ────────────────────────────────────────────────
if current_role == "client":
    my_notifications = [n for n in notifications if n["client_name"] == my_name]
    unread_count = sum(1 for n in my_notifications if n.get("read", 0) == 0)

    if unread_count > 0:
        st.markdown(f"### 🟡 {unread_count} Unread Alert{'s' if unread_count > 1 else ''}")
    else:
        st.markdown("### ✅ All caught up!")

    my_notifications = sorted(my_notifications, key=lambda x: x["date"], reverse=True)

else:
    # OWNER/ADMIN: Lahat ng notifications
    my_notifications = notifications
    st.subheader("All Empire Notifications")

# ────────────────────────────────────────────────
# SEND NEW NOTIFICATION (ADMIN/OWNER ONLY)
# ────────────────────────────────────────────────
if current_role in ["owner", "admin"]:
    st.subheader("📢 Send New Notification")
    with st.form("notif_send_form", clear_on_submit=True):
        target = st.selectbox("Send to", ["All Clients"] + client_names)
        category = st.selectbox("Category", [
            "Profit Share", "Withdrawal Update", "License Granted",
            "Milestone", "EA Update", "General Alert", "Team Message"
        ])
        title = st.text_input("Title *", placeholder="e.g. New Profit Distributed!")
        message = st.text_area("Message *", height=150, placeholder="Details here...")

        submitted = st.form_submit_button("🔔 Send Alert", type="primary", use_container_width=True)

        if submitted:
            if not title.strip() or not message.strip():
                st.error("Title and message required")
            else:
                try:
                    inserts = []
                    if target == "All Clients":
                        for name in client_names:
                            inserts.append({
                                "client_name": name,
                                "title": title.strip(),
                                "message": message.strip(),
                                "date": datetime.now().isoformat(),
                                "category": category,
                                "read": 0
                            })
                    else:
                        inserts.append({
                            "client_name": target,
                            "title": title.strip(),
                            "message": message.strip(),
                            "date": datetime.now().isoformat(),
                            "category": category,
                            "read": 0
                        })

                    if inserts:
                        supabase.table("notifications").insert(inserts).execute()
                        log_action("Notification Sent", f"To: {'All' if target == 'All Clients' else target} | Title: {title}")
                        st.success(f"Notification sent to {'all clients' if target == 'All Clients' else target}!")
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"Send failed: {str(e)}")

# ────────────────────────────────────────────────
# SEARCH & FILTER
# ────────────────────────────────────────────────
st.subheader("🔍 Search & Filter")
col_s1, col_s2 = st.columns(2)
with col_s1:
    search = st.text_input("Search title/message", "")
with col_s2:
    cat_filter = st.selectbox("Category", ["All"] + sorted(set(n.get("category", "General") for n in my_notifications if n.get("category"))))

filtered = my_notifications
if search:
    s = search.lower()
    filtered = [n for n in filtered if s in n["title"].lower() or s in n["message"].lower()]
if cat_filter != "All":
    filtered = [n for n in filtered if n.get("category") == cat_filter]

filtered = sorted(filtered, key=lambda x: x["date"], reverse=True)

# ────────────────────────────────────────────────
# NOTIFICATION CARDS
# ────────────────────────────────────────────────
st.subheader(f"Your Alerts ({len(filtered)} total)")
if filtered:
    for n in filtered:
        is_unread = n.get("read", 0) == 0
        badge_color = "#00ffaa" if is_unread else "#888888"
        badge_text = "🟡 UNREAD" if is_unread else "✅ Read"

        client_balance = user_map.get(n["client_name"], {"balance": 0})["balance"]

        with st.container(border=True):
            st.markdown(f"""
            <div class='glass-card' style='padding:1.8rem; border-left:6px solid {badge_color};'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <h4 style='margin:0; color:#00ffaa;'>{n['title']}</h4>
                    <span style='background:{badge_color}; color:white; padding:0.4rem 1rem; border-radius:20px; font-weight:bold;'>
                        {badge_text}
                    </span>
                </div>
                <small style='opacity:0.8;'>
                    {n.get('category', 'General')} • For <strong>{n['client_name']}</strong>
                    (Balance: ${client_balance:,.2f}) • {n['date'][:10]}
                </small>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(n['message'])

            # Mark as read (client lang)
            if current_role == "client" and is_unread:
                if st.button("Mark as Read", key=f"read_{n['id']}", use_container_width=True):
                    try:
                        supabase.table("notifications").update({"read": 1}).eq("id", n["id"]).execute()
                        st.success("Marked as read!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

            # Admin delete
            if current_role in ["owner", "admin"]:
                if st.button("🗑️ Delete Notification", key=f"del_{n['id']}", type="secondary", use_container_width=True):
                    try:
                        supabase.table("notifications").delete().eq("id", n["id"]).execute()
                        log_action("Notification Deleted", f"ID: {n['id']} | Title: {n['title']}")
                        st.success("Deleted")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {str(e)}")

            st.divider()
else:
    st.info("No notifications match your filters • All clear!")

st.caption("🤖 Auto-notifications: Profits, withdrawals, licenses, milestones • Delivered instantly")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">
        Realtime Empire Alerts
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 2rem auto;">
        Prominent unread badges • Instant mark read • Search/filter • Auto-push • Team always informed & aligned.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX Notifications • Fully Fixed 2026</h2>
</div>
""", unsafe_allow_html=True)