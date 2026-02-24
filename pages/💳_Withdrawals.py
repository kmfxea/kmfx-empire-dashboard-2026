# pages/11_💳_Withdrawals.py
import streamlit as st
import pandas as pd
from datetime import datetime
import requests

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import upload_to_supabase, log_action

require_auth()  # Lahat authenticated, pero role-based access

st.header("Withdrawal Management 💳")
st.markdown("**Empire payout engine: Clients request from earned balances • Permanent proof upload • Owner approve/pay/reject • Auto-deduct on paid • Realtime sync & transparency**")

current_role = st.session_state.get("role", "guest")
my_name = st.session_state.full_name

# ────────────────────────────────────────────────
# REALTIME CACHE (10s TTL)
# ────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_withdrawals_full():
    try:
        wd_resp = supabase.table("withdrawals").select("*").order("date_requested", desc=True).execute()
        withdrawals = wd_resp.data or []

        users_resp = supabase.table("users").select("id, full_name, balance, role").execute()
        users = users_resp.data or []

        user_map = {u["full_name"]: {"id": u["id"], "balance": u["balance"] or 0.0} for u in users}

        # All proofs (para sa related display)
        proofs_resp = supabase.table("client_files").select(
            "id, original_name, file_url, storage_path, category, assigned_client, notes, upload_date"
        ).order("upload_date", desc=True).execute()
        proofs = proofs_resp.data or []

        return withdrawals, user_map, proofs
    except Exception as e:
        st.error(f"Withdrawals load error: {str(e)}")
        return [], {}, []

withdrawals, user_map, proofs = fetch_withdrawals_full()

