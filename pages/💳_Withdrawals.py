import streamlit as st
import requests
from datetime import date

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase, upload_to_supabase  # ← FIXED: added upload_to_supabase

render_sidebar()
require_auth(min_role="client")  # clients request, admin/owner manage

# ─── THEME (consistent across app) ───
accent_primary = "#00ffaa"
accent_gold = "#ffd700"
accent_glow = "#00ffaa40"

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

st.header("💳 Withdrawal Management")
st.markdown("**Empire payout engine** • Clients request from earned balances • Permanent proof upload • Owner approve/pay/reject • Auto-deduct on paid • Realtime sync & full transparency")

current_role = st.session_state.get("role", "guest").lower()

# ─── ULTRA-REALTIME FETCH (10s TTL) ───
@st.cache_data(ttl=10, show_spinner="Syncing withdrawals & proofs...")
def fetch_withdrawals_full():
    try:
        withdrawals = supabase.table("withdrawals").select("*").order("date_requested", desc=True).execute().data or []
        users = supabase.table("users").select("id, full_name, balance, role").execute().data or []
        user_map = {u["full_name"]: {"id": u["id"], "balance": u.get("balance", 0)} for u in users}
        proofs = supabase.table("client_files").select(
            "id, original_name, file_url, storage_path, category, assigned_client, notes, upload_date"
        ).order("upload_date", desc=True).execute().data or []
        return withdrawals, user_map, proofs
    except Exception as e:
        st.error(f"Withdrawals sync error: {str(e)}")
        return [], {}, []

withdrawals, user_map, proofs = fetch_withdrawals_full()

