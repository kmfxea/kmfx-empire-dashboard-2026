# pages/📊_Whitelist_Monitor.py
import streamlit as st
from datetime import datetime
import time
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

# ────────────────────────────────────────────────
# AUTH + SIDEBAR
# ────────────────────────────────────────────────
render_sidebar()
require_auth(min_role="admin")  # Only admin & owner

# ─── THEME & SCROLL-TO-TOP ───
accent_primary = "#00ffaa"
st.markdown("""
<style>
    .message-card { background: rgba(30,41,59,0.7); border-radius:12px; padding:1.2rem; margin:1rem 0; 
                    border:1px solid #334155; box-shadow:0 4px 15px rgba(0,0,0,0.25); }
    .unread { border-left:5px solid #f59e0b; }
    .read   { border-left:5px solid #10b981; }
    .timestamp { color:#94a3b8; font-size:0.9rem; margin-bottom:0.6rem; }
    .reply-box { margin-top:1rem; }
</style>
<script>
function scrollToTop() { window.scrollTo({top:0, behavior:'smooth'}); }
setTimeout(scrollToTop, 100);
</script>
""", unsafe_allow_html=True)

# ─── HEADER ───
col1, col2 = st.columns([8, 2])
with col1:
    st.title("📡 Whitelist Message Monitor")
    st.caption("Real-time monitoring & quick replies • Admin only")
with col2:
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        for k in ["authenticated", "username", "full_name", "role", "user_id", "theme"]:
            st.session_state.pop(k, None)
        st.session_state["logging_out"] = True
        st.session_state["logout_message"] = "Logged out. See you soon! 👑"
        st.switch_page("main.py")

# ─── CONTROLS ───
col_mode, col_search, col_size, col_refresh = st.columns([2.2, 2, 1.3, 1.2])
with col_mode:
    view_mode = st.radio("View", ["All Messages", "Inbox (Received)", "Sent", "Unread Only"], horizontal=True)
with col_search:
    search_term = st.text_input("Search (user/message)", placeholder="weber urgent", key="msg_search")
with col_size:
    page_size = st.number_input("Per page", 10, 100, 20, 5)
with col_refresh:
    auto_refresh = st.toggle("Auto-refresh 10s", value=True)

@st.cache_data(ttl=9, show_spinner="Loading messages...")
def get_messages(page=1, page_size=20, mode="All", search=""):
    offset = (page - 1) * page_size
    current_uid = st.session_state.get("user_id")

    # ── Paginated data query ───────────────────────────────────────────────
    q = supabase.table("messages").select("""
        id, sender_id, sender_username, receiver_id, receiver_username, 
        message, timestamp, is_read
    """).order("timestamp", desc=True)

    if mode == "Inbox (Received)" and current_uid:
        q = q.eq("receiver_id", current_uid)
    elif mode == "Sent" and current_uid:
        q = q.eq("sender_id", current_uid)
    elif mode == "Unread Only" and current_uid:
        q = q.eq("receiver_id", current_uid).eq("is_read", False)

    if search.strip():
        s = search.strip().lower()
        q = q.or_(f"message.ilike.%{s}%,sender_username.ilike.%{s}%,receiver_username.ilike.%{s}%")

    data_resp = q.range(offset, offset + page_size - 1).execute()
    data = data_resp.data or []

    # ── Accurate total count (separate query) ──────────────────────────────
    count_q = supabase.table("messages").select("id", count="exact")

    if mode == "Inbox (Received)" and current_uid:
        count_q = count_q.eq("receiver_id", current_uid)
    elif mode == "Sent" and current_uid:
        count_q = count_q.eq("sender_id", current_uid)
    elif mode == "Unread Only" and current_uid:
        count_q = count_q.eq("receiver_id", current_uid).eq("is_read", False)

    if search.strip():
        count_q = count_q.or_(f"message.ilike.%{s}%,sender_username.ilike.%{s}%,receiver_username.ilike.%{s}%")

    count_resp = count_q.execute()
    # Safe handling: count can be None when 0 rows
    total = count_resp.count if count_resp.count is not None else 0

    return data, total

# ─── PAGINATION STATE ───
if "msg_page" not in st.session_state:
    st.session_state.msg_page = 1

data, total_count = get_messages(
    page=st.session_state.msg_page,
    page_size=page_size,
    mode=view_mode,
    search=search_term
)

total_pages = max(1, (total_count + page_size - 1) // page_size)

# Pagination controls
col_prev, col_info, col_next = st.columns([1, 5, 1])
with col_prev:
    if st.button("← Previous", disabled=st.session_state.msg_page <= 1):
        st.session_state.msg_page -= 1
        st.rerun()
with col_info:
    st.markdown(f"**Page {st.session_state.msg_page} / {total_pages}**  •  {total_count:,} messages total")
with col_next:
    if st.button("Next →", disabled=st.session_state.msg_page >= total_pages):
        st.session_state.msg_page += 1
        st.rerun()

# ─── DISPLAY MESSAGES ───
if not data:
    st.info("No messages match the current filters.")
else:
    for msg in data:
        ts_raw = msg.get("timestamp")
        ts_str = "—"
        if ts_raw:
            try:
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                ts_str = dt.strftime("%b %d, %Y  %I:%M %p")
            except:
                ts_str = ts_raw[:19].replace("T", " ")

        sender = msg.get("sender_username", "Unknown")
        receiver = msg.get("receiver_username", "—")
        content = msg.get("message", "").strip()
        is_read = msg.get("is_read", False)

        card_class = "message-card unread" if not is_read else "message-card read"

        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<div class="timestamp">{ts_str}</div>', unsafe_allow_html=True)
            st.markdown(f"**{sender}** → **{receiver}**")
            st.write(content)

            # Actions
            col_read, col_reply, col_send = st.columns([1.5, 3, 1])
            with col_read:
                if not is_read and st.button("Mark Read", key=f"read_{msg['id']}"):
                    try:
                        supabase.table("messages").update({"is_read": True}).eq("id", msg["id"]).execute()
                        st.toast("Marked as read", icon="✅")
                        time.sleep(0.6)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")

            with col_reply:
                reply_key = f"reply_{msg['id']}"
                reply_text = st.text_input("Quick reply...", key=reply_key, label_visibility="collapsed")

            with col_send:
                if st.button("Send", key=f"send_{msg['id']}") and reply_text.strip():
                    try:
                        supabase.table("messages").insert({
                            "sender_id": st.session_state.get("user_id"),
                            "sender_username": st.session_state.get("username", "Admin"),
                            "receiver_id": msg["sender_id"],
                            "receiver_username": sender,
                            "message": reply_text.strip()
                        }).execute()
                        st.session_state[reply_key] = ""
                        st.toast("Reply sent", icon="📤")
                        time.sleep(0.8)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Send failed: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

# ─── AUTO-REFRESH ───
if auto_refresh:
    time.sleep(10)
    st.rerun()
else:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()