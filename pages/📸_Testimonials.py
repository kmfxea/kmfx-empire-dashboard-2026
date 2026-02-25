# pages/📸_Testimonials.py
import streamlit as st
import requests
from datetime import date

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase, log_action

render_sidebar()
require_auth(min_role="client")  # clients submit, everyone views approved, owner/admin approves

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

st.header("📸 Team Testimonials")
st.markdown("**Empire motivation hub** • Share your success stories + photos (permanent storage + fully visible) • Owner approve/reject with auto-announce • Realtime grid • Search • Inspiration for all")

current_role = st.session_state.get("role", "guest").lower()

# ─── ULTRA-REALTIME FETCH (10s TTL) ───
@st.cache_data(ttl=10, show_spinner="Syncing testimonials...")
def fetch_testimonials_full():
    try:
        # Approved
        approved = supabase.table("testimonials") \
            .select("id, client_name, message, image_url, storage_path, date_submitted, status") \
            .eq("status", "Approved") \
            .order("date_submitted", desc=True) \
            .execute().data or []

        # Pending
        pending = supabase.table("testimonials") \
            .select("id, client_name, message, image_url, storage_path, date_submitted, status") \
            .eq("status", "Pending") \
            .order("date_submitted", desc=True) \
            .execute().data or []

        # User balance map
        users = supabase.table("users").select("full_name, balance").execute().data or []
        user_map = {u["full_name"]: u.get("balance", 0) for u in users}

        # Image URLs: public first, then fresh signed
        all_testis = approved + pending
        for t in all_testis:
            public_url = t.get("image_url")  # if bucket public
            signed_url = None

            if not public_url and t.get("storage_path"):
                try:
                    signed = supabase.storage.from_("testimonials").create_signed_url(
                        t["storage_path"], expires_in=3600 * 24  # 24 hours - fresh on load
                    )
                    signed_url = signed.signed_url
                    # Debug (comment out after testing)
                    # st.write(f"Generated signed URL for {t['client_name']}: {signed_url}")
                except Exception as sign_err:
                    st.warning(f"Signed URL failed for {t['client_name']}: {str(sign_err)}")

            t["display_url"] = public_url or signed_url

        return approved, pending, user_map
    except Exception as e:
        st.error(f"Testimonials sync error: {str(e)}")
        return [], [], {}

approved, pending, user_map = fetch_testimonials_full()

if st.button("🔄 Refresh Testimonials Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Testimonials auto-refresh every 10s • Photos permanent & fully visible")

# ─── CLIENT SUBMISSION ───
if current_role == "client":
    my_name = st.session_state.get("full_name", "")
    my_balance = user_map.get(my_name, 0)
    st.subheader(f"Share Your Success Story (Balance: **${my_balance:,.2f}**)")
    with st.expander("➕ Submit Testimonial", expanded=True):
        with st.form("testi_form", clear_on_submit=True):
            story = st.text_area("Your Story *", height=200, placeholder="How KMFX changed my life, profits, journey...")
            photo = st.file_uploader("Upload Photo * (Permanent + Visible)", type=["png", "jpg", "jpeg", "gif"])
            submitted = st.form_submit_button("Submit for Approval", type="primary", use_container_width=True)

            if submitted:
                if not story.strip() or not photo:
                    st.error("Story and photo are required")
                else:
                    with st.spinner("Submitting testimonial..."):
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
                                "date_submitted": date.today().isoformat(),
                                "status": "Pending"
                            }).execute()
                            st.success("Testimonial submitted permanently! Photo will be visible once approved.")
                            st.balloons()
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Submission failed: {str(e)}")

# ─── APPROVED SUCCESS STORIES GRID ───
st.subheader("🌟 Approved Success Stories")
if approved:
    search = st.text_input("Search stories or name", placeholder="e.g. profit journey")
    filtered_approved = approved
    if search:
        s = search.lower()
        filtered_approved = [t for t in approved if s in t["message"].lower() or s in t["client_name"].lower()]

    cols = st.columns(3)
    for idx, t in enumerate(filtered_approved):
        with cols[idx % 3]:
            balance = user_map.get(t["client_name"], 0)
            display_url = t.get("display_url")
            st.markdown(f"""
            <div style="
                background:rgba(30,35,45,0.7);
                backdrop-filter:blur(12px);
                border-radius:16px;
                padding:1.4rem;
                margin-bottom:1.6rem;
                box-shadow:0 6px 20px rgba(0,0,0,0.15);
                border:1px solid rgba(100,100,100,0.25);
            ">
            """, unsafe_allow_html=True)

            if display_url:
                # Reliable bytes load (fixes most Streamlit image issues)
                try:
                    r = requests.get(display_url, timeout=5)
                    if r.status_code == 200:
                        st.image(r.content, use_column_width=True, caption=t["client_name"])
                    else:
                        st.caption(f"Image unavailable (status {r.status_code})")
                except:
                    st.caption("Image load error")
            else:
                st.markdown("<div style='height:180px; background:rgba(50,55,65,0.5); border-radius:10px; display:flex; align-items:center; justify-content:center; color:#aaa;'>No Photo</div>", unsafe_allow_html=True)

            st.markdown(f"**{t['client_name']}** (Balance: **${balance:,.2f}**)")
            st.markdown(t["message"].replace("\n", "<br>"), unsafe_allow_html=True)
            st.caption(f"Submitted: {t['date_submitted']}")
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No approved testimonials yet • Inspire the empire with your story!")

# ─── PENDING APPROVAL (OWNER/ADMIN ONLY) ───
if current_role in ["owner", "admin"] and pending:
    st.subheader("⏳ Pending Approval")
    for p in pending:
        balance = user_map.get(p["client_name"], 0)
        display_url = p.get("display_url")
        with st.expander(f"{p['client_name']} • {p['date_submitted']} • Balance ${balance:,.2f}", expanded=False):
            if display_url:
                try:
                    r = requests.get(display_url, timeout=5)
                    if r.status_code == 200:
                        st.image(r.content, use_column_width=True, caption="Submitted Photo")
                    else:
                        st.caption(f"Image unavailable (status {r.status_code})")
                except:
                    st.caption("Image load error")
            else:
                st.caption("No photo uploaded")
            st.markdown(p["message"])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Approve & Auto-Announce", key=f"app_{p['id']}"):
                    try:
                        supabase.table("testimonials").update({"status": "Approved"}).eq("id", p["id"]).execute()
                        supabase.table("announcements").insert({
                            "title": f"🌟 New Testimonial from {p['client_name']}!",
                            "message": p["message"],
                            "date": date.today().isoformat(),
                            "posted_by": "System (Auto)",
                            "category": "Testimonial",
                            "pinned": False
                        }).execute()
                        st.success("Approved & announced empire-wide!")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Approve failed: {str(e)}")
            with col2:
                if st.button("Reject & Delete", key=f"rej_{p['id']}", type="secondary"):
                    try:
                        if p.get("storage_path"):
                            supabase.storage.from_("testimonials").remove([p["storage_path"]])
                        supabase.table("testimonials").delete().eq("id", p["id"]).execute()
                        st.success("Rejected & deleted permanently")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Reject failed: {str(e)}")

# ─── MOTIVATIONAL FOOTER ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Empire Success Stories & Motivation
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Permanent photos • Full visibility • Balance context • Auto-announce on approval • Realtime inspiration
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Shared for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)