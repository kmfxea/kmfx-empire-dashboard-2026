# pages/💰_Profit_Sharing.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ────────────────────────────────────────────────
# AUTH + SIDEBAR + REQUIRE AUTH (must be first)
# ────────────────────────────────────────────────
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth(min_role="admin")  # owner/admin only — stricter than client dashboard

# ─── THEME (sync with Dashboard & FTMO Accounts) ───
accent_primary = "#00ffaa"
accent_gold    = "#ffd700"
accent_glow    = "#00ffaa40"

# ─── SCROLL TO TOP (same as Dashboard) ───
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

st.header("💰 Profit Sharing & Auto-Distribution")
st.markdown("**Empire engine** • Record FTMO profit → Auto-split via stored v2 tree • Bulletproof balance updates • Premium HTML emails (incl. Growth Fund) • Realtime previews • Instant sync across pages")

current_role = st.session_state.get("role", "guest").lower()
if current_role not in ["owner", "admin"]:
    st.warning("Profit recording & distribution → owner / admin only")
    st.stop()

# ─── DATA FETCH ───
@st.cache_data(ttl=60, show_spinner="Syncing accounts & users...")
def fetch_profit_data():
    try:
        accounts = supabase.table("ftmo_accounts").select(
            "id, name, current_phase, current_equity, "
            "participants_v2, contributors_v2, contributor_share_pct"
        ).execute().data or []

        users = supabase.table("users").select("id, full_name, email, balance").execute().data or []

        uid_to_display = {str(u["id"]): u["full_name"] for u in users}
        uid_to_email   = {str(u["id"]): u.get("email") for u in users}
        uid_to_balance = {str(u["id"]): u.get("balance", 0.0) for u in users}

        return accounts, uid_to_display, uid_to_email, uid_to_balance
    except Exception as e:
        st.error(f"Data sync failed: {str(e)}")
        return [], {}, {}, {}

accounts, uid_to_display, uid_to_email, uid_to_balance = fetch_profit_data()

if not accounts:
    st.info("No accounts yet • Launch one in FTMO Accounts first")
    st.stop()

# ─── ACCOUNT SELECTION ───
account_options = {
    f"{a['name']} • Phase: {a['current_phase']} • Equity ${a.get('current_equity', 0):,.0f} • Pool {a.get('contributor_share_pct', 0):.1f}%": a
    for a in accounts
}
selected_key = st.selectbox("Select Account", list(account_options.keys()))
acc = account_options[selected_key]

acc_id   = acc["id"]
acc_name = acc["name"]

participants       = acc.get("participants_v2", [])
contributors       = acc.get("contributors_v2", [])
contributor_share_pct = acc.get("contributor_share_pct", 0.0)

if not participants:
    st.error("Missing v2 participants • Re-edit account in FTMO Accounts page")
    st.stop()

st.success(f"**Recording profit for:** {acc_name} • Contributor Pool: **{contributor_share_pct:.1f}%** • v2 tree active")

