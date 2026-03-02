# pages/👤_Admin_Management.py
import streamlit as st
import uuid
import qrcode
from io import BytesIO
import bcrypt

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="owner")  # strict — owner only

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

st.header("👤 Empire Team Management")
st.markdown("**Owner-exclusive control** • Register/edit team members with full details & titles • Realtime balances • Secure QR login • Joined dates • Advanced search/filter")

current_role = st.session_state.get("role", "guest").lower()
if current_role != "owner":
    st.error("🔒 Team Management is **OWNER-ONLY** for empire security.")
    st.stop()

# ─── FULL REALTIME CACHE (30s TTL) ───
@st.cache_data(ttl=30, show_spinner="Syncing empire team...")
def fetch_users_full():
    try:
        users = supabase.table("users").select("*").order("created_at", desc=True).execute().data or []
        return users
    except Exception as e:
        st.error(f"Team sync error: {str(e)}")
        return []

users = fetch_users_full()

if st.button("🔄 Refresh Team Management Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Team auto-refreshes every 30s • All changes instantly sync empire-wide")

# ─── TEAM SUMMARY METRICS ───
team = [u for u in users if u.get("username") != "kingminted"]
clients = [u for u in team if u.get("role") == "client"]
admins = [u for u in team if u.get("role") == "admin"]
total_balance = sum(u.get("balance", 0) for u in clients)

cols = st.columns(4)
cols[0].metric("Total Team Members", len(team))
cols[1].metric("Clients", len(clients))
cols[2].metric("Admins", len(admins))
cols[3].metric("Total Client Balances", f"${total_balance:,.2f}")

# ─── REGISTER NEW TEAM MEMBER ───
st.subheader("➕ Register New Team Member")
with st.form("add_user_form", clear_on_submit=True):
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        username = st.text_input("Username *", placeholder="e.g. michael2026")
        full_name = st.text_input("Full Name *", placeholder="e.g. Michael Reyes")
    with col_u2:
        initial_pwd = st.text_input("Initial Password *", type="password")
        urole = st.selectbox("Role *", ["client", "admin"])
    st.markdown("### Additional Details (Optional)")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        accounts = st.text_input("MT5 Account Logins (comma-separated)", placeholder="e.g. 333723156, 12345678")
        email = st.text_input("Email", placeholder="e.g. michael@example.com")
    with col_info2:
        contact_no = st.text_input("Contact No.", placeholder="e.g. 09128197085")
        address = st.text_area("Address", placeholder="e.g. Rodriguez 1, Malabon City")
    title = st.selectbox(
        "Title/Label (shows as 'Name (Title)' in dropdowns)",
        ["None", "Pioneer", "Distributor", "VIP", "Elite Trader", "Contributor"]
    )
    submitted = st.form_submit_button("🚀 Register Member", type="primary", use_container_width=True)
    if submitted:
        if not username.strip() or not full_name.strip() or not initial_pwd:
            st.error("Username, full name, and initial password required")
        else:
            with st.spinner("Registering..."):
                try:
                    hashed = bcrypt.hashpw(initial_pwd.encode(), bcrypt.gensalt()).decode()
                    insert_data = {
                        "username": username.strip().lower(),
                        "password": hashed,
                        "full_name": full_name.strip(),
                        "role": urole,
                        "balance": 0.0,
                        "title": title if title != "None" else None,
                        "accounts": accounts.strip() or None,
                        "email": email.strip() or None,
                        "contact_no": contact_no.strip() or None,
                        "address": address.strip() or None
                    }
                    supabase.table("users").insert(insert_data).execute()
                    st.success(f"**{full_name.strip()}** registered & synced!")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")

