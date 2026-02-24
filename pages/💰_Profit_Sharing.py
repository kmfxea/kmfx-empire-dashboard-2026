# pages/04_💰_Profit_Sharing.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action

require_auth(min_role="admin")  # Owner & Admin lang pwede mag-record

st.header("Profit Sharing & Auto-Distribution 💰")
st.markdown("**Empire engine: Record FTMO profit → Auto-split via stored v2 tree • Balances + Growth Fund updated realtime • Premium HTML email to all involved**")

# ────────────────────────────────────────────────
#  CACHED DATA FETCH
# ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_profit_data():
    try:
        accounts = supabase.table("ftmo_accounts").select(
            "id, name, current_phase, current_equity, "
            "participants_v2, contributors_v2, contributor_share_pct"
        ).execute().data or []
        users = supabase.table("users").select("id, full_name, email, balance").execute().data or []
        user_id_to_display = {str(u["id"]): u["full_name"] for u in users}
        user_id_to_email = {str(u["id"]): u.get("email") for u in users}
        user_id_to_balance = {str(u["id"]): u.get("balance", 0.0) for u in users}
        return accounts, users, user_id_to_display, user_id_to_email, user_id_to_balance
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return [], [], {}, {}, {}

accounts, raw_users, user_id_to_display, user_id_to_email, user_id_to_balance = fetch_profit_data()

if not accounts:
    st.info("No FTMO accounts yet • Launch one first in FTMO Accounts page")
    st.stop()

# Account selector
account_options = {
    f"{a['name']} • Phase: {a['current_phase']} • Equity ${a.get('current_equity', 0):,.0f} • Pool {a.get('contributor_share_pct', 0):.1f}%": a
    for a in accounts
}
selected_key = st.selectbox("Select Account to Record Profit For", list(account_options.keys()))
acc = account_options[selected_key]
acc_id = acc["id"]
acc_name = acc["name"]

# Force v2 structures
participants = acc.get("participants_v2", [])
contributors = acc.get("contributors_v2", [])
contributor_share_pct = acc.get("contributor_share_pct", 0.0)

if not participants:
    st.error("This account is missing v2 participant tree • Please re-edit in FTMO Accounts page to migrate/fix")
    st.stop()

st.success(f"**Recording profit for:** {acc_name} • Contributor Pool: {contributor_share_pct:.1f}% • v2 tree active")

