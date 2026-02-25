# pages/🔑_License_Generator.py
import streamlit as st
from datetime import date, datetime, timedelta

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="owner")  # strict — owner only

# ─── THEME (sync across all pages) ───
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

st.header("🔑 EA License Generator")
st.markdown("**Universal Security** • ANY Broker • Flexible Accounts • LIVE/DEMO Control • XOR Encryption • Realtime History & Revoke")

if st.session_state.get("role", "").lower() != "owner":
    st.error("🔒 Access Denied — Owner only feature")
    st.stop()

# ─── CLEAN XOR ENCRYPTION (unchanged) ───
def mt_encrypt(plain: str, key: str) -> str:
    if not key:
        return ""
    result = bytearray()
    klen = len(key)
    for i, ch in enumerate(plain):
        k = ord(key[i % klen])
        result.append(ord(ch) ^ k)
    return ''.join(f'{b:02X}' for b in result).upper()

# ─── REALTIME DATA FETCH (10s TTL) ───
@st.cache_data(ttl=10, show_spinner="Syncing clients & licenses...")
def fetch_license_data():
    try:
        clients = supabase.table("users").select("id, full_name, balance, role").eq("role", "client").execute().data or []
        history = supabase.table("client_licenses").select("*").order("date_generated", desc=True).execute().data or []
        user_map = {str(c["id"]): {"name": c["full_name"] or "Unknown", "balance": c["balance"] or 0} for c in clients}
        return clients, history, user_map
    except Exception as e:
        st.error(f"License data sync error: {str(e)}")
        return [], [], {}

clients, history, user_map = fetch_license_data()

