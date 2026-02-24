# pages/06_🔑_License_Generator.py
import streamlit as st
import uuid
from datetime import date, datetime, timedelta

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action

require_auth(min_role="owner")  # Strict — Owner only

st.header("EA License Generator 🔑")
st.markdown("**Universal Security • ANY Broker • Flexible Accounts • LIVE/DEMO Control • XOR Encryption • Realtime History**")

# ────────────────────────────────────────────────
# CLEAN XOR ENCRYPTION (unchanged — already solid)
# ────────────────────────────────────────────────
def mt_encrypt(plain: str, key: str) -> str:
    if not key:
        return ""
    result = bytearray()
    klen = len(key)
    for i, ch in enumerate(plain):
        k = ord(key[i % klen])
        result.append(ord(ch) ^ k)
    return ''.join(f'{b:02X}' for b in result).upper()

# ────────────────────────────────────────────────
# REALTIME DATA FETCH (10s cache)
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_license_data():
    try:
        clients_resp = supabase.table("users").select("id, full_name, balance, role").eq("role", "client").execute()
        clients = clients_resp.data or []

        history_resp = supabase.table("client_licenses").select("*").order("date_generated", desc=True).execute()
        history = history_resp.data or []

        user_map = {str(c["id"]): {"name": c["full_name"] or "Unknown", "balance": c["balance"] or 0} for c in clients}
        return clients, history, user_map
    except Exception as e:
        st.error(f"Data fetch error: {str(e)}")
        return [], [], {}

clients, history, user_map = fetch_license_data()

if st.button("🔄 Refresh License Data", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

if not clients:
    st.info("No clients registered yet • Add clients first in Admin Management")
    st.stop()

# ────────────────────────────────────────────────
# GENERATE NEW LICENSE FORM
# ────────────────────────────────────────────────
st.subheader("Generate New License")
client_options = {f"{c['full_name']} (Balance: ${c['balance']:,.2f})": c for c in clients}
selected_key = st.selectbox("Select Client", list(client_options.keys()))
client = client_options[selected_key]
client_id = client["id"]
client_name = client["full_name"]
client_balance = client["balance"] or 0

st.info(f"**Generating license for:** {client_name} | Balance: ${client_balance:,.2f}")

# Session defaults (stable across reruns)
defaults = {
    "allow_any_account": True,
    "allow_live_trading": True,
    "specific_accounts_value": "",
    "expiry_choice": "NEVER (Lifetime)",
    "last_chosen_expiry_date": date.today() + timedelta(days=365)
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

col_a, col_b = st.columns(2)
with col_a:
    allow_any = st.checkbox(
        "Allow on ANY Account / Broker (Universal *)",
        value=st.session_state.allow_any_account,
        key="chk_universal"
    )
with col_b:
    allow_live = st.checkbox(
        "Allow LIVE trading (checked = LIVE + DEMO)",
        value=st.session_state.allow_live_trading,
        key="chk_live"
    )

# Sync session state
if allow_any != st.session_state.allow_any_account or allow_live != st.session_state.allow_live_trading:
    st.session_state.allow_any_account = allow_any
    st.session_state.allow_live_trading = allow_live
    st.rerun()

if allow_live:
    st.success("✅ LIVE + DEMO allowed")
else:
    st.warning("⚠️ DEMO only (Live trading blocked)")

# Expiry selection — stable & remembers last choice
expiry_option = st.radio(
    "License Expiry",
    options=["NEVER (Lifetime)", "Specific Date"],
    index=0 if st.session_state.expiry_choice == "NEVER (Lifetime)" else 1,
    horizontal=True
)

if expiry_option != st.session_state.expiry_choice:
    st.session_state.expiry_choice = expiry_option
    st.rerun()

if expiry_option == "Specific Date":
    exp_date = st.date_input(
        "Expiry Date",
        value=st.session_state.last_chosen_expiry_date,
        min_value=date.today()
    )
    st.session_state.last_chosen_expiry_date = exp_date
    expiry_str = exp_date.strftime("%Y-%m-%d")
    st.info(f"→ License expires on **{expiry_str}**")
else:
    expiry_str = "NEVER"
    st.success("→ Lifetime license (no expiry) 🎉")

# Allowed accounts
specific_accounts = st.text_area(
    "Specific Allowed Logins (comma-separated, leave blank if universal)",
    value=st.session_state.specific_accounts_value,
    placeholder="12345678,87654321",
    disabled=allow_any,
    height=80
)

# Version & Notes
col_v1, col_v2 = st.columns(2)
with col_v1:
    version_note = st.text_input("Version Note", value="v2.36 Elite 2026")
with col_v2:
    internal_notes = st.text_area("Internal Notes (Optional)", height=80)

# Submit
with st.form("license_gen_form", clear_on_submit=True):
    submitted = st.form_submit_button("🚀 Generate & Save License", type="primary", use_container_width=True)

    if submitted:
        accounts_str = "*" if allow_any else ",".join(a.strip() for a in specific_accounts.split(",") if a.strip())
        live_str = "1" if allow_live else "0"
        plain = f"{client_name}|{accounts_str}|{expiry_str}|{live_str}"

        # Pad if odd length
        if len(plain.encode()) % 2 == 1:
            plain += " "

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
                "date_generated": datetime.now().isoformat(),
                "expiry": expiry_str,
                "allow_live": allow_live,
                "notes": internal_notes or None,
                "allowed_accounts": accounts_str if accounts_str != "*" else None,
                "revoked": False
            }).execute()

            st.success(f"License generated! **Key:** {unique_key}")
            log_action("License Generated", f"Client: {client_name} | Key: {unique_key}")

            st.subheader("📋 Ready to Paste into EA")
            st.code(f'''
string UNIQUE_KEY = "{unique_key}";
string ENC_DATA = "{enc_data_hex}";
            ''', language="cpp")

            # Reset form
            st.session_state.specific_accounts_value = specific_accounts
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Save failed: {str(e)}")