# ─── FORM ───
with st.form("profit_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 2])  # wider input column
    with col1:
        gross_profit = st.number_input(
            "Gross Profit Received (USD) *",
            min_value=0.01,
            step=500.0,
            format="%.2f"
        )
    with col2:
        record_date = st.date_input("Record Date", value=date.today())

    st.subheader("Stored Unified Tree (edit in FTMO Accounts)")
    part_df = pd.DataFrame([
        {
            "Name": uid_to_display.get(p.get("user_id"), p.get("display_name", "Unknown")) if p.get("user_id") else p.get("display_name", "Unknown"),
            "Role": p.get("role", ""),
            "%": f"{p['percentage']:.2f}"
        } for p in participants
    ])
    st.dataframe(part_df, use_container_width=True, hide_index=True)

    # ─── CALCULATIONS & PREVIEWS ───
    if gross_profit > 0:
        involved_user_ids = set()
        contrib_preview = []
        part_preview = []
        gf_add = 0.0
        total_funded_php = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors)
        contributor_pool = gross_profit * (contributor_share_pct / 100)

        # Contributors
        if total_funded_php > 0 and contributor_share_pct > 0:
            for c in contributors:
                user_id = c.get("user_id")
                if not user_id:
                    continue
                involved_user_ids.add(user_id)
                funded = c.get("units", 0) * c.get("php_per_unit", 0)
                share = contributor_pool * (funded / total_funded_php)
                display = uid_to_display.get(user_id, "Unknown")
                contrib_preview.append({"Name": display, "Funded PHP": f"₱{funded:,.0f}", "Share": f"${share:,.2f}"})

        # Participants (incl Growth Fund & manual)
        for p in participants:
            user_id = p.get("user_id")
            display = uid_to_display.get(user_id, p.get("display_name", "Unknown")) if user_id else p.get("display_name", "Unknown")
            share = gross_profit * (p["percentage"] / 100)
            if "growth fund" in display.lower():
                gf_add += share
            part_preview.append({
                "Name": display,
                "%": f"{p['percentage']:.2f}",
                "Share": f"${share:,.2f}"
            })
            if user_id:
                involved_user_ids.add(user_id)

        # Previews
        col_prev1, col_prev2 = st.columns(2)
        with col_prev1:
            st.subheader("Contributor Pool Preview")
            if contrib_preview:
                st.dataframe(pd.DataFrame(contrib_preview), use_container_width=True, hide_index=True)
            else:
                st.info("No contributors or 0% pool")

        with col_prev2:
            st.subheader("Participants Preview (incl. Growth Fund)")
            st.dataframe(pd.DataFrame(part_preview), use_container_width=True, hide_index=True)

        # Metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Gross Profit", f"${gross_profit:,.2f}")
        col_m2.metric("Contributor Pool", f"${contributor_pool:,.2f}")
        col_m3.metric("Growth Fund Add", f"${gf_add:,.2f}")

        # Sankey
        labels = [f"Gross ${gross_profit:,.0f}"]
        values = []
        source = []
        target = []
        idx = 1

        if contributor_pool > 0 and contrib_preview:
            labels.append("Contributor Pool")
            values.append(contributor_pool)
            source.append(0)
            target.append(idx)
            contrib_idx = idx
            idx += 1
            for c in contrib_preview:
                share_val = float(c["Share"].replace("$", "").replace(",", ""))
                labels.append(c["Name"])
                values.append(share_val)
                source.append(contrib_idx)
                target.append(idx)
                idx += 1

        for p in part_preview:
            share_val = float(p["Share"].replace("$", "").replace(",", ""))
            labels.append(p["Name"])
            values.append(share_val)
            source.append(0)
            target.append(idx)
            idx += 1

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=20,
                thickness=30,
                label=labels,
                color=["#00ffaa"] + ["#ffd700"]*len(contrib_preview) + ["#00cc99"]*len(part_preview)
            ),
            link=dict(source=source, target=target, value=values)
        )])
        fig.update_layout(title="Distribution Flow Preview (incl. Growth Fund)", height=600)
        st.plotly_chart(fig, use_container_width=True)

    submitted = st.form_submit_button("🚀 Record & Distribute Profit", type="primary", use_container_width=True)

    if submitted:
        if gross_profit <= 0:
            st.error("Gross profit must be greater than 0")
        else:
            try:
                # ─── Supabase operations ───
                profit_resp = supabase.table("profits").insert({
                    "account_id": acc_id,
                    "gross_profit": gross_profit,
                    "record_date": str(record_date),
                    "units_generated": gross_profit / 3000.0 if gross_profit > 0 else 0,
                    "growth_fund_add": gf_add,
                    "contributor_share_pct": contributor_share_pct
                }).execute()
                profit_id = profit_resp.data[0]["id"]

                distributions = []
                balance_updates = []

                # Contributors
                if contributor_pool > 0 and total_funded_php > 0:
                    for c in contributors:
                        user_id = c.get("user_id")
                        if not user_id: continue
                        display = uid_to_display.get(user_id, "Unknown")
                        funded = c.get("units", 0) * c.get("php_per_unit", 0)
                        share = contributor_pool * (funded / total_funded_php)
                        pro_rata_pct = (funded / total_funded_php) * 100
                        distributions.append({
                            "profit_id": profit_id,
                            "participant_name": display,
                            "participant_user_id": user_id,
                            "participant_role": "Contributor",
                            "percentage": round(pro_rata_pct, 2),
                            "share_amount": share,
                            "is_growth_fund": False
                        })
                        new_bal = uid_to_balance.get(user_id, 0) + share
                        balance_updates.append((user_id, new_bal))

                # Participants
                for p in participants:
                    user_id = p.get("user_id")
                    display = uid_to_display.get(user_id, p.get("display_name", "Unknown")) if user_id else p.get("display_name", "Unknown")
                    share = gross_profit * (p["percentage"] / 100)
                    is_gf = "growth fund" in display.lower()
                    distributions.append({
                        "profit_id": profit_id,
                        "participant_name": display,
                        "participant_user_id": user_id,
                        "participant_role": p.get("role", ""),
                        "percentage": p["percentage"],
                        "share_amount": share,
                        "is_growth_fund": is_gf
                    })
                    if user_id and not is_gf:
                        new_bal = uid_to_balance.get(user_id, 0) + share
                        balance_updates.append((user_id, new_bal))

                if distributions:
                    supabase.table("profit_distributions").insert(distributions).execute()

                for uid, new_bal in balance_updates:
                    supabase.table("users").update({"balance": new_bal}).eq("id", uid).execute()

                if gf_add > 0:
                    supabase.table("growth_fund_transactions").insert({
                        "date": str(record_date),
                        "type": "In",
                        "amount": gf_add,
                        "description": f"Auto from {acc_name} profit",
                        "account_source": acc_name,
                        "recorded_by": st.session_state.get("full_name", "System")
                    }).execute()

                # ─── EMAIL ───
                date_str = record_date.strftime("%B %d, %Y")
                html_breakdown = f"""
                <html><body style="font-family:Arial,sans-serif;background:#f8fbff;padding:20px;">
                    <div style="max-width:800px;margin:auto;background:white;border-radius:20px;padding:30px;box-shadow:0 10px 30px rgba(0,0,0,0.1);">
                        <h1 style="color:#00ffaa;text-align:center;">🚀 KMFX Profit Distribution</h1>
                        <h2 style="text-align:center;">{acc_name} • {date_str}</h2>
                        <p style="text-align:center;font-size:1.2rem;">Gross: <strong>${gross_profit:,.2f}</strong> • Pool ({contributor_share_pct:.1f}%): <strong>${contributor_pool:,.2f}</strong></p>
                        <h3>Contributor Breakdown</h3>
                        <table style="width:100%;border-collapse:collapse;">
                            <tr style="background:#00ffaa;color:black;"><th style="padding:12px;border:1px solid #ddd;">Name</th><th>Funded PHP</th><th>Share</th></tr>
                            {''.join(f'<tr><td style="padding:12px;border:1px solid #ddd;">{r["Name"]}</td><td>{r["Funded PHP"]}</td><td>{r["Share"]}</td></tr>' for r in contrib_preview) or '<tr><td colspan="3" style="text-align:center;padding:12px;">None</td></tr>'}
                        </table>
                        <h3>Participants Breakdown (incl. Growth Fund)</h3>
                        <table style="width:100%;border-collapse:collapse;">
                            <tr style="background:#ffd700;color:black;"><th style="padding:12px;border:1px solid #ddd;">Name</th><th>%</th><th>Share</th></tr>
                            {''.join(f'<tr><td style="padding:12px;border:1px solid #ddd;">{r["Name"]}</td><td>{r["%"]}%</td><td>{r["Share"]}</td></tr>' for r in part_preview)}
                        </table>
                        <p style="margin-top:30px;text-align:center;">Thank you for scaling the Empire 👑</p>
                    </div>
                </body></html>
                """

                st.subheader("Auto-Email Preview")
                st.markdown(html_breakdown, unsafe_allow_html=True)

                sender_email = os.getenv("EMAIL_SENDER")
                sender_password = os.getenv("EMAIL_PASSWORD")
                sent = 0

                if sender_email and sender_password and involved_user_ids:
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(sender_email, sender_password)
                        for uid in involved_user_ids:
                            email = uid_to_email.get(uid)
                            if email:
                                msg = MIMEMultipart()
                                msg["From"] = sender_email
                                msg["To"] = email
                                msg["Subject"] = f"KMFX Profit - {acc_name} {date_str}"
                                msg.attach(MIMEText(html_breakdown, "html"))
                                server.sendmail(sender_email, email, msg.as_string())
                                sent += 1
                        server.quit()
                        st.success(f"Emails sent to {sent} recipients 🚀")
                    except Exception as e:
                        st.error(f"Email sending failed: {str(e)} • Check secrets / App Password")

                st.success("Profit recorded & distributed! Balances + Growth Fund updated.")
                st.balloons()
                st.cache_data.clear()
                st.rerun()

            except Exception as e:
                st.error(f"Operation failed: {str(e)}")

# ─── FOOTER (same style as Dashboard) ───
st.markdown(f"""
<div style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
    border-radius:24px; border:2px solid {accent_primary}40;
    background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
    box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Fully Automatic • Realtime • Exponential Empire
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Every profit auto-syncs • Trees update instantly • Empire scales itself.
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith, Shared for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)