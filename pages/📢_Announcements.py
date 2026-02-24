# pages/08_📢_Announcements.py
import streamlit as st
import pandas as pd
from datetime import datetime
import requests

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase, log_action

require_auth()  # Lahat pwede magbasa/like/comment, pero post/delete para sa admin/owner

st.header("Empire Announcements 📢")
st.markdown("**Central realtime communication: Broadcast updates • Rich images/attachments (permanent + visible) • Likes • Comments • Pinning • Search & filters**")

current_role = st.session_state.get("role", "guest")
current_user = st.session_state.full_name

# ────────────────────────────────────────────────
# REALTIME CACHE (10s) + Signed URLs
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_announcements_realtime():
    try:
        ann_resp = supabase.table("announcements").select("*").order("date", desc=True).execute()
        announcements = ann_resp.data or []

        # Attachments with signed URLs (30 days)
        for ann in announcements:
            att_resp = supabase.table("announcement_files").select(
                "id, original_name, storage_path"
            ).eq("announcement_id", ann["id"]).execute()
            attachments = []
            for att in att_resp.data or []:
                signed_url = None
                if att.get("storage_path"):
                    try:
                        signed = supabase.storage.from_("announcements").create_signed_url(
                            att["storage_path"], 3600 * 24 * 30  # 30 days
                        )
                        signed_url = signed.get("signedURL")
                    except:
                        pass
                attachments.append({
                    "id": att["id"],
                    "original_name": att["original_name"],
                    "signed_url": signed_url
                })
            ann["attachments"] = attachments

        # Comments
        comm_resp = supabase.table("announcement_comments").select("*").order("timestamp", desc=True).execute()
        comments_map = {}
        for c in comm_resp.data or []:
            comments_map.setdefault(c["announcement_id"], []).append(c)
        for ann in announcements:
            ann["comments"] = comments_map.get(ann["id"], [])

        return announcements
    except Exception as e:
        st.error(f"Announcements load error: {str(e)}")
        return []

announcements = fetch_announcements_realtime()