if st.button("🔄 Refresh Withdrawals Now", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.rerun()

st.caption("🔄 Withdrawals auto-refresh every 10s • Proofs permanent & visible")

# ────────────────────────────────────────────────
# CLIENT VIEW: Sariling requests + new request
# ────────────────────────────────────────────────
if current_role == "client":
    my_balance = user_map.get(my_name, {"balance": 0.0})["balance"]
    my_withdrawals = [w for w in withdrawals if w["client_name"] == my_name]

    st.subheader(f"Your Withdrawals • Available Balance: **${my_balance:,.2f}**")

    if my_balance > 0:
        with st.expander("➕ Request New Withdrawal", expanded=True):
            with st.form("client_wd_request", clear_on_submit=True):
                amount = st.number_input("Amount (USD)", min_value=1.0, max_value=my_balance, step=50.0)
                method = st.selectbox("Method", ["USDT", "Bank Transfer", "Wise", "PayPal", "GCash", "Other"])
                details = st.text_area("Payout Details (Wallet / Bank Info / etc.)")
                proof_file = st.file_uploader("Upload Proof * (Permanent)", type=["png", "jpg", "jpeg", "pdf", "gif"])

                submitted = st.form_submit_button("Submit Request", type="primary", use_container_width=True)

                if submitted:
                    if amount > my_balance:
                        st.error("Amount exceeds your available balance")
                    elif not proof_file:
                        st.error("Proof upload is required")
                    else:
                        try:
                            url, path = upload_to_supabase(
                                file=proof_file,
                                bucket="client_files",
                                folder="withdrawal_proofs"
                            )

                            supabase.table("client_files").insert({
                                "original_name": proof_file.name,
                                "file_url": url,
                                "storage_path": path,
                                "upload_date": datetime.now().isoformat(),
                                "sent_by": my_name,
                                "category": "Withdrawal Proof",
                                "assigned_client": my_name,
                                "notes": f"Proof for ${amount:,.2f} withdrawal request"
                            }).execute()

                            supabase.table("withdrawals").insert({
                                "client_name": my_name,
                                "amount": amount,
                                "method": method,
                                "details": details,
                                "status": "Pending",
                                "date_requested": datetime.now().isoformat()
                            }).execute()

                            log_action("Withdrawal Request Submitted", f"Amount: ${amount:,.2f}")
                            st.success("Request submitted! Proof permanently stored • Owner will review soon")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Submission failed: {str(e)}")
    else:
        st.info("No available balance yet • Earnings accumulate from profits")

    # Client history
    st.subheader("Your Request History")
    if my_withdrawals:
        for w in my_withdrawals:
            status_colors = {"Pending": "#ffa502", "Approved": "#00ffaa", "Paid": "#2ed573", "Rejected": "#ff4757"}
            color = status_colors.get(w["status"], "#888888")
            st.markdown(f"""
            <div class='glass-card' style='padding:1.6rem; border-left:6px solid {color}; margin-bottom:1rem;'>
                <h4 style='margin:0;'>${w['amount']:,.2f} • <span style='color:{color};'>{w['status']}</span></h4>
                <small>Method: {w['method']} • Requested: {w['date_requested'][:10]}</small>
            </div>
            """, unsafe_allow_html=True)
            if w.get("details"):
                with st.expander("Payout Details"):
                    st.write(w["details"])
            st.divider()
    else:
        st.info("No withdrawal requests yet")

# ────────────────────────────────────────────────
# ADMIN/OWNER VIEW: Lahat ng requests + actions
# ────────────────────────────────────────────────
else:
    st.subheader("All Empire Withdrawal Requests")
    if withdrawals:
        for w in withdrawals:
            client_balance = user_map.get(w["client_name"], {"balance": 0.0})["balance"]
            status_colors = {"Pending": "#ffa502", "Approved": "#00ffaa", "Paid": "#2ed573", "Rejected": "#ff4757"}
            color = status_colors.get(w["status"], "#888888")

            with st.container(border=True):
                st.markdown(f"""
                <div class='glass-card' style='padding:1.8rem; border-left:6px solid {color};'>
                    <h4 style='margin:0;'>{w['client_name']} • ${w['amount']:,.2f} • <span style='color:{color};'>{w['status']}</span></h4>
                    <small>Method: {w['method']} • Requested: {w['date_requested'][:10]} • Balance: ${client_balance:,.2f}</small>
                </div>
                """, unsafe_allow_html=True)

                if w.get("details"):
                    with st.expander("Payout Details"):
                        st.write(w["details"])

                # Related proofs
                related_proofs = [
                    p for p in proofs
                    if p.get("assigned_client") == w["client_name"]
                    and "withdrawal" in (p.get("category") or "").lower()
                    and "proof" in (p.get("notes") or "").lower()
                ]

                if related_proofs:
                    st.markdown("**Attached Proofs (Permanent):**")
                    proof_cols = st.columns(min(4, len(related_proofs)))
                    for idx, p in enumerate(related_proofs):
                        file_url = p.get("file_url")
                        if file_url:
                            with proof_cols[idx % len(proof_cols)]:
                                if p["original_name"].lower().endswith(('.png','.jpg','.jpeg','.gif')):
                                    st.image(file_url, caption=p["original_name"], use_column_width=True)
                                else:
                                    st.markdown(f"**{p['original_name']}** • {p['upload_date'][:10]}")
                                    try:
                                        r = requests.get(file_url, timeout=8)
                                        if r.status_code == 200:
                                            st.download_button(
                                                f"⬇ {p['original_name']}",
                                                r.content,
                                                p["original_name"],
                                                use_container_width=True,
                                                key=f"proof_dl_{p['id']}"
                                            )
                                    except:
                                        st.caption("Download unavailable")

                # Actions
                col_act1, col_act2, col_act3 = st.columns(3)
                if w["status"] == "Pending":
                    with col_act1:
                        if st.button("Approve", key=f"approve_{w['id']}", use_container_width=True):
                            try:
                                supabase.table("withdrawals").update({
                                    "status": "Approved",
                                    "date_processed": datetime.now().isoformat(),
                                    "processed_by": my_name
                                }).eq("id", w["id"]).execute()
                                log_action("Withdrawal Approved", f"ID: {w['id']} | Amount: ${w['amount']}")
                                st.success("Approved!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

                    with col_act2:
                        if st.button("Reject", key=f"reject_{w['id']}", use_container_width=True, type="secondary"):
                            try:
                                supabase.table("withdrawals").update({
                                    "status": "Rejected",
                                    "date_processed": datetime.now().isoformat(),
                                    "processed_by": my_name
                                }).eq("id", w["id"]).execute()
                                log_action("Withdrawal Rejected", f"ID: {w['id']} | Amount: ${w['amount']}")
                                st.success("Rejected")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

                if w["status"] == "Approved":
                    with col_act1:
                        if st.button("Mark as Paid → Auto-Deduct", key=f"paid_{w['id']}", type="primary", use_container_width=True):
                            try:
                                client_id = user_map.get(w["client_name"], {}).get("id")
                                if client_id:
                                    new_balance = max(0.0, client_balance - w["amount"])
                                    supabase.table("users").update({"balance": new_balance}).eq("id", client_id).execute()
                                supabase.table("withdrawals").update({
                                    "status": "Paid",
                                    "date_processed": datetime.now().isoformat(),
                                    "processed_by": my_name
                                }).eq("id", w["id"]).execute()
                                log_action("Withdrawal Paid", f"ID: {w['id']} | Deducted: ${w['amount']}")
                                st.success("Marked as Paid • Balance auto-deducted!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

                st.divider()
    else:
        st.info("No withdrawal requests yet • Empire cashflow smooth")

# ────────────────────────────────────────────────
# MOTIVATIONAL FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class='glass-card' style='padding:4rem 2rem; text-align:center; margin:4rem 0; border: 2px solid #00ffaa; border-radius: 30px;'>
    <h1 style="background: linear-gradient(90deg, #00ffaa, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">
        Secure & Automatic Payouts
    </h1>
    <p style="font-size: 1.4rem; opacity: 0.9; max-width: 900px; margin: 2rem auto;">
        Permanent proofs • Balance-limited requests • Instant approve/pay/reject • Auto-deduct on paid • Realtime everywhere • Empire cashflow elite.
    </p>
    <h2 style="color: #ffd700; font-size: 2.2rem;">👑 KMFX Withdrawals • Cloud Permanent 2026</h2>
</div>
""", unsafe_allow_html=True)