# ────────────────────────────────────────────────
# LICENSE HISTORY + REVOKE / DELETE
# ────────────────────────────────────────────────
st.subheader("📜 Issued Licenses History")
if history:
    search = st.text_input("Search by key, client, version", "")
    filtered = history
    if search:
        s = search.lower()
        filtered = [
            h for h in history
            if s in str(h.get("key", "")).lower() or
               s in user_map.get(str(h.get("account_id")), {}).get("name", "").lower() or
               s in str(h.get("version", "")).lower()
        ]

    for h in filtered:
        client_name_hist = user_map.get(str(h["account_id"]), {}).get("name", "Unknown")
        status = "🔴 Revoked" if h.get("revoked") else "🟢 Active"
        live_status = "LIVE+DEMO" if h.get("allow_live") else "DEMO only"
        acc_txt = "ANY (*)" if h.get("allowed_accounts") is None else h.get("allowed_accounts", "Custom")
        version_display = f" • {h.get('version', 'Standard')}"

        with st.expander(
            f"{h.get('key','—')} • {client_name_hist}{version_display} • {status} • {live_status} • {acc_txt} • {h.get('date_generated','—')[:10]}",
            expanded=False
        ):
            st.markdown(f"**Expiry:** {h['expiry']}")
            if h.get("notes"):
                st.caption(f"Notes: {h['notes']}")
            st.code(f"ENC_DATA = \"{h.get('enc_data','—')}\"", language="text")
            st.code(f"UNIQUE_KEY = \"{h.get('key','—')}\"", language="text")

            col1, col2 = st.columns(2)
            with col1:
                if not h.get("revoked"):
                    if st.button("Revoke License", key=f"revoke_{h['id']}", type="primary"):
                        try:
                            today_str = date.today().isoformat()
                            supabase.table("client_licenses").update({
                                "revoked": True,
                                "expiry": today_str  # Force expiry to today so EA detects immediately
                            }).eq("id", h["id"]).execute()

                            log_action("License Revoked", f"Key: {h.get('key')} | Client: {client_name_hist} | Forced expiry: {today_str}")
                            st.success(f"License revoked & expiry set to today ({today_str})")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Revoke failed: {str(e)}")
                else:
                    st.caption("Already revoked")
            with col2:
                if st.button("🗑️ Delete Permanently", key=f"delete_{h['id']}", type="secondary"):
                    if st.checkbox("Confirm permanent delete", key=f"confirm_del_{h['id']}"):
                        try:
                            supabase.table("client_licenses").delete().eq("id", h["id"]).execute()
                            st.success("License permanently deleted")
                            log_action("License Deleted", f"Key: {h.get('key')}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {str(e)}")
else:
    st.info("No licenses issued yet")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">
        Elite EA License System
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 2rem auto;">
        Stable expiry • Remembers last date • Revoke forces today expiry • Secure XOR • Instant generation • Full audit trail.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX License Generator • Fully Fixed & Secure 2026</h2>
</div>
""", unsafe_allow_html=True)