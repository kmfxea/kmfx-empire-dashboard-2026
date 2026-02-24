# pages/03_📊_FTMO_Accounts.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from utils.auth import require_auth
from utils.supabase_client import supabase
from utils.helpers import log_action

require_auth(min_role="client")  # Lahat pwede, pero may role-based views

st.header("FTMO Accounts Management 🚀")
st.markdown("**Empire core: Launch/edit accounts with unified trees • Contributor Pool enforced • Exact 100% validation • Auto v2 migration • Realtime previews**")

current_role = st.session_state.get("role", "guest")

# ────────────────────────────────────────────────
#  CACHED DATA FETCH
# ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_all_data():
    try:
        accounts = supabase.table("ftmo_accounts").select("*").order("created_date", desc=True).execute().data or []
        users = supabase.table("users").select("id, full_name, role, title").execute().data or []
        return accounts, users
    except Exception as e:
        st.error(f"Data fetch error: {str(e)}")
        return [], []

accounts, all_users = fetch_all_data()

# User mapping
user_id_to_display = {}
display_to_user_id = {}
user_id_to_full_name = {}
for u in all_users:
    if u["role"] in ["client", "owner"]:
        uid_str = str(u["id"])
        display = u["full_name"]
        if u.get("title"):
            display += f" ({u['title']})"
        user_id_to_display[uid_str] = display
        display_to_user_id[display] = uid_str
        user_id_to_full_name[uid_str] = u["full_name"]

special_options = ["Contributor Pool", "Manual Payout (Temporary)", "Growth Fund"]
participant_options = special_options + list(display_to_user_id.keys())
contributor_options = list(user_id_to_display.values())

owner_display = next(
    (d for d, uid in display_to_user_id.items() if uid and any(str(uu["id"]) == uid and uu["role"] == "owner" for uu in all_users)),
    "King Minted"
)

