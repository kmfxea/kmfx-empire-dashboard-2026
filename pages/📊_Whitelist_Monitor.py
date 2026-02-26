# pages/📊_Whitelist_Monitor.py
import streamlit as st
from datetime import datetime
import time
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="admin")

# ─── PAGE CONFIG & STYLING ───
st.set_page_config(page_title="Whitelist / Waitlist Monitor", layout="wide")

st.markdown("""
<style>
    .card {
        background: rgba(30,41,59,0.75);
        border-radius: 10px;
        padding: 1.1rem;
        margin: 0.8rem 0;
        border: 1px solid #3f4a5c;
        box-shadow: 0 2px 12px rgba(0,0,0,0.25);
    }
    .pending  { border-left: 4px solid #f59e0b; }
    .approved { border-left: 4px solid #10b981; }
    .rejected { border-left: 4px solid #ef4444; }
    .unsub    { border-left: 4px solid #6b7280; }
    .timestamp { color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.5rem; display: block; }
    hr.thin { border: none; border-top: 1px solid #444; margin: 0.4rem 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ─── HEADER (no logout here) ───
st.title("👥 Whitelist / Waitlist Monitor")
st.caption("Waitlist signups + messages from approved clients • Admin only")

# ─── TABS ───
tab_waitlist, tab_messages = st.tabs(["📋 Waitlist Submissions", "💬 Whitelisted Messages"])

# ────────────────────────────────────────────────
# WAITLIST TAB
# ────────────────────────────────────────────────
with tab_waitlist:
    st.subheader("Public Waitlist Entries")

    # Filters
    col1, col2, col3 = st.columns([2.2, 2.5, 1.4])
    with col1:
        status_filter = st.multiselect(
            "Status",
            ["Pending", "Approved", "Rejected", "Unsubscribed"],
            default=["Pending"],
            key="wl_status_filter"
        )
    with col2:
        search_term = st.text_input("Search name / email / message", key="wl_search")
    with col3:
        page_size = st.number_input("Per page", 10, 100, 20, 5, key="wl_page_size")

    # Fetch
    @st.cache_data(ttl=12, show_spinner="Loading waitlist...")
    def fetch_waitlist(page=1, size=20, statuses=None, search=""):
        offset = (page - 1) * size
        q = supabase.table("waitlist").select("""
            id, full_name, email, message, language, status, 
            subscribed, created_at
        """).order("created_at", desc=True)

        if statuses:
            q = q.in_("status", statuses)
        if search.strip():
            s = search.strip().lower()
            q = q.or_(f"full_name.ilike.%{s}%,email.ilike.%{s}%,message.ilike.%{s}%")

        data_resp = q.range(offset, offset + size - 1).execute()
        data = data_resp.data or []

        count_q = supabase.table("waitlist").select("id", count="exact")
        if statuses:
            count_q = count_q.in_("status", statuses)
        if search.strip():
            count_q = count_q.or_(f"full_name.ilike.%{s}%,email.ilike.%{s}%,message.ilike.%{s}%")
        count_resp = count_q.execute()
        total = count_resp.count if count_resp.count is not None else 0

        return data, total

    if "wl_page" not in st.session_state:
        st.session_state.wl_page = 1

    data, total = fetch_waitlist(
        page=st.session_state.wl_page,
        size=page_size,
        statuses=status_filter,
        search=search_term
    )

    total_pages = max(1, (total + page_size - 1) // page_size)

    # Pagination
    col_prev, col_info, col_next = st.columns([1, 5, 1])
    with col_prev:
        if st.button("← Prev", disabled=st.session_state.wl_page <= 1, key="wl_prev_btn"):
            st.session_state.wl_page -= 1
            st.rerun()
    with col_info:
        st.markdown(f"**Page {st.session_state.wl_page} / {total_pages}**  •  {total:,} entries")
    with col_next:
        if st.button("Next →", disabled=st.session_state.wl_page >= total_pages, key="wl_next_btn"):
            st.session_state.wl_page += 1
            st.rerun()

    if not data:
        st.info("No matching waitlist entries.")
    else:
        for entry in data:
            created_str = entry.get("created_at", "—")[:19].replace("T", " ") if entry.get("created_at") else "—"
            name = entry.get("full_name") or "—"
            email = entry.get("email", "—")
            message = (entry.get("message") or "").strip()
            status = entry.get("status", "Pending")
            subscribed = "Yes" if entry.get("subscribed", True) else "No"
            lang = entry.get("language", "en").upper()

            card_class = f"card {status.lower()[:3]}"

            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<span class="timestamp">Submitted: {created_str} • Lang: {lang}</span>')
            st.markdown(f"**Name:** {name}")
            st.markdown(f"**Email:** {email}")
            if message:
                st.markdown("**Why join:**")
                st.write(message)

            badge_color = {"Pending": "orange", "Approved": "green", "Rejected": "red", "Unsubscribed": "gray"}.get(status, "blue")
            st.caption(f"Status: :{badge_color}-background[**{status}**] • Subscribed: {subscribed}")

            col_a, col_r, col_u = st.columns(3)
            with col_a:
                if status != "Approved" and st.button("Approve", key=f"approve_{entry['id']}"):
                    try:
                        supabase.table("waitlist").update({"status": "Approved"}).eq("id", entry["id"]).execute()
                        st.toast("Approved!", icon="✅")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Approve failed: {str(e)}")
            with col_r:
                if status != "Rejected" and st.button("Reject", key=f"reject_{entry['id']}"):
                    try:
                        supabase.table("waitlist").update({"status": "Rejected"}).eq("id", entry["id"]).execute()
                        st.toast("Rejected", icon="❌")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Reject failed: {str(e)}")
            with col_u:
                if status != "Unsubscribed" and st.button("Unsubscribe", key=f"unsub_{entry['id']}"):
                    try:
                        supabase.table("waitlist").update({"status": "Unsubscribed", "subscribed": False}).eq("id", entry["id"]).execute()
                        st.toast("Unsubscribed", icon="🗑️")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Unsubscribe failed: {str(e)}")

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('<hr class="thin">', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# MESSAGES TAB
# ────────────────────────────────────────────────
with tab_messages:
    st.subheader("Messages from Approved Clients")

    col_m1, col_m2, col_m3 = st.columns([2.2, 2.5, 1.5])
    with col_m1:
        msg_mode = st.radio("View Mode", ["All Messages", "Inbox (Received)", "Sent", "Unread Only"], horizontal=True, key="msg_mode_select")
    with col_m2:
        msg_search = st.text_input("Search user / message", key="msg_search_input")
    with col_m3:
        msg_page_size = st.number_input("Per page", 10, 100, 20, 5, key="msg_page_size_input")

    @st.cache_data(ttl=8, show_spinner="Loading messages...")
    def fetch_messages(page=1, size=20, mode="All", search=""):
        offset = (page - 1) * size
        uid = st.session_state.get("user_id")

        q = supabase.table("messages").select("""
            id, sender_id, sender_username, receiver_id, receiver_username,
            message, timestamp, is_read
        """).order("timestamp", desc=True)

        if mode == "Inbox (Received)" and uid:
            q = q.eq("receiver_id", uid)
        elif mode == "Sent" and uid:
            q = q.eq("sender_id", uid)
        elif mode == "Unread Only" and uid:
            q = q.eq("receiver_id", uid).eq("is_read", False)

        if search.strip():
            s = search.strip().lower()
            q = q.or_(f"message.ilike.%{s}%,sender_username.ilike.%{s}%,receiver_username.ilike.%{s}%")

        data_resp = q.range(offset, offset + size - 1).execute()
        data = data_resp.data or []

        count_q = supabase.table("messages").select("id", count="exact")
        if mode == "Inbox (Received)" and uid:
            count_q = count_q.eq("receiver_id", uid)
        elif mode == "Sent" and uid:
            count_q = count_q.eq("sender_id", uid)
        elif mode == "Unread Only" and uid:
            count_q = count_q.eq("receiver_id", uid).eq("is_read", False)
        if search.strip():
            count_q = count_q.or_(f"message.ilike.%{s}%,sender_username.ilike.%{s}%,receiver_username.ilike.%{s}%")

        count_resp = count_q.execute()
        total = count_resp.count if count_resp.count is not None else 0

        return data, total

    if "msg_page" not in st.session_state:
        st.session_state.msg_page = 1

    msg_data, msg_total = fetch_messages(
        page=st.session_state.msg_page,
        size=msg_page_size,
        mode=msg_mode,
        search=msg_search
    )

    msg_total_pages = max(1, (msg_total + msg_page_size - 1) // msg_page_size)

    col_mp1, col_mp2, col_mp3 = st.columns([1, 5, 1])
    with col_mp1:
        if st.button("← Prev", disabled=st.session_state.msg_page <= 1, key="msg_prev_btn"):
            st.session_state.msg_page -= 1
            st.rerun()
    with col_mp2:
        st.markdown(f"**Page {st.session_state.msg_page} / {msg_total_pages}**  •  {msg_total:,} messages")
    with col_mp3:
        if st.button("Next →", disabled=st.session_state.msg_page >= msg_total_pages, key="msg_next_btn"):
            st.session_state.msg_page += 1
            st.rerun()

    if not msg_data:
        st.info("No messages match the filters.")
    else:
        for msg in msg_data:
            ts_raw = msg.get("timestamp")
            ts_str = "—"
            if ts_raw:
                try:
                    dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                    ts_str = dt.strftime("%b %d, %Y %I:%M %p")
                except:
                    ts_str = ts_raw[:19].replace("T", " ")

            sender = msg.get("sender_username", "Unknown")
            receiver = msg.get("receiver_username", "—")
            content = msg.get("message", "").strip()
            is_read = msg.get("is_read", False)

            card_class = f"card {'unread' if not is_read else 'read'}"

            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<span class="timestamp">{ts_str}</span>')
            st.markdown(f"**{sender}** → **{receiver}**")
            st.write(content)

            col_read, col_reply, col_send = st.columns([1.3, 3.5, 1.2])
            with col_read:
                if not is_read and st.button("Mark Read", key=f"msg_read_{msg['id']}"):
                    try:
                        supabase.table("messages").update({"is_read": True}).eq("id", msg["id"]).execute()
                        st.toast("Marked as read", icon="✅")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

            with col_reply:
                reply_key = f"msg_reply_{msg['id']}"
                reply_text = st.text_input("", placeholder="Quick reply...", key=reply_key, label_visibility="collapsed")

            with col_send:
                if st.button("Send", key=f"msg_send_{msg['id']}") and reply_text.strip():
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
                        time.sleep(0.6)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Send failed: {str(e)}")

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('<hr class="thin">', unsafe_allow_html=True)

# ─── OPTIONAL GLOBAL REFRESH ───
if st.toggle("Auto-refresh every 15s (both tabs)", value=False, key="global_auto"):
    time.sleep(15)
    st.rerun()