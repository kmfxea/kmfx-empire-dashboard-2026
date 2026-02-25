# pages/🔔_Notifications.py
import streamlit as st
from datetime import date

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="client")  # clients see their own, admin/owner see/send to all

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

st.header("🔔 Empire Notifications")
st.markdown("**Realtime alert system** • Auto-push on profits, withdrawals, licenses, milestones • Prominent unread badges • Search & filters • Mark read • Instant sync & team alignment")

current_role = st.session_state.get("role", "guest").lower()

# ─── ULTRA-REALTIME FETCH (10s TTL) ───
@st.cache_data(ttl=10, show_spinner="Syncing notifications...")
def fetch_notifications_full():
    try:
        notifs = supabase.table("notifications").select("*").order("date", desc=True).execute().data or []
        users = supabase.table("users").select("id, full_name, balance, role").execute().data or []
        user_map = {u["full_name"]: {"balance": u.get("balance", 0)} for u in users}
        client_names = sorted(u["full_name"] for u in users if u["role"] == "client")
        return notifs, user_map, client_names
    except Exception as e:
        st.error(f"Notifications sync error: {str(e)}")
        return [], {}, []

notifications, user_map, client_names = fetch_notifications_full()

if st.button("🔄 Refresh Notifications Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Notifications auto-refresh every 10s • Auto-generated on key empire events")

# ─── CLIENT VIEW: Own notifications + unread count ───
if current_role == "client":
    my_name = st.session_state.get("full_name", "")
    my_notifications = [n for n in notifications if n.get("client_name") == my_name]
    unread_count = sum(1 for n in my_notifications if n.get("read", 0) == 0)
    st.subheader("Your Notifications 🔔")
    if unread_count > 0:
        st.markdown(f"### 🟡 {unread_count} Unread Alert{'s' if unread_count != 1 else ''}")
    else:
        st.markdown("### ✅ All caught up!")
else:
    # OWNER/ADMIN: Full view
    my_notifications = notifications
    st.subheader("All Empire Notifications")

# ─── SEND NEW NOTIFICATION (OWNER/ADMIN ONLY) ───
if current_role in ["owner", "admin"]:
    st.subheader("📢 Send New Notification")
    with st.form("notif_form", clear_on_submit=True):
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
                st.error("Title and message are required")
            else:
                try:
                    inserts = []
                    if target == "All Clients":
                        for name in client_names:
                            inserts.append({
                                "client_name": name,
                                "title": title.strip(),
                                "message": message.strip(),
                                "date": date.today().isoformat(),
                                "category": category,
                                "read": 0
                            })
                    else:
                        inserts.append({
                            "client_name": target,
                            "title": title.strip(),
                            "message": message.strip(),
                            "date": date.today().isoformat(),
                            "category": category,
                            "read": 0
                        })

                    if inserts:
                        supabase.table("notifications").insert(inserts).execute()

                    st.success(f"Notification sent to **{'all clients' if target == 'All Clients' else target}**!")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Send failed: {str(e)}")

# ─── SEARCH & FILTER ───
st.subheader("🔍 Search & Filter")
col_s1, col_s2 = st.columns(2)
with col_s1:
    search = st.text_input("Search title/message", placeholder="e.g. profit, license")
with col_s2:
    cat_filter = st.selectbox("Category", ["All"] + sorted(set(n.get("category", "General") for n in my_notifications)))

filtered = my_notifications
if search:
    s = search.lower()
    filtered = [n for n in filtered if s in n["title"].lower() or s in n["message"].lower()]

if cat_filter != "All":
    filtered = [n for n in filtered if n.get("category") == cat_filter]

# Sort: newest first
filtered = sorted(filtered, key=lambda x: x["date"], reverse=True)

# ─── NOTIFICATION CARDS ───
st.subheader(f"📬 Alerts ({len(filtered)} total)")
if filtered:
    for n in filtered:
        is_unread = n.get("read", 0) == 0
        badge_color = accent_primary if is_unread else "#6b7280"
        badge_text = "🟡 UNREAD" if is_unread else "✅ Read"
        client_balance = user_map.get(n.get("client_name", ""), {"balance": 0})["balance"]

        with st.container():
            st.markdown(f"""
            <div style="
                background:rgba(30,35,45,0.7); 
                backdrop-filter:blur(12px); 
                border-radius:16px; 
                padding:1.8rem; 
                margin-bottom:1.6rem; 
                box-shadow:0 6px 20px rgba(0,0,0,0.15); 
                border-left:6px solid {badge_color};
                border:1px solid rgba(100,100,100,0.25);
            ">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                    <h4 style="margin:0; color:{accent_primary};">{n['title']}</h4>
                    <span style="
                        background:{badge_color}; 
                        color:white; 
                        padding:0.4rem 1rem; 
                        border-radius:20px; 
                        font-weight:bold; 
                        font-size:0.9rem;
                    ">
                        {badge_text}
                    </span>
                </div>
                <small style="opacity:0.8; display:block; margin-bottom:0.8rem;">
                    {n.get('category', 'General')} • For <strong>{n.get('client_name', 'Empire')}</strong>
                    (Balance: ${client_balance:,.2f}) • {n['date']}
                </small>
                <div style="line-height:1.6;">
                    {n['message'].replace('\n', '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Mark as read (client view)
            if is_unread and current_role == "client":
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
                        st.success("Notification deleted")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {str(e)}")

            st.divider()
else:
    st.info("No notifications match your filters • All clear!")

st.caption("🤖 Auto-notifications: Profits, withdrawals, licenses, milestones • Delivered instantly to relevant clients")

# ─── MOTIVATIONAL FOOTER (sync style) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Realtime Empire Alert System
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Auto-push • Unread badges • Instant mark read • Search/filter • Always informed
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Aligned for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)