# ────────────────────────────────────────────────
#  CREATE NEW ACCOUNT (OWNER/ADMIN ONLY)
# ────────────────────────────────────────────────
if current_role in ["owner", "admin"]:
    with st.expander("➕ Launch New FTMO Account", expanded=not accounts):
        with st.form("create_account_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Account Name *", placeholder="e.g. KMFX Scaled 200K")
                ftmo_id = st.text_input("FTMO ID (Optional)")
                phase = st.selectbox("Current Phase *", ["Challenge P1", "Challenge P2", "Verification", "Funded", "Scaled"])
            with col2:
                equity = st.number_input("Current Equity (USD)", min_value=0.0, value=100000.0, step=1000.0)
                withdrawable = st.number_input("Current Withdrawable (USD)", min_value=0.0, value=0.0, step=500.0)

            notes = st.text_area("Notes (Optional)")

            st.subheader("🌱 Growth Fund Allocation (Optional)")
            gf_pct = st.number_input("Growth Fund % from Gross Profit", min_value=0.0, max_value=50.0, value=10.0, step=0.5)
            if gf_pct > 0:
                st.success(f"✅ {gf_pct:.1f}% will auto-allocate to Growth Fund")
            else:
                st.info("No Growth Fund allocation")

            st.subheader("🌳 Profit Distribution Tree (%)")
            st.info("Must have **exactly one** 'Contributor Pool' • Total + GF = **exactly 100%**")

            default_rows = [
                {"display_name": "Contributor Pool", "role": "Funding Contributors (pro-rata)", "percentage": 30.0},
                {"display_name": owner_display, "role": "Founder/Owner", "percentage": max(70.0 - gf_pct, 0.0)}
            ]

            tree_df = pd.DataFrame(default_rows)
            edited_tree = st.data_editor(
                tree_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "display_name": st.column_config.SelectboxColumn("Name *", options=participant_options, required=True),
                    "role": st.column_config.TextColumn("Role"),
                    "percentage": st.column_config.NumberColumn("% *", min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
                },
                key="create_participants_editor"
            )

            total_tree = edited_tree["percentage"].sum() if not edited_tree.empty else 0.0
            total_incl_gf = total_tree + gf_pct

            st.progress(min(total_incl_gf / 100.0, 1.0))
            st.caption(f"Current Total: {total_incl_gf:.2f}% (must be exactly 100.00%)")

            contrib_rows = edited_tree[edited_tree["display_name"] == "Contributor Pool"]
            valid_contrib = len(contrib_rows) == 1
            valid_total = abs(total_incl_gf - 100.0) <= 0.01

            if not valid_contrib:
                st.error("Exactly one 'Contributor Pool' row required")
            if not valid_total:
                st.error(f"Total (incl. GF) must be exactly 100.00% (current: {total_incl_gf:.2f}%)")
            if valid_contrib and valid_total:
                st.success("✅ Distribution valid")

            # Manual payout custom names
            manual_inputs = []
            for idx, row in edited_tree.iterrows():
                if row["display_name"] == "Manual Payout (Temporary)":
                    custom = st.text_input(f"Custom name for manual row {idx+1}", key=f"manual_create_{idx}")
                    if custom.strip():
                        manual_inputs.append((idx, custom.strip()))

            st.subheader("🌳 Contributors Funding Tree (PHP)")
            contrib_df = pd.DataFrame(columns=["display_name", "units", "php_per_unit"])
            edited_contrib = st.data_editor(
                contrib_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "display_name": st.column_config.SelectboxColumn("Contributor *", options=contributor_options, required=True),
                    "units": st.column_config.NumberColumn("Units", min_value=0.0, step=0.5),
                    "php_per_unit": st.column_config.NumberColumn("PHP per Unit", min_value=100.0, step=100.0)
                },
                key="create_contributors_editor"
            )

            if not edited_contrib.empty:
                total_php = (edited_contrib["units"] * edited_contrib["php_per_unit"]).sum()
                st.metric("Total Funded (PHP)", f"₱{total_php:,.0f}")

            # Previews
            tab_prev1, tab_prev2 = st.tabs(["Profit Tree Preview", "Funding Tree Preview"])
            with tab_prev1:
                if not edited_tree.empty:
                    labels = ["Gross Profit"]
                    values = []
                    for _, row in edited_tree.iterrows():
                        d = row["display_name"]
                        if d == "Contributor Pool":
                            d = "Contributor Pool (pro-rata)"
                        labels.append(f"{d} ({row['percentage']:.2f}%)")
                        values.append(row["percentage"])
                    if gf_pct > 0:
                        labels.append(f"Growth Fund ({gf_pct:.2f}%)")
                        values.append(gf_pct)
                    fig = go.Figure(data=[go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels),
                        link=dict(source=[0]*len(values), target=list(range(1, len(labels))), value=values)
                    )])
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Add rows to see preview")

            with tab_prev2:
                if not edited_contrib.empty:
                    labels = ["Funded (PHP)"]
                    values = (edited_contrib["units"] * edited_contrib["php_per_unit"]).tolist()
                    contrib_labels = [f"{row['display_name']} ({row['units']}u @ ₱{row['php_per_unit']:,.0f})" for _, row in edited_contrib.iterrows()]
                    fig = go.Figure(data=[go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels + contrib_labels),
                        link=dict(source=[0]*len(values), target=list(range(1, len(values)+1)), value=values)
                    )])
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Add contributors to see preview")

            if st.form_submit_button("🚀 Launch Account", type="primary", use_container_width=True):
                if not name.strip():
                    st.error("Account name is required")
                elif not valid_contrib or not valid_total:
                    st.error("Fix distribution tree before launching")
                else:
                    try:
                        final_part_v2 = []
                        for row in edited_tree.to_dict("records"):
                            display = row["display_name"]
                            user_id = display_to_user_id.get(display)
                            final_part_v2.append({
                                "user_id": user_id,
                                "display_name": display,
                                "percentage": row["percentage"],
                                "role": row["role"]
                            })

                        # Apply custom names for manual payouts
                        for idx, custom in manual_inputs:
                            if idx < len(final_part_v2):
                                final_part_v2[idx]["display_name"] = custom
                                final_part_v2[idx]["user_id"] = None

                        # Remove any existing Growth Fund row before adding new one
                        final_part_v2 = [p for p in final_part_v2 if "growth fund" not in p.get("display_name", "").lower()]

                        if gf_pct > 0:
                            final_part_v2.append({
                                "user_id": None,
                                "display_name": "Growth Fund",
                                "percentage": gf_pct,
                                "role": "Empire Reinvestment Fund"
                            })

                        final_contrib_v2 = []
                        for row in edited_contrib.to_dict("records"):
                            display = row["display_name"]
                            user_id = display_to_user_id.get(display)
                            final_contrib_v2.append({
                                "user_id": user_id,
                                "units": row.get("units", 0),
                                "php_per_unit": row.get("php_per_unit", 0)
                            })

                        # Legacy format for backward compatibility
                        final_part_old = [{"name": user_id_to_full_name.get(p["user_id"], p["display_name"]) if p["user_id"] else p["display_name"],
                                           "role": p["role"], "percentage": p["percentage"]} for p in final_part_v2]
                        final_contrib_old = [{"name": user_id_to_full_name.get(c["user_id"], "Unknown"),
                                              "units": c["units"], "php_per_unit": c["php_per_unit"]} for c in final_contrib_v2]

                        supabase.table("ftmo_accounts").insert({
                            "name": name.strip(),
                            "ftmo_id": ftmo_id or None,
                            "current_phase": phase,
                            "current_equity": equity,
                            "withdrawable_balance": withdrawable,
                            "notes": notes or None,
                            "created_date": date.today().isoformat(),
                            "participants": final_part_old,
                            "contributors": final_contrib_old,
                            "participants_v2": final_part_v2,
                            "contributors_v2": final_contrib_v2,
                            "contributor_share_pct": contrib_rows.iloc[0]["percentage"] if not contrib_rows.empty else 30.0
                        }).execute()

                        st.success("Account launched successfully! 🎉")
                        log_action("Created FTMO Account", f"Name: {name}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Launch failed: {str(e)}")