if st.button("🔄 Refresh License Data", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if not clients:
    st.info("No clients registered yet • Add via Team Management or Users page")
    st.stop()

# ─── GENERATE NEW LICENSE ───
st.subheader("Generate New License")
client_options = {f"{c['full_name']} (Balance: ${c['balance'] or 0:,.2f})": c for c in clients}
selected_key = st.selectbox("Select Client", list(client_options.keys()))
client = client_options[selected_key]
client_id = client["id"]
client_name = client["full_name"]
client_balance = client["balance"] or 0

st.info(f"**Generating license for:** {client_name} • Balance: **${client_balance:,.2f}**")

# Session state defaults (stable across reruns)
defaults = {
    "allow_any_account": True,
    "allow_live_trading": True,
    "specific_accounts_value": "",
    "expiry_choice": "NEVER (Lifetime)"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

col_a, col_b = st.columns(2)
with col_a:
    allow_any = st.checkbox("Allow on **ANY** Account / Broker (Universal)", value=st.session_state.allow_any_account, key="chk_universal")
with col_b:
    allow_live = st.checkbox("Allow **LIVE** trading (checked = LIVE + DEMO)", value=st.session_state.allow_live_trading, key="chk_live")

# Persist checkbox changes
if allow_any != st.session_state.allow_any_account or allow_live != st.session_state.allow_live_trading:
    st.session_state.allow_any_account = allow_any
    st.session_state.allow_live_trading = allow_live
    st.rerun()

if allow_live:
    st.success("✅ LIVE + DEMO allowed")
else:
    st.warning("⚠️ DEMO trading only (LIVE blocked)")

# ─── EXPIRY SELECTION (stable & fixed) ───
expiry_option = st.radio(
    "License Expiry",
    options=["NEVER (Lifetime)", "Specific Date"],
    index=0 if st.session_state.expiry_choice == "NEVER (Lifetime)" else 1,
    horizontal=True
)

if expiry_option != st.session_state.expiry_choice:
    st.session_state.expiry_choice = expiry_option

if expiry_option == "Specific Date":
    default_exp = st.session_state.get("last_chosen_expiry_date", date.today() + timedelta(days=365))
    exp_date = st.date_input("Expiry Date", value=default_exp, min_value=date.today())
    st.session_state.last_chosen_expiry_date = exp_date
    expiry_str = exp_date.strftime("%Y-%m-%d")
    st.info(f"→ License expires on **{expiry_str}**")
else:
    expiry_str = "NEVER"
    st.success("→ Lifetime license (no expiry) 🎉")

# ─── GENERATION FORM ───
with st.form("license_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        specific_accounts = st.text_area(
            "Specific Allowed Logins (comma-separated)",
            placeholder="12345678,87654321 (leave blank if universal)",
            value=st.session_state.specific_accounts_value,
            disabled=allow_any,
            height=110
        )
    with col2:
        version_note = st.text_input("Version Note", value="v2.36 Elite 2026")
        internal_notes = st.text_area("Internal Notes (optional)", height=110)

    submitted = st.form_submit_button("🚀 Generate & Save License", type="primary", use_container_width=True)

    if submitted:
        accounts_str = "*" if allow_any else ",".join(a.strip() for a in specific_accounts.split(",") if a.strip())
        live_str = "1" if allow_live else "0"
        plain = f"{client_name}|{accounts_str}|{expiry_str}|{live_str}"
        if len(plain.encode()) % 2 == 1:
            plain += " "  # padding for even length

        name_clean = "".join(c for c in client_name.upper() if c.isalnum())
        key_date = "NEVER" if expiry_str == "NEVER" else expiry_str[8:] + expiry_str[5:7] + expiry_str[2:4]
        unique_key = f"KMFX_{name_clean}_{key_date}"
        enc_data_hex = mt_encrypt(plain, unique_key)

        try:
            supabase.table("client_licenses").insert({
                "account_id": client_id,
                "key": unique_key,
                "enc_data": enc_data_hex,
                "version": version_note,
                "date_generated": date.today().isoformat(),
                "expiry": expiry_str,
                "allow_live": allow_live,
                "notes": internal_notes or None,
                "allowed_accounts": accounts_str if accounts_str != "*" else None,
                "revoked": False
            }).execute()

            st.success(f"License **{unique_key}** generated & saved!")
            st.balloons()

            # Reset form
            st.session_state.specific_accounts_value = ""
            st.session_state.expiry_choice = "NEVER (Lifetime)"
            if "last_chosen_expiry_date" in st.session_state:
                del st.session_state.last_chosen_expiry_date

            st.subheader("📋 Ready to Paste into EA")
            st.code(f'''
string UNIQUE_KEY = "{unique_key}";
string ENC_DATA   = "{enc_data_hex}";
            ''', language="cpp")

            st.cache_data.clear()
            st.rerun()

        except Exception as e:
            st.error(f"Save failed: {str(e)}")

# ─── LICENSE HISTORY ───
st.subheader("📜 Issued Licenses History (Realtime)")
if history:
    search_term = st.text_input("Search by key, client name, or version", "")
    filtered = history
    if search_term:
        s = search_term.lower()
        filtered = [
            h for h in history
            if s in str(h.get("key", "")).lower()
            or s in user_map.get(str(h.get("account_id")), {}).get("name", "").lower()
            or s in str(h.get("version", "")).lower()
        ]

    for h in filtered:
        client_hist = user_map.get(str(h["account_id"]), {}).get("name", "Unknown")
        status = "🔴 Revoked" if h.get("revoked") else "🟢 Active"
        live_status = "LIVE+DEMO" if h.get("allow_live") else "DEMO only"
        acc_txt = "ANY (*)" if h.get("allowed_accounts") is None else h.get("allowed_accounts", "Custom")
        version_disp = f" • {h.get('version', 'Standard')}"

        with st.expander(
            f"{h.get('key','—')} • {client_hist}{version_disp} • {status} • {live_status} • {acc_txt} • {h.get('date_generated','—')}",
            expanded=False
        ):
            st.markdown(f"**Expiry:** {h['expiry']}")
            if h.get("notes"):
                st.caption(f"Notes: {h['notes']}")

            st.code(f"ENC_DATA   = \"{h.get('enc_data','—')}\"", language="text")
            st.code(f"UNIQUE_KEY = \"{h.get('key','—')}\"", language="text")

            col_rev, col_del = st.columns(2)
            with col_rev:
                if not h.get("revoked"):
                    if st.button("Revoke License", key=f"rev_{h['id']}"):
                        try:
                            expiry_raw = h.get("expiry")
                            if expiry_raw == "NEVER":
                                effective_exp = None
                            else:
                                try:
                                    effective_exp = datetime.strptime(expiry_raw, "%Y-%m-%d").date()
                                except:
                                    effective_exp = date(2000, 1, 1)

                            today = date.today()
                            today_str = today.isoformat()
                            already_exp = effective_exp is not None and effective_exp < today

                            supabase.table("client_licenses").update({
                                "revoked": True,
                                "expiry": today_str
                            }).eq("id", h["id"]).execute()

                            msg = f"Revoked • Expiry forced to **{today_str}**"
                            if already_exp:
                                msg += " (was already expired)"
                            st.success(msg)
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Revoke failed: {str(e)}")
                else:
                    st.caption("Already revoked")

            with col_del:
                if st.button("🗑️ Delete Permanently", key=f"del_{h['id']}", type="secondary"):
                    try:
                        supabase.table("client_licenses").delete().eq("id", h["id"]).execute()
                        st.success("License deleted permanently")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {str(e)}")
else:
    st.info("No licenses issued yet • Generate one above")

# ─── MOTIVATIONAL FOOTER (sync style) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Elite EA License System • Secure & Realtime
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Universal • XOR Encrypted • Lifetime or Expiry • Revoke forces today • Instant sync
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Protected for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)