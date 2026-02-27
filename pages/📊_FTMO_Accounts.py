import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime
from utils.auth import require_auth
from utils.sidebar import render_sidebar
from utils.supabase_client import supabase

render_sidebar()
require_auth()  # Allow both owner/admin and client

# ────────────────────────────────────────────────
# THEME COLORS (match Dashboard)
# ────────────────────────────────────────────────
accent_primary = "#00ffaa"
accent_gold = "#ffd700"
accent_glow = "#00ffaa40"

st.header("📊 FTMO Accounts Management 🚀")
st.markdown("**Empire core** • Flexible trees • Optional Contributor Pool & Growth Fund • Fixed 50/50 or pro-rata • Exact 100% validation • Auto v2 migration • Realtime previews")

current_role = st.session_state.get("role", "guest").lower()

# ────────────────────────────────────────────────
# SHARED DATA FETCH
# ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_ftmo_data():
    accs = supabase.table("ftmo_accounts").select("*").order("created_date", desc=True).execute().data or []
    users = supabase.table("users").select("id, full_name, role, title").execute().data or []
  
    uid_to_display = {}
    display_to_uid = {}
    uid_to_name = {}
    for u in users:
        if u["role"] in ["client", "owner"]:
            uid = str(u["id"])
            display = u["full_name"]
            if u.get("title"):
                display += f" ({u['title']})"
            uid_to_display[uid] = display
            display_to_uid[display] = uid
            uid_to_name[uid] = u["full_name"]
  
    special = ["Contributor Pool", "Manual Payout (Temporary)"]  # Removed "Growth Fund" (auto only)
    for s in special:
        display_to_uid[s] = None
  
    part_options = special + list(display_to_uid.keys())
    contrib_options = list(uid_to_display.values())
  
    owner_display = next((d for d, uid in display_to_uid.items() if uid and any(uu["role"] == "owner" for uu in users if str(uu["id"]) == uid)), "King Minted")
  
    return accs, uid_to_display, display_to_uid, uid_to_name, part_options, contrib_options, owner_display

accounts, uid_to_display, display_to_uid, uid_to_name, part_options, contrib_options, owner_display = fetch_ftmo_data()