# ────────────────────────────────────────────────
#  LIVE ACCOUNTS LIST + EDIT/DELETE (OWNER/ADMIN)
# ────────────────────────────────────────────────
st.subheader("Live Empire Accounts")
if accounts:
    for acc in accounts:
        use_v2 = bool(acc.get("participants_v2"))
        participants = acc.get("participants_v2") if use_v2 else acc.get("participants", [])
        contributors = acc.get("contributors_v2") if use_v2 else acc.get("contributors", [])
        total_funded_php = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors)
        contrib_pct = acc.get("contributor_share_pct", 0.0)
        gf_pct_acc = sum(p.get("percentage", 0) for p in participants if "growth fund" in p.get("display_name", "").lower())

        expander_label = f"🌟 {acc['name']} • {acc['current_phase']} • Equity ${acc.get('current_equity', 0):,.0f} • Funded ₱{total_funded_php:,.0f} • Pool {contrib_pct:.1f}% • GF {gf_pct_acc:.1f}%"
        if not use_v2:
            expander_label += " (Legacy)"

        with st.expander(expander_label):
            tab1, tab2 = st.tabs(["Profit Tree", "Funding Tree"])
            with tab1:
                labels = ["Gross Profit"]
                values = []
                for p in participants:
                    display = p.get("display_name") or user_id_to_display.get(str(p.get("user_id")), p.get("name", "Unknown"))
                    if display == "Contributor Pool":
                        display = "Contributor Pool (pro-rata)"
                    labels.append(f"{display} ({p['percentage']:.2f}%)")
                    values.append(p["percentage"])
                fig = go.Figure(data=[go.Sankey(
                    node=dict(pad=15, thickness=20, label=labels),
                    link=dict(source=[0]*len(values), target=list(range(1, len(labels))), value=values)
                )])
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                if contributors:
                    labels = ["Funded (PHP)"]
                    values = []
                    for c in contributors:
                        display = user_id_to_display.get(str(c.get("user_id")), c.get("name", "Unknown"))
                        funded = c.get("units", 0) * c.get("php_per_unit", 0)
                        labels.append(f"{display} ({c.get('units', 0)}u @ ₱{c.get('php_per_unit', 0):,.0f})")
                        values.append(funded)
                    fig = go.Figure(data=[go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels),
                        link=dict(source=[0]*len(values), target=list(range(1, len(values))), value=values)
                    )])
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No contributors assigned")

            if current_role in ["owner", "admin"]:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit Account", key=f"edit_btn_{acc['id']}"):
                        st.session_state["edit_ftmo_id"] = acc["id"]
                        st.session_state["edit_ftmo_data"] = acc
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"del_btn_{acc['id']}", type="secondary"):
                        try:
                            supabase.table("ftmo_accounts").delete().eq("id", acc["id"]).execute()
                            st.success("Account deleted")
                            log_action("Deleted FTMO Account", f"ID: {acc['id']}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {str(e)}")

    # ────────────────────────────────────────────────
    #  EDIT FORM (OWNER/ADMIN ONLY)
    # ────────────────────────────────────────────────
    if "edit_ftmo_id" in st.session_state:
        eid = st.session_state["edit_ftmo_id"]
        cur = st.session_state["edit_ftmo_data"]
        with st.expander(f"✏️ Editing {cur['name']}", expanded=True):
            with st.form(f"edit_form_{eid}", clear_on_submit=False):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Account Name *", value=cur["name"])
                    new_ftmo_id = st.text_input("FTMO ID", value=cur.get("ftmo_id") or "")
                    new_phase = st.selectbox("Current Phase", ["Challenge P1", "Challenge P2", "Verification", "Funded", "Scaled"],
                                             index=["Challenge P1", "Challenge P2", "Verification", "Funded", "Scaled"].index(cur["current_phase"]))
                with col2:
                    new_equity = st.number_input("Current Equity (USD)", value=float(cur.get("current_equity", 0)), step=1000.0)
                    new_withdrawable = st.number_input("Current Withdrawable (USD)", value=float(cur.get("withdrawable_balance", 0)), step=500.0)

                new_notes = st.text_area("Notes", value=cur.get("notes") or "")

                use_v2 = bool(cur.get("participants_v2"))
                current_part = pd.DataFrame(cur["participants_v2"] if use_v2 else cur.get("participants", []))

                current_gf_pct = sum(row.get("percentage", 0.0) for _, row in current_part.iterrows() if "growth fund" in row.get("display_name", "").lower())

                st.subheader("🌱 Growth Fund Allocation")
                gf_pct = st.number_input("Growth Fund %", min_value=0.0, max_value=50.0, value=current_gf_pct, step=0.5)

                st.subheader("🌳 Profit Distribution Tree")
                if not use_v2:
                    st.info("Legacy format detected • Will migrate to v2 on save")
                    legacy = pd.DataFrame(cur.get("participants", []))
                    current_part = pd.DataFrame([{
                        "display_name": next((d for d, uid in display_to_user_id.items() if user_id_to_full_name.get(uid) == p["name"]), p["name"]),
                        "role": p.get("role", ""),
                        "percentage": p["percentage"]
                    } for p in legacy])

                # Ensure Contributor Pool exists
                if "Contributor Pool" not in current_part["display_name"].values:
                    contrib_row = pd.DataFrame([{"display_name": "Contributor Pool", "role": "Funding Contributors (pro-rata)", "percentage": cur.get("contributor_share_pct", 30.0)}])
                    current_part = pd.concat([contrib_row, current_part], ignore_index=True)
                    st.info("Auto-added missing Contributor Pool")

                # Remove existing GF row before editing
                current_part = current_part[~current_part["display_name"].str.lower().str.contains("growth fund", na=False)]

                edited_tree = st.data_editor(
                    current_part,
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"edit_participants_{eid}",
                    column_config={
                        "display_name": st.column_config.SelectboxColumn("Name *", options=participant_options, required=True),
                        "role": st.column_config.TextColumn("Role"),
                        "percentage": st.column_config.NumberColumn("% *", min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
                    }
                )

                total_tree = edited_tree["percentage"].sum() if not edited_tree.empty else 0.0
                total_incl_gf = total_tree + gf_pct
                st.progress(min(total_incl_gf / 100.0, 1.0))
                st.caption(f"Total: {total_incl_gf:.2f}% (must be 100.00%)")

                contrib_rows = edited_tree[edited_tree["display_name"] == "Contributor Pool"]
                valid_contrib = len(contrib_rows) == 1
                valid_total = abs(total_incl_gf - 100.0) <= 0.01

                if not valid_contrib:
                    st.error("Exactly one 'Contributor Pool' row required")
                if not valid_total:
                    st.error(f"Total must be exactly 100.00% (current: {total_incl_gf:.2f}%)")

                manual_inputs = []
                for idx, row in edited_tree.iterrows():
                    if row["display_name"] == "Manual Payout (Temporary)":
                        custom = st.text_input(f"Custom name for manual row {idx+1}", key=f"manual_edit_{eid}_{idx}")
                        if custom.strip():
                            manual_inputs.append((idx, custom.strip()))

                st.subheader("🌳 Contributors Tree")
                current_contrib = pd.DataFrame(cur.get("contributors_v2", []) if use_v2 else cur.get("contributors", []))
                if not use_v2:
                    current_contrib["display_name"] = current_contrib["user_id"].apply(lambda uid: user_id_to_display.get(str(uid), "Unknown"))

                edited_contrib = st.data_editor(
                    current_contrib[["display_name", "units", "php_per_unit"]],
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"edit_contributors_{eid}",
                    column_config={
                        "display_name": st.column_config.SelectboxColumn("Contributor *", options=contributor_options, required=True),
                        "units": st.column_config.NumberColumn("Units", min_value=0.0, step=0.5),
                        "php_per_unit": st.column_config.NumberColumn("PHP/Unit", min_value=100.0, step=100.0)
                    }
                )

                if not edited_contrib.empty:
                    total_php = (edited_contrib["units"] * edited_contrib["php_per_unit"]).sum()
                    st.metric("Total Funded (PHP)", f"₱{total_php:,.0f}")

                # Previews (same as create)
                tab_prev1, tab_prev2 = st.tabs(["Profit Preview", "Funding Preview"])
                with tab_prev1:
                    if not edited_tree.empty:
                        labels = ["Gross Profit"]
                        values = []
                        for _, row in edited_tree.iterrows():
                            d = row["display_name"]
                            if d == "Contributor Pool":
                                d = "Contributor Pool (pro-rata)"
                            labels.append(f"{d} ({row['percentage']:.2f}%)")
                            values.append(row["percentage"])
                        if gf_pct > 0:
                            labels.append(f"Growth Fund ({gf_pct:.2f}%)")
                            values.append(gf_pct)
                        fig = go.Figure(data=[go.Sankey(
                            node=dict(pad=15, thickness=20, label=labels),
                            link=dict(source=[0]*len(values), target=list(range(1, len(labels))), value=values)
                        )])
                        st.plotly_chart(fig, use_container_width=True)

                with tab_prev2:
                    if not edited_contrib.empty:
                        labels = ["Funded (PHP)"]
                        values = (edited_contrib["units"] * edited_contrib["php_per_unit"]).tolist()
                        contrib_labels = [f"{row['display_name']} ({row['units']}u @ ₱{row['php_per_unit']:,.0f})" for _, row in edited_contrib.iterrows()]
                        fig = go.Figure(data=[go.Sankey(
                            node=dict(pad=15, thickness=20, label=labels + contrib_labels),
                            link=dict(source=[0]*len(values), target=list(range(1, len(values)+1)), value=values)
                        )])
                        st.plotly_chart(fig, use_container_width=True)

                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                        if not new_name.strip() or not valid_contrib or not valid_total:
                            st.error("Please fix required fields and distribution")
                        else:
                            try:
                                final_part_v2 = []
                                for row in edited_tree.to_dict("records"):
                                    display = row["display_name"]
                                    user_id = display_to_user_id.get(display)
                                    final_part_v2.append({
                                        "user_id": user_id,
                                        "display_name": display,
                                        "percentage": row["percentage"],
                                        "role": row["role"]
                                    })

                                for idx, custom in manual_inputs:
                                    if idx < len(final_part_v2):
                                        final_part_v2[idx]["display_name"] = custom
                                        final_part_v2[idx]["user_id"] = None

                                final_part_v2 = [p for p in final_part_v2 if "growth fund" not in p.get("display_name", "").lower()]

                                if gf_pct > 0:
                                    final_part_v2.append({
                                        "user_id": None,
                                        "display_name": "Growth Fund",
                                        "percentage": gf_pct,
                                        "role": "Empire Reinvestment Fund"
                                    })

                                final_contrib_v2 = []
                                for row in edited_contrib.to_dict("records"):
                                    display = row["display_name"]
                                    user_id = display_to_user_id.get(display)
                                    final_contrib_v2.append({
                                        "user_id": user_id,
                                        "units": row.get("units", 0),
                                        "php_per_unit": row.get("php_per_unit", 0)
                                    })

                                final_part_old = [{"name": user_id_to_full_name.get(p["user_id"], p["display_name"]) if p["user_id"] else p["display_name"],
                                                   "role": p["role"], "percentage": p["percentage"]} for p in final_part_v2]
                                final_contrib_old = [{"name": user_id_to_full_name.get(c["user_id"], "Unknown"),
                                                      "units": c["units"], "php_per_unit": c["php_per_unit"]} for c in final_contrib_v2]

                                supabase.table("ftmo_accounts").update({
                                    "name": new_name.strip(),
                                    "ftmo_id": new_ftmo_id or None,
                                    "current_phase": new_phase,
                                    "current_equity": new_equity,
                                    "withdrawable_balance": new_withdrawable,
                                    "notes": new_notes or None,
                                    "participants": final_part_old,
                                    "contributors": final_contrib_old,
                                    "participants_v2": final_part_v2,
                                    "contributors_v2": final_contrib_v2,
                                    "contributor_share_pct": contrib_rows.iloc[0]["percentage"] if not contrib_rows.empty else 30.0
                                }).eq("id", eid).execute()

                                st.success("Account updated successfully!")
                                log_action("Updated FTMO Account", f"ID: {eid}")
                                del st.session_state["edit_ftmo_id"]
                                del st.session_state["edit_ftmo_data"]
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Update failed: {str(e)}")

                with col_cancel:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        del st.session_state["edit_ftmo_id"]
                        del st.session_state["edit_ftmo_data"]
                        st.rerun()

else:
    # ────────────────────────────────────────────────
    #  CLIENT VIEW (READ-ONLY)
    # ────────────────────────────────────────────────
    my_name = st.session_state.full_name
    my_accounts = []
    for acc in accounts:
        participants = acc.get("participants_v2") or acc.get("participants", [])
        if any(
            p.get("display_name") == my_name or
            p.get("name") == my_name or
            user_id_to_full_name.get(str(p.get("user_id")), "") == my_name
            for p in participants
        ):
            my_accounts.append(acc)

    st.subheader(f"Your Shared Accounts ({len(my_accounts)})")
    if my_accounts:
        for acc in my_accounts:
            participants = acc.get("participants_v2") or acc.get("participants", [])
            my_pct = next((p["percentage"] for p in participants if
                           p.get("display_name") == my_name or
                           p.get("name") == my_name or
                           user_id_to_full_name.get(str(p.get("user_id")), "") == my_name), 0.0)

            contributors = acc.get("contributors_v2") or acc.get("contributors", [])
            my_funded = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors
                            if user_id_to_full_name.get(str(c.get("user_id")), "") == my_name or c.get("name") == my_name)

            gf_pct_acc = sum(p.get("percentage", 0) for p in participants if "growth fund" in p.get("display_name", "").lower())

            with st.expander(f"🌟 {acc['name']} • Your Share: {my_pct:.2f}% • Funded ₱{my_funded:,.0f} • Phase: {acc['current_phase']}"):
                st.metric("Equity", f"${acc.get('current_equity', 0):,.0f}")
                st.metric("Withdrawable", f"${acc.get('withdrawable_balance', 0):,.0f}")

                tab1, tab2 = st.tabs(["Profit Tree", "Funding Tree"])
                with tab1:
                    labels = ["Gross Profit"]
                    values = []
                    for p in participants:
                        display = p.get("display_name") or user_id_to_display.get(str(p.get("user_id")), p.get("name", "Unknown"))
                        if display == "Contributor Pool":
                            display = "Contributor Pool (pro-rata)"
                        labels.append(f"{display} ({p['percentage']:.2f}%)")
                        values.append(p["percentage"])
                    fig = go.Figure(data=[go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels),
                        link=dict(source=[0]*len(values), target=list(range(1, len(labels))), value=values)
                    )])
                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    if contributors:
                        labels = ["Funded (PHP)"]
                        values = []
                        for c in contributors:
                            display = user_id_to_display.get(str(c.get("user_id")), c.get("name", "Unknown"))
                            funded = c.get("units", 0) * c.get("php_per_unit", 0)
                            labels.append(f"{display} ({c.get('units', 0)}u @ ₱{c.get('php_per_unit', 0):,.0f})")
                            values.append(funded)
                        fig = go.Figure(data=[go.Sankey(
                            node=dict(pad=15, thickness=20, label=labels),
                            link=dict(source=[0]*len(values), target=list(range(1, len(values))), value=values)
                        )])
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("You are not yet assigned to any accounts.")

    st.subheader("All Empire Accounts Overview (Read-Only)")
    for acc in accounts:
        total_funded = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in (acc.get("contributors_v2") or acc.get("contributors", [])))
        gf_pct_acc = sum(p.get("percentage", 0) for p in (acc.get("participants_v2") or acc.get("participants", [])) if "growth fund" in p.get("display_name", "").lower())
        with st.expander(f"{acc['name']} • {acc['current_phase']} • Equity ${acc.get('current_equity', 0):,.0f} • Funded ₱{total_funded:,.0f} • GF {gf_pct_acc:.1f}%"):
            participants = acc.get("participants_v2") or acc.get("participants", [])
            contributors = acc.get("contributors_v2") or acc.get("contributors", [])

            tab1, tab2 = st.tabs(["Profit Tree", "Funding Tree"])
            with tab1:
                labels = ["Gross Profit"]
                values = []
                for p in participants:
                    display = p.get("display_name") or user_id_to_display.get(str(p.get("user_id")), p.get("name", "Unknown"))
                    if display == "Contributor Pool":
                        display = "Contributor Pool (pro-rata)"
                    labels.append(f"{display} ({p['percentage']:.2f}%)")
                    values.append(p["percentage"])
                fig = go.Figure(data=[go.Sankey(
                    node=dict(pad=15, thickness=20, label=labels),
                    link=dict(source=[0]*len(values), target=list(range(1, len(labels))), value=values)
                )])
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                if contributors:
                    labels = ["Funded (PHP)"]
                    values = []
                    for c in contributors:
                        display = user_id_to_display.get(str(c.get("user_id")), c.get("name", "Unknown"))
                        funded = c.get("units", 0) * c.get("php_per_unit", 0)
                        labels.append(f"{display} ({c.get('units', 0)}u @ ₱{c.get('php_per_unit', 0):,.0f})")
                        values.append(funded)
                    fig = go.Figure(data=[go.Sankey(
                        node=dict(pad=15, thickness=20, label=labels),
                        link=dict(source=[0]*len(values), target=list(range(1, len(values))), value=values)
                    )])
                    st.plotly_chart(fig, use_container_width=True)

    if not accounts:
        st.info("No accounts launched yet • Contact owner to start empire growth")
