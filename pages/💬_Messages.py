# pages/09_💬_Messages.py
import streamlit as st
import pandas as pd
from datetime import datetime
import requests

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase, log_action

require_auth()  # Lahat authenticated, pero role-based chat logic

st.header("Private Messages 💬")
st.markdown("**Secure 1:1 communication • File attachments with inline previews • Search • Balance context • Realtime updates**")

current_role = st.session_state.get("role", "guest")
my_name = st.session_state.full_name

# ────────────────────────────────────────────────
# REALTIME DATA FETCH (6s TTL para sa chat feel)
# ────────────────────────────────────────────────
@st.cache_data(ttl=6)
def fetch_messages_data():
    try:
        # Users for mapping & client list
        users_resp = supabase.table("users").select("id, full_name, role, balance").execute()
        users = users_resp.data or []

        # Messages (oldest first para chronological)
        msg_resp = supabase.table("messages").select(
            "id, message, timestamp, from_admin, from_client, to_client"
        ).order("timestamp", desc=False).execute()
        messages = msg_resp.data or []

        name_by_id = {str(u["id"]): u["full_name"] for u in users}
        balance_by_name = {u["full_name"]: u.get("balance", 0.0) for u in users}

        return users, messages, name_by_id, balance_by_name
    except Exception as e:
        st.error(f"Messages load error: {str(e)}")
        return [], [], {}, {}

all_users, all_messages, name_by_id, balance_by_name = fetch_messages_data()

if st.button("🔄 Refresh Messages", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Messages refresh every 6s • Attachments fully visible")

# ────────────────────────────────────────────────
# Determine chat partner
# ────────────────────────────────────────────────
partner_name = None
partner_balance = None

if current_role in ["owner", "admin"]:
    client_names = [u["full_name"] for u in all_users if u["role"] == "client"]
    if not client_names:
        st.info("No clients yet • Messaging activates once team members are added")
        st.stop()

    client_options = {
        f"{name} (Balance: ${balance_by_name.get(name, 0.0):,.2f})": name
        for name in sorted(client_names)
    }

    selected_key = st.selectbox(
        "Chat with team member",
        options=list(client_options.keys()),
        index=0
    )
    partner_name = client_options[selected_key]
    partner_balance = balance_by_name.get(partner_name, 0.0)
    st.info(f"**Chatting with:** {partner_name} • Balance: **${partner_balance:,.2f}**")

else:  # Client view — fixed to admin
    partner_name = "KMFX Admin"
    st.info("**Private channel with KMFX Admin** • Updates on profits, withdrawals, licenses, etc.")

# ────────────────────────────────────────────────
# Filter conversation
# ────────────────────────────────────────────────
convo = []
if current_role in ["owner", "admin"]:
    convo = [
        m for m in all_messages
        if (m.get("from_client") == partner_name and m.get("to_client") is None) or
           (m.get("from_admin") == my_name and m.get("to_client") == partner_name) or
           (m.get("from_client") == partner_name and m.get("to_client") == my_name)
    ]
else:
    convo = [
        m for m in all_messages
        if (m.get("from_client") == my_name) or
           (m.get("to_client") == my_name)
    ]

# ────────────────────────────────────────────────
# Chat Display with Auto-Scroll
# ────────────────────────────────────────────────
st.subheader("Conversation")
if convo:
    search_term = st.text_input("Search messages", "")
    display_msgs = convo
    if search_term:
        s = search_term.lower()
        display_msgs = [m for m in convo if s in m["message"].lower()]

    chat_container = st.container(height=500)  # Fixed height for better scroll
    with chat_container:
        for msg in display_msgs:
            # Direction & sender
            if current_role in ["owner", "admin"]:
                is_from_me = msg.get("from_admin") == my_name
                sender = my_name if is_from_me else (msg.get("from_client") or "System")
            else:
                is_from_me = msg.get("from_client") == my_name
                sender = my_name if is_from_me else "KMFX Admin"

            align = "flex-end" if is_from_me else "flex-start"
            bubble_bg = "#00ffaa" if is_from_me else "#2d3748"
            text_color = "#000000" if is_from_me else "#e2e8f0"
            time_str = msg["timestamp"][:16].replace("T", " ")

            st.markdown(
                f"""
                <div style="
                    display: flex;
                    justify-content: {align};
                    margin: 1rem 0;
                ">
                    <div style="
                        background: {bubble_bg};
                        color: {text_color};
                        padding: 1rem 1.5rem;
                        border-radius: 20px;
                        max-width: 75%;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    ">
                        <div style="font-weight: 600; margin-bottom: 0.3rem;">{sender}</div>
                        <div style="font-size: 0.85rem; opacity: 0.7; margin-bottom: 0.5rem;">{time_str}</div>
                        {msg['message'].replace('\n', '<br>')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Auto-scroll script
    st.markdown(
        """
        <script>
        const chat = window.parent.document.querySelector('.stChatMessage, .stContainer')?.lastElementChild;
        if (chat) chat.scrollIntoView({behavior: 'smooth', block: 'end'});
        </script>
        """,
        unsafe_allow_html=True
    )
else:
    st.info("No messages yet • Start the conversation below ↓")

# ────────────────────────────────────────────────
# SEND MESSAGE FORM
# ────────────────────────────────────────────────
st.subheader("Send Message")
with st.form("send_message_form", clear_on_submit=True):
    col_msg, col_attach = st.columns([3, 2])
    with col_msg:
        new_message = st.text_area(
            "Type your message...",
            height=120,
            placeholder="Write here...",
            label_visibility="collapsed"
        )
    with col_attach:
        attached_files = st.file_uploader(
            "Attach files/images",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "gif", "pdf", "txt", "docx"]
        )

    submitted = st.form_submit_button("Send →", type="primary", use_container_width=True)

    if submitted:
        if not new_message.strip() and not attached_files:
            st.error("Please write a message or attach a file")
        else:
            with st.spinner("Sending..."):
                try:
                    content_parts = [new_message.strip()] if new_message.strip() else []

                    # Attachments
                    if attached_files:
                        for file in attached_files:
                            try:
                                url, _ = upload_to_supabase(
                                    file=file,
                                    bucket="messages",
                                    folder="chat_attachments"
                                )
                                if file.type.startswith("image/"):
                                    content_parts.append(f"![{file.name}]({url})")
                                else:
                                    content_parts.append(f"[{file.name}]({url})")
                            except Exception as e:
                                st.warning(f"Upload failed for {file.name}: {str(e)}")

                    final_message = "\n\n".join(content_parts) or "📎 Attachment only"

                    # Insert logic
                    insert_data = {
                        "message": final_message,
                        "timestamp": datetime.now().isoformat()
                    }
                    if current_role in ["owner", "admin"]:
                        insert_data["from_admin"] = my_name
                        insert_data["to_client"] = partner_name
                    else:
                        insert_data["from_client"] = my_name
                        # to_admin implicit or add "to_admin": "KMFX Admin"

                    supabase.table("messages").insert(insert_data).execute()
                    log_action("Message Sent", f"{'To ' + partner_name if current_role in ['owner','admin'] else 'From client'}")

                    st.success("Message sent successfully!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Send failed: {str(e)}")

st.caption("ℹ️ System messages (profits, withdrawals, licenses) appear here automatically.")