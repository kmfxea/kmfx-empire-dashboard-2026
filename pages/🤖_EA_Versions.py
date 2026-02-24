# pages/12_🤖_EA_Versions.py
import streamlit as st
import requests
from datetime import datetime

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase, log_action

require_auth()  # Lahat pwede mag-download, pero release/delete owner only

st.header("EA Versions Management 🤖")
st.markdown("**Elite EA distribution: Owner release with changelog • Auto-announce • Download tracking • Latest version license gated • Permanent files • Realtime list**")

current_role = st.session_state.get("role", "guest")
my_name = st.session_state.full_name

# ────────────────────────────────────────────────
# REALTIME CACHE (10s TTL)
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_ea_full():
    try:
        # Versions
        versions_resp = supabase.table("ea_versions").select("*").order("upload_date", desc=True).execute()
        versions = versions_resp.data or []

        # Download counts
        downloads_resp = supabase.table("ea_downloads").select("version_id").execute()
        download_counts = {}
        for d in downloads_resp.data or []:
            vid = d["version_id"]
            download_counts[vid] = download_counts.get(vid, 0) + 1

        # Client license check (latest only)
        client_license = None
        if current_role == "client":
            user_resp = supabase.table("users").select("id").eq("full_name", my_name).single().execute()
            if user_resp.data:
                user_id = user_resp.data["id"]
                license_resp = supabase.table("client_licenses").select(
                    "allow_live, version, revoked, expiry"
                ).eq("account_id", user_id).order("date_generated", desc=True).limit(1).execute()
                if license_resp.data and not license_resp.data[0].get("revoked", False):
                    client_license = license_resp.data[0]

        return versions, download_counts, client_license
    except Exception as e:
        st.error(f"EA Versions load error: {str(e)}")
        return [], {}, None

versions, download_counts, client_license = fetch_ea_full()

if st.button("🔄 Refresh EA Versions Now", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 EA versions auto-refresh every 10s • Files permanent in Supabase Storage")

# ────────────────────────────────────────────────
# RELEASE NEW VERSION (OWNER ONLY)
# ────────────────────────────────────────────────
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
                st.error("Version name, file, and changelog required")
            else:
                try:
                    url, storage_path = upload_to_supabase(
                        file=ea_file,
                        bucket="ea_versions",
                        folder="releases"
                    )

                    insert_data = {
                        "version": version_name.strip(),
                        "file_url": url,
                        "storage_path": storage_path,
                        "upload_date": datetime.now().isoformat(),
                        "notes": changelog.strip()
                    }

                    resp = supabase.table("ea_versions").insert(insert_data).execute()
                    version_id = resp.data[0]["id"]

                    if announce:
                        supabase.table("announcements").insert({
                            "title": f"🚀 New EA Version Released: {version_name.strip()}",
                            "message": f"Elite update available!\n\n**Changelog:**\n{changelog.strip()}\n\nDownload now in EA Versions page.\n\nStay elite!",
                            "date": datetime.now().isoformat(),
                            "posted_by": my_name,
                            "category": "EA Update",
                            "pinned": True
                        }).execute()

                    log_action("EA Version Released", f"{version_name} | ID: {version_id}")
                    st.success(f"Version {version_name} released permanently!")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Release failed: {str(e)}")

elif current_role == "admin":
    st.info("Admins can view & track downloads • Only owner can release new versions")

# ────────────────────────────────────────────────
# EA VERSIONS LIST + DOWNLOAD (WITH GATING)
# ────────────────────────────────────────────────
st.subheader("Available EA Versions")
if versions:
    latest_version = versions[0]
    for v in versions:
        vid = v["id"]
        downloads = download_counts.get(vid, 0)
        file_url = v.get("file_url")
        is_latest = v == latest_version

        # License gating for latest version only
        can_download = True
        gating_msg = ""
        if current_role == "client" and is_latest and client_license:
            if not client_license.get("allow_live", False):
                can_download = False
                gating_msg = "🔒 Active LIVE license required for latest version • Contact owner"
            elif client_license.get("revoked", False):
                can_download = False
                gating_msg = "🔒 Your license is revoked • Contact owner"
            elif client_license.get("expiry") != "NEVER":
                exp_date = client_license.get("expiry")
                if exp_date != "NEVER" and datetime.strptime(exp_date, "%Y-%m-%d").date() < datetime.now().date():
                    can_download = False
                    gating_msg = f"🔒 License expired on {exp_date} • Renew with owner"

        with st.expander(
            f"🤖 {v['version']} • Released {v['upload_date'][:10]} • {downloads} downloads" +
            (" 👑 LATEST" if is_latest else ""),
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
                            file_name=f"KMFX_EA_{v['version']}.ex5",
                            mime="application/octet-stream",
                            use_container_width=True,
                            key=f"dl_ea_{vid}"
                        ):
                            try:
                                supabase.table("ea_downloads").insert({
                                    "version_id": vid,
                                    "downloaded_by": my_name,
                                    "download_date": datetime.now().isoformat()
                                }).execute()
                                log_action("EA Downloaded", f"{v['version']} by {my_name}")
                            except:
                                pass  # silent fail — download pa rin
                    else:
                        st.error("File temporarily unavailable • Try again")
                except:
                    st.error("Download failed • Contact owner")
            elif file_url:
                st.info("Contact owner for access or license renewal")
            else:
                st.error("File missing • Contact owner")

            # Owner delete
            if current_role == "owner":
                if st.button("🗑️ Delete Version Permanently", key=f"del_ea_{vid}", type="secondary"):
                    try:
                        if v.get("storage_path"):
                            supabase.storage.from_("ea_versions").remove([v["storage_path"]])
                        supabase.table("ea_versions").delete().eq("id", vid).execute()
                        supabase.table("ea_downloads").delete().eq("version_id", vid).execute()
                        log_action("EA Version Deleted", f"{v['version']} | ID: {vid}")
                        st.success("Version & downloads history deleted permanently")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {str(e)}")

else:
    st.info("No EA versions released yet • Owner uploads activate elite distribution")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">
        Elite EA Distribution System
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 2rem auto;">
        Permanent files • Latest version license gated • Download tracked • Auto-announce on release • Owner full control • Empire performance elite.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX EA Versions • Cloud Permanent 2026</h2>
</div>
""", unsafe_allow_html=True)