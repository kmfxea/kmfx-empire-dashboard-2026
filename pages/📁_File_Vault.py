# pages/07_📁_File_Vault.py
import streamlit as st
import pandas as pd
from datetime import datetime

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase, log_action

require_auth()  # Lahat ng authenticated users pwede, pero may role-based limits

st.header("📁 File Vault")
st.markdown("**Secure permanent storage • Proofs, documents, screenshots • Realtime upload & view • Owner/Admin full access • Client personal vault**")

current_role = st.session_state.get("role", "guest")
current_user = st.session_state.full_name

# ────────────────────────────────────────────────
# REALTIME FILE FETCH (10s cache)
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_vault_files():
    try:
        query = supabase.table("client_files").select("*").order("upload_date", desc=True)
        
        if current_role == "client":
            query = query.eq("assigned_client", current_user)
        # Owner/Admin see everything
        
        files = query.execute().data or []
        return files
    except Exception as e:
        st.error(f"Vault load error: {str(e)}")
        return []

files = fetch_vault_files()

if st.button("🔄 Refresh Vault", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

# ────────────────────────────────────────────────
# UPLOAD NEW FILE (ALL USERS)
# ────────────────────────────────────────────────
st.subheader("Upload New File / Proof")
with st.form("upload_file_form", clear_on_submit=True):
    category = st.selectbox("Category", [
        "Withdrawal Proof", "Identity Verification", "Payment Screenshot",
        "Trade Journal", "Contract / Agreement", "Other"
    ])
    notes = st.text_area("Notes / Description (Optional)")
    uploaded_file = st.file_uploader("Choose file", type=["png", "jpg", "jpeg", "pdf", "docx", "txt", "zip"])

    submitted = st.form_submit_button("Upload to Vault", type="primary", use_container_width=True)

    if submitted:
        if not uploaded_file:
            st.error("Please select a file to upload")
        else:
            try:
                url, storage_path = upload_to_supabase(
                    file=uploaded_file,
                    bucket="client_files",
                    folder="vault",
                    use_signed_url=False
                )

                supabase.table("client_files").insert({
                    "original_name": uploaded_file.name,
                    "file_url": url,
                    "storage_path": storage_path,
                    "upload_date": datetime.now().isoformat(),
                    "sent_by": current_user,
                    "category": category,
                    "assigned_client": current_user if current_role == "client" else None,
                    "notes": notes or None
                }).execute()

                log_action("File Uploaded", f"File: {uploaded_file.name} | Category: {category}")
                st.success("File successfully uploaded to permanent vault!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {str(e)}")

# ────────────────────────────────────────────────
# VAULT FILE LIST & VIEW/DOWNLOAD
# ────────────────────────────────────────────────
st.subheader(f"Vault Contents ({len(files)} files)")
if files:
    # Filter for clients (optional search)
    search_term = st.text_input("Search by filename, category, or notes", "")
    filtered_files = files
    if search_term:
        term = search_term.lower()
        filtered_files = [
            f for f in files
            if term in f.get("original_name", "").lower() or
               term in f.get("category", "").lower() or
               term in (f.get("notes") or "").lower()
        ]

    # Grid layout
    cols = st.columns(4)
    for idx, file in enumerate(filtered_files):
        with cols[idx % 4]:
            file_name = file["original_name"]
            upload_date = file["upload_date"][:10]
            category = file["category"]
            uploader = file["sent_by"]

            # Signed URL for secure access
            file_url = file.get("file_url")
            if file.get("storage_path"):
                try:
                    signed = supabase.storage.from_("client_files").create_signed_url(file["storage_path"], 3600 * 24 * 7)  # 7 days
                    file_url = signed.get("signedURL") or file_url
                except:
                    pass

            # Preview if image
            if file_url and file_name.lower().endswith(('.png','.jpg','.jpeg','.gif')):
                st.image(file_url, use_column_width=True, caption=f"{file_name}\n{category}")
            else:
                st.markdown(f"**{file_name}**")
                st.caption(f"{category} • {upload_date} • by {uploader}")

            # Download button
            if file_url:
                try:
                    import requests
                    r = requests.get(file_url, timeout=10)
                    if r.status_code == 200:
                        st.download_button(
                            "⬇ Download",
                            r.content,
                            file_name=file_name,
                            use_container_width=True,
                            key=f"dl_{file['id']}"
                        )
                except:
                    st.caption("Download unavailable")

            # Admin/Owner delete option
            if current_role in ["owner", "admin"]:
                if st.button("🗑️ Delete", key=f"del_file_{file['id']}", type="secondary"):
                    try:
                        if file.get("storage_path"):
                            supabase.storage.from_("client_files").remove([file["storage_path"]])
                        supabase.table("client_files").delete().eq("id", file["id"]).execute()
                        log_action("File Deleted", f"File: {file_name} | By: {current_user}")
                        st.success("File permanently deleted")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {str(e)}")
else:
    st.info("Vault is empty • Upload your first file above")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">
        Permanent & Secure Vault
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 2rem auto;">
        All proofs & documents stored forever • Realtime access • Admin oversight • Client privacy respected • Empire-grade security.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX File Vault • Built for Transparency 2026</h2>
</div>
""", unsafe_allow_html=True)