# ─── CURRENT TEAM LIST ───
st.subheader("👥 Current Empire Team")
if team:
    col_search1, col_search2 = st.columns(2)
    with col_search1:
        search_user = st.text_input("Search by Name / Username / Email / Contact / Accounts")
    with col_search2:
        filter_role = st.selectbox("Filter Role", ["All", "client", "admin"])

    filtered_team = team
    if search_user:
        s = search_user.lower()
        filtered_team = [u for u in filtered_team if s in str(u.get("full_name", "")).lower() or s in str(u.get("username", "")).lower() or s in str(u.get("email", "")).lower() or s in str(u.get("contact_no", "")).lower() or s in str(u.get("accounts", "")).lower()]
    if filter_role != "All":
        filtered_team = [u for u in filtered_team if u.get("role") == filter_role]

    st.caption(f"Showing {len(filtered_team)} member{'s' if len(filtered_team) != 1 else ''}")

    for u in filtered_team:
        title_display = f" ({u.get('title', '')})" if u.get('title') else ""
        balance = u.get("balance", 0.0)
        joined = u.get("created_at", "Unknown")[:10] if u.get("created_at") else "Unknown"
        with st.expander(
            f"**{u['full_name']}{title_display}** (@{u['username']}) • {u['role'].title()} • Balance **${balance:,.2f}** • Joined {joined}",
            expanded=False
        ):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown(f"**MT5 Accounts:** {u.get('accounts') or 'None'}")
                st.markdown(f"**Email:** {u.get('email') or 'None'}")
            with col_d2:
                st.markdown(f"**Contact No.:** {u.get('contact_no') or 'None'}")
                st.markdown(f"**Address:** {u.get('address') or 'None'}")

            # QR Code Management (unchanged)
            st.markdown("### 🔑 Quick Login QR Code")
            current_qr_token = u.get("qr_token")
            app_url = "https://kmfxea.streamlit.app"
            qr_url = f"{app_url}/?qr={current_qr_token}" if current_qr_token else None
            if current_qr_token:
                buf = BytesIO()
                qr = qrcode.QRCode(version=1, box_size=12, border=5)
                qr.add_data(qr_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(buf, format="PNG")
                qr_bytes = buf.getvalue()
                col_qr1, col_qr2 = st.columns([1, 3])
                with col_qr1:
                    st.image(qr_bytes, caption="Scan for Instant Login", use_column_width=True)
                with col_qr2:
                    st.code(qr_url, language="text")
                    st.download_button("⬇ Download QR PNG", qr_bytes, f"{u['full_name'].replace(' ', '_')}_QR.png", "image/png", use_container_width=True)
                col_regen, col_revoke = st.columns(2)
                with col_regen:
                    if st.button("🔄 Regenerate QR Code", key=f"regen_{u['id']}"):
                        new_token = str(uuid.uuid4())
                        supabase.table("users").update({"qr_token": new_token}).eq("id", u["id"]).execute()
                        st.success("New QR token generated")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                with col_revoke:
                    if st.button("❌ Revoke QR Code", key=f"revoke_{u['id']}", type="secondary"):
                        supabase.table("users").update({"qr_token": None}).eq("id", u["id"]).execute()
                        st.success("QR token revoked")
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.info("No QR login code yet")
                if st.button("🚀 Generate QR Code", key=f"gen_{u['id']}"):
                    new_token = str(uuid.uuid4())
                    supabase.table("users").update({"qr_token": new_token}).eq("id", u["id"]).execute()
                    st.success("QR code generated • Refresh to view")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()

            # Actions (unchanged)
            st.markdown("### Actions")
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("✏️ Edit Member", key=f"edit_{u['id']}"):
                    st.session_state.edit_user_id = u["id"]
                    st.session_state.edit_user_data = u.copy()
                    st.rerun()
            with col_act2:
                st.warning("⚠️ Delete is permanent")
                if st.button("🗑️ Delete Member", key=f"del_confirm_{u['id']}", type="secondary"):
                    try:
                        supabase.table("users").delete().eq("id", u["id"]).execute()
                        st.success(f"**{u['full_name']}** removed")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {str(e)}")

            # Edit Form (unchanged)
            if st.session_state.get("edit_user_id") == u["id"]:
                edit_data = st.session_state.edit_user_data
                with st.form(key=f"edit_form_{u['id']}", clear_on_submit=True):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        new_username = st.text_input("Username *", value=edit_data.get("username", ""))
                        new_full_name = st.text_input("Full Name *", value=edit_data.get("full_name", ""))
                    with col_e2:
                        new_pwd = st.text_input("New Password (leave blank)", type="password")
                        new_role = st.selectbox("Role *", ["client", "admin"], index=0 if edit_data.get("role") == "client" else 1)
                    st.markdown("### Details")
                    col_einfo1, col_einfo2 = st.columns(2)
                    with col_einfo1:
                        new_accounts = st.text_input("MT5 Accounts", value=edit_data.get("accounts") or "")
                        new_email = st.text_input("Email", value=edit_data.get("email") or "")
                    with col_einfo2:
                        new_contact = st.text_input("Contact No.", value=edit_data.get("contact_no") or "")
                        new_address = st.text_area("Address", value=edit_data.get("address") or "")
                    title_options = ["None", "Pioneer", "Distributor", "VIP", "Elite Trader", "Contributor"]
                    current_title_idx = title_options.index(edit_data.get("title")) if edit_data.get("title") in title_options else 0
                    new_title = st.selectbox("Title/Label", title_options, index=current_title_idx)
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Save Changes", type="primary"):
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
                                    st.success("Member updated!")
                                    del st.session_state.edit_user_id
                                    del st.session_state.edit_user_data
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Update failed: {str(e)}")
                    with col_cancel:
                        if st.form_submit_button("Cancel"):
                            del st.session_state.edit_user_id
                            del st.session_state.edit_user_data
                            st.rerun()
else:
    st.info("No team members yet • Start building your empire!")

# ────────────────────────────────────────────────
# MANUAL BADGE AWARDING – FINAL VERSION
# ────────────────────────────────────────────────
st.markdown("---")
st.subheader("🏅 Award Badges to Clients")
st.markdown("Public badges appear in landing page teaser (Empire Heroes section).")

@st.cache_data(ttl=300)
def get_badge_definitions():
    try:
        resp = supabase.table("badge_definitions").select("badge_name, description, icon_emoji, is_special, max_slots").execute()
        return {row["badge_name"]: row for row in resp.data or []}
    except:
        st.warning("No badge definitions found. Using fallback.")
        return {
            "Pioneer": {"badge_name": "Pioneer", "description": "Early joiner", "icon_emoji": "🛡️", "is_special": False, "max_slots": None},
            "VIP Elite": {"badge_name": "VIP Elite", "description": "Top contributor", "icon_emoji": "💎", "is_special": True, "max_slots": 20},
            "Consistency Star": {"badge_name": "Consistency Star", "description": "Consistent performance", "icon_emoji": "⭐", "is_special": False, "max_slots": None},
        }

badges_dict = get_badge_definitions()
badge_options = list(badges_dict.keys())

@st.cache_data(ttl=60)
def get_clients_for_badges():
    try:
        resp = supabase.table("users").select("id, username, full_name, email, role").eq("role", "client").execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Client fetch error: {str(e)}")
        return []

clients_list = get_clients_for_badges()

if not clients_list:
    st.info("No client accounts yet. Register clients above.")
else:
    with st.form("award_badge_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            client_display = [f"{c.get('full_name', 'Unknown')} ({c.get('username', 'no-username')}) – {c.get('email', 'no-email')}" for c in clients_list]
            selected_client_str = st.selectbox(
                "Select Client",
                options=[""] + client_display,
                index=0,
                placeholder="Choose a client...",
                key="badge_client_select"
            )
        with col2:
            selected_badge = st.selectbox(
                "Select Badge",
                options=[""] + badge_options,
                index=0,
                placeholder="Choose badge...",
                key="badge_type_select"
            )

        evidence = ""
        make_public = True
        if selected_badge and selected_badge != "" and badges_dict.get(selected_badge, {}).get("is_special", False):
            st.info(f"{selected_badge} is special (limited slots). Provide evidence.")
            evidence = st.text_area("Evidence / Reason (required)", height=100, placeholder="e.g. Top tester, fund contributor...")
            make_public = st.checkbox("Make public (show in landing teaser)", value=True)

        award_submitted = st.form_submit_button("AWARD BADGE 👑", type="primary", use_container_width=True)

        if award_submitted:
            if not selected_client_str or not selected_badge:
                st.error("Select both client and badge.")
            else:
                selected_client = next((c for c in clients_list if f"{c.get('full_name', 'Unknown')} ({c.get('username', 'no-username')}) – {c.get('email', 'no-email')}" == selected_client_str), None)
                if not selected_client:
                    st.error("Client not found.")
                else:
                    badge_info = badges_dict.get(selected_badge, {})
                    max_slots = badge_info.get("max_slots")
                    if max_slots is not None:
                        current_count = supabase.table("client_badges").select("count", count="exact").eq("badge_name", selected_badge).execute().count or 0
                        if current_count >= max_slots:
                            st.error(f"{selected_badge} slots full ({current_count}/{max_slots}).")
                            st.stop()
                    if badge_info.get("is_special", False) and not evidence.strip():
                        st.error("Evidence required for special badges.")
                        st.stop()

                    with st.spinner(f"Awarding {selected_badge}..."):
                        try:
                            insert_data = {
                                "user_id": selected_client["id"],
                                "badge_name": selected_badge,
                                "awarded_at": "NOW()",
                                "is_active": True,
                                "is_public": make_public,
                                "awarded_by": st.session_state.get("user_id")  # from auth.py login
                            }
                            resp = supabase.table("client_badges").insert(insert_data).execute()
                            if resp.data:
                                awarded_name = selected_client.get("full_name", selected_client["username"])
                                st.success(f"{selected_badge} awarded to {awarded_name}! 🎉")
                                if make_public:
                                    st.info("Badge is public — check landing page teaser.")
                                st.balloons()
                            else:
                                st.error("Insert failed — no data returned.")
                        except Exception as e:
                            err = str(e).lower()
                            if "duplicate" in err or "unique" in err:
                                st.info(f"{awarded_name} already has {selected_badge} badge.")
                            else:
                                st.error(f"Award failed: {str(e)}")

# ─── RECENT BADGES PREVIEW ───
st.markdown("### Recently Awarded Badges (Last 5)")
try:
    recent_badges = supabase.table("client_badges") \
        .select("badge_name, awarded_at, users!inner(full_name), is_public") \
        .order("awarded_at", desc=True) \
        .limit(5) \
        .execute().data or []
    if recent_badges:
        for b in recent_badges:
            name = b.get("users", {}).get("full_name", "Unknown")
            st.caption(f"{b['badge_name']} → {name} • {b['awarded_at'][:19]} • Public: {b['is_public']}")
    else:
        st.caption("No badges awarded yet.")
except:
    st.caption("Could not load recent badges.")

# ─── MOTIVATIONAL FOOTER ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Owner Team Control Center
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Full member CRUD • Titles sync empire-wide • Secure QR login • Realtime balances • Elite team oversight
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Led for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)