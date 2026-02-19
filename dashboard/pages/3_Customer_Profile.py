"""
Page 3 — Customer Profile
Searchable customer list at top. Click a row to view full profile below.
Profile shows: Customer Details, Behaviour Summary, Risk Explanation.
"""
import streamlit as st
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
    st.warning("Awaiting live transactions. Ensure Kafka pipeline and feature engine are running.")
    st.stop()

# Ensure risk_score is numeric
if "risk_score" in df.columns:
    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(0)

# ═══════════════════════════════════════════════════════════════
# SECTION 1: SEARCHABLE CUSTOMER TABLE
# ═══════════════════════════════════════════════════════════════

st.markdown("## Search Customers")
st.markdown(
    '<p style="color:#334155; font-size:0.88rem; margin-bottom:12px;">'
    'Search by Customer ID, City, or Employment Type. Select a customer to view full profile below.</p>',
    unsafe_allow_html=True,
)

# Search bar + filters
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

# Display the customer list as a styled HTML table
if search_df.empty:
    st.info("No customers match your search criteria.")
else:
    list_cols = ["customer_id", "risk_level", "risk_score", "hardship_type",
                 "city", "employment_type", "recommended_action"]
    available_cols = [c for c in list_cols if c in search_df.columns]
    list_df = search_df[available_cols].copy()

    col_headers = {
        "customer_id": "Customer ID",
        "risk_level": "Risk Level",
        "risk_score": "Risk Score",
        "hardship_type": "Hardship",
        "city": "City",
        "employment_type": "Employment",
        "recommended_action": "Action",
    }

    def risk_pill(level):
        lvl = str(level).upper()
        cls = {"HIGH": "eq-pill-high", "MEDIUM": "eq-pill-medium", "LOW": "eq-pill-low"}.get(lvl, "")
        return f'<span class="eq-pill {cls}">{lvl}</span>'

    header_cells = "".join(f"<th>{col_headers.get(c, c)}</th>" for c in available_cols)
    table_html = f'''<div class="eq-table-container" style="max-height:450px;">
    <table class="eq-table">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>'''

    for _, row in list_df.iterrows():
        table_html += "<tr>"
        for c in available_cols:
            val = row.get(c, "")
            if c == "risk_level":
                cell = risk_pill(val)
            elif c == "hardship_type":
                cell = str(val).replace("_", " ").title() if val and val != "NONE" else "None"
            elif c == "employment_type":
                cell = str(val).replace("_", " ").title() if pd.notna(val) else "Unknown"
            elif c == "risk_score":
                try:
                    cell = f"{int(float(val)):,}"
                except (ValueError, TypeError):
                    cell = str(val)
            else:
                cell = str(val) if pd.notna(val) else ""
            table_html += f'<td>{cell}</td>'
        table_html += "</tr>"

    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)
    st.caption(f"Showing {len(list_df):,} of {len(df):,} customers")

# ═══════════════════════════════════════════════════════════════
# SECTION 2: FULL CUSTOMER PROFILE VIEW
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Customer Detail")

# Use session state from Risk Queue page if available
default_cid = st.session_state.get("selected_customer_id", "")

cid_input = st.text_input(
    "Enter Customer ID",
    value=default_cid,
    placeholder="e.g. C001, C042…",
    key="cp_profile_cid_input",
)

selected_id = cid_input.strip() if cid_input else ""

if not selected_id:
    st.info("Enter a Customer ID above to view their full profile.")
    st.stop()

profile = get_customer_profile(selected_id)
if not profile:
    st.error(f"No profile found for customer {selected_id}.")
    st.stop()

# ── Extract fields ──
risk_level = profile.get("risk_level", "LOW")
try:
    risk_score = int(float(profile.get("risk_score", 0)))
except (ValueError, TypeError):
    risk_score = 0
hardship = profile.get("hardship_type", "NONE")
txn_count = int(float(profile.get("txn_count", 0)))
total_spend = float(profile.get("total_spend", 0))
essential = float(profile.get("essential_spend", 0))
discretionary = float(profile.get("discretionary_spend", 0))
salary_count = int(float(profile.get("salary_count", 0)))
days_since = int(float(profile.get("days_since_salary", -1)))
atm_7d = int(float(profile.get("atm_withdrawals_7d", 0)))
withdrawals = int(float(profile.get("withdrawals", 0)))
spend_change = float(profile.get("spending_change_pct", 0))
recommended_action = profile.get("recommended_action", "Continue monitoring")
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
        <span style="font-size:1.2rem; font-weight:700; color:#0f172a;">Customer {selected_id}</span>
        <span style="background:{style['bg']}; color:{style['text']};
               font-weight:700; padding:5px 14px; border-radius:12px; font-size:0.88rem;">
            {risk_level} — Score {risk_score}/10
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Customer Details ──
st.markdown("### Customer Details")

try:
    monthly_income = f"₹{int(float(static_salary)):,}" if static_salary else "N/A"
except (ValueError, TypeError):
    monthly_income = "N/A"

# Get loan_emi from profile if available
loan_emi = profile.get("loan_emi", profile.get("emi", ""))
try:
    loan_emi_display = f"₹{int(float(loan_emi)):,}" if loan_emi else "N/A"
except (ValueError, TypeError):
    loan_emi_display = "N/A"

d1, d2, d3, d4, d5, d6 = st.columns(6)
with d1:
    st.metric("Customer ID", selected_id)
with d2:
    st.metric("Age", age if age else "N/A")
with d3:
    st.metric("City", city)
with d4:
    st.metric("Employment", employment)
with d5:
    st.metric("Monthly Income", monthly_income)
with d6:
    st.metric("Loan EMI", loan_emi_display)

# ── Behaviour Summary ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("### Behaviour Summary")

b1, b2, b3, b4 = st.columns(4)
with b1:
    st.metric("Transaction Count", f"{txn_count:,}")
with b2:
    st.metric("Salary Credits", f"{salary_count:,}")
with b3:
    st.metric("Withdrawals", f"{withdrawals:,}")
with b4:
    st.metric("Total Spend", f"₹{total_spend:,.0f}")

# ── Risk Explanation ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("### Risk Explanation")
st.markdown(
    '<p style="color:#334155; font-size:0.88rem;">Behavioural signals driving the risk assessment.</p>',
    unsafe_allow_html=True,
)

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
    factors.append((f"High discretionary spending: ₹{discretionary:,.0f}", "Possible overspending pattern", "warning"))

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

# ── Hardship & Recommended Action ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
hardship_display = hardship.replace("_", " ").title() if hardship != "NONE" else "None"

h1, h2 = st.columns(2)
with h1:
    st.markdown(f"""
    <div class="eq-card" style="padding:18px;">
        <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Hardship Type</div>
        <div style="font-size:1.1rem; font-weight:700; color:#0f172a; margin:6px 0;">{hardship_display}</div>
    </div>
    """, unsafe_allow_html=True)
with h2:
    st.markdown(f"""
    <div class="eq-card" style="padding:18px;">
        <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Recommended Action</div>
        <div style="font-size:0.9rem; font-weight:600; color:#1F6FEB; margin:6px 0; line-height:1.5;">{recommended_action}</div>
    </div>
    """, unsafe_allow_html=True)