if st.button("🔄 Refresh Feed Now", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Feed auto-refreshes every 10s • Pin to top default OFF • Attachments fully visible")

# ────────────────────────────────────────────────
# POST NEW ANNOUNCEMENT (ADMIN/OWNER ONLY)
# ────────────────────────────────────────────────
if current_role in ["owner", "admin"]:
    st.subheader("📢 Broadcast New Announcement")
    with st.form("ann_form", clear_on_submit=True):
        title = st.text_input("Title *")
        category = st.selectbox("Category", [
            "General", "Profit Distribution", "Withdrawal Update",
            "License Update", "Milestone Achieved", "EA Version Release",
            "Team Alert", "Motivation", "Other"
        ])
        message = st.text_area("Message *", height=180)
        attachments = st.file_uploader(
            "Attachments (Images/Files - Permanent & Visible)",
            accept_multiple_files=True
        )
        pin = st.checkbox("📌 Pin to Top (show at the very top)", value=False)

        submitted = st.form_submit_button("📢 Post Announcement", type="primary", use_container_width=True)

        if submitted:
            if not title.strip() or not message.strip():
                st.error("Title and message are required")
            else:
                try:
                    resp = supabase.table("announcements").insert({
                        "title": title.strip(),
                        "message": message.strip(),
                        "date": datetime.now().isoformat(),
                        "posted_by": current_user,
                        "likes": 0,
                        "category": category,
                        "pinned": pin
                    }).execute()
                    ann_id = resp.data[0]["id"]

                    if attachments:
                        progress = st.progress(0)
                        for idx, file in enumerate(attachments):
                            try:
                                url, path = upload_to_supabase(
                                    file=file,
                                    bucket="announcements",
                                    folder="attachments"
                                )
                                supabase.table("announcement_files").insert({
                                    "announcement_id": ann_id,
                                    "original_name": file.name,
                                    "file_url": url,
                                    "storage_path": path
                                }).execute()
                            except Exception as e:
                                st.warning(f"Attachment {file.name} failed: {str(e)}")
                            progress.progress((idx + 1) / len(attachments))
                        progress.empty()

                    st.success("Announcement posted! Everyone can see it realtime.")
                    log_action("Posted Announcement", f"Title: {title}")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Post failed: {str(e)}")

# ────────────────────────────────────────────────
# SEARCH & FILTER
# ────────────────────────────────────────────────
st.subheader("🔍 Search & Filter")
col_s1, col_s2 = st.columns(2)
with col_s1:
    search = st.text_input("Search title or message", "")
with col_s2:
    cat_filter = st.selectbox("Category", ["All"] + sorted(set(a.get("category", "General") for a in announcements)))

filtered = announcements
if cat_filter != "All":
    filtered = [a for a in filtered if a.get("category") == cat_filter]
if search:
    s = search.lower()
    filtered = [a for a in filtered if s in a["title"].lower() or s in a["message"].lower()]

# Sort: pinned first, then newest
filtered = sorted(filtered, key=lambda x: (not x.get("pinned", False), x["date"]), reverse=True)

# ────────────────────────────────────────────────
# RICH FEED DISPLAY
# ────────────────────────────────────────────────
st.subheader(f"Live Empire Feed ({len(filtered)} posts)")
if filtered:
    for ann in filtered:
        pinned = " 📌 PINNED" if ann.get("pinned") else ""
        with st.container(border=True):
            st.markdown(f"<h3 style='color:#00ffaa;'>{ann['title']}{pinned}</h3>", unsafe_allow_html=True)
            st.caption(f"{ann.get('category', 'General')} • by {ann['posted_by']} • {ann['date'][:10]}")
            st.markdown(ann['message'])

            # Attachments
            if ann["attachments"]:
                image_cols = st.columns(min(len([a for a in ann["attachments"] if a["signed_url"] and a["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif'))]), 4))
                img_idx = 0
                for att in ann["attachments"]:
                    if att["signed_url"]:
                        if att["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif')):
                            with image_cols[img_idx % len(image_cols)]:
                                st.image(att["signed_url"], use_column_width=True, caption=att["original_name"])
                            img_idx += 1
                        else:
                            try:
                                r = requests.get(att["signed_url"], timeout=8)
                                if r.status_code == 200:
                                    st.download_button(
                                        label=f"⬇ {att['original_name']}",
                                        data=r.content,
                                        file_name=att["original_name"],
                                        use_container_width=True
                                    )
                            except:
                                st.caption(f"{att['original_name']} (preview unavailable)")
                    else:
                        st.caption(f"{att['original_name']} (loading failed)")

            # Likes
            likes_count = ann.get("likes", 0)
            like_key = f"like_{ann['id']}"
            if st.button(f"❤️ {likes_count}", key=like_key):
                supabase.table("announcements").update({"likes": likes_count + 1}).eq("id", ann["id"]).execute()
                st.cache_data.clear()
                st.rerun()

            # Comments
            with st.expander(f"💬 Comments ({len(ann['comments'])})"):
                for c in ann["comments"]:
                    st.markdown(f"**{c['user_name']}** • {c['timestamp'][:16].replace('T', ' ')}")
                    st.markdown(c['message'])
                    st.divider()

                with st.form(key=f"comment_form_{ann['id']}"):
                    comment = st.text_area("Add your comment...", height=80, label_visibility="collapsed")
                    if st.form_submit_button("Post Comment"):
                        if comment.strip():
                            supabase.table("announcement_comments").insert({
                                "announcement_id": ann["id"],
                                "user_name": current_user,
                                "message": comment.strip(),
                                "timestamp": datetime.now().isoformat()
                            }).execute()
                            st.cache_data.clear()
                            st.rerun()

            # Admin controls
            if current_role in ["owner", "admin"]:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📌 Pin / Unpin", key=f"pin_{ann['id']}"):
                        supabase.table("announcements").update({"pinned": not ann.get("pinned", False)}).eq("id", ann["id"]).execute()
                        st.cache_data.clear()
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete Announcement", key=f"del_{ann['id']}", type="secondary"):
                        try:
                            # Delete storage files
                            for att in ann["attachments"]:
                                if att.get("storage_path"):
                                    try:
                                        supabase.storage.from_("announcements").remove([att["storage_path"]])
                                    except:
                                        pass
                            # Delete DB entries
                            supabase.table("announcement_files").delete().eq("announcement_id", ann["id"]).execute()
                            supabase.table("announcement_comments").delete().eq("announcement_id", ann["id"]).execute()
                            supabase.table("announcements").delete().eq("id", ann["id"]).execute()
                            log_action("Announcement Deleted", f"ID: {ann['id']} | Title: {ann['title']}")
                            st.success("Announcement & attachments deleted")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {str(e)}")
            st.divider()
else:
    st.info("No announcements yet • Empire is ready for your first broadcast!")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">
        Realtime Empire Feed
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 2rem auto;">
        Permanent attachments • Likes & threaded comments • Pinning • Search • Full team engagement • Empire stays connected.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX Announcements • Fully Fixed & Enhanced 2026</h2>
</div>
""", unsafe_allow_html=True)