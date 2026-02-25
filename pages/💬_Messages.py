# pages/💬_Messages.py
import streamlit as st
from datetime import datetime

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="client")  # everyone can message, admin has multi-client view

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

st.header("💬 Private Messages")
st.markdown("**Secure 1:1 communication** • File attachments with inline previews • Search • Balance context • Realtime updates • Empire private channel")

current_role = st.session_state.get("role", "guest").lower()
my_name = st.session_state.get("full_name", "User")

# ─── REALTIME FETCH (6s TTL for chat feel) ───
@st.cache_data(ttl=6, show_spinner="Syncing messages...")
def fetch_messages_data():
    try:
        users = supabase.table("users").select("id, full_name, role, balance").execute().data or []
        messages = supabase.table("messages").select(
            "id, message, timestamp, from_admin, from_client, to_client"
        ).order("timestamp", desc=False).execute().data or []  # oldest first
        return users, messages
    except Exception as e:
        st.error(f"Messages sync error: {str(e)}")
        return [], []

all_users, all_messages = fetch_messages_data()

if st.button("🔄 Refresh Messages", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ─── NAME & BALANCE MAPS ───
name_by_id = {str(u["id"]): u["full_name"] for u in all_users}
balance_by_name = {u["full_name"]: u.get("balance", 0) for u in all_users}

# ─── DETERMINE CONVERSATION PARTNER ───
if current_role in ["owner", "admin"]:
    client_names = [u["full_name"] for u in all_users if u["role"] == "client"]
    if not client_names:
        st.info("No clients yet • Messaging activates once team members are added")
        st.stop()

    client_options = {
        f"{name} (Balance: ${balance_by_name.get(name, 0):,.2f})": name
        for name in sorted(client_names)
    }
    selected_display = st.selectbox(
        "Chat with team member",
        options=list(client_options.keys()),
        index=0
    )
    partner_name = client_options[selected_display]
    partner_balance = balance_by_name.get(partner_name, 0)
    st.info(f"**Chatting with:** {partner_name} • Balance: **${partner_balance:,.2f}**")

    # Filter messages for this partner (admin ↔ client)
    convo = [
        m for m in all_messages
        if (m.get("from_client") == partner_name and m.get("to_client") is None) or
           (m.get("from_admin") == my_name and m.get("to_client") == partner_name) or
           (m.get("from_client") == partner_name and m.get("to_client") == my_name)
    ]
else:  # Client view — always with admin/system
    partner_name = "KMFX Admin"
    partner_balance = None
    st.info("**Private channel with KMFX Admin** • Updates on profits, withdrawals, licenses, etc.")
    convo = [
        m for m in all_messages
        if (m.get("from_client") == my_name) or
           (m.get("to_client") == my_name)
    ]

# ─── CHAT DISPLAY ───
if convo:
    search_term = st.text_input("Search messages", "", placeholder="Type to filter...")
    display_msgs = convo
    if search_term:
        s = search_term.lower()
        display_msgs = [m for m in convo if s in m["message"].lower()]

    chat_container = st.container()
    with chat_container:
        for msg in display_msgs:
            # Determine sender & direction
            if current_role in ["owner", "admin"]:
                is_from_me = msg.get("from_admin") == my_name
                sender_name = my_name if is_from_me else (msg.get("from_client") or "System")
            else:
                is_from_me = msg.get("from_client") == my_name
                sender_name = my_name if is_from_me else "KMFX Admin"

            align = "flex-end" if is_from_me else "flex-start"
            bubble_bg = accent_primary + "30" if is_from_me else "#2d3748"
            text_color = "#000000" if is_from_me else "#e2e8f0"
            time_str = msg["timestamp"][:16].replace("T", " ")

            st.markdown(
                f"""
                <div style="
                    display: flex;
                    justify-content: {align};
                    margin: 1.2rem 0;
                ">
                    <div style="
                        background: {bubble_bg};
                        color: {text_color};
                        padding: 1rem 1.4rem;
                        border-radius: 18px;
                        max-width: 75%;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    ">
                        <div style="font-weight: 600; margin-bottom: 0.3rem;">{sender_name}</div>
                        <div style="font-size: 0.8rem; opacity: 0.7; margin-bottom: 0.5rem;">{time_str}</div>
                        {msg['message'].replace('\n', '<br>')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Auto-scroll attempt (better targeting)
    st.markdown(
        """
        <script>
        const containers = window.parent.document.querySelectorAll('.stContainer');
        if (containers.length > 0) {
            containers[containers.length - 1].scrollIntoView({behavior: 'smooth', block: 'end'});
        }
        </script>
        """,
        unsafe_allow_html=True
    )

    st.caption(f"{len(convo)} message{'s' if len(convo) != 1 else ''} • newest at bottom")
else:
    st.info("No messages yet • Start the conversation below ↓")

# ─── SEND MESSAGE FORM ───
st.subheader("Send a Message")
with st.form("send_message_form", clear_on_submit=True):
    col_msg, col_file = st.columns([4, 3])
    with col_msg:
        new_message = st.text_area(
            "Your message...",
            height=110,
            placeholder="Type here...",
            label_visibility="collapsed"
        )
    with col_file:
        attached_files = st.file_uploader(
            "Attach images / files (visible inline)",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "gif", "pdf", "txt", "docx"]
        )

    submitted = st.form_submit_button("Send →", type="primary", use_container_width=True)

    if submitted:
        if not new_message.strip() and not attached_files:
            st.error("Write a message or attach at least one file")
        else:
            with st.spinner("Sending message..."):
                try:
                    content_parts = [new_message.strip()] if new_message.strip() else []

                    # Handle attachments
                    if attached_files:
                        for file in attached_files:
                            try:
                                url, _ = upload_to_supabase(  # assuming helper exists
                                    file=file,
                                    bucket="messages",
                                    folder="chat_attachments",
                                    use_signed_url=False  # public for inline visibility
                                )
                                if file.type.startswith("image/"):
                                    content_parts.append(f"![{file.name}]({url})")
                                else:
                                    content_parts.append(f"[{file.name}]({url})")
                            except Exception as upload_err:
                                st.warning(f"Upload failed for {file.name}: {upload_err}")

                    final_content = "\n\n".join(content_parts) or "📎 Attachment only"

                    # Prepare insert
                    insert_row = {
                        "message": final_content,
                        "timestamp": datetime.now().isoformat()
                    }

                    if current_role in ["owner", "admin"]:
                        insert_row["from_admin"] = my_name
                        insert_row["to_client"] = partner_name
                    else:
                        insert_row["from_client"] = my_name
                        # to_admin implicit or add "to_admin": "KMFX Admin" if needed

                    supabase.table("messages").insert(insert_row).execute()

                    st.success("Message sent!")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to send: {str(e)}")

st.caption("ℹ️ Auto-messages (profits, withdrawals, licenses, etc.) appear here automatically.")

# ─── MOTIVATIONAL FOOTER (sync style) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Secure Private Communication • Empire Connected
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Realtime 1:1 • Attachments with previews • Auto-updates • Balance context • Always private
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Protected for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)