# ────────────────────────────────────────────────
# OWNER / ADMIN FULL MANAGEMENT
# ────────────────────────────────────────────────
if current_role in ["owner", "admin"]:
    # ─── CREATE NEW ACCOUNT ───
    with st.expander("➕ Launch New FTMO Account", expanded=True):
        with st.form("create_ftmo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Account Name *", placeholder="e.g. KMFX Scaled 200K")
                ftmo_id = st.text_input("FTMO ID (Optional)")
                phase = st.selectbox("Current Phase *", ["Challenge P1", "Challenge P2", "Verification", "Funded", "Scaled"])
            with c2:
                equity = st.number_input("Current Equity (USD)", min_value=0.0, value=100000.0, step=1000.0)
                withdrawable = st.number_input("Current Withdrawable (USD)", min_value=0.0, value=0.0, step=500.0)
            notes = st.text_area("Notes (Optional)")

            st.subheader("🌱 Growth Fund Allocation (Optional)")
            gf_pct = st.number_input("Growth Fund % from Gross Profit", 0.0, 50.0, 0.0, 0.5)  # default 0
            if gf_pct > 0:
                st.success(f"✅ {gf_pct:.1f}% auto-allocated to Growth Fund")
            else:
                st.info("ℹ️ No Growth Fund – perfect for fixed shares")

            st.subheader("🌳 Unified Profit Distribution Tree (%)")
            st.info("Flexible: Optional 'Contributor Pool' (0 or 1 row) • Fixed shares (50/50 etc.) or pro-rata • Total + GF = exactly 100%")
           
            default_rows = [
                {"display_name": owner_display, "role": "Founder/Owner", "percentage": max(100.0 - gf_pct, 0.0)}
            ]
            tree_df = pd.DataFrame(default_rows)
            edited_tree = st.data_editor(
                tree_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "display_name": st.column_config.SelectboxColumn("Name *", options=part_options, required=True),
                    "role": st.column_config.TextColumn("Role"),
                    "percentage": st.column_config.NumberColumn("% *", min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
                },
                key="tree_create"
            )

            total_tree_sum = edited_tree["percentage"].sum() if not edited_tree.empty else 0.0
            total_with_gf = total_tree_sum + gf_pct
            st.progress(min(total_with_gf / 100.0, 1.0))
            st.caption(f"Current Total: {total_with_gf:.2f}% (must be exactly 100.00%)")

            contrib_rows = edited_tree[edited_tree["display_name"] == "Contributor Pool"]
            if len(contrib_rows) > 1:
                st.error("❌ At most one 'Contributor Pool' row allowed")
                contrib_pct = 0.0
            elif abs(total_with_gf - 100.0) > 0.01:
                st.error(f"❌ Total must be exactly 100.00% (current: {total_with_gf:.2f}%)")
                contrib_pct = 0.0
            else:
                st.success("✅ Valid distribution")
                contrib_pct = contrib_rows.iloc[0]["percentage"] if not contrib_rows.empty else 0.0

            manual_inputs = []
            for idx, row in edited_tree.iterrows():
                if row["display_name"] == "Manual Payout (Temporary)":
                    custom = st.text_input(f"Custom name for row {idx+1}", key=f"manual_{idx}")
                    if custom.strip():
                        manual_inputs.append((idx, custom.strip()))

            st.subheader("🌳 Contributors Funding Tree (PHP Units) – Optional")
            contrib_df = pd.DataFrame(columns=["display_name", "units", "php_per_unit"])
            edited_contrib = st.data_editor(
                contrib_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "display_name": st.column_config.SelectboxColumn("Contributor *", options=contrib_options, required=True),
                    "units": st.column_config.NumberColumn("Units", min_value=0.0, step=0.5),
                    "php_per_unit": st.column_config.NumberColumn("PHP per Unit", min_value=100.0, step=100.0)
                },
                key="contrib_create"
            )
            if not edited_contrib.empty:
                total_php = (edited_contrib["units"] * edited_contrib["php_per_unit"]).sum()
                st.metric("Total Funded (PHP)", f"₱{total_php:,.0f}")

            tab_prev1, tab_prev2 = st.tabs(["Profit Tree Preview", "Funding Tree Preview"])
            with tab_prev1:
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
                    link=dict(source=[0]*len(values), target=list(range(1, len(labels)+1)), value=values)
                )])
                fig.update_layout(height=400)
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
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            submitted = st.form_submit_button("🚀 Launch Account", type="primary", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("Account name required")
                elif len(contrib_rows) > 1:
                    st.error("At most one 'Contributor Pool' row allowed")
                elif abs(total_with_gf - 100.0) > 0.01:
                    st.error(f"Total must be exactly 100.00% (current: {total_with_gf:.2f}%)")
                else:
                    try:
                        final_part_v2 = []
                        for row in edited_tree.to_dict("records"):
                            display = row["display_name"]
                            user_id = display_to_uid.get(display)
                            final_part_v2.append({
                                "user_id": user_id,
                                "display_name": display,
                                "percentage": row["percentage"],
                                "role": row["role"]
                            })
                        for idx, custom in manual_inputs:
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
                            user_id = display_to_uid.get(display)
                            final_contrib_v2.append({
                                "user_id": user_id,
                                "units": row.get("units", 0),
                                "php_per_unit": row.get("php_per_unit", 0)
                            })
                        final_part_old = [{"name": uid_to_name.get(p["user_id"], p["display_name"]) if p["user_id"] else p["display_name"],
                                           "role": p["role"], "percentage": p["percentage"]} for p in final_part_v2]
                        final_contrib_old = [{"name": uid_to_name.get(c["user_id"], "Unknown"),
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
                            "contributor_share_pct": contrib_pct
                        }).execute()
                        st.success("Account launched successfully! 🎉")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Launch failed: {str(e)}")

    # ─── LIVE ACCOUNTS LIST + EDIT/DELETE ───
    st.subheader("Live Empire Accounts")
    if accounts:
        for acc in accounts:
            use_v2 = bool(acc.get("participants_v2"))
            participants = acc.get("participants_v2") if use_v2 else acc.get("participants", [])
            contributors = acc.get("contributors_v2") if use_v2 else acc.get("contributors", [])
            total_funded_php = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors)
            contrib_pct = acc.get("contributor_share_pct", 0)
            gf_pct_acc = sum(p.get("percentage", 0) for p in participants if "growth fund" in p.get("display_name", "").lower())
            with st.expander(f"🌟 {acc['name']} • {acc['current_phase']} • Equity ${acc.get('current_equity', 0):,.0f} • Funded ₱{total_funded_php:,.0f} • Pool {contrib_pct:.1f}% • GF {gf_pct_acc:.1f}% {'(v2)' if use_v2 else '(Legacy)'}"):
                tab1, tab2 = st.tabs(["Profit Tree", "Funding Tree"])
                with tab1:
                    labels = ["Gross Profit"]
                    values = []
                    for p in participants:
                        display = p.get("display_name") or uid_to_display.get(p.get("user_id"), p.get("name", "Unknown"))
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
                            display = uid_to_display.get(c.get("user_id"), c.get("name", "Unknown"))
                            funded = c.get("units", 0) * c.get("php_per_unit", 0)
                            labels.append(f"{display} ({c.get('units', 0)}u @ ₱{c.get('php_per_unit', 0):,.0f})")
                            values.append(funded)
                        fig = go.Figure(data=[go.Sankey(
                            node=dict(pad=15, thickness=20, label=labels),
                            link=dict(source=[0]*len(values), target=list(range(1, len(values))), value=values)
                        )])
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No contributors yet")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    if st.button("✏️ Edit", key=f"edit_{acc['id']}"):
                        st.session_state.edit_acc_id = acc["id"]
                        st.session_state.edit_acc_data = acc
                        st.rerun()
                with col_e2:
                    if st.button("🗑️ Delete", key=f"del_{acc['id']}", type="secondary"):
                        try:
                            supabase.table("ftmo_accounts").delete().eq("id", acc["id"]).execute()
                            st.success("Account deleted")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

        # ─── EDIT FORM ───
        if "edit_acc_id" in st.session_state:
            eid = st.session_state.edit_acc_id
            cur = st.session_state.edit_acc_data
            with st.expander(f"✏️ Editing {cur['name']}", expanded=True):
                with st.form(f"edit_form_{eid}", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Account Name *", value=cur["name"])
                        new_ftmo_id = st.text_input("FTMO ID", value=cur.get("ftmo_id") or "")
                        new_phase = st.selectbox("Current Phase *", ["Challenge P1", "Challenge P2", "Verification", "Funded", "Scaled"],
                                                 index=["Challenge P1", "Challenge P2", "Verification", "Funded", "Scaled"].index(cur["current_phase"]))
                    with col2:
                        new_equity = st.number_input("Current Equity (USD)", value=float(cur.get("current_equity", 0)), step=1000.0)
                        new_withdrawable = st.number_input("Current Withdrawable (USD)", value=float(cur.get("withdrawable_balance", 0)), step=500.0)
                    new_notes = st.text_area("Notes", value=cur.get("notes") or "")

                    use_v2 = bool(cur.get("participants_v2"))
                    current_part = pd.DataFrame(cur["participants_v2"] if use_v2 else cur.get("participants", []))
                    current_gf_pct = sum(row.get("percentage", 0.0) for _, row in current_part.iterrows() if "growth fund" in row.get("display_name", "").lower())

                    st.subheader("🌱 Growth Fund Allocation (Optional per Account)")
                    gf_pct = st.number_input("Growth Fund % from Gross Profit", min_value=0.0, max_value=50.0, value=current_gf_pct, step=0.5)

                    st.subheader("🌳 Unified Profit Tree (%)")
                    if use_v2:
                        current_part = current_part[["display_name", "role", "percentage"]]
                    else:
                        legacy = pd.DataFrame(cur.get("participants", []))
                        current_part = pd.DataFrame([{
                            "display_name": next((d for d, uid in display_to_uid.items() if uid_to_name.get(uid) == p["name"]), p["name"]),
                            "role": p.get("role", ""),
                            "percentage": p["percentage"]
                        } for p in legacy])
                        st.info("🔄 Legacy → Saving will migrate to v2")

                    current_part = current_part[~current_part["display_name"].str.lower().str.contains("growth fund", na=False)]

                    edited_tree = st.data_editor(
                        current_part,
                        num_rows="dynamic",
                        use_container_width=True,
                        key=f"edit_part_{eid}",
                        column_config={
                            "display_name": st.column_config.SelectboxColumn("Name *", options=part_options, required=True),
                            "role": st.column_config.TextColumn("Role"),
                            "percentage": st.column_config.NumberColumn("% *", min_value=0.0, max_value=100.0, step=0.1, format="%.2f")
                        }
                    )

                    total_tree_sum = edited_tree["percentage"].sum() if not edited_tree.empty else 0.0
                    total_with_gf = total_tree_sum + gf_pct
                    st.progress(min(total_with_gf / 100.0, 1.0))
                    st.caption(f"Current Total: {total_with_gf:.2f}% (must be exactly 100.00%)")

                    contrib_rows = edited_tree[edited_tree["display_name"] == "Contributor Pool"]
                    if len(contrib_rows) > 1:
                        st.error("❌ At most one 'Contributor Pool' row allowed")
                    elif abs(total_with_gf - 100.0) > 0.01:
                        st.error(f"❌ Total exactly 100.00% required (current: {total_with_gf:.2f}%)")
                    else:
                        st.success("✅ Valid distribution")
                        contrib_pct = contrib_rows.iloc[0]["percentage"] if not contrib_rows.empty else 0.0

                    manual_inputs = []
                    for idx, row in edited_tree.iterrows():
                        if row["display_name"] == "Manual Payout (Temporary)":
                            custom = st.text_input(f"Custom name for row {idx+1}", key=f"manual_edit_{eid}_{idx}")
                            if custom.strip():
                                manual_inputs.append((idx, custom.strip()))

                    st.subheader("🌳 Contributors Tree")
                    if use_v2:
                        current_contrib = pd.DataFrame(cur.get("contributors_v2", []))
                        current_contrib["display_name"] = current_contrib["user_id"].apply(lambda uid: uid_to_display.get(uid, "Unknown"))
                    else:
                        legacy_contrib = pd.DataFrame(cur.get("contributors", []))
                        current_contrib = pd.DataFrame([{
                            "display_name": next((d for d, uid in display_to_uid.items() if uid_to_name.get(uid) == c["name"]), c["name"]),
                            "units": c.get("units", 0),
                            "php_per_unit": c.get("php_per_unit", 0)
                        } for c in legacy_contrib])
                        st.info("🔄 Legacy contributors → Saving migrates to v2")

                    edited_contrib = st.data_editor(
                        current_contrib[["display_name", "units", "php_per_unit"]],
                        num_rows="dynamic",
                        use_container_width=True,
                        key=f"edit_contrib_{eid}",
                        column_config={
                            "display_name": st.column_config.SelectboxColumn("Contributor *", options=contrib_options, required=True),
                            "units": st.column_config.NumberColumn("Units", min_value=0.0, step=0.5),
                            "php_per_unit": st.column_config.NumberColumn("PHP/Unit", min_value=100.0, step=100.0)
                        }
                    )

                    if not edited_contrib.empty:
                        total_php = (edited_contrib["units"] * edited_contrib["php_per_unit"]).sum()
                        st.metric("Total Funded (PHP)", f"₱{total_php:,.0f}")

                    tab_prev1, tab_prev2 = st.tabs(["Profit Tree Preview", "Funding Tree Preview"])
                    with tab_prev1:
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
                                link=dict(source=[0]*len(values), target=list(range(1, len(values))), value=values)
                            )])
                            st.plotly_chart(fig, use_container_width=True)

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                            if not new_name.strip():
                                st.error("Name required")
                            elif len(contrib_rows) > 1:
                                st.error("At most one 'Contributor Pool' row allowed")
                            elif abs(total_with_gf - 100.0) > 0.01:
                                st.error("Valid tree + Growth Fund % required")
                            else:
                                try:
                                    final_part_v2 = []
                                    for row in edited_tree.to_dict("records"):
                                        display = row["display_name"]
                                        user_id = display_to_uid.get(display)
                                        final_part_v2.append({
                                            "user_id": user_id,
                                            "display_name": display,
                                            "percentage": row["percentage"],
                                            "role": row["role"]
                                        })
                                    for idx, custom in manual_inputs:
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
                                        user_id = display_to_uid.get(display)
                                        final_contrib_v2.append({
                                            "user_id": user_id,
                                            "units": row.get("units", 0),
                                            "php_per_unit": row.get("php_per_unit", 0)
                                        })
                                    final_part_old = [{"name": uid_to_name.get(p["user_id"], p["display_name"]) if p["user_id"] else p["display_name"],
                                                       "role": p["role"], "percentage": p["percentage"]} for p in final_part_v2]
                                    final_contrib_old = [{"name": uid_to_name.get(c["user_id"], "Unknown"),
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
                                        "contributor_share_pct": contrib_pct
                                    }).eq("id", eid).execute()
                                    st.success("Updated successfully! 🎉")
                                    del st.session_state.edit_acc_id
                                    del st.session_state.edit_acc_data
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Update failed: {str(e)}")
                    with col_cancel:
                        if st.form_submit_button("Cancel", type="secondary"):
                            del st.session_state.edit_acc_id
                            del st.session_state.edit_acc_data
                            st.rerun()

