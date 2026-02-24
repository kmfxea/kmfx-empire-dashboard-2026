# pages/13_📸_Testimonials.py
import streamlit as st
import pandas as pd
from datetime import datetime
import requests

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase, log_action

require_auth()  # Lahat authenticated, pero role-based

st.header("Team Testimonials 📸")
st.markdown("**Empire motivation hub: Clients submit success stories + photos (permanent & visible) • Balance context • Owner approve/reject with auto-announce • Realtime grid • Search**")

current_role = st.session_state.get("role", "guest")
my_name = st.session_state.full_name

# ────────────────────────────────────────────────
# REALTIME CACHE (10s TTL)
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_testimonials_full():
    try:
        # Approved
        approved_resp = supabase.table("testimonials").select("*").eq("status", "Approved").order("date_submitted", desc=True).execute()
        approved = approved_resp.data or []

        # Pending
        pending_resp = supabase.table("testimonials").select("*").eq("status", "Pending").order("date_submitted", desc=True).execute()
        pending = pending_resp.data or []

        # Users for balance
        users_resp = supabase.table("users").select("full_name, balance").execute()
        user_map = {u["full_name"]: u["balance"] or 0.0 for u in users_resp.data or []}

        # Signed URLs for ALL images (30 days)
        all_testimonials = approved + pending
        for t in all_testimonials:
            signed_url = t.get("image_url")
            if t.get("storage_path"):
                try:
                    signed = supabase.storage.from_("testimonials").create_signed_url(
                        t["storage_path"], 3600 * 24 * 30
                    )
                    signed_url = signed.get("signedURL") or signed_url
                except:
                    pass
            t["signed_url"] = signed_url

        return approved, pending, user_map
    except Exception as e:
        st.error(f"Testimonials load error: {str(e)}")
        return [], [], {}

approved, pending, user_map = fetch_testimonials_full()

if st.button("🔄 Refresh Testimonials Now", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Testimonials auto-refresh every 10s • Photos permanent & fully visible (signed URLs)")

# ────────────────────────────────────────────────
# CLIENT SUBMIT FORM
# ────────────────────────────────────────────────
if current_role == "client":
    my_balance = user_map.get(my_name, 0.0)
    st.subheader(f"Share Your Success Story (Balance: **${my_balance:,.2f}**)")
    with st.expander("➕ Submit Testimonial", expanded=True):
        with st.form("testi_submit_form", clear_on_submit=True):
            story = st.text_area("Your Story *", height=200, placeholder="How KMFX changed my life, profits, journey...")
            photo = st.file_uploader("Upload Photo * (Permanent + Visible)", type=["png", "jpg", "jpeg", "gif"])

            submitted = st.form_submit_button("Submit for Approval", type="primary", use_container_width=True)

            if submitted:
                if not story.strip() or not photo:
                    st.error("Story and photo required")
                else:
                    try:
                        url, storage_path = upload_to_supabase(
                            file=photo,
                            bucket="testimonials",
                            folder="photos"
                        )

                        supabase.table("testimonials").insert({
                            "client_name": my_name,
                            "message": story.strip(),
                            "image_url": url,
                            "storage_path": storage_path,
                            "date_submitted": datetime.now().isoformat(),
                            "status": "Pending"
                        }).execute()

                        log_action("Testimonial Submitted", f"By: {my_name}")
                        st.success("Testimonial submitted permanently! Photo visible on approval.")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Submission failed: {str(e)}")

# ────────────────────────────────────────────────
# APPROVED GRID (FULL IMAGE PREVIEWS)
# ────────────────────────────────────────────────
st.subheader("🌟 Approved Success Stories")
if approved:
    search = st.text_input("Search stories or name", "")
    filtered = approved
    if search:
        s = search.lower()
        filtered = [t for t in approved if s in t["message"].lower() or s in t["client_name"].lower()]

    cols = st.columns(3)
    for idx, t in enumerate(filtered):
        with cols[idx % 3]:
            balance = user_map.get(t["client_name"], 0.0)
            signed_url = t.get("signed_url")

            with st.container(border=True):
                if signed_url:
                    st.image(signed_url, use_column_width=True, caption=t["client_name"])
                else:
                    st.caption("No photo available")
                st.markdown(f"**{t['client_name']}** (Balance: **${balance:,.2f}**)")
                st.markdown(t["message"])
                st.caption(f"Submitted: {t['date_submitted'][:10]}")
else:
    st.info("No approved testimonials yet • Inspire the empire!")

# ────────────────────────────────────────────────
# PENDING APPROVAL (OWNER/ADMIN ONLY)
# ────────────────────────────────────────────────
if current_role in ["owner", "admin"] and pending:
    st.subheader("⏳ Pending Approval")
    for p in pending:
        balance = user_map.get(p["client_name"], 0.0)
        signed_url = p.get("signed_url")

        with st.expander(f"{p['client_name']} • {p['date_submitted'][:10]} • Balance ${balance:,.2f}", expanded=False):
            if signed_url:
                st.image(signed_url, use_column_width=True)
            else:
                st.caption("No photo")

            st.markdown(p["message"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Approve & Auto-Announce", key=f"approve_testi_{p['id']}", use_container_width=True):
                    try:
                        supabase.table("testimonials").update({"status": "Approved"}).eq("id", p["id"]).execute()

                        supabase.table("announcements").insert({
                            "title": f"🌟 New Testimonial from {p['client_name']}!",
                            "message": p["message"],
                            "date": datetime.now().isoformat(),
                            "posted_by": "System (Auto)",
                            "category": "Testimonial",
                            "pinned": False
                        }).execute()

                        log_action("Testimonial Approved", f"By: {p['client_name']}")
                        st.success("Approved & auto-announced to empire!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

            with col2:
                if st.button("Reject & Delete", key=f"reject_testi_{p['id']}", type="secondary", use_container_width=True):
                    try:
                        if p.get("storage_path"):
                            supabase.storage.from_("testimonials").remove([p["storage_path"]])
                        supabase.table("testimonials").delete().eq("id", p["id"]).execute()
                        log_action("Testimonial Rejected & Deleted", f"By: {p['client_name']}")
                        st.success("Rejected & permanently deleted")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">
        Empire Success Stories
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 2rem auto;">
        Permanent photos • Full visibility • Balance context • Auto-announce on approval • Realtime inspiration • Empire motivated forever.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX Testimonials • Cloud Permanent 2026</h2>
</div>
""", unsafe_allow_html=True)