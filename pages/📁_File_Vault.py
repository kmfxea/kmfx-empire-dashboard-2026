# pages/📁_File_Vault.py
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
require_auth(min_role="client")  # clients can view their files, admin/owner full access

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

st.header("📁 Secure File Vault")
st.markdown("**Permanent encrypted storage** • All file types supported • Proofs & documents secured • Auto-assigned access • Realtime grid with previews • Empire fortress")

current_role = st.session_state.get("role", "guest").lower()

# ─── ULTRA-REALTIME FETCH (10s TTL) ───
@st.cache_data(ttl=10, show_spinner="Syncing secure vault...")
def fetch_vault_data():
    try:
        files_resp = supabase.table("client_files").select(
            "id, original_name, file_url, storage_path, upload_date, sent_by, "
            "category, assigned_client, tags, notes"
        ).order("upload_date", desc=True).execute()
        files = files_resp.data or []

        users_resp = supabase.table("users").select("id, full_name, role").execute()
        users = users_resp.data or []
        registered_clients = sorted(set(u["full_name"] for u in users if u["role"] == "client"))

        return files, registered_clients
    except Exception as e:
        st.error(f"Vault sync error: {str(e)}")
        return [], []

files, registered_clients = fetch_vault_data()

if st.button("🔄 Refresh Vault Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Vault auto-refreshes every 10s • Files stored permanently in Supabase Storage")

# ─── CLIENT VIEW RESTRICTION ───
if current_role == "client":
    my_name = st.session_state.get("full_name", "")
    files = [f for f in files if f["sent_by"] == my_name or f.get("assigned_client") == my_name]
    st.info(f"Showing your files only ({len(files)} total)")

# ─── UPLOAD SECTION (OWNER/ADMIN ONLY) ───
if current_role in ["owner", "admin"]:
    st.subheader("📤 Upload New Files (Permanent)")
    with st.form("file_upload_form", clear_on_submit=True):
        col_upload, col_options = st.columns([3, 2])
        with col_upload:
            uploaded_files = st.file_uploader(
                "Choose files (PDF, images, .ex5, zip, docs, etc.)",
                accept_multiple_files=True,
                help="Max 200MB per file • All types supported • .ex5 fully allowed"
            )
        with col_options:
            category = st.selectbox("Category", [
                "Payout Proof", "Withdrawal Proof", "Agreement", "KYC/ID",
                "Contributor Contract", "Testimonial Image", "EA File",
                "License Key", "Other"
            ])
            assigned_client = st.selectbox("Assign to Client (optional)", ["None"] + registered_clients)
            tags = st.text_input("Tags (comma-separated)", placeholder="e.g. payout, 2026, ex5")
            notes = st.text_area("Notes (optional)", height=100)

        submitted = st.form_submit_button("📤 Upload Permanently", type="primary", use_container_width=True)

        if submitted and uploaded_files:
            success_count = 0
            failed = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, file in enumerate(uploaded_files):
                status_text.text(f"Uploading {file.name} ({idx+1}/{len(uploaded_files)})...")
                try:
                    # Assuming you have this helper function defined in utils or elsewhere
                    url, storage_path = upload_to_supabase(
                        file=file,
                        bucket="client_files",
                        folder="vault",
                        use_signed_url=False
                    )

                    supabase.table("client_files").insert({
                        "original_name": file.name,
                        "file_url": url,
                        "storage_path": storage_path,
                        "upload_date": date.today().isoformat(),
                        "sent_by": st.session_state.get("full_name", "System"),
                        "category": category,
                        "assigned_client": assigned_client if assigned_client != "None" else None,
                        "tags": tags.strip() or None,
                        "notes": notes.strip() or None
                    }).execute()

                    success_count += 1
                    # Optional: log_action("File Uploaded (Permanent)", f"{file.name} → {category} → {assigned_client}")
                except Exception as e:
                    failed.append(f"{file.name}: {str(e)}")

                progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.empty()
            progress_bar.empty()

            if success_count:
                st.success(f"**{success_count}/{len(uploaded_files)}** files uploaded permanently!")
                st.balloons()
                st.cache_data.clear()
                st.rerun()

            if failed:
                st.error("Some uploads failed:")
                for fail in failed:
                    st.caption(f"• {fail}")

