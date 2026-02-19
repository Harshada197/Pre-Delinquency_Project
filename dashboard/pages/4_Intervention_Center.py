"""
Page 4 — Intervention Center
Enter Customer ID → view risk profile → auto-generate template message
→ edit → send via SMS/WhatsApp/Call/Reviewed → log to data/intervention_log.csv.
Full message history for each customer shown below.
"""
import streamlit as st
import pandas as pd
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import (
    load_css, render_header, render_sidebar, render_live_tag,
    fetch_all_customers, get_customer_profile, write_intervention_feedback,
    REFRESH_INTERVAL_MS,
)
from audit_log import log_audit_event, load_audit_log

st.set_page_config(page_title="Intervention Center — Equilibrate", page_icon="E", layout="wide")
load_css()

from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="intervention_refresh")

render_sidebar()
render_header()

title_col, live_col = st.columns([4, 1])
with title_col:
    st.markdown("# Intervention Center")
with live_col:
    st.markdown("<br>", unsafe_allow_html=True)
    render_live_tag()

st.markdown("""
<div class="eq-card" style="padding:14px; background:#F0F4FF; border-left:4px solid #1F6FEB;">
    <span style="font-weight:700; color:#0f172a;">Notice:</span>
    <span style="color:#334155; font-size:0.9rem;">
        All messages use pre-approved policy templates. Staff must review messages before sending.
    </span>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TEMPLATE MESSAGE ENGINE (rule-based, NO LLM)
# ════════════════════════════════════════════════════════════

MESSAGE_TEMPLATES = {
    "INCOME_SHOCK": (
        "Dear Customer, we noticed a disruption in your income credits. "
        "We can assist with flexible repayment options. Please contact support."
    ),
    "EXPENSE_COMPRESSION": (
        "We see increased essential expenses. Our advisors can help restructure your EMI."
    ),
    "OVER_LEVERAGE": (
        "You may have multiple financial obligations. We can consolidate or restructure payments."
    ),
    "OVERSPENDING": (
        "We have observed elevated discretionary spending. Our financial advisors "
        "can help with budgeting and spending discipline."
    ),
    "LIQUIDITY_STRESS": (
        "We notice signs of liquidity stress in your account. Our team can "
        "offer short-term relief options. Please reach out to us."
    ),
}

DEFAULT_MESSAGE = (
    "Dear Customer, we would like to inform you about our support options. "
    "Please contact our helpline at 1800-XXX-XXXX for more information."
)


def get_template_message(hardship_type, customer_id, channel="SMS"):
    """Generate a message from the template engine based on hardship type."""
    template = MESSAGE_TEMPLATES.get(hardship_type, DEFAULT_MESSAGE)
    if channel == "WhatsApp":
        template = f"[WhatsApp] {template}"
    elif channel == "Voice":
        template = f"[Voice/IVR] {template}"
    return template


# ════════════════════════════════════════════════════════════
# STEP 1: Enter Customer ID
# ════════════════════════════════════════════════════════════

st.markdown("## Select Customer for Intervention")

# Use session state if navigating from Risk Queue
default_cid = st.session_state.get("selected_customer_id", "")

cid_input = st.text_input(
    "Enter Customer ID",
    value=default_cid,
    placeholder="e.g. C001, C042…",
    key="int_cid_input",
)

selected_id = cid_input.strip() if cid_input else ""

if not selected_id:
    st.info("Enter a Customer ID above to begin intervention workflow.")
    st.stop()


# ════════════════════════════════════════════════════════════
# STEP 2: Fetch and Display Profile
# ════════════════════════════════════════════════════════════

profile = get_customer_profile(selected_id)
if not profile:
    st.error(f"No profile found for customer {selected_id}.")
    st.stop()

risk_level = profile.get("risk_level", "LOW")
try:
    risk_score = int(float(profile.get("risk_score", 0)))
except (ValueError, TypeError):
    risk_score = 0
hardship = profile.get("hardship_type", "NONE")
recommended_action = profile.get("recommended_action", "Continue monitoring")

BADGE = {
    "HIGH": {"bg": "#FEE2E2", "text": "#B91C1C", "border": "#E5484D"},
    "MEDIUM": {"bg": "#FEF3C7", "text": "#B45309", "border": "#F59E0B"},
    "LOW": {"bg": "#DCFCE7", "text": "#166534", "border": "#22C55E"},
}
sty = BADGE.get(risk_level, BADGE["LOW"])

# Display: Risk Level, Hardship Type, Risk Factors, Recommended Action
st.markdown(f"""
<div class="eq-card" style="border-left: 5px solid {sty['border']}; padding:16px;">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
        <span style="font-size:1.1rem; font-weight:700; color:#0f172a;">Customer {selected_id}</span>
        <span style="background:{sty['bg']}; color:{sty['text']}; font-weight:700;
               padding:5px 14px; border-radius:12px; font-size:0.88rem;">
            {risk_level} | Score: {risk_score}/10
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

info1, info2, info3 = st.columns(3)
with info1:
    hardship_display = hardship.replace("_", " ").title() if hardship != "NONE" else "None"
    st.markdown(f"""
    <div class="eq-card" style="padding:14px;">
        <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Hardship Type</div>
        <div style="font-size:1rem; font-weight:700; color:#0f172a; margin-top:4px;">{hardship_display}</div>
    </div>
    """, unsafe_allow_html=True)

with info2:
    # Risk factors summary
    factors = []
    salary_c = int(float(profile.get("salary_count", 0)))
    days_s = int(float(profile.get("days_since_salary", -1)))
    atm_7d = int(float(profile.get("atm_withdrawals_7d", 0)))
    spendchg = float(profile.get("spending_change_pct", 0))

    if salary_c == 0:
        factors.append("No salary credit")
    if days_s > 30:
        factors.append(f"Salary gap: {days_s}d")
    if atm_7d >= 5:
        factors.append(f"ATM: {atm_7d} in 7d")
    if spendchg < -30:
        factors.append(f"Spend drop: {abs(spendchg):.0f}%")
    if not factors:
        factors.append("Within normal parameters")

    factors_str = "<br>".join(factors)
    st.markdown(f"""
    <div class="eq-card" style="padding:14px;">
        <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Risk Factors</div>
        <div style="font-size:0.88rem; color:#0f172a; margin-top:4px; line-height:1.6;">{factors_str}</div>
    </div>
    """, unsafe_allow_html=True)

with info3:
    st.markdown(f"""
    <div class="eq-card" style="padding:14px;">
        <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Recommended Action</div>
        <div style="font-size:0.9rem; font-weight:600; color:#1F6FEB; margin-top:4px; line-height:1.5;">{recommended_action}</div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# STEP 3: Auto-generate outreach message using TEMPLATE ENGINE
# ════════════════════════════════════════════════════════════

st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Outreach Message")

channel = st.radio(
    "Communication Channel",
    ["SMS", "WhatsApp", "Voice"],
    horizontal=True,
    key="int_channel",
)

# Generate template-based message (NOT LLM)
auto_message = get_template_message(hardship, selected_id, channel=channel)

# Editable message area
edited_message = st.text_area(
    "Review and edit before sending:",
    value=auto_message,
    height=120,
    key="int_message_area",
)


# ════════════════════════════════════════════════════════════
# STEP 4: Action Buttons
# ════════════════════════════════════════════════════════════

st.markdown("### Intervention Actions")
a1, a2, a3, a4 = st.columns(4)

with a1:
    if st.button("Send SMS", key="send_sms_btn", use_container_width=True):
        log_audit_event(
            customer_id=selected_id,
            action_type="SMS_SENT",
            message=edited_message,
            risk_level=risk_level,
        )
        write_intervention_feedback(selected_id, "SMS_SENT", edited_message)
        st.success(f"SMS logged for Customer {selected_id}.")

with a2:
    if st.button("Send WhatsApp", key="send_wa_btn", use_container_width=True):
        log_audit_event(
            customer_id=selected_id,
            action_type="WHATSAPP_SENT",
            message=edited_message,
            risk_level=risk_level,
        )
        write_intervention_feedback(selected_id, "WHATSAPP_SENT", edited_message)
        st.success(f"WhatsApp logged for Customer {selected_id}.")

with a3:
    if st.button("Schedule Call", key="schedule_call_btn", use_container_width=True):
        log_audit_event(
            customer_id=selected_id,
            action_type="CALL_SCHEDULED",
            message=f"Outbound call scheduled for customer {selected_id}.",
            risk_level=risk_level,
        )
        write_intervention_feedback(selected_id, "CALL_SCHEDULED", "Outbound call scheduled")
        st.success(f"Call scheduled for Customer {selected_id}.")

with a4:
    if st.button("Mark Reviewed", key="mark_reviewed_btn", use_container_width=True):
        log_audit_event(
            customer_id=selected_id,
            action_type="REVIEWED",
            message="Case reviewed by officer.",
            risk_level=risk_level,
        )
        write_intervention_feedback(selected_id, "REVIEWED", "Case reviewed")
        st.success(f"Customer {selected_id} marked as reviewed.")


# ════════════════════════════════════════════════════════════
# STEP 5: Full Message History for this Customer
# ════════════════════════════════════════════════════════════

st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Message History")

audit_df = load_audit_log()
if audit_df is not None and not audit_df.empty and "customer_id" in audit_df.columns:
    cust_audit = audit_df[audit_df["customer_id"].astype(str) == selected_id]
    if not cust_audit.empty:
        # Sort by timestamp descending
        if "timestamp" in cust_audit.columns:
            cust_audit = cust_audit.sort_values("timestamp", ascending=False)

        st.markdown(
            f'<p style="font-weight:700; color:#0f172a; font-size:0.95rem;">'
            f'{len(cust_audit)} entries for Customer {selected_id}</p>',
            unsafe_allow_html=True,
        )

        # Styled HTML table — no leading whitespace to avoid markdown code-block parsing
        table_html = '<div class="eq-table-container" style="max-height:400px;">'
        table_html += '<table class="eq-table">'
        table_html += '<thead><tr>'
        table_html += '<th>Timestamp</th><th>Risk Level</th><th>Action</th><th>Message</th>'
        table_html += '</tr></thead><tbody>'

        for _, row in cust_audit.iterrows():
            ts = row.get("timestamp", "")
            rl = row.get("risk_level", "")
            act = row.get("action", "")
            msg = str(row.get("message", ""))[:150]

            # Color-code action types
            act_color = "#1F6FEB"
            if "SENT" in str(act).upper():
                act_color = "#22C55E"
            elif "REVIEWED" in str(act).upper():
                act_color = "#F59E0B"
            elif "SCHEDULED" in str(act).upper():
                act_color = "#6366F1"

            table_html += f'<tr><td style="white-space:nowrap;">{ts}</td>'
            table_html += f'<td>{rl}</td>'
            table_html += f'<td style="color:{act_color} !important; font-weight:700;">{act}</td>'
            table_html += f'<td style="max-width:350px;">{msg}</td></tr>'

        table_html += '</tbody></table></div>'
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info(f"No intervention history for Customer {selected_id}.")
else:
    st.info("No intervention entries recorded yet. Send an intervention to create the first entry.")
