# pages/📊_Whitelist_Monitor.py
import streamlit as st
from utils.supabase_client import supabase
import time
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title="Whitelist Message Monitor • KMFX Empire",
    page_icon="📡",
    layout="wide"
)

# ── Security ────────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please log in first.")
    st.stop()

if st.session_state.get("role") not in ["owner", "admin"]:
    st.error("Access restricted to Owner and Admin only.")
    st.stop()

# ── Page Styling ────────────────────────────────────────────────────────────
st.markdown("""
    <style>
        .message-card {
            background: rgba(30, 41, 59, 0.6);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            border: 1px solid #334155;
        }
        .unread { border-left: 4px solid #f59e0b; }
        .read { border-left: 4px solid #10b981; }
        .timestamp { color: #94a3b8; font-size: 0.85rem; }
    </style>
""", unsafe_allow_html=True)

# ── Header & Controls ───────────────────────────────────────────────────────
st.title("📡 Whitelist Message Monitor")
st.caption("Live monitoring of messages from whitelisted / client users")

col_settings1, col_settings2, col_settings3, col_settings4 = st.columns([2, 1.5, 1.2, 1])
with col_settings1:
    view_mode = st.radio("View Mode", ["All Messages", "Inbox (Received)", "Sent"], horizontal=True, key="view_mode")
with col_settings2:
    search_term = st.text_input("Search by username or keyword", placeholder="e.g. weber OR gold", key="search")
with col_settings3:
    page_size = st.number_input("Messages per page", min_value=10, max_value=100, value=20, step=5)
with col_settings4:
    auto_refresh = st.toggle("Auto-refresh (every 10s)", value=True, key="auto_refresh")

# ── Data Fetching Function ──────────────────────────────────────────────────
@st.cache_data(ttl=10, show_spinner=False)
def fetch_messages(page=1, page_size=20, mode="All", search=""):
    offset = (page - 1) * page_size
    
    query = supabase.table("messages") \
        .select("""
            id,
            sender_id,
            sender_username,
            receiver_id,
            receiver_username,
            message,
            timestamp,
            is_read
        """) \
        .order("timestamp", desc=True) \
        .range(offset, offset + page_size - 1)

    # Filter by view mode
    current_user_id = st.session_state.get("user_id")  # assuming you store this on login
    if mode == "Inbox (Received)":
        query = query.eq("receiver_id", current_user_id)
    elif mode == "Sent":
        query = query.eq("sender_id", current_user_id)

    # Search filter (simple text search on message + usernames)
    if search.strip():
        search = search.strip().lower()
        query = query.or_(
            f"message.ilike.%{search}%,"
            f"sender_username.ilike.%{search}%,"
            f"receiver_username.ilike.%{search}%"
        )

    # Optional: only whitelisted senders (if column exists)
    try:
        whitelisted = supabase.table("users").select("id").eq("is_whitelisted", True).execute().data
        if whitelisted:
            wl_ids = [r["id"] for r in whitelisted]
            query = query.in_("sender_id", wl_ids)
    except:
        pass  # skip if column doesn't exist yet

    try:
        response = query.execute()
        return response.data or [], response.count or 0
    except Exception as e:
        st.error(f"Failed to load messages: {str(e)}")
        return [], 0

# ── Pagination & Data ───────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

data, total_count = fetch_messages(
    page=st.session_state.current_page,
    page_size=page_size,
    mode=view_mode,
    search=search_term
)

total_pages = max(1, (total_count + page_size - 1) // page_size)

# Pagination controls
col_p1, col_p2, col_p3 = st.columns([1, 4, 1])
with col_p1:
    if st.button("← Prev", disabled=st.session_state.current_page <= 1):
        st.session_state.current_page -= 1
        st.rerun()
with col_p2:
    st.markdown(f"**Page {st.session_state.current_page} of {total_pages}**  •  Total: {total_count:,} messages")
with col_p3:
    if st.button("Next →", disabled=st.session_state.current_page >= total_pages):
        st.session_state.current_page += 1
        st.rerun()

# ── Display Messages ────────────────────────────────────────────────────────
if not data:
    st.info("No messages found matching your filters.")
else:
    selected_msgs = []
    for msg in data:
        ts = msg.get("timestamp", "—")
        if ts != "—":
            try:
                ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts_str = ts_dt.strftime("%b %d, %Y  %I:%M %p")
            except:
                ts_str = ts

        sender = msg.get("sender_username", "Unknown")
        receiver = msg.get("receiver_username", "System")
        content = msg["message"].strip()
        is_read = msg.get("is_read", False)
        
        card_class = "message-card unread" if not is_read else "message-card read"
        
        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<div class="timestamp">{ts_str}</div>', unsafe_allow_html=True)
            st.markdown(f"**From:** {sender}  →  **To:** {receiver}")
            st.write(content)
            
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                if st.button("Mark as Read", key=f"read_{msg['id']}"):
                    try:
                        supabase.table("messages").update({"is_read": True}).eq("id", msg["id"]).execute()
                        st.success("Marked as read!")
                        time.sleep(0.8)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Failed to update: {ex}")
            
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

# ── Auto-refresh logic ──────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(10)
    st.rerun()
else:
    if st.button("🔄 Manual Refresh"):
        st.rerun()