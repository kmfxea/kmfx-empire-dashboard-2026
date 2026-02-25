# pages/📢_Announcements.py
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
require_auth(min_role="client")  # everyone sees feed, owner/admin can post/delete/pin

# ─── THEME ───
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
st.markdown("**Central realtime communication** • Broadcast updates • Rich images/attachments • Likes ❤️ • Threaded comments 💬 • Pinning 📌 • Search & filters")

current_role = st.session_state.get("role", "guest").lower()

# ─── ULTRA-REALTIME FETCH (10s TTL) ───
@st.cache_data(ttl=10, show_spinner="Syncing empire feed...")
def fetch_announcements_realtime():
    try:
        ann_resp = supabase.table("announcements").select("*").order("date", desc=True).execute()
        announcements = ann_resp.data or []

        # Attachments – try public URL first, then fresh signed
        for ann in announcements:
            att_resp = supabase.table("announcement_files").select(
                "id, original_name, storage_path, file_url"
            ).eq("announcement_id", ann["id"]).execute()
            attachments = []
            for att in att_resp.data or []:
                public_url = att.get("file_url")  # direct public URL if bucket public
                signed_url = None

                if not public_url and att.get("storage_path"):
                    try:
                        signed = supabase.storage.from_("announcements").create_signed_url(
                            att["storage_path"], expires_in=3600 * 24  # 24 hours - fresh every load
                        )
                        signed_url = signed.signed_url
                        # Temporary debug - comment out after testing
                        # st.write(f"Generated signed URL for {att['original_name']}: {signed_url}")
                    except Exception as sign_err:
                        st.warning(f"Signed URL failed for {att['original_name']}: {str(sign_err)}")

                attachments.append({
                    "id": att["id"],
                    "original_name": att["original_name"],
                    "storage_path": att["storage_path"],
                    "public_url": public_url,
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

st.caption("🔄 Feed auto-refreshes every 10s • Images & attachments fully visible")

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
                with st.spinner("Posting announcement..."):
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
                                except Exception as upload_err:
                                    st.warning(f"Attachment {file.name} failed: {str(upload_err)}")
                                progress.progress((idx + 1) / len(attachments))
                            progress.empty()

                        st.success("Announcement broadcasted! Visible to entire empire.")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Post failed: {str(e)}")

# ─── SEARCH & FILTER ───
st.subheader("🔍 Search & Filter Feed")
col_s1, col_s2 = st.columns(2)
with col_s1:
    search = st.text_input("Search title or message", placeholder="e.g. profit update")
with col_s2:
    cat_filter = st.selectbox("Category", ["All"] + sorted(set(a.get("category", "General") for a in announcements if a.get("category"))))

filtered = announcements
if cat_filter != "All":
    filtered = [a for a in filtered if a.get("category") == cat_filter]
if search:
    s = search.lower()
    filtered = [a for a in filtered if s in a["title"].lower() or s in a["message"].lower()]

# Sort: pinned first, then newest
filtered = sorted(filtered, key=lambda x: (not x.get("pinned", False), x["date"]), reverse=True)

# ─── RICH FEED DISPLAY ───
st.subheader(f"📻 Live Empire Feed ({len(filtered)} posts)")
if filtered:
    for ann in filtered:
        pinned_tag = " 📌 PINNED" if ann.get("pinned") else ""
        with st.container(border=True):
            st.markdown(f"<h3 style='color:{accent_primary}; margin-bottom:0.5rem;'>{ann['title']}{pinned_tag}</h3>", unsafe_allow_html=True)
            st.caption(f"{ann.get('category', 'General')} • by {ann['posted_by']} • {ann['date']}")
            st.markdown(ann['message'])

            # Attachments: try public first, then fresh signed, then bytes load
            images = [att for att in ann.get("attachments", []) if att["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif'))]
            if images:
                img_cols = st.columns(min(4, len(images)))
                for i, att in enumerate(images):
                    url = att.get("public_url") or att.get("signed_url")
                    if url:
                        with img_cols[i % 4]:
                            try:
                                r = requests.get(url, timeout=10)
                                if r.status_code == 200:
                                    st.image(r.content, use_column_width=True, caption=att["original_name"])
                                else:
                                    st.caption(f"{att['original_name']} (status {r.status_code})")
                                    # Debug
                                    st.write("Failed URL:", url)
                            except Exception as load_err:
                                st.caption(f"{att['original_name']} (load error)")
                                st.write("Load error:", str(load_err))
                    else:
                        st.caption(f"Image failed to load: {att['original_name']}")

            # Other files (downloadable)
            non_images = [att for att in ann.get("attachments", []) if not att["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif'))]
            if non_images:
                st.markdown("**Attached Files:**")
                for att in non_images:
                    url = att.get("public_url") or att.get("signed_url")
                    if url:
                        try:
                            r = requests.get(url, timeout=10)
                            if r.status_code == 200:
                                st.download_button(
                                    label=att["original_name"],
                                    data=r.content,
                                    file_name=att["original_name"],
                                    mime="application/octet-stream",
                                    use_container_width=True,
                                    key=f"dl_ann_{ann['id']}_{att['id']}"
                                )
                            else:
                                st.caption(f"{att['original_name']} (status {r.status_code})")
                        except:
                            st.caption(f"{att['original_name']} (download failed)")
                    else:
                        st.caption(att["original_name"])

            # Likes
            like_key = f"like_{ann['id']}"
            if st.button(f"❤️ {ann.get('likes', 0)}", key=like_key):
                supabase.table("announcements").update({"likes": ann.get('likes', 0) + 1}).eq("id", ann["id"]).execute()
                st.cache_data.clear()
                st.rerun()

            # Comments
            with st.expander(f"💬 Comments ({len(ann.get('comments', []))})"):
                for c in ann.get("comments", []):
                    ts = c["timestamp"][:16].replace("T", " ")
                    st.markdown(f"**{c['user_name']}** • {ts}")
                    st.markdown(c["message"])
                    st.divider()

                with st.form(key=f"comment_{ann['id']}"):
                    comment_text = st.text_area("Add your comment...", height=80, label_visibility="collapsed")
                    if st.form_submit_button("Post Comment"):
                        if comment_text.strip():
                            supabase.table("announcement_comments").insert({
                                "announcement_id": ann["id"],
                                "user_name": st.session_state.get("full_name", "Member"),
                                "message": comment_text.strip(),
                                "timestamp": datetime.now().isoformat()
                            }).execute()
                            st.cache_data.clear()
                            st.rerun()

            # Admin controls
            if current_role in ["owner", "admin"]:
                col_pin, col_del = st.columns(2)
                with col_pin:
                    if st.button("📌 Pin / Unpin", key=f"pin_{ann['id']}"):
                        supabase.table("announcements").update({"pinned": not ann.get("pinned", False)}).eq("id", ann["id"]).execute()
                        st.cache_data.clear()
                        st.rerun()
                with col_del:
                    if st.button("🗑️ Delete Announcement", key=f"del_{ann['id']}", type="secondary"):
                        try:
                            # Clean storage
                            for att in ann.get("attachments", []):
                                if att.get("storage_path"):
                                    try:
                                        supabase.storage.from_("announcements").remove([att["storage_path"]])
                                    except:
                                        pass
                            # Delete DB
                            supabase.table("announcement_files").delete().eq("announcement_id", ann["id"]).execute()
                            supabase.table("announcement_comments").delete().eq("announcement_id", ann["id"]).execute()
                            supabase.table("announcements").delete().eq("id", ann["id"]).execute()
                            st.success("Announcement deleted permanently")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {str(e)}")

            st.divider()
else:
    st.info("No announcements yet • Empire feed is ready for your broadcast!")

# ─── MOTIVATIONAL FOOTER ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Realtime Empire Communication Hub
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Broadcasts • Likes • Comments • Pinned updates • Permanent attachments • Full team sync
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Connected for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)