"""
Page 4 — Intervention Center
Policy-based communication + audit trail.
Messages use templates only (no LLM). Staff can review/edit before sending.
Audio generation via gTTS for IVR/WhatsApp simulation.
Supports SMS, WhatsApp, Voice channels.
Feedback loop writes intervention data back to Redis.
"""
import streamlit as st
import pandas as pd
import sys, os, json
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import (
    load_css, render_header, render_sidebar, render_live_tag,
    fetch_all_customers, get_customer_profile, write_intervention_feedback,
    generate_policy_message, REFRESH_INTERVAL_MS,
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
        All messages use pre-approved policy templates. LLM-based personalisation
        can be added post compliance approval. Staff must review messages before sending.
    </span>
</div>
""", unsafe_allow_html=True)

df = fetch_all_customers()
if df.empty:
    st.warning("No customer data available.")
    st.stop()

# ── Customer Selector ──
st.markdown("## Select Customer for Intervention")

if "risk_score" in df.columns:
    df_sorted = df.sort_values("risk_score", ascending=False)
else:
    df_sorted = df

# Clean selector — show ID, Risk, Hardship but not repeated useless info
customer_options = []
for _, row in df_sorted.iterrows():
    cid = row.get("customer_id", "?")
    rl = row.get("risk_level", "?")
    ht = str(row.get("hardship_type", "NONE")).replace("_", " ").title()
    rs = row.get("risk_score", 0)
    customer_options.append(f"{cid} | {rl} (Score: {int(rs)}) | {ht}")

selected = st.selectbox("Customer (ID | Risk | Hardship)", customer_options, key="int_cust_sel")

if not selected:
    st.info("Select a customer to begin.")
    st.stop()

selected_id = str(selected.split("|")[0].strip())
profile = get_customer_profile(selected_id)

if not profile:
    st.error(f"Profile not found for customer {selected_id}.")
    st.stop()

risk_level = profile.get("risk_level", "LOW")
risk_score = int(float(profile.get("risk_score", 0)))
hardship = profile.get("hardship_type", "NONE")
persona = profile.get("persona", "UNKNOWN")
city = profile.get("city", "Unknown")
employment = str(profile.get("employment_type", "Unknown")).replace("_", " ").title()

BADGE = {
    "HIGH": {"bg": "#FEE2E2", "text": "#B91C1C", "border": "#E5484D"},
    "MEDIUM": {"bg": "#FEF3C7", "text": "#B45309", "border": "#F59E0B"},
    "LOW": {"bg": "#DCFCE7", "text": "#166534", "border": "#22C55E"},
}
style = BADGE.get(risk_level, BADGE["LOW"])

st.markdown(f"""
<div class="eq-card" style="border-left: 5px solid {style['border']}; padding:16px;">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
        <span style="font-size:1.1rem; font-weight:700; color:#0f172a;">Customer {selected_id}</span>
        <span style="background:{style['bg']}; color:{style['text']}; font-weight:700;
               padding:5px 14px; border-radius:12px; font-size:0.88rem;">
            {risk_level} | Score: {risk_score}/10
        </span>
    </div>
    <div style="font-size:0.88rem; color:#334155; margin-top:8px;">
        Hardship: <b>{hardship.replace('_', ' ').title()}</b> |
        Persona: <b>{persona.replace('_', ' ').title()}</b> |
        City: <b>{city}</b> |
        Employment: <b>{employment}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Channel Selection + Message Generation ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Policy-Based Message")

ref_id = str(uuid.uuid4())[:8].upper()

chan_col, msg_col = st.columns([1, 3])
with chan_col:
    channel = st.radio(
        "Communication Channel",
        ["SMS", "WhatsApp", "Voice"],
        key="int_channel",
    )

message = generate_policy_message(selected_id, hardship, risk_level, ref_id, channel=channel)
action = profile.get("recommended_action", "Continue monitoring")

with msg_col:
    st.markdown(f"""
    <div class="eq-card" style="padding:14px;">
        <div style="font-weight:700; color:#0f172a; margin-bottom:6px;">Recommended Action</div>
        <div style="font-size:0.92rem; color:#1F6FEB; font-weight:600; margin-bottom:14px;">{action}</div>
        <div style="font-weight:700; color:#0f172a; margin-bottom:6px;">Channel: {channel}</div>
    </div>
    """, unsafe_allow_html=True)

# Editable message
edited_message = st.text_area(
    "Review and edit before sending:",
    value=message,
    height=120,
    key="int_message_area",
)

# ── Actions ──
st.markdown("### Intervention Actions")
a1, a2, a3 = st.columns(3)

with a1:
    send_label = f"Send {channel}"
    if st.button(send_label, key="send_msg_btn", use_container_width=True):
        log_audit_event(
            customer_id=selected_id,
            action_type=f"{channel.upper()}_SENT",
            message=edited_message,
            officer="System",
            ref_id=ref_id,
        )
        write_intervention_feedback(selected_id, f"{channel.upper()}_SENT", edited_message)
        st.success(f"{channel} logged for Customer {selected_id}. Ref: {ref_id}")

with a2:
    if st.button("Mark as Reviewed", key="mark_reviewed_btn", use_container_width=True):
        log_audit_event(
            customer_id=selected_id,
            action_type="REVIEWED",
            message="Case reviewed by officer.",
            officer="System",
            ref_id=ref_id,
        )
        write_intervention_feedback(selected_id, "REVIEWED", "Case reviewed")
        st.success(f"Customer {selected_id} marked as reviewed.")

with a3:
    if st.button("Schedule Call", key="schedule_call_btn", use_container_width=True):
        log_audit_event(
            customer_id=selected_id,
            action_type="CALL_SCHEDULED",
            message=f"Outbound call scheduled for customer {selected_id}.",
            officer="System",
            ref_id=ref_id,
        )
        write_intervention_feedback(selected_id, "CALL_SCHEDULED", "Outbound call scheduled")
        st.success(f"Call scheduled for Customer {selected_id}.")

# ── Audio Message (gTTS) ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Audio Message (IVR / WhatsApp Simulation)")

st.markdown("""
<div class="eq-card" style="padding:12px; background:#F0F4FF;">
    <span style="font-size:0.88rem; color:#334155;">
        Generate a text-to-speech audio file from the policy message.
        Simulates WhatsApp / IVR outreach without external APIs.
    </span>
</div>
""", unsafe_allow_html=True)

if st.button("Generate Audio", key="gen_audio_btn"):
    try:
        from gtts import gTTS
        import tempfile

        audio_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audio_messages")
        os.makedirs(audio_dir, exist_ok=True)

        filename = f"customer_{selected_id}_{ref_id}.mp3"
        filepath = os.path.join(audio_dir, filename)

        tts = gTTS(text=edited_message, lang="en", slow=False)
        tts.save(filepath)

        st.success(f"Audio generated: {filename}")
        st.audio(filepath, format="audio/mp3")

        log_audit_event(
            customer_id=selected_id,
            action_type="AUDIO_GENERATED",
            message=f"Audio message generated: {filename}",
            officer="System",
            ref_id=ref_id,
        )

    except ImportError:
        st.error("gTTS not installed. Run: pip install gTTS")
    except Exception as e:
        st.error(f"Audio generation failed: {e}")

# ═══════════════════════════════════════════════════════════════
# AUDIT TRAIL — IMPROVED VISIBILITY
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Audit Trail")

audit_df = load_audit_log()
if audit_df is not None and not audit_df.empty:
    # Per-customer audit entries
    if "customer_id" in audit_df.columns:
        cust_audit = audit_df[audit_df["customer_id"].astype(str) == selected_id]
        if not cust_audit.empty:
            st.markdown(
                f'<p style="font-weight:700; color:#0f172a; font-size:0.95rem;">'
                f'{len(cust_audit)} audit entries for Customer {selected_id}</p>',
                unsafe_allow_html=True,
            )

            # Render as styled HTML table for better visibility
            sort_col = "timestamp" if "timestamp" in cust_audit.columns else None
            if sort_col:
                cust_audit = cust_audit.sort_values(sort_col, ascending=False)

            # Styled table with visible borders and dark text
            table_html = """
            <div style="overflow-x:auto; margin-bottom:16px;">
            <table style="width:100%; border-collapse:collapse; font-size:0.88rem; font-family:Inter, sans-serif;">
                <thead>
                    <tr style="background:#1F6FEB; color:#FFFFFF;">
                        <th style="padding:10px 12px; text-align:left; font-weight:700;">Timestamp</th>
                        <th style="padding:10px 12px; text-align:left; font-weight:700;">Action</th>
                        <th style="padding:10px 12px; text-align:left; font-weight:700;">Message</th>
                        <th style="padding:10px 12px; text-align:left; font-weight:700;">Officer</th>
                        <th style="padding:10px 12px; text-align:left; font-weight:700;">Ref ID</th>
                    </tr>
                </thead>
                <tbody>
            """
            for i, (_, row) in enumerate(cust_audit.iterrows()):
                bg = "#F8FAFC" if i % 2 == 0 else "#FFFFFF"
                ts = row.get("timestamp", "")
                act = row.get("action_type", "")
                msg = str(row.get("message", ""))[:120]
                off = row.get("officer", "")
                rid = row.get("ref_id", "")

                # Color-code action types
                act_color = "#1F6FEB"
                if "SENT" in str(act).upper():
                    act_color = "#22C55E"
                elif "REVIEWED" in str(act).upper():
                    act_color = "#F59E0B"
                elif "SCHEDULED" in str(act).upper():
                    act_color = "#6366F1"

                table_html += f"""
                    <tr style="background:{bg}; border-bottom:1px solid #E2E8F0;">
                        <td style="padding:8px 12px; color:#0f172a; white-space:nowrap;">{ts}</td>
                        <td style="padding:8px 12px; color:{act_color}; font-weight:700;">{act}</td>
                        <td style="padding:8px 12px; color:#1e293b; max-width:300px;">{msg}</td>
                        <td style="padding:8px 12px; color:#334155;">{off}</td>
                        <td style="padding:8px 12px; color:#64748b; font-family:monospace; font-size:0.82rem;">{rid}</td>
                    </tr>
                """
            table_html += "</tbody></table></div>"
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.info(f"No audit entries for Customer {selected_id}.")

    # Full log in expander
    with st.expander("View Full Audit Log"):
        if "timestamp" in audit_df.columns:
            audit_df = audit_df.sort_values("timestamp", ascending=False)

        st.dataframe(
            audit_df,
            use_container_width=True,
            height=400,
            hide_index=True,
        )
        st.caption(f"Total entries: {len(audit_df):,}")
else:
    st.info("No audit entries recorded yet. Send an intervention to create the first entry.")
