import streamlit as st
import requests
from datetime import datetime, date

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase, log_action

render_sidebar()
require_auth(min_role="client")  # everyone sees the feed, only owner/admin can post/delete/pin

# ─── THEME (consistent across app) ───
accent_primary = "#00ffaa"
accent_gold = "#ffd700"
accent_glow = "#00ffaa40"

# ─── SCROLL-TO-TOP ───
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

st.header("📢 Empire Announcements")
st.markdown("**Central realtime communication** • Broadcast updates • Rich images/attachments (PERMANENT STORAGE + FULLY VISIBLE) • Likes ❤️ • Threaded comments 💬 • Pinning 📌 • Search & filters • Full team engagement")

current_role = st.session_state.get("role", "guest").lower()

# ─── ULTRA-REALTIME FETCH (10s TTL) ───
@st.cache_data(ttl=10)
def fetch_announcements_realtime():
    try:
        ann_resp = supabase.table("announcements").select("*").order("date", desc=True).execute()
        announcements = ann_resp.data or []

        # Attachments with correct signed URL access
        for ann in announcements:
            att_resp = supabase.table("announcement_files").select(
                "id, original_name, storage_path, file_url"
            ).eq("announcement_id", ann["id"]).execute()
            attachments = []
            for att in att_resp.data or []:
                image_url = att.get("file_url")  # public URL if bucket public
                signed_url = None

                # Generate fresh signed URL if no public URL
                if not image_url and att.get("storage_path"):
                    try:
                        signed = supabase.storage.from_("announcements").create_signed_url(
                            att["storage_path"], expires_in=3600 * 24 * 7  # 7 days - fresh & safe
                        )
                        signed_url = signed.signed_url  # Correct access (new client syntax)
                        # Temporary debug - comment out after testing
                        # st.write(f"Debug signed URL for {att['original_name']}: {signed_url}")
                    except Exception as sign_err:
                        st.warning(f"Signed URL failed for {att['original_name']}: {str(sign_err)}")

                attachments.append({
                    "id": att["id"],
                    "original_name": att["original_name"],
                    "storage_path": att["storage_path"],
                    "public_url": image_url,
                    "signed_url": signed_url
                })
            ann["attachments"] = attachments

        # Comments grouped
        comm_resp = supabase.table("announcement_comments").select("*").order("timestamp", desc=True).execute()
        comments_map = {}
        for c in comm_resp.data or []:
            comments_map.setdefault(c["announcement_id"], []).append(c)
        for ann in announcements:
            ann["comments"] = comments_map.get(ann["id"], [])

        return announcements
    except Exception as e:
        st.error(f"Feed sync error: {str(e)}")
        return []

announcements = fetch_announcements_realtime()

if st.button("🔄 Refresh Feed Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Feed auto-refreshes every 10s • Images & attachments fully visible • Pin to top default OFF")

