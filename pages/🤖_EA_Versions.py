# pages/🤖_EA_Versions.py
import streamlit as st
import requests
from datetime import date

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="client")  # clients download (gated), owner releases

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

st.header("🤖 EA Versions Management")
st.markdown("**Elite EA distribution** • Owner release with changelog • Auto-announce • Download tracking • Latest version license gated • Permanent files • Realtime list")

current_role = st.session_state.get("role", "guest").lower()

# ─── ULTRA-REALTIME FETCH (10s TTL) ───
@st.cache_data(ttl=10, show_spinner="Syncing EA versions...")
def fetch_ea_full():
    try:
        versions = supabase.table("ea_versions").select("*").order("upload_date", desc=True).execute().data or []
        downloads = supabase.table("ea_downloads").select("*").execute().data or []
        download_counts = {}
        for d in downloads:
            vid = d["version_id"]
            download_counts[vid] = download_counts.get(vid, 0) + 1

        # Client license check (latest active non-revoked)
        client_license = None
        if current_role == "client":
            my_name = st.session_state.get("full_name", "")
            user_resp = supabase.table("users").select("id").eq("full_name", my_name).single().execute()
            if user_resp.data:
                user_id = user_resp.data["id"]
                license_resp = supabase.table("client_licenses").select("allow_live, version, revoked").eq("account_id", user_id).order("date_generated", desc=True).limit(1).execute()
                if license_resp.data and not license_resp.data[0].get("revoked", False):
                    client_license = license_resp.data[0]

        return versions, download_counts, client_license
    except Exception as e:
        st.error(f"EA versions sync error: {str(e)}")
        return [], {}, None

versions, download_counts, client_license = fetch_ea_full()

if st.button("🔄 Refresh EA Versions Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Versions auto-refresh every 10s • EA files stored permanently in Supabase Storage")

# ─── RELEASE NEW VERSION (OWNER ONLY) ───
if current_role == "owner":
    st.subheader("📤 Release New EA Version")
    with st.form("ea_release_form", clear_on_submit=True):
        version_name = st.text_input("Version Name *", placeholder="e.g. v3.0 Elite Scalper 2026")
        ea_file = st.file_uploader("Upload EA File (.ex5 / .mq5) *", type=["ex5", "mq5"])
        changelog = st.text_area("Changelog *", height=200, placeholder="• New gold scalping filters\n• Reduced drawdown\n• FTMO optimized")
        announce = st.checkbox("📢 Auto-Announce to Empire", value=True)
        submitted = st.form_submit_button("🚀 Release Version", type="primary", use_container_width=True)

        if submitted:
            if not version_name.strip() or not ea_file or not changelog.strip():
                st.error("Version name, file, and changelog are required")
            else:
                with st.spinner("Releasing new version..."):
                    try:
                        url, storage_path = upload_to_supabase(  # assuming helper exists
                            file=ea_file,
                            bucket="ea_versions",
                            folder="releases"
                        )
                        supabase.table("ea_versions").insert({
                            "version": version_name.strip(),
                            "file_url": url,
                            "storage_path": storage_path,
                            "upload_date": date.today().isoformat(),
                            "notes": changelog.strip()
                        }).execute()

                        if announce:
                            supabase.table("announcements").insert({
                                "title": f"🚀 New EA Version Released: {version_name.strip()}",
                                "message": f"Elite update available!\n\n**Changelog:**\n{changelog.strip()}\n\nDownload now in EA Versions page (license required for latest).",
                                "date": date.today().isoformat(),
                                "posted_by": st.session_state.get("full_name", "Owner"),
                                "category": "EA Update",
                                "pinned": True
                            }).execute()

                        st.success(f"Version **{version_name}** released permanently!")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Release failed: {str(e)}")

elif current_role == "admin":
    st.info("Admins can view versions & track downloads • Only owner can release new versions")

# ─── REALTIME VERSION LIST ───
st.subheader("Available EA Versions")
if versions:
    latest_version = versions[0]
    for v in versions:
        vid = v["id"]
        downloads = download_counts.get(vid, 0)
        file_url = v.get("file_url")
        is_latest = v == latest_version

        # License gating for latest version (clients only)
        can_download = True
        gating_msg = ""
        if current_role == "client" and is_latest and client_license:
            if not client_license.get("allow_live", False):
                can_download = False
                gating_msg = "🔒 Active LIVE license required for latest version • Contact owner"
            elif client_license.get("revoked", False):
                can_download = False
                gating_msg = "🔒 Your license is revoked • Contact owner"

        with st.expander(
            f"🤖 {v['version']} • Released {v['upload_date']} • {downloads} downloads" + (" 👑 LATEST" if is_latest else ""),
            expanded=is_latest
        ):
            st.markdown(f"**Changelog:**\n{v['notes'].replace('\n', '<br>')}", unsafe_allow_html=True)

            if gating_msg:
                st.warning(gating_msg)

            if file_url and can_download:
                try:
                    r = requests.get(file_url, timeout=10)
                    if r.status_code == 200:
                        if st.download_button(
                            f"⬇️ Download {v['version']}",
                            data=r.content,
                            file_name=f"KMFX_EA_{v['version'].replace(' ', '_')}.ex5",
                            mime="application/octet-stream",
                            use_container_width=True,
                            key=f"dl_ea_{vid}"
                        ):
                            try:
                                supabase.table("ea_downloads").insert({
                                    "version_id": vid,
                                    "downloaded_by": st.session_state.get("full_name", "User"),
                                    "download_date": date.today().isoformat()
                                }).execute()
                                st.success("Download tracked!")
                            except:
                                pass  # silent fail on tracking
                    else:
                        st.error("File temporarily unavailable")
                except:
                    st.error("Download failed • Try again later")
            elif file_url:
                st.info("Contact owner for access")
            else:
                st.error("File missing • Contact owner")

            # Owner delete
            if current_role == "owner":
                if st.button("🗑️ Delete Version Permanently", key=f"del_ea_{vid}", type="secondary", use_container_width=True):
                    try:
                        if v.get("storage_path"):
                            supabase.storage.from_("ea_versions").remove([v["storage_path"]])
                        supabase.table("ea_versions").delete().eq("id", vid).execute()
                        supabase.table("ea_downloads").delete().eq("version_id", vid).execute()
                        st.success("Version deleted permanently")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {str(e)}")
else:
    st.info("No EA versions released yet • Owner uploads activate elite distribution")

# ─── MOTIVATIONAL FOOTER (sync style) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Elite EA Distribution System
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Permanent files • License gating • Download tracking • Auto-announce • Owner control • Empire performance elite
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Powered for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)