else:
    # ────────────────────────────────────────────────
    # CLIENT VIEW (read-only)
    # ────────────────────────────────────────────────
    my_name = st.session_state.full_name
    my_accounts = [a for a in accounts if any(
        p.get("display_name") == my_name or p.get("name") == my_name or
        uid_to_name.get(p.get("user_id")) == my_name
        for p in (a.get("participants_v2") or a.get("participants", []))
    )]
    st.subheader(f"Your Shared Accounts ({len(my_accounts)})")
    if my_accounts:
        for acc in my_accounts:
            participants = acc.get("participants_v2") or acc.get("participants", [])
            my_pct = next((p["percentage"] for p in participants if
                           p.get("display_name") == my_name or p.get("name") == my_name or
                           uid_to_name.get(p.get("user_id")) == my_name), 0.0)
            contributors = acc.get("contributors_v2") or acc.get("contributors", [])
            my_funded = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in contributors
                            if uid_to_name.get(c.get("user_id")) == my_name or c.get("name") == my_name)
            gf_pct_acc = sum(p.get("percentage", 0) for p in participants if "growth fund" in p.get("display_name", "").lower())
            with st.expander(f"🌟 {acc['name']} • Your Share: {my_pct:.2f}% • Funded ₱{my_funded:,.0f} • Phase: {acc['current_phase']} • GF {gf_pct_acc:.1f}%"):
                st.metric("Equity", f"${acc.get('current_equity', 0):,.0f}")
                st.metric("Withdrawable", f"${acc.get('withdrawable_balance', 0):,.0f}")
                tab1, tab2 = st.tabs(["Profit Tree", "Funding Tree"])
                with tab1:
                    labels = ["Gross Profit"]
                    values = []
                    for p in participants:
                        display = p.get("display_name") or uid_to_display.get(p.get("user_id"), p.get("name", "Unknown"))
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
                            display = uid_to_display.get(c.get("user_id"), c.get("name", "Unknown"))
                            funded = c.get("units", 0) * c.get("php_per_unit", 0)
                            labels.append(f"{display} ({c.get('units', 0)}u @ ₱{c.get('php_per_unit', 0):,.0f})")
                            values.append(funded)
                        fig = go.Figure(data=[go.Sankey(
                            node=dict(pad=15, thickness=20, label=labels),
                            link=dict(source=[0]*len(values), target=list(range(1, len(values))), value=values)
                        )])
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("You are not participating in any FTMO accounts yet.")

    st.subheader("All Empire Accounts Overview")
    for acc in accounts:
        total_funded = sum(c.get("units", 0) * c.get("php_per_unit", 0) for c in (acc.get("contributors_v2") or acc.get("contributors", [])))
        gf_pct_acc = sum(p.get("percentage", 0) for p in (acc.get("participants_v2") or acc.get("participants", [])) if "growth fund" in p.get("display_name", "").lower())
        with st.expander(f"{acc['name']} • {acc['current_phase']} • Equity ${acc.get('current_equity', 0):,.0f} • Funded ₱{total_funded:,.0f} • GF {gf_pct_acc:.1f}%"):
            participants = acc.get("participants_v2") or acc.get("participants", [])
            contributors = acc.get("contributors_v2") or acc.get("contributors", [])
            labels = ["Gross Profit"]
            values = []
            for p in participants:
                display = p.get("display_name") or uid_to_display.get(p.get("user_id"), p.get("name", "Unknown"))
                if display == "Contributor Pool":
                    display = "Contributor Pool (pro-rata)"
                labels.append(f"{display} ({p['percentage']:.2f}%)")
                values.append(p["percentage"])
            fig = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=20, label=labels),
                link=dict(source=[0]*len(values), target=list(range(1, len(labels))), value=values)
            )])
            st.plotly_chart(fig, use_container_width=True)
            if contributors:
                labels = ["Funded (PHP)"]
                values = []
                for c in contributors:
                    display = uid_to_display.get(c.get("user_id"), c.get("name", "Unknown"))
                    funded = c.get("units", 0) * c.get("php_per_unit", 0)
                    labels.append(f"{display} ({c.get('units', 0)}u @ ₱{c.get('php_per_unit', 0):,.0f})")
                    values.append(funded)
                fig = go.Figure(data=[go.Sankey(
                    node=dict(pad=15, thickness=20, label=labels),
                    link=dict(source=[0]*len(values), target=list(range(1, len(values))), value=values)
                )])
                st.plotly_chart(fig, use_container_width=True)

    if not accounts:
        st.info("No accounts yet • Owner launches empire growth")

# ────────────────────────────────────────────────
# DASHBOARD-STYLE FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class="glass-card" style="padding:4rem 2rem; text-align:center; margin:5rem auto; max-width:1100px;
            border-radius:24px; border:2px solid {accent_primary}40;
            background:linear-gradient(135deg, rgba(0,255,170,0.08), rgba(255,215,0,0.05));
            box-shadow:0 20px 50px rgba(0,255,170,0.15);">
    <h1 style="font-size:3.2rem; background:linear-gradient(90deg,{accent_primary},{accent_gold});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Fully Automatic • Realtime • Exponential Empire
    </h1>
    <p style="font-size:1.4rem; opacity:0.9; margin:1.5rem 0;">
        Every transaction auto-syncs • Trees update instantly • Empire scales itself.
    </p>
    <h2 style="color:{accent_gold}; font-size:2.2rem; margin:1rem 0;">
        Built by Faith, Shared for Generations 👑
    </h2>
    <p style="opacity:0.8; font-style:italic;">
        KMFX Pro • Cloud Edition 2026 • Mark Jeff Blando
    </p>
</div>
""", unsafe_allow_html=True)