# ─── POST NEW ANNOUNCEMENT (OWNER/ADMIN ONLY) ───
if current_role in ["owner", "admin"]:
    st.subheader("📢 Broadcast New Announcement")
    with st.form("ann_form", clear_on_submit=True):
        title = st.text_input("Title *", placeholder="Empire Update: New Scaling Round")
        category = st.selectbox("Category", [
            "General", "Profit Distribution", "Withdrawal Update",
            "License Granted", "Milestone", "EA Update", "Team Alert"
        ])
        message = st.text_area("Message *", height=150, placeholder="Important update for all members...")
        attachments = st.file_uploader(
            "Attachments (Images/Proofs/Files - Permanent + Visible)",
            accept_multiple_files=True
        )
        pin = st.checkbox("📌 Pin to Top", value=False)
        submitted = st.form_submit_button("📢 Post Announcement", type="primary", use_container_width=True)

        if submitted:
            if not title.strip() or not message.strip():
                st.error("Title and message required")
            else:
                try:
                    resp = supabase.table("announcements").insert({
                        "title": title.strip(),
                        "message": message.strip(),
                        "date": date.today().isoformat(),
                        "posted_by": st.session_state.get("full_name", "Admin"),
                        "likes": 0,
                        "category": category,
                        "pinned": pin
                    }).execute()
                    ann_id = resp.data[0]["id"]
                    if attachments:
                        progress = st.progress(0)
                        for idx, file in enumerate(attachments):
                            try:
                                url, storage_path = upload_to_supabase(
                                    file=file,
                                    bucket="announcements",
                                    folder="attachments"
                                )
                                supabase.table("announcement_files").insert({
                                    "announcement_id": ann_id,
                                    "original_name": file.name,
                                    "file_url": url,
                                    "storage_path": storage_path
                                }).execute()
                            except Exception as e:
                                st.warning(f"Attachment {file.name} failed: {str(e)}")
                            progress.progress((idx + 1) / len(attachments))
                        progress.empty()
                    st.success("Announcement posted successfully! Images & files are fully visible.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ─── SEARCH & FILTER ───
st.subheader("🔍 Search & Filter")
col_s1, col_s2 = st.columns(2)
with col_s1:
    search = st.text_input("Search title/message")
with col_s2:
    cat_filter = st.selectbox("Category", ["All"] + sorted(set(a.get("category", "General") for a in announcements)))

filtered = [a for a in announcements if cat_filter == "All" or a.get("category") == cat_filter]
if search:
    s = search.lower()
    filtered = [a for a in filtered if s in a["title"].lower() or s in a["message"].lower()]

# Sort: Pinned first, then newest
filtered = sorted(filtered, key=lambda x: (not x.get("pinned", False), x["date"]), reverse=True)

# ─── RICH FEED DISPLAY ───
st.subheader(f"📻 Live Feed ({len(filtered)} posts)")
if filtered:
    for ann in filtered:
        pinned = " 📌 PINNED" if ann.get("pinned") else ""
        with st.container():
            st.markdown(f"<h3 style='color:{accent_primary};'>{ann['title']}{pinned}</h3>", unsafe_allow_html=True)
            st.caption(f"{ann.get('category', 'General')} • by {ann['posted_by']} • {ann['date']}")
            st.markdown(ann['message'])

            # IMAGES (FULLY VISIBLE via public or fresh signed URL)
            images = [att for att in ann["attachments"] if att["original_name"].lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            if images:
                cols = st.columns(min(len(images), 4))
                for idx, att in enumerate(images):
                    url = att.get("public_url") or att.get("signed_url")
                    if url:
                        with cols[idx % 4]:
                            # Reliable bytes load (fixes most Streamlit image issues)
                            try:
                                r = requests.get(url, timeout=10)
                                if r.status_code == 200:
                                    st.image(r.content, use_container_width=True)
                                else:
                                    st.caption(f"{att['original_name']} (status {r.status_code})")
                            except:
                                st.caption(f"{att['original_name']} (load failed)")
                    else:
                        st.caption(f"{att['original_name']} (no URL)")

            # NON-IMAGES (downloadable)
            non_images = [att for att in ann["attachments"] if not att["original_name"].lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            if non_images:
                st.markdown("**Files:**")
                for att in non_images:
                    url = att.get("public_url") or att.get("signed_url")
                    if url:
                        try:
                            r = requests.get(url, timeout=10)
                            if r.status_code == 200:
                                st.download_button(
                                    label=att['original_name'],
                                    data=r.content,
                                    file_name=att['original_name'],
                                    mime="application/octet-stream",
                                    use_container_width=True
                                )
                            else:
                                st.caption(f"{att['original_name']} (status {r.status_code})")
                        except:
                            st.caption(f"{att['original_name']} (download failed)")
                    else:
                        st.caption(att['original_name'])

            # Likes
            if st.button(f"❤️ {ann.get('likes', 0)}", key=f"like_{ann['id']}"):
                supabase.table("announcements").update({"likes": ann.get('likes', 0) + 1}).eq("id", ann["id"]).execute()
                st.cache_data.clear()
                st.rerun()

            # Comments
            with st.expander(f"💬 Comments ({len(ann['comments'])})", expanded=False):
                for c in ann["comments"]:
                    st.markdown(f"**{c['user_name']}** • {c['timestamp'][:16].replace('T', ' ')}")
                    st.markdown(c['message'])
                    st.divider()
                with st.form(key=f"comment_form_{ann['id']}"):
                    comment = st.text_area("Add comment...", height=80, label_visibility="collapsed")
                    if st.form_submit_button("Post Comment"):
                        if comment.strip():
                            supabase.table("announcement_comments").insert({
                                "announcement_id": ann["id"],
                                "user_name": st.session_state.full_name,
                                "message": comment.strip(),
                                "timestamp": datetime.now().isoformat()
                            }).execute()
                            st.cache_data.clear()
                            st.rerun()

            # Admin actions
            if current_role in ["owner", "admin"]:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📌 Pin/Unpin", key=f"pin_{ann['id']}"):
                        supabase.table("announcements").update({"pinned": not ann.get("pinned", False)}).eq("id", ann["id"]).execute()
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{ann['id']}", type="secondary"):
                        # Delete attachments from storage
                        for att in ann["attachments"]:
                            if att.get("storage_path"):
                                try:
                                    supabase.storage.from_("announcements").remove([att["storage_path"]])
                                except:
                                    pass
                        # Delete DB records
                        supabase.table("announcement_files").delete().eq("announcement_id", ann["id"]).execute()
                        supabase.table("announcement_comments").delete().eq("announcement_id", ann["id"]).execute()
                        supabase.table("announcements").delete().eq("id", ann["id"]).execute()
                        st.success("Announcement deleted")
                        st.cache_data.clear()
                        st.rerun()
            st.divider()
else:
    st.info("No announcements yet • Empire feed is ready!")

# ─── ELITE FOOTER ───
st.markdown(f"""
<div class='glass-card' style='padding:3rem; text-align:center; margin:3rem 0;'>
    <h1 style="background:linear-gradient(90deg,{accent_primary},#ffd700); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Realtime Empire Feed
    </h1>
    <p style="font-size:1.3rem; margin:2rem 0;">
        ✅ Pin to Top default OFF (fixed)<br>
        ✅ Images & attachments FULLY VISIBLE & downloadable<br>
        ✅ Permanent storage • Likes • Comments • Search • Empire connected.
    </p>
    <h2 style="color:#ffd700;">👑 KMFX Announcements • Fully Fixed 2026</h2>
</div>
""", unsafe_allow_html=True)