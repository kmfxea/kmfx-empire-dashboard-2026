# pages/17_👤_Admin_Management.py
import streamlit as st
import uuid
import qrcode
from io import BytesIO
import bcrypt
from datetime import datetime

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action

require_auth(min_role="owner")  # Strict owner-only

st.header("Empire Team Management 👤")
st.markdown("**Owner-exclusive: Full team control • Register with complete details & titles (synced to all dropdowns/trees as 'Name (Title)') • Realtime balances • Secure edit/delete • QR login token generate/regenerate/revoke • Joined date • Advanced search/filter**")

current_role = st.session_state.get("role", "guest")

# ────────────────────────────────────────────────
# REALTIME CACHE (30s TTL)
# ────────────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_users_full():
    try:
        users_resp = supabase.table("users").select("*").order("created_at", desc=True).execute()
        return users_resp.data or []
    except Exception as e:
        st.error(f"Team data fetch error: {str(e)}")
        return []

users = fetch_users_full()

if st.button("🔄 Refresh Team Management Now", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Team auto-refresh every 30s • Titles & details sync instantly across empire")

# ────────────────────────────────────────────────
# TEAM SUMMARY METRICS
# ────────────────────────────────────────────────
team = [u for u in users if u["username"] != "kingminted"]  # Exclude owner
clients = [u for u in team if u["role"] == "client"]
admins = [u for u in team if u["role"] == "admin"]
total_balance = sum(u.get("balance", 0.0) for u in clients)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Total Team Members", len(team))
col_m2.metric("Clients", len(clients))
col_m3.metric("Admins", len(admins))
col_m4.metric("Total Client Balances", f"${total_balance:,.2f}")

# ────────────────────────────────────────────────
# REGISTER NEW TEAM MEMBER
# ────────────────────────────────────────────────
st.subheader("➕ Register New Team Member")
with st.form("add_user_form", clear_on_submit=True):
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        username = st.text_input("Username *", placeholder="e.g. michael2026")
        full_name = st.text_input("Full Name *", placeholder="e.g. Michael Reyes")
    with col_u2:
        initial_pwd = st.text_input("Initial Password *", type="password")
        urole = st.selectbox("Role *", ["client", "admin"])

    st.markdown("### Additional Details (Recommended)")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        accounts = st.text_input("MT5 Account Logins (comma-separated)", placeholder="e.g. 333723156,12345678")
        email = st.text_input("Email", placeholder="e.g. michael@example.com")
    with col_info2:
        contact_no = st.text_input("Contact No.", placeholder="e.g. 09128197085")
        address = st.text_area("Address", placeholder="e.g. Rodriguez 1, Rodriguez Dampalit, Malabon City")

    title = st.selectbox(
        "Title/Label (Displayed as 'Name (Title)')",
        ["None", "Pioneer", "Distributor", "VIP", "Elite Trader", "Contributor"],
        help="Syncs instantly to all empire dropdowns & trees"
    )

    submitted = st.form_submit_button("🚀 Register Member", type="primary", use_container_width=True)

    if submitted:
        if not username.strip() or not full_name.strip() or not initial_pwd:
            st.error("Username, full name, and initial password required")
        else:
            try:
                hashed = bcrypt.hashpw(initial_pwd.encode(), bcrypt.gensalt()).decode()
                supabase.table("users").insert({
                    "username": username.strip().lower(),
                    "password": hashed,
                    "full_name": full_name.strip(),
                    "role": urole,
                    "balance": 0.0,
                    "title": title if title != "None" else None,
                    "accounts": accounts.strip() or None,
                    "email": email.strip() or None,
                    "contact_no": contact_no.strip() or None,
                    "address": address.strip() or None,
                    "created_at": datetime.now().isoformat()
                }).execute()

                log_action("Team Member Registered", f"{full_name.strip()} ({title if title != 'None' else ''}) as {urole}")
                st.success(f"{full_name.strip()} registered successfully & synced empire-wide!")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Registration failed: {str(e)}")

# ────────────────────────────────────────────────
# CURRENT TEAM LIST + EDIT/DELETE/QR
# ────────────────────────────────────────────────
st.subheader("👥 Current Empire Team")
if team:
    # Search & Filter
    col_search1, col_search2 = st.columns(2)
    with col_search1:
        search_user = st.text_input("Search by Name / Username / Email / Contact / Accounts")
    with col_search2:
        filter_role = st.selectbox("Filter Role", ["All", "client", "admin"])

    filtered_team = team
    if search_user:
        s = search_user.lower()
        filtered_team = [
            u for u in filtered_team
            if s in u["full_name"].lower()
            or s in u["username"].lower()
            or s in str(u.get("email", "")).lower()
            or s in str(u.get("contact_no", "")).lower()
            or s in str(u.get("accounts", "")).lower()
        ]
    if filter_role != "All":
        filtered_team = [u for u in filtered_team if u["role"] == filter_role]

    st.caption(f"Showing {len(filtered_team)} member{'' if len(filtered_team) == 1 else 's'}")

    for u in filtered_team:
        title_display = f" ({u.get('title', '')})" if u.get('title') else ""
        balance = u.get("balance", 0.0)
        joined = u.get("created_at", "Unknown")[:10] if u.get("created_at") else "Unknown"

        with st.expander(
            f"**{u['full_name']}{title_display}** (@{u['username']}) • {u['role'].title()} • Balance ${balance:,.2f} • Joined {joined}",
            expanded=False
        ):
            # Details
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown(f"**MT5 Accounts:** {u.get('accounts') or 'None'}")
                st.markdown(f"**Email:** {u.get('email') or 'None'}")
            with col_d2:
                st.markdown(f"**Contact No.:** {u.get('contact_no') or 'None'}")
                st.markdown(f"**Address:** {u.get('address') or 'None'}")

            # QR Code Management
            st.markdown("### 🔑 Quick Login QR Code")
            current_qr_token = u.get("qr_token")
            app_url = "https://kmfxeaftmo.streamlit.app"  # Update if your app URL changes

            qr_url = f"{app_url}/?qr={current_qr_token}" if current_qr_token else None

            if current_qr_token:
                buf = BytesIO()
                qr = qrcode.QRCode(version=1, box_size=12, border=5)
                qr.add_data(qr_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(buf, format="PNG")
                qr_bytes = buf.getvalue()

                col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 2])
                with col_qr1:
                    st.image(qr_bytes, caption="QR Login Code", use_column_width=True)
                with col_qr2:
                    st.code(qr_url, language="text")
                    st.download_button(
                        "⬇ Download QR PNG",
                        qr_bytes,
                        f"{u['full_name'].replace(' ', '_')}_QR.png",
                        "image/png",
                        use_container_width=True
                    )
                with col_qr3:
                    st.info("Scan for instant login on any device")
                    col_regen, col_revoke = st.columns(2)
                    with col_regen:
                        if st.button("🔄 Regenerate Token", key=f"regen_{u['id']}"):
                            new_token = str(uuid.uuid4())
                            supabase.table("users").update({"qr_token": new_token}).eq("id", u["id"]).execute()
                            log_action("QR Token Regenerated", f"For {u['full_name']}")
                            st.success("New token generated • Old revoked")
                            st.cache_data.clear()
                            st.rerun()
                    with col_revoke:
                        if st.button("❌ Revoke Token", key=f"revoke_{u['id']}", type="secondary"):
                            supabase.table("users").update({"qr_token": None}).eq("id", u["id"]).execute()
                            log_action("QR Token Revoked", f"For {u['full_name']}")
                            st.success("Token revoked")
                            st.cache_data.clear()
                            st.rerun()
            else:
                st.info("No QR login token generated yet")
                if st.button("🚀 Generate QR Token", key=f"gen_{u['id']}"):
                    new_token = str(uuid.uuid4())
                    supabase.table("users").update({"qr_token": new_token}).eq("id", u["id"]).execute()
                    log_action("QR Token Generated", f"For {u['full_name']}")
                    st.success("Token generated • Refresh to view")
                    st.cache_data.clear()
                    st.rerun()

            # Actions
            st.markdown("### Actions")
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("✏️ Edit Member", key=f"edit_{u['id']}"):
                    st.session_state.edit_user_id = u["id"]
                    st.session_state.edit_user_data = u.copy()
                    st.rerun()

            with col_act2:
                st.warning("⚠️ Delete is permanent • Licenses, shares, and history will be affected")
                if st.button("🗑️ Delete Member", key=f"del_confirm_{u['id']}", type="secondary"):
                    try:
                        supabase.table("users").delete().eq("id", u["id"]).execute()
                        log_action("Team Member Deleted", f"{u['full_name']}{title_display}")
                        st.success("Member permanently removed")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {str(e)}")

            # Edit Form (inside expander)
            if st.session_state.get("edit_user_id") == u["id"]:
                edit_data = st.session_state.edit_user_data
                with st.form(key=f"edit_form_{u['id']}", clear_on_submit=True):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        new_username = st.text_input("Username *", value=edit_data["username"])
                        new_full_name = st.text_input("Full Name *", value=edit_data["full_name"])
                    with col_e2:
                        new_pwd = st.text_input("New Password (leave blank to keep)", type="password")
                        new_role = st.selectbox("Role *", ["client", "admin"],
                                                index=0 if edit_data["role"] == "client" else 1)

                    st.markdown("### Details")
                    col_einfo1, col_einfo2 = st.columns(2)
                    with col_einfo1:
                        new_accounts = st.text_input("MT5 Accounts", value=edit_data.get("accounts") or "")
                        new_email = st.text_input("Email", value=edit_data.get("email") or "")
                    with col_einfo2:
                        new_contact = st.text_input("Contact No.", value=edit_data.get("contact_no") or "")
                        new_address = st.text_area("Address", value=edit_data.get("address") or "")

                    title_options = ["None", "Pioneer", "Distributor", "VIP", "Elite Trader", "Contributor"]
                    current_title_idx = title_options.index(edit_data.get("title", "None")) if edit_data.get("title") in title_options else 0
                    new_title = st.selectbox("Title/Label", title_options, index=current_title_idx)

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_submitted = st.form_submit_button("💾 Save Changes", type="primary")
                    with col_cancel:
                        cancel_submitted = st.form_submit_button("Cancel")

                    if cancel_submitted:
                        if "edit_user_id" in st.session_state:
                            del st.session_state.edit_user_id
                        if "edit_user_data" in st.session_state:
                            del st.session_state.edit_user_data
                        st.rerun()

                    if save_submitted:
                        if not new_username.strip() or not new_full_name.strip():
                            st.error("Username and full name required")
                        else:
                            try:
                                update_data = {
                                    "username": new_username.strip().lower(),
                                    "full_name": new_full_name.strip(),
                                    "role": new_role,
                                    "title": new_title if new_title != "None" else None,
                                    "accounts": new_accounts.strip() or None,
                                    "email": new_email.strip() or None,
                                    "contact_no": new_contact.strip() or None,
                                    "address": new_address.strip() or None
                                }
                                if new_pwd.strip():
                                    hashed_new = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt()).decode()
                                    update_data["password"] = hashed_new

                                supabase.table("users").update(update_data).eq("id", u["id"]).execute()
                                log_action("Team Member Edited", f"{new_full_name} ({new_title if new_title != 'None' else ''})")
                                st.success("Member updated successfully!")
                                if "edit_user_id" in st.session_state:
                                    del st.session_state.edit_user_id
                                if "edit_user_data" in st.session_state:
                                    del st.session_state.edit_user_data
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Update failed: {str(e)}")
else:
    st.info("No team members yet • Start building your empire!")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">
        Owner Team Control Center
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 2rem auto;">
        Realtime team metrics • Instant title sync • Secure QR management • Full edit/delete • Empire team elite & secure forever.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX Team Management • Fully Fixed & Elite 2026</h2>
</div>
""", unsafe_allow_html=True)