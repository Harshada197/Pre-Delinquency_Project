"""
Page 2 — Risk Queue
Prioritised work queue with filters. Shows why each customer is risky.
Color-coded risk badges. Table includes City, Employment, Salary Credits,
Withdrawals, Recommended Action. Click-through to Customer Profile.
"""
import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import (
    load_css, render_header, render_sidebar, render_live_tag,
    fetch_all_customers, REFRESH_INTERVAL_MS,
)

st.set_page_config(page_title="Risk Queue — Equilibrate", page_icon="E", layout="wide")
load_css()

from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="queue_refresh")

render_sidebar()
render_header()

title_col, live_col = st.columns([4, 1])
with title_col:
    st.markdown("# Risk Queue")
with live_col:
    st.markdown("<br>", unsafe_allow_html=True)
    render_live_tag()

df = fetch_all_customers()
if df.empty:
    st.warning("No customer data available.")
    st.stop()

# ── Filters ──
st.markdown("## Filter Risk Queue")
f1, f2, f3 = st.columns(3)
with f1:
    risk_filter = st.multiselect(
        "Risk Level", ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM"],
        key="rq_risk_filter"
    )
with f2:
    hardship_options = ["All"] + sorted([
        h for h in df["hardship_type"].unique() if h and h != "NONE"
    ]) if "hardship_type" in df.columns else ["All"]
    hardship_filter = st.selectbox("Hardship Type", hardship_options, key="rq_hardship_filter")
with f3:
    persona_options = ["All"] + sorted([
        p for p in df["persona"].unique() if p and p != "UNKNOWN"
    ]) if "persona" in df.columns else ["All"]
    persona_filter = st.selectbox("Persona", persona_options, key="rq_persona_filter")

# ── Apply filters ──
filtered = df.copy()
if risk_filter and "risk_level" in filtered.columns:
    filtered = filtered[filtered["risk_level"].isin(risk_filter)]
if hardship_filter != "All" and "hardship_type" in filtered.columns:
    filtered = filtered[filtered["hardship_type"] == hardship_filter]
if persona_filter != "All" and "persona" in filtered.columns:
    filtered = filtered[filtered["persona"] == persona_filter]

# Sort by risk score descending
if "risk_score" in filtered.columns:
    filtered = filtered.sort_values("risk_score", ascending=False)

# ── Stats bar ──
high_count = len(filtered[filtered["risk_level"] == "HIGH"]) if "risk_level" in filtered.columns else 0
med_count = len(filtered[filtered["risk_level"] == "MEDIUM"]) if "risk_level" in filtered.columns else 0
low_count = len(filtered[filtered["risk_level"] == "LOW"]) if "risk_level" in filtered.columns else 0

st.markdown(f"""
<div class="eq-card" style="display:flex; justify-content:space-around; padding:14px; background:#F8FAFC;">
    <span style="font-weight:700;color:#E5484D; font-size:0.95rem;">HIGH: {high_count}</span>
    <span style="font-weight:700;color:#D97706; font-size:0.95rem;">MEDIUM: {med_count}</span>
    <span style="font-weight:700;color:#16A34A; font-size:0.95rem;">LOW: {low_count}</span>
    <span style="font-weight:700;color:#0f172a; font-size:0.95rem;">TOTAL: {len(filtered)}</span>
</div>
""", unsafe_allow_html=True)

# ── Render table ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Customer Risk Table")

if filtered.empty:
    st.info("No customers match the selected filters.")