# ─── FILTERS & SEARCH ───
st.subheader("🔍 Search & Filter Vault")
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    search = st.text_input("Search name/tags/notes", placeholder="e.g. payout proof, .ex5")
with col_f2:
    cat_filter = st.selectbox("Category", ["All"] + sorted(set(f.get("category", "Other") for f in files)))
with col_f3:
    client_filter = st.selectbox("Assigned Client", ["All"] + sorted(set(f.get("assigned_client") for f in files if f.get("assigned_client"))))
with col_f4:
    sort_by = st.selectbox("Sort By", ["Newest First", "Oldest First", "Name A-Z", "Name Z-A"])

# Apply filters
filtered = files
if search:
    s = search.lower()
    filtered = [f for f in filtered if s in f["original_name"].lower() or
                s in (f.get("tags") or "").lower() or
                s in (f.get("notes") or "").lower()]

if cat_filter != "All":
    filtered = [f for f in filtered if f.get("category") == cat_filter]

if client_filter != "All":
    filtered = [f for f in filtered if f.get("assigned_client") == client_filter]

# Sorting
reverse = False
if sort_by == "Newest First":
    key = lambda x: x["upload_date"]
    reverse = True
elif sort_by == "Oldest First":
    key = lambda x: x["upload_date"]
elif sort_by == "Name A-Z":
    key = lambda x: x["original_name"].lower()
elif sort_by == "Name Z-A":
    key = lambda x: x["original_name"].lower()
    reverse = True

filtered = sorted(filtered, key=key, reverse=reverse)

# ─── VAULT GRID ───
st.subheader(f"Vault Contents ({len(filtered)} files)")
if filtered:
    cols = st.columns(3)
    for idx, f in enumerate(filtered):
        with cols[idx % 3]:
            file_url = f.get("file_url")
            assigned = f.get("assigned_client")
            tags = f.get("tags", "")
            notes = f.get("notes", "")

            # Glass card style
            st.markdown(f"""
            <div style="background:rgba(30,35,45,0.7); backdrop-filter:blur(12px); border-radius:16px; padding:1.4rem; margin-bottom:1.6rem; box-shadow:0 6px 20px rgba(0,0,0,0.15); border:1px solid rgba(100,100,100,0.25);">
            """, unsafe_allow_html=True)

            # Preview
            if file_url and f["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif')):
                st.image(file_url, use_container_width=True)
            else:
                st.markdown("<div style='height:140px; background:rgba(50,55,65,0.5); border-radius:10px; display:flex; align-items:center; justify-content:center; color:#aaa; font-size:1rem;'>No Preview</div>", unsafe_allow_html=True)

            st.markdown(f"**{f['original_name']}**")
            st.caption(f"{f['upload_date']} • By {f['sent_by']}")
            st.caption(f"Category: **{f.get('category','Other')}**")

            if assigned:
                st.caption(f"Assigned: **{assigned}**")
            if tags:
                st.caption(f"Tags: {tags}")

            if notes:
                with st.expander("Notes"):
                    st.write(notes)

            # Download
            if file_url:
                try:
                    r = requests.get(file_url, timeout=10)
                    if r.status_code == 200:
                        st.download_button(
                            "⬇ Download",
                            data=r.content,
                            file_name=f["original_name"],
                            use_container_width=True,
                            key=f"dl_{f['id']}_{idx}"
                        )
                    else:
                        st.caption("Download unavailable")
                except:
                    st.caption("Download failed")

            # Delete (owner/admin only)
            if current_role in ["owner", "admin"]:
                if st.button("🗑️ Delete Permanently", key=f"del_{f['id']}_{idx}", type="secondary", use_container_width=True):
                    try:
                        if f.get("storage_path"):
                            supabase.storage.from_("client_files").remove([f["storage_path"]])
                        supabase.table("client_files").delete().eq("id", f["id"]).execute()
                        st.success(f"Deleted: {f['original_name']}")
                        # Optional: log_action("File Deleted (Permanent)", f"{f['original_name']} by {st.session_state.get('full_name')}")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {str(e)}")

            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No files match your filters • Vault is secure and permanent")

# ─── MOTIVATIONAL FOOTER (sync style) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Permanent Secure Vault • Empire Documents Fortress
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Supabase Storage • Full previews • Advanced filters • Permanent delete • Client-restricted access
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Secured for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)