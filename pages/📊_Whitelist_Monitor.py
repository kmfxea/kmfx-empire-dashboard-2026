# pages/📊_Whitelist_Monitor.py
import streamlit as st
import time
from datetime import datetime
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
render_sidebar()
require_auth(min_role="admin")  # Only admin & owner can access

# ─── THEME COLORS (consistent with Dashboard) ───
accent_primary = "#00ffaa"
accent_gold = "#ffd700"
accent_glow = "#00ffaa40"
accent_hover = "#00ffcc"

# ─── SCROLL-TO-TOP SCRIPT (same as Dashboard) ───
st.markdown("""
<script>
function forceScrollToTop() {
    window.scrollTo({top: 0, behavior: 'smooth'});
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}
setTimeout(forceScrollToTop, 100);
setTimeout(forceScrollToTop, 800);
setTimeout(forceScrollToTop, 2000);
</script>
""", unsafe_allow_html=True)

# ─── HEADER WITH LOGOUT (consistent style) ───
col_header1, col_header2 = st.columns([8, 2])
with col_header1:
    st.title("📡 Whitelist Message Monitor")
    st.caption("Live monitoring of messages from whitelisted / client users")
with col_header2:
    if st.button("🚪 Logout", type="secondary", use_container_width=True, key="monitor_logout"):
        for key in ["authenticated", "username", "full_name", "role", "user_id", "theme", "just_logged_in"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["logging_out"] = True
        st.session_state["logout_message"] = "Logged out successfully. See you soon! 👑"
        st.switch_page("main.py")
        st.rerun()

# ── Page Styling (glass-card consistent) ────────────────────────────────────
st.markdown("""
<style>
    .message-card {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .unread { border-left: 5px solid #f59e0b; }
    .read { border-left: 5px solid #10b981; }
    .timestamp { color: #94a3b8; font-size: 0.9rem; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Controls ────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns([2, 1.5, 1.2, 1])
with col1:
    view_mode = st.radio("View Mode", ["All Messages", "Inbox (Received)", "Sent"], horizontal=True, key="monitor_view_mode")
with col2:
    search_term = st.text_input("Search (username/message)", placeholder="weber OR urgent", key="monitor_search")
with col3:
    page_size = st.number_input("Messages per page", min_value=10, max_value=100, value=20, step=5, key="monitor_page_size")
with col4:
    auto_refresh = st.toggle("Auto-refresh (10s)", value=True, key="monitor_refresh")

# ── Data Fetching ───────────────────────────────────────────────────────────
@st.cache_data(ttl=8, show_spinner="Syncing messages...")
def fetch_messages(page=1, page_size=20, mode="All", search=""):
    offset = (page - 1) * page_size
    query = supabase.table("messages") \
        .select("id, sender_id, sender_username, receiver_id, receiver_username, message, timestamp, is_read") \
        .order("timestamp", desc=True) \
        .range(offset, offset + page_size - 1)

    current_user_id = st.session_state.get("user_id")
    if mode == "Inbox (Received)" and current_user_id:
        query = query.eq("receiver_id", current_user_id)
    elif mode == "Sent" and current_user_id:
        query = query.eq("sender_id", current_user_id)

    if search.strip():
        s = search.strip().lower()
        query = query.or_(f"message.ilike.%{s}%,sender_username.ilike.%{s}%,receiver_username.ilike.%{s}%")

    try:
        resp = query.execute()
        data = resp.data or []
        total = len(data) if not hasattr(resp, 'count') else resp.count
        return data, total
    except Exception as e:
        st.error(f"Error loading messages: {str(e)}")
        return [], 0

# ── Pagination ──────────────────────────────────────────────────────────────
if "monitor_current_page" not in st.session_state:
    st.session_state.monitor_current_page = 1

data, total_count = fetch_messages(
    page=st.session_state.monitor_current_page,
    page_size=page_size,
    mode=view_mode,
    search=search_term
)

total_pages = max(1, (total_count + page_size - 1) // page_size)

col_p1, col_p2, col_p3 = st.columns([1, 4, 1])
with col_p1:
    if st.button("← Prev", disabled=st.session_state.monitor_current_page <= 1):
        st.session_state.monitor_current_page -= 1
        st.rerun()
with col_p2:
    st.markdown(f"**Page {st.session_state.monitor_current_page} of {total_pages}** • Total: {total_count:,} messages")
with col_p3:
    if st.button("Next →", disabled=st.session_state.monitor_current_page >= total_pages):
        st.session_state.monitor_current_page += 1
        st.rerun()

# ── Display Messages ────────────────────────────────────────────────────────
if not data:
    st.info("No messages found matching your filters.")
else:
    for msg in data:
        ts = msg.get("timestamp", "—")
        ts_str = ts
        if ts != "—":
            try:
                ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts_str = ts_dt.strftime("%b %d, %Y  %I:%M %p")
            except:
                pass

        sender = msg.get("sender_username", "Unknown")
        receiver = msg.get("receiver_username", "—")
        content = msg.get("message", "").strip()
        is_read = msg.get("is_read", False)

        card_class = "message-card unread" if not is_read else "message-card read"

        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<div class="timestamp">{ts_str}</div>', unsafe_allow_html=True)
            st.markdown(f"**From:** {sender} → **To:** {receiver}")
            st.write(content)

            col_a, col_b, col_c = st.columns([3, 2, 1])
            with col_a:
                if st.button("Mark as Read", key=f"read_{msg['id']}"):
                    try:
                        supabase.table("messages").update({"is_read": True}).eq("id", msg["id"]).execute()
                        st.success("Marked as read!")
                        time.sleep(0.8)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Failed: {ex}")

            with col_b:
                reply_text = st.text_input("Quick reply...", key=f"reply_{msg['id']}", label_visibility="collapsed")

            with col_c:
                if st.button("Send", key=f"send_{msg['id']}") and reply_text.strip():
                    try:
                        supabase.table("messages").insert({
                            "sender_id": st.session_state.get("user_id"),
                            "sender_username": st.session_state.get("username", "Admin"),
                            "receiver_id": msg["sender_id"],
                            "receiver_username": sender,
                            "message": reply_text.strip()
                        }).execute()
                        st.success("Reply sent!")
                        st.session_state[f"reply_{msg['id']}"] = ""
                        time.sleep(1)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Reply failed: {ex}")

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")

# ── Auto-refresh ────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(10)
    st.rerun()
else:
    if st.button("🔄 Manual Refresh", use_container_width=True):
        st.rerun()