# ────────────────────────────────────────────────
#  PROFIT RECORD FORM
# ────────────────────────────────────────────────
with st.form("profit_record_form", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        gross_profit = st.number_input("Gross Profit Received (USD) *", min_value=0.01, step=500.0, format="%.2f")
    with col2:
        record_date = st.date_input("Record Date", value=date.today())

    # Stored Tree Preview
    st.subheader("Stored Distribution Tree (edit in FTMO Accounts)")
    part_df = pd.DataFrame([{
        "Name": user_id_to_display.get(str(p.get("user_id")), p.get("display_name", "Unknown")) if p.get("user_id") else p.get("display_name", "Unknown"),
        "Role": p.get("role", ""),
        "%": f"{p['percentage']:.2f}"
    } for p in participants])
    st.dataframe(part_df, use_container_width=True, hide_index=True)

    # Calculations & Previews
    if gross_profit > 0:
        contributor_pool = gross_profit * (contributor_share_pct / 100)
        gf_add = 0.0
        part_preview = []
        contrib_preview = []
        involved_user_ids = set()

        total_funded_php = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors)

        # Contributor Pool pro-rata
        if contributor_pool > 0 and total_funded_php > 0:
            for c in contributors:
                uid = str(c.get("user_id"))
                if not uid:
                    continue
                involved_user_ids.add(uid)
                funded = c.get("units", 0) * c.get("php_per_unit", 0)
                share = contributor_pool * (funded / total_funded_php)
                display = user_id_to_display.get(uid, "Unknown")
                contrib_preview.append({
                    "Name": display,
                    "Funded PHP": f"₱{funded:,.0f}",
                    "Share": f"${share:,.2f}"
                })

        # All participants (incl. Growth Fund)
        for p in participants:
            uid = str(p.get("user_id")) if p.get("user_id") else None
            display = user_id_to_display.get(uid, p.get("display_name", "Unknown")) if uid else p.get("display_name", "Unknown")
            share = gross_profit * (p["percentage"] / 100)
            if "growth fund" in display.lower():
                gf_add += share
            part_preview.append({
                "Name": display,
                "%": f"{p['percentage']:.2f}",
                "Share": f"${share:,.2f}"
            })
            if uid:
                involved_user_ids.add(uid)

        col_prev1, col_prev2 = st.columns(2)
        with col_prev1:
            st.subheader("Contributor Pool Preview")
            if contrib_preview:
                st.dataframe(pd.DataFrame(contrib_preview), use_container_width=True, hide_index=True)
            else:
                st.info("No contributors or 0% pool")

        with col_prev2:
            st.subheader("Full Participants Preview")
            st.dataframe(pd.DataFrame(part_preview), use_container_width=True, hide_index=True)

        # Metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Gross Profit", f"${gross_profit:,.2f}")
        col_m2.metric("Contributor Pool", f"${contributor_pool:,.2f}")
        col_m3.metric("Growth Fund Add", f"${gf_add:,.2f}")

        # Sankey Preview
        st.subheader("Distribution Flow Preview")
        labels = [f"Gross ${gross_profit:,.0f}"]
        values = []
        source = []
        target = []
        idx = 1

        if contributor_pool > 0:
            labels.append("Contributor Pool")
            values.append(contributor_pool)
            source.append(0)
            target.append(idx)
            contrib_idx = idx
            idx += 1
            for cp in contrib_preview:
                share = float(cp["Share"].replace("$", "").replace(",", ""))
                labels.append(cp["Name"])
                values.append(share)
                source.append(contrib_idx)
                target.append(idx)
                idx += 1

        for pp in part_preview:
            share = float(pp["Share"].replace("$", "").replace(",", ""))
            labels.append(pp["Name"])
            values.append(share)
            source.append(0)
            target.append(idx)
            idx += 1

        fig = go.Figure(data=[go.Sankey(
            node=dict(pad=20, thickness=30, label=labels,
                      color=["#00ffaa"] + ["#ffd700"]*len(contrib_preview) + ["#00cc99"]*len(part_preview)),
            link=dict(source=source, target=target, value=values)
        )])
        fig.update_layout(title="Auto-Distribution Flow", height=600)
        st.plotly_chart(fig, use_container_width=True)

    # Submit
    submitted = st.form_submit_button("🚀 Record & Auto-Distribute Profit", type="primary", use_container_width=True)

    if submitted:
        if gross_profit <= 0:
            st.error("Gross profit must be greater than 0")
        else:
            try:
                # 1. Record the profit entry
                profit_resp = supabase.table("profits").insert({
                    "account_id": acc_id,
                    "gross_profit": gross_profit,
                    "record_date": str(record_date),
                    "growth_fund_add": gf_add,
                    "contributor_share_pct": contributor_share_pct
                }).execute()
                profit_id = profit_resp.data[0]["id"]

                distributions = []
                balance_updates = []

                # 2. Contributor Pool pro-rata
                if contributor_pool > 0 and total_funded_php > 0:
                    for c in contributors:
                        uid = str(c.get("user_id"))
                        if not uid:
                            continue
                        funded = c.get("units", 0) * c.get("php_per_unit", 0)
                        share = contributor_pool * (funded / total_funded_php)
                        pro_rata_pct = (funded / total_funded_php) * 100
                        display = user_id_to_display.get(uid, "Unknown")
                        distributions.append({
                            "profit_id": profit_id,
                            "participant_name": display,
                            "participant_user_id": uid,
                            "participant_role": "Contributor",
                            "percentage": round(pro_rata_pct, 2),
                            "share_amount": share,
                            "is_growth_fund": False
                        })
                        new_bal = user_id_to_balance.get(uid, 0.0) + share
                        balance_updates.append((uid, new_bal))

                # 3. Direct participants (incl. GF but no balance update for GF)
                for p in participants:
                    uid = str(p.get("user_id")) if p.get("user_id") else None
                    display = user_id_to_display.get(uid, p.get("display_name", "Unknown")) if uid else p.get("display_name", "Unknown")
                    share = gross_profit * (p["percentage"] / 100)
                    is_gf = "growth fund" in display.lower()
                    distributions.append({
                        "profit_id": profit_id,
                        "participant_name": display,
                        "participant_user_id": uid,
                        "participant_role": p.get("role", ""),
                        "percentage": p["percentage"],
                        "share_amount": share,
                        "is_growth_fund": is_gf
                    })
                    if uid and not is_gf:
                        new_bal = user_id_to_balance.get(uid, 0.0) + share
                        balance_updates.append((uid, new_bal))

                # 4. Bulk insert distributions
                if distributions:
                    supabase.table("profit_distributions").insert(distributions).execute()

                # 5. Bulk update user balances
                for uid, new_bal in balance_updates:
                    supabase.table("users").update({"balance": new_bal}).eq("id", uid).execute()

                # 6. Growth Fund transaction if any
                if gf_add > 0:
                    supabase.table("growth_fund_transactions").insert({
                        "date": str(record_date),
                        "type": "In",
                        "amount": gf_add,
                        "description": f"Auto from {acc_name} profit record",
                        "account_source": acc_name,
                        "recorded_by": st.session_state.full_name
                    }).execute()

                # 7. Send HTML email to involved members
                sender_email = st.secrets.get("EMAIL_SENDER")
                sender_password = st.secrets.get("EMAIL_PASSWORD")

                if sender_email and sender_password and involved_user_ids:
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(sender_email, sender_password)

                        date_str = record_date.strftime("%B %d, %Y")
                        html_body = f"""
                        <html>
                        <body style="font-family:Arial,sans-serif; background:#f8fbff; padding:20px;">
                            <div style="max-width:800px; margin:auto; background:white; border-radius:20px; padding:30px; box-shadow:0 10px 30px rgba(0,0,0,0.1);">
                                <h1 style="color:#00ffaa; text-align:center;">🚀 KMFX Profit Distribution</h1>
                                <h2 style="text-align:center;">{acc_name} • {date_str}</h2>
                                <p style="text-align:center; font-size:1.2rem;">
                                    Gross: <strong>${gross_profit:,.2f}</strong> • 
                                    Pool ({contributor_share_pct:.1f}%): <strong>${contributor_pool:,.2f}</strong>
                                </p>
                                <h3>Contributor Pool Breakdown</h3>
                                <table style="width:100%; border-collapse:collapse;">
                                    <tr style="background:#00ffaa; color:black;">
                                        <th style="padding:12px; border:1px solid #ddd;">Name</th>
                                        <th style="padding:12px; border:1px solid #ddd;">Funded PHP</th>
                                        <th style="padding:12px; border:1px solid #ddd;">Share</th>
                                    </tr>
                                    {''.join(f'<tr><td style="padding:12px; border:1px solid #ddd;">{r["Name"]}</td><td>{r["Funded PHP"]}</td><td>{r["Share"]}</td></tr>' for r in contrib_preview) or '<tr><td colspan="3" style="text-align:center; padding:12px;">None</td></tr>'}
                                </table>
                                <h3>Participants Breakdown (incl. Growth Fund)</h3>
                                <table style="width:100%; border-collapse:collapse;">
                                    <tr style="background:#ffd700; color:black;">
                                        <th style="padding:12px; border:1px solid #ddd;">Name</th>
                                        <th style="padding:12px; border:1px solid #ddd;">%</th>
                                        <th style="padding:12px; border:1px solid #ddd;">Share</th>
                                    </tr>
                                    {''.join(f'<tr><td style="padding:12px; border:1px solid #ddd;">{r["Name"]}</td><td>{r["%"]}%</td><td>{r["Share"]}</td></tr>' for r in part_preview)}
                                </table>
                                <p style="margin-top:30px; text-align:center; font-size:1.1rem;">
                                    Thank you for being part of the Empire scaling 👑<br>
                                    Keep trading smart!
                                </p>
                            </div>
                        </body>
                        </html>
                        """

                        sent_count = 0
                        for uid in involved_user_ids:
                            email = user_id_to_email.get(uid)
                            if email:
                                msg = MIMEMultipart()
                                msg["From"] = sender_email
                                msg["To"] = email
                                msg["Subject"] = f"KMFX Profit Distribution - {acc_name} ({date_str})"
                                msg.attach(MIMEText(html_body, "html"))
                                server.sendmail(sender_email, email, msg.as_string())
                                sent_count += 1

                        server.quit()
                        if sent_count > 0:
                            st.success(f"Profit distributed & email sent to {sent_count} member(s)! 🚀")
                        else:
                            st.warning("Profit recorded but no emails sent (check member emails)")
                    except Exception as email_err:
                        st.warning(f"Profit recorded but email failed: {str(email_err)} • Check secrets & App Password")
                else:
                    st.warning("Profit recorded but no email sent • Set EMAIL_SENDER & EMAIL_PASSWORD in secrets")

                log_action("Recorded Profit", f"Account: {acc_name} | Gross: ${gross_profit:,.2f}")
                st.success("Profit successfully recorded & auto-distributed! Balances + Growth Fund updated realtime.")
                st.cache_data.clear()
                st.rerun()

            except Exception as e:
                st.error(f"Failed to record profit: {str(e)}")