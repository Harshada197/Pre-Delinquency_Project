"""
Page 3 — Customer Profile
Searchable customer list + click-to-view 360-degree profile.
No more dropdown with repeated "LOW | Score: 3" entries.
Search by Customer ID, City, or Employment Type.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import (
    load_css, render_header, render_sidebar, render_live_tag,
    fetch_all_customers, get_customer_profile, REFRESH_INTERVAL_MS,
)

st.set_page_config(page_title="Customer Profile — Equilibrate", page_icon="E", layout="wide")
load_css()

from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="profile_refresh")

render_sidebar()
render_header()

title_col, live_col = st.columns([4, 1])
with title_col:
    st.markdown("# Customer Profile")
with live_col:
    st.markdown("<br>", unsafe_allow_html=True)
    render_live_tag()

df = fetch_all_customers()
if df.empty:
    st.warning("No customer data available.")
    st.stop()

# ═══════════════════════════════════════════════════════════════
# SECTION 1: SEARCHABLE CUSTOMER LIST
# ═══════════════════════════════════════════════════════════════

st.markdown("## Search Customers")
st.markdown(
    '<p style="color:#334155; font-size:0.88rem; margin-bottom:12px;">'
    'Search by Customer ID, City, or Employment Type. Click a row to view the full profile below.</p>',
    unsafe_allow_html=True,
)

# Search bar
search_col1, search_col2, search_col3 = st.columns([2, 1, 1])

with search_col1:
    search_query = st.text_input(
        "Search Customer ID / City / Employment",
        value="",
        placeholder="Type to search...",
        key="cp_search_query",
    )

with search_col2:
    risk_filter = st.selectbox(
        "Filter by Risk",
        ["All", "HIGH", "MEDIUM", "LOW"],
        key="cp_risk_filter",
    )

with search_col3:
    sort_option = st.selectbox(
        "Sort by",
        ["Risk Score (High→Low)", "Risk Score (Low→High)", "Customer ID"],
        key="cp_sort_option",
    )

# Apply search + filter
search_df = df.copy()

if search_query:
    q = search_query.strip().lower()
    mask = pd.Series([False] * len(search_df), index=search_df.index)
    if "customer_id" in search_df.columns:
        mask |= search_df["customer_id"].astype(str).str.lower().str.contains(q, na=False)
    if "city" in search_df.columns:
        mask |= search_df["city"].astype(str).str.lower().str.contains(q, na=False)
    if "employment_type" in search_df.columns:
        mask |= search_df["employment_type"].astype(str).str.lower().str.contains(q, na=False)
    search_df = search_df[mask]

if risk_filter != "All" and "risk_level" in search_df.columns:
    search_df = search_df[search_df["risk_level"] == risk_filter]

# Sort
if sort_option == "Risk Score (High→Low)" and "risk_score" in search_df.columns:
    search_df = search_df.sort_values("risk_score", ascending=False)
elif sort_option == "Risk Score (Low→High)" and "risk_score" in search_df.columns:
    search_df = search_df.sort_values("risk_score", ascending=True)
elif sort_option == "Customer ID" and "customer_id" in search_df.columns:
    search_df = search_df.sort_values("customer_id")

# Display the customer list table
if search_df.empty:
    st.info("No customers match your search criteria.")
else:
    list_cols = ["customer_id", "risk_level", "risk_score", "hardship_type",
                 "city", "employment_type", "salary_count", "recommended_action"]
    available_cols = [c for c in list_cols if c in search_df.columns]

    list_df = search_df[available_cols].copy()
    list_rename = {
        "customer_id": "Customer ID",
        "risk_level": "Risk Level",
        "risk_score": "Risk Score",
        "hardship_type": "Hardship",
        "city": "City",
        "employment_type": "Employment",
        "salary_count": "Salary Credits",
        "recommended_action": "Action",
    }
    list_df = list_df.rename(columns=list_rename)

    if "Hardship" in list_df.columns:
        list_df["Hardship"] = list_df["Hardship"].apply(
            lambda x: str(x).replace("_", " ").title() if x and x != "NONE" else "None"
        )
    if "Employment" in list_df.columns:
        list_df["Employment"] = list_df["Employment"].apply(
            lambda x: str(x).replace("_", " ").title() if pd.notna(x) else "Unknown"
        )

    st.dataframe(
        list_df.reset_index(drop=True),
        use_container_width=True,
        height=min(450, 45 + len(list_df) * 35),
        hide_index=True,
        column_config={
            "Risk Score": st.column_config.NumberColumn("Risk Score", format="%d", width="small"),
            "Salary Credits": st.column_config.NumberColumn("Salary Credits", format="%d", width="small"),
        },
    )
    st.caption(f"Showing {len(list_df):,} of {len(df):,} customers")

# ═══════════════════════════════════════════════════════════════
# SECTION 2: CUSTOMER 360 PROFILE VIEW
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Customer 360 Profile")

# Use session state from Risk Queue page if available
default_cid = st.session_state.get("selected_customer_id", "")

# Clean customer ID selector — just the ID, no repeated scores
cid_list = search_df["customer_id"].astype(str).tolist() if not search_df.empty else df["customer_id"].astype(str).tolist()

# If default from session state, put it first
if default_cid and default_cid in cid_list:
    cid_list.remove(default_cid)
    cid_list.insert(0, default_cid)

selected_id = st.selectbox(
    "Select Customer ID",
    cid_list,
    key="cp_profile_selector",
)

if not selected_id:
    st.info("Select a customer above to view their full profile.")
    st.stop()

profile = get_customer_profile(selected_id)
if not profile:
    st.error(f"No profile found for customer {selected_id}.")
    st.stop()

# ── Extract fields ──
risk_level = profile.get("risk_level", "LOW")
risk_score = 0
try:
    risk_score = int(float(profile.get("risk_score", 0)))
except (ValueError, TypeError):
    risk_score = 0
hardship = profile.get("hardship_type", "NONE")
persona = profile.get("persona", "UNKNOWN")
txn_count = int(float(profile.get("txn_count", 0)))
total_spend = float(profile.get("total_spend", 0))
essential = float(profile.get("essential_spend", 0))
discretionary = float(profile.get("discretionary_spend", 0))
salary_count = int(float(profile.get("salary_count", 0)))
days_since = int(float(profile.get("days_since_salary", -1)))
atm_7d = int(float(profile.get("atm_withdrawals_7d", 0)))
txn_freq = int(float(profile.get("txn_frequency_7d", 0)))
spend_change = float(profile.get("spending_change_pct", 0))
recommended_action = profile.get("recommended_action", "Continue monitoring")
last_updated = profile.get("last_updated", "")
city = profile.get("city", "Unknown")
employment = str(profile.get("employment_type", "Unknown")).replace("_", " ").title()
age = profile.get("age", "")
static_salary = profile.get("static_salary", "")

# ── Badge colors ──
BADGE = {
    "HIGH": {"bg": "#FEE2E2", "text": "#B91C1C", "border": "#E5484D"},
    "MEDIUM": {"bg": "#FEF3C7", "text": "#B45309", "border": "#F59E0B"},
    "LOW": {"bg": "#DCFCE7", "text": "#166534", "border": "#22C55E"},
}
style = BADGE.get(risk_level, BADGE["LOW"])

# ── Header Card ──
st.markdown(f"""
<div class="eq-card" style="border-left: 5px solid {style['border']}; padding:18px; margin:12px 0;">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
        <div>
            <span style="font-size:1.2rem; font-weight:700; color:#0f172a;">Customer {selected_id}</span>
            <span style="margin-left:12px; background:{style['bg']}; color:{style['text']};
                   font-weight:700; padding:5px 14px; border-radius:12px; font-size:0.88rem;">
                {risk_level} — Score {risk_score}/10
            </span>
        </div>
        <div style="text-align:right; font-size:0.85rem; color:#334155;">
            {city} | {employment} | Age: {age}<br>
            <span style="color:#64748b;">Updated: {last_updated}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Row 1: Risk Gauge + Key Metrics ──
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Risk Score")
    gauge_color = style["border"]
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={"text": "Risk Score", "font": {"size": 14, "family": "Inter", "color": "#0f172a"}},
        number={"font": {"size": 34, "family": "Inter", "color": "#0f172a"}, "suffix": "/10"},
        gauge=dict(
            axis=dict(range=[0, 10], tickwidth=1, tickcolor="#D1D5DB"),
            bar=dict(color=gauge_color),
            steps=[
                dict(range=[0, 3], color="#DCFCE7"),
                dict(range=[3, 6], color="#FEF3C7"),
                dict(range=[6, 10], color="#FEE2E2"),
            ],
            threshold=dict(line=dict(color="#0f172a", width=2), thickness=0.8, value=risk_score),
        ),
    ))
    fig_gauge.update_layout(
        height=210, margin=dict(t=30, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with col2:
    st.markdown("### Key Metrics")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Transactions", f"{txn_count:,}")
    with m2:
        st.metric("Total Spend", f"Rs {total_spend:,.0f}")
    with m3:
        st.metric("Salary Credits", f"{salary_count:,}")
    with m4:
        days_display = f"{days_since}d" if days_since >= 0 else "N/A"
        st.metric("Days No Salary", days_display)

    m5, m6, m7, m8 = st.columns(4)
    with m5:
        st.metric("Essential Spend", f"Rs {essential:,.0f}")
    with m6:
        st.metric("Discretionary", f"Rs {discretionary:,.0f}")
    with m7:
        st.metric("ATM (7d)", f"{atm_7d}")
    with m8:
        delta_color = "inverse" if spend_change < 0 else "normal"
        st.metric("Spend Change", f"{spend_change:.1f}%", delta=f"{spend_change:.1f}%", delta_color=delta_color)

# ── Row 2: Risk Explainability ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Risk Explainability")
st.markdown(
    '<p style="color:#334155; font-size:0.88rem;">Why is this customer flagged? '
    'Below are the specific behavioural signals driving the risk assessment.</p>',
    unsafe_allow_html=True,
)

col_explain, col_action = st.columns([2, 1])

with col_explain:
    factors = []

    if salary_count == 0 and txn_count > 5:
        factors.append(("No salary credit detected", "Possible income disruption or job loss", "critical"))
    elif days_since > 30:
        factors.append((f"Last salary was {days_since} days ago", "Extended income gap may indicate employment issues", "warning"))

    if atm_7d >= 10:
        factors.append((f"Very high ATM withdrawals ({atm_7d} in 7d)", "Panic liquidity behaviour — withdrawing reserves", "critical"))
    elif atm_7d >= 5:
        factors.append((f"Elevated ATM activity ({atm_7d} in 7d)", "Above-normal withdrawal frequency", "warning"))

    if spend_change < -40:
        factors.append((f"Spending dropped {abs(spend_change):.0f}%", "Significant financial contraction", "critical"))
    elif spend_change < -20:
        factors.append((f"Spending declined {abs(spend_change):.0f}%", "Early contraction signal", "warning"))

    if essential > 0 and discretionary == 0 and txn_count > 5:
        factors.append(("Zero discretionary spending", "Customer in survival mode — only essentials", "critical"))
    elif essential > 0 and discretionary > 0 and essential > discretionary * 3:
        ratio = round(essential / max(discretionary, 1), 1)
        factors.append((f"Essential-to-discretionary ratio: {ratio}x", "Financial stress indicator", "warning"))

    if discretionary > essential * 2 and discretionary > 5000:
        factors.append((f"High discretionary spending: Rs {discretionary:,.0f}", "Possible overspending pattern", "warning"))

    if not factors:
        st.markdown("""
        <div class="eq-card" style="padding:16px; text-align:center;">
            <span style="font-weight:600; color:#22C55E; font-size:0.95rem;">No significant risk factors detected</span><br>
            <span style="font-size:0.88rem; color:#334155;">Customer profile is within expected parameters.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        for title, desc, severity in factors:
            sev_color = "#E5484D" if severity == "critical" else "#F59E0B"
            st.markdown(f"""
            <div class="eq-card" style="border-left:4px solid {sev_color}; padding:14px; margin-bottom:6px;">
                <span style="font-weight:700; color:#0f172a; font-size:0.92rem;">{title}</span><br>
                <span style="font-size:0.85rem; color:#334155;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)

with col_action:
    hardship_display = hardship.replace("_", " ").title() if hardship != "NONE" else "None"
    persona_display = persona.replace("_", " ").title() if persona else "Unknown"
    st.markdown(f"""
    <div class="eq-card" style="padding:18px;">
        <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Hardship Type</div>
        <div style="font-size:1.1rem; font-weight:700; color:#0f172a; margin:6px 0 14px;">{hardship_display}</div>

        <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Persona</div>
        <div style="font-size:1.0rem; font-weight:600; color:#0f172a; margin:6px 0 14px;">{persona_display}</div>

        <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Recommended Action</div>
        <div style="font-size:0.9rem; font-weight:600; color:#1F6FEB; margin:6px 0; line-height:1.5;">
            {recommended_action}
        </div>

        <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600; margin-top:14px;">Transaction Freq (7d)</div>
        <div style="font-size:1.1rem; font-weight:700; color:#0f172a;">{txn_freq}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Row 3: Spending Analysis ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Spending Analysis")

if essential > 0 or discretionary > 0:
    col_sp1, col_sp2 = st.columns(2)

    with col_sp1:
        fig_spend = go.Figure(data=[go.Pie(
            labels=["Essential", "Discretionary"],
            values=[essential, max(discretionary, 0.01)],
            marker=dict(
                colors=["#1F6FEB", "#F59E0B"],
                line=dict(color="#FFFFFF", width=2),
            ),
            hole=0.55,
            textinfo="label+percent",
            textfont=dict(size=12, family="Inter", color="#0f172a"),
            hovertemplate="<b>%{label}</b><br>Amount: Rs %{value:,.0f}<br>Share: %{percent}<extra></extra>",
        )])
        fig_spend.update_layout(
            height=280, margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5,
                        font=dict(size=12, color="#334155")),
        )
        st.plotly_chart(fig_spend, use_container_width=True)

    with col_sp2:
        st.markdown(f"""
        <div class="eq-card" style="padding:18px;">
            <div style="margin-bottom:12px;">
                <span style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Essential Spending</span><br>
                <span style="font-size:1.1rem; font-weight:700; color:#1F6FEB;">Rs {essential:,.0f}</span>
            </div>
            <div style="margin-bottom:12px;">
                <span style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Discretionary Spending</span><br>
                <span style="font-size:1.1rem; font-weight:700; color:#F59E0B;">Rs {discretionary:,.0f}</span>
            </div>
            <div style="margin-bottom:12px;">
                <span style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Total Spend</span><br>
                <span style="font-size:1.1rem; font-weight:700; color:#0f172a;">Rs {total_spend:,.0f}</span>
            </div>
            <div>
                <span style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Essential : Discretionary Ratio</span><br>
                <span style="font-size:1.1rem; font-weight:700; color:#0f172a;">
                    {essential / max(discretionary, 1):.1f}x
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Insufficient spending data for this customer.")

# ── Intervention History ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Intervention History")

last_intervention = profile.get("last_intervention", "")
intervention_status = profile.get("intervention_status", "")
intervention_ts = profile.get("intervention_timestamp", "")

if last_intervention:
    status_color = {
        "SMS_SENT": "#1F6FEB",
        "REVIEWED": "#F59E0B",
        "COMPLETED": "#22C55E",
        "CALL_SCHEDULED": "#6366F1",
        "AUDIO_GENERATED": "#8B5CF6",
    }.get(intervention_status.upper() if intervention_status else "", "#64748b")

    st.markdown(f"""
    <div class="eq-card" style="padding:18px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <span style="font-weight:700; color:#0f172a;">Last Intervention</span>
            <span style="background:{status_color}18; color:{status_color}; font-weight:700;
                   padding:4px 12px; border-radius:12px; font-size:0.85rem;">
                {intervention_status.replace('_', ' ').title() if intervention_status else 'N/A'}
            </span>
        </div>
        <div style="font-size:0.92rem; color:#1e293b;">{last_intervention}</div>
        <div style="font-size:0.82rem; color:#64748b; margin-top:8px;">{intervention_ts}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No interventions have been recorded for this customer.")