if st.button("🔄 Refresh Withdrawals Now", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Withdrawals auto-refresh every 10s • Proofs permanent & fully visible in Supabase Storage")

# ─── CLIENT VIEW ───
if current_role == "client":
    my_name = st.session_state.get("full_name", "")
    my_data = user_map.get(my_name, {"id": None, "balance": 0})
    my_balance = my_data["balance"]
    my_withdrawals = [w for w in withdrawals if w.get("client_name") == my_name]

    st.subheader(f"Your Withdrawals • Available: **${my_balance:,.2f}**")

    # Request form
    if my_balance > 0:
        with st.expander("➕ Request New Withdrawal", expanded=True):
            with st.form("client_wd_form", clear_on_submit=True):
                amount = st.number_input("Amount (USD)", min_value=1.0, max_value=my_balance, step=100.0, format="%.2f")
                method = st.selectbox("Method", ["USDT", "Bank Transfer", "Wise", "PayPal", "GCash", "Other"])
                details = st.text_area("Payout Details (Wallet/Address/Bank Info)", placeholder="e.g. USDT: 0x... or Bank: Account #12345")
                proof = st.file_uploader("Upload Proof * (Permanent)", type=["png", "jpg", "jpeg", "pdf", "gif"])
                submitted = st.form_submit_button("Submit Request", type="primary", use_container_width=True)

                if submitted:
                    if amount > my_balance:
                        st.error("Amount exceeds your balance")
                    elif not proof:
                        st.error("Proof document is required")
                    else:
                        with st.spinner("Submitting request..."):
                            try:
                                url, storage_path = upload_to_supabase(
                                    file=proof,
                                    bucket="client_files",
                                    folder="withdrawals"
                                )

                                # Save proof permanently
                                supabase.table("client_files").insert({
                                    "original_name": proof.name,
                                    "file_url": url,
                                    "storage_path": storage_path,
                                    "upload_date": date.today().isoformat(),
                                    "sent_by": my_name,
                                    "category": "Withdrawal Proof",
                                    "assigned_client": my_name,
                                    "notes": f"Proof for ${amount:,.2f} withdrawal request"
                                }).execute()

                                # Create withdrawal request
                                supabase.table("withdrawals").insert({
                                    "client_name": my_name,
                                    "amount": amount,
                                    "method": method,
                                    "details": details.strip() or None,
                                    "status": "Pending",
                                    "date_requested": date.today().isoformat()
                                }).execute()

                                st.success("Withdrawal request submitted with permanent proof!")
                                st.balloons()
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Submission failed: {str(e)}")
    else:
        st.info("No available balance yet • Earnings from profits will appear here")

    # Client history
    st.subheader("Your Request History")
    if my_withdrawals:
        for w in my_withdrawals:
            status_color = {
                "Pending": "#ffa502",
                "Approved": accent_primary,
                "Paid": "#2ed573",
                "Rejected": "#ff4757"
            }.get(w.get("status"), "#888888")
            st.markdown(f"""
            <div style="
                background:rgba(30,35,45,0.7);
                backdrop-filter:blur(12px);
                border-radius:16px;
                padding:1.6rem;
                margin-bottom:1.2rem;
                border-left:6px solid {status_color};
            ">
                <h4 style="margin:0;">${w['amount']:,.2f} • <span style="color:{status_color};">{w['status']}</span></h4>
                <small>Method: {w.get('method', '—')} • Requested: {w.get('date_requested', '—')}</small>
            </div>
            """, unsafe_allow_html=True)
            if w.get("details"):
                with st.expander("Payout Details"):
                    st.write(w["details"])
            st.divider()
    else:
        st.info("No withdrawal requests yet")

# ─── ADMIN/OWNER VIEW ───
else:
    st.subheader("All Empire Withdrawal Requests")
    if withdrawals:
        for w in withdrawals:
            client_balance = user_map.get(w.get("client_name"), {"balance": 0})["balance"]
            status_color = {
                "Pending": "#ffa502",
                "Approved": accent_primary,
                "Paid": "#2ed573",
                "Rejected": "#ff4757"
            }.get(w.get("status"), "#888888")
            with st.container():
                st.markdown(f"""
                <div style="
                    background:rgba(30,35,45,0.7);
                    backdrop-filter:blur(12px);
                    border-radius:16px;
                    padding:1.8rem;
                    margin-bottom:1.6rem;
                    border-left:6px solid {status_color};
                    border:1px solid rgba(100,100,100,0.25);
                ">
                    <h4 style="margin:0;">{w.get('client_name', '—')} • ${w['amount']:,.2f} • <span style="color:{status_color};">{w['status']}</span></h4>
                    <small>Method: {w.get('method', '—')} • Requested: {w.get('date_requested', '—')} • Balance: ${client_balance:,.2f}</small>
                </div>
                """, unsafe_allow_html=True)
                if w.get("details"):
                    with st.expander("Payout Details"):
                        st.write(w["details"])

                # Related permanent proofs
                related_proofs = [
                    p for p in proofs
                    if p.get("assigned_client") == w.get("client_name")
                    and p.get("category") in ["Withdrawal Proof", "Payout Proof"]
                    and "withdrawal" in str(p.get("notes") or "").lower()
                ]
                if related_proofs:
                    st.markdown("**Attached Proofs (Permanent):**")
                    proof_cols = st.columns(min(4, len(related_proofs)))
                    for idx, p in enumerate(related_proofs):
                        file_url = p.get("file_url")
                        if file_url:
                            with proof_cols[idx % 4]:
                                if p["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif')):
                                    st.image(file_url, caption=p["original_name"], use_container_width=True)
                                else:
                                    st.markdown(f"**{p['original_name']}** • {p.get('upload_date', '—')}")
                                    try:
                                        r = requests.get(file_url, timeout=10)
                                        if r.status_code == 200:
                                            st.download_button(
                                                f"Download {p['original_name']}",
                                                data=r.content,
                                                file_name=p["original_name"],
                                                use_container_width=True,
                                                key=f"proof_dl_{p['id']}_{idx}"
                                            )
                                    except:
                                        st.caption("Download unavailable")

                # Actions
                if w["status"] == "Pending":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Approve", key=f"app_{w['id']}", use_container_width=True):
                            try:
                                supabase.table("withdrawals").update({
                                    "status": "Approved",
                                    "date_processed": date.today().isoformat(),
                                    "processed_by": st.session_state.get("full_name", "Admin")
                                }).eq("id", w["id"]).execute()
                                st.success("Request approved!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Approve failed: {str(e)}")
                    with col2:
                        if st.button("Reject", key=f"rej_{w['id']}", type="secondary", use_container_width=True):
                            try:
                                supabase.table("withdrawals").update({
                                    "status": "Rejected",
                                    "date_processed": date.today().isoformat(),
                                    "processed_by": st.session_state.get("full_name", "Admin")
                                }).eq("id", w["id"]).execute()
                                st.success("Request rejected")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Reject failed: {str(e)}")

                if w["status"] == "Approved":
                    if st.button("Mark as Paid → Auto-Deduct Balance", key=f"paid_{w['id']}", type="primary", use_container_width=True):
                        try:
                            client_id = user_map.get(w.get("client_name"), {}).get("id")
                            if client_id:
                                new_bal = max(0, client_balance - w["amount"])
                                supabase.table("users").update({"balance": new_bal}).eq("id", client_id).execute()
                            supabase.table("withdrawals").update({
                                "status": "Paid",
                                "date_processed": date.today().isoformat(),
                                "processed_by": st.session_state.get("full_name", "Admin")
                            }).eq("id", w["id"]).execute()
                            st.success("Marked as paid • Balance auto-deducted!")
                            st.balloons()
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Pay failed: {str(e)}")

                st.divider()
    else:
        st.info("No withdrawal requests yet • Empire cashflow is smooth")

# ─── MOTIVATIONAL FOOTER (sync style) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Secure & Automatic Empire Payouts
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Permanent proofs • Balance-checked requests • Instant approve/pay/reject • Auto-deduct • Realtime transparency
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith • Flowing for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)