else:
    # Include City, Employment, Salary Credits, Withdrawals as required
    all_display_cols = [
        "customer_id", "risk_level", "risk_score", "hardship_type",
        "salary_count", "withdrawals", "city", "employment_type",
        "recommended_action",
    ]

    display_cols = [c for c in all_display_cols if c in filtered.columns]
    display_df = filtered[display_cols].copy()

    rename_map = {
        "customer_id": "Customer ID",
        "risk_level": "Risk Level",
        "risk_score": "Score",
        "hardship_type": "Hardship",
        "salary_count": "Salary Credits",
        "withdrawals": "Withdrawals",
        "city": "City",
        "employment_type": "Employment",
        "recommended_action": "Recommended Action",
    }
    display_df = display_df.rename(columns=rename_map)

    if "Hardship" in display_df.columns:
        display_df["Hardship"] = display_df["Hardship"].apply(
            lambda x: str(x).replace("_", " ").title() if x and x != "NONE" else "None"
        )
    if "Employment" in display_df.columns:
        display_df["Employment"] = display_df["Employment"].apply(
            lambda x: str(x).replace("_", " ").title() if pd.notna(x) else "Unknown"
        )

    # Streamlit dataframe with scrolling
    st.dataframe(
        display_df.reset_index(drop=True),
        use_container_width=True,
        height=min(600, 45 + len(display_df) * 35),
        hide_index=True,
        column_config={
            "Risk Level": st.column_config.TextColumn("Risk Level", width="small"),
            "Score": st.column_config.NumberColumn("Score", format="%d", width="small"),
            "Salary Credits": st.column_config.NumberColumn("Salary Credits", format="%d", width="small"),
            "Withdrawals": st.column_config.NumberColumn("Withdrawals", format="%d", width="small"),
        },
    )

    st.caption(f"Showing {len(display_df):,} customers | Sorted by risk score descending")

    # ── Clickable row to navigate to Customer Profile ──
    st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
    st.markdown("## View Customer Detail")
    st.markdown(
        '<p style="color:#334155; font-size:0.88rem;">Select a customer below to view their '
        'full profile on the <b>Customer Profile</b> page.</p>',
        unsafe_allow_html=True,
    )

    cid_options = filtered["customer_id"].tolist()
    if cid_options:
        selected_cid = st.selectbox(
            "Select Customer ID",
            cid_options,
            key="rq_navigate_cid",
        )
        if st.button("View Profile", key="rq_view_profile_btn", use_container_width=True):
            st.session_state["selected_customer_id"] = str(selected_cid)
            st.info(f"Open the **Customer Profile** page from the sidebar to view Customer {selected_cid}.")

    # ── Risk Explanation cards for HIGH risk ──
    high_in_view = filtered[filtered["risk_level"] == "HIGH"] if "risk_level" in filtered.columns else pd.DataFrame()

    if not high_in_view.empty:
        st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
        st.markdown("## Risk Explanation — HIGH Risk Customers")

        for _, row in high_in_view.head(10).iterrows():
            cid = row.get("customer_id", "?")
            score = row.get("risk_score", "?")
            hardship_val = str(row.get("hardship_type", "NONE")).replace("_", " ").title()
            city = row.get("city", "Unknown")
            emp = str(row.get("employment_type", "Unknown")).replace("_", " ").title()
            action = row.get("recommended_action", "Continue monitoring")
            days = row.get("days_since_salary", -1)
            atm = row.get("atm_withdrawals_7d", 0)
            spendchg = row.get("spending_change_pct", 0)
            salary_c = row.get("salary_count", 0)

            try:
                salary_c = int(salary_c)
            except (ValueError, TypeError):
                salary_c = 0
            try:
                days_val = int(days)
            except (ValueError, TypeError):
                days_val = -1
            try:
                atm_val = int(atm)
            except (ValueError, TypeError):
                atm_val = 0
            try:
                spendchg_val = float(spendchg)
            except (ValueError, TypeError):
                spendchg_val = 0

            factors = []
            if salary_c == 0:
                factors.append("No salary credit detected — possible income disruption")
            elif days_val > 30:
                factors.append(f"Last salary {days_val} days ago — extended income gap")
            if atm_val >= 5:
                factors.append(f"High ATM withdrawals: {atm_val} in 7 days")
            if spendchg_val < -30:
                factors.append(f"Spending dropped {abs(spendchg_val):.0f}%")
            if not factors:
                factors.append("Multiple converging risk signals")

            factors_html = "".join([f"<li style='color:#1e293b;'>{f}</li>" for f in factors])

            st.markdown(f"""
            <div class="eq-card" style="border-left: 4px solid #E5484D; padding:16px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-weight:700; color:#0f172a; font-size:0.95rem;">Customer {cid}</span>
                    <span style="background:#FEE2E2; color:#B91C1C; font-weight:700; padding:4px 12px; border-radius:12px; font-size:0.82rem;">
                        Score: {score}/10
                    </span>
                </div>
                <div style="display:flex; gap:16px; margin-bottom:8px; flex-wrap:wrap;">
                    <span style="font-size:0.85rem; color:#334155;">Hardship: <b>{hardship_val}</b></span>
                    <span style="font-size:0.85rem; color:#334155;">City: <b>{city}</b></span>
                    <span style="font-size:0.85rem; color:#334155;">Employment: <b>{emp}</b></span>
                </div>
                <ul style="margin:0 0 8px 0; padding-left:20px;">{factors_html}</ul>
                <div style="font-size:0.85rem; color:#1F6FEB; font-weight:600;">
                    Action: {action}
                </div>
            </div>
            """, unsafe_allow_html=True)
