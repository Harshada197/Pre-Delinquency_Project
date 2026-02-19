"""
Equilibrate — Home (Operations Hub)
KPI overview + Immediate Attention table + hardship breakdown.
Auto-refreshes every 3 minutes.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    load_css, render_header, render_sidebar, render_live_tag,
    fetch_all_customers, risk_counts, hardship_distribution,
    REFRESH_INTERVAL_MS,
)

st.set_page_config(
    page_title="Home — Equilibrate",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

# Auto Refresh — every 3 minutes
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="home_refresh")

render_sidebar()
render_header()

title_col, live_col = st.columns([4, 1])
with title_col:
    st.markdown("# Operations Hub")
with live_col:
    st.markdown("<br>", unsafe_allow_html=True)
    render_live_tag()

# ── Data ──
df = fetch_all_customers()

if df.empty:
    st.warning("No customer data available. Ensure the Kafka pipeline and feature engine are running.")
    st.stop()

counts = risk_counts(df)
total = len(df)

# ── KPI Cards ──
st.markdown("## Key Performance Indicators")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Customers", f"{total:,}")
with c2:
    st.metric("High Risk", f"{counts['HIGH']:,}")
with c3:
    st.metric("Medium Risk", f"{counts['MEDIUM']:,}")
with c4:
    st.metric("Low Risk", f"{counts['LOW']:,}")

# ── Live Timestamps (proof of real-time) ──
from utils import get_last_live_transaction_time, get_last_risk_evaluation_time
last_txn_time = get_last_live_transaction_time()
last_risk_time = get_last_risk_evaluation_time()

t1, t2 = st.columns(2)
with t1:
    st.markdown(f"""
<div class="eq-card" style="padding:12px 18px; border-left:4px solid #1F6FEB;">
    <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Last Live Transaction</div>
    <div style="font-size:1rem; font-weight:700; color:#0f172a; margin-top:4px;">{last_txn_time or 'Waiting for stream…'}</div>
</div>
""", unsafe_allow_html=True)
with t2:
    st.markdown(f"""
<div class="eq-card" style="padding:12px 18px; border-left:4px solid #22C55E;">
    <div style="font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">Last Risk Evaluation</div>
    <div style="font-size:1rem; font-weight:700; color:#0f172a; margin-top:4px;">{last_risk_time or 'Waiting for engine…'}</div>
</div>
""", unsafe_allow_html=True)

# ── High Risk % indicator ──
h_pct = 100 * counts["HIGH"] / total if total else 0
severity = "normal" if h_pct < 3 else "elevated" if h_pct < 5 else "critical"
color_map = {"normal": "#22C55E", "elevated": "#F59E0B", "critical": "#E5484D"}
st.markdown(f"""
<div class="eq-card" style="text-align:center; padding:14px;">
    <span style="font-size:0.9rem; color:#0f172a;">High Risk Rate: </span>
    <span style="font-size:1.2rem; font-weight:700; color:{color_map[severity]};">{h_pct:.1f}%</span>
    <span style="font-size:0.82rem; color:#64748b;"> ({severity})</span>
</div>
""", unsafe_allow_html=True)

# ── Risk Distribution Donut ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Risk Distribution")

chart_col, summary_col = st.columns([2, 1])
with chart_col:
    fig = go.Figure(data=[go.Pie(
        labels=["HIGH", "MEDIUM", "LOW"],
        values=[counts["HIGH"], counts["MEDIUM"], counts["LOW"]],
        marker=dict(
            colors=["#E5484D", "#F59E0B", "#22C55E"],
            line=dict(color="#FFFFFF", width=2),
        ),
        hole=0.58,
        textinfo="value+percent",
        textfont=dict(size=13, family="Inter, sans-serif", color="#0f172a"),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    )])
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color="#0f172a"),
        margin=dict(t=20, b=30, l=30, r=30),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.08, xanchor="center", x=0.5,
            font=dict(size=12, family="Inter, sans-serif", color="#0f172a"),
        ),
        annotations=[dict(
            text=f"<b>{total:,}</b><br><span style='font-size:11px;color:#64748b'>Total</span>",
            x=0.5, y=0.5, font_size=20, font_family="Inter, sans-serif",
            showarrow=False, font_color="#0f172a",
        )],
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)

with summary_col:
    for level, color, label in [("HIGH", "#E5484D", "High Risk"), ("MEDIUM", "#F59E0B", "Medium Risk"), ("LOW", "#22C55E", "Low Risk")]:
        pct = 100 * counts[level] / total if total else 0
        st.markdown(f"""
        <div class="eq-card" style="border-left:4px solid {color}; padding:12px 16px; margin-bottom:8px;">
            <div style="font-size:0.82rem; color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:0.8px;">{label}</div>
            <div style="font-size:1.4rem; font-weight:700; color:#0f172a;">{counts[level]:,}
                <span style="font-size:0.82rem; color:#64748b; font-weight:500;">({pct:.1f}%)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Immediate Attention Table ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Immediate Attention Required")

if "risk_level" in df.columns:
    high_df = df[df["risk_level"] == "HIGH"].copy()

    if high_df.empty:
        st.info("No customers currently classified as HIGH risk.")
    else:
        if "risk_score" in high_df.columns:
            high_df = high_df.sort_values("risk_score", ascending=False)

        col_map = {
            "customer_id": "Customer ID",
            "risk_score": "Risk Score",
            "hardship_type": "Hardship Type",
            "city": "City",
            "employment_type": "Employment",
            "salary_count": "Salary Credits",
            "atm_withdrawals_7d": "ATM (7d)",
            "recommended_action": "Recommended Action",
        }

        display_cols = [c for c in col_map if c in high_df.columns]
        display_df = high_df[display_cols].rename(columns=col_map).reset_index(drop=True)

        if "Hardship Type" in display_df.columns:
            display_df["Hardship Type"] = display_df["Hardship Type"].apply(
                lambda x: str(x).replace("_", " ").title() if pd.notna(x) and x != "NONE" else "None"
            )

        if "Employment" in display_df.columns:
            display_df["Employment"] = display_df["Employment"].apply(
                lambda x: str(x).replace("_", " ").title() if pd.notna(x) else "Unknown"
            )

        st.dataframe(
            display_df,
            use_container_width=True,
            height=min(400, 40 + len(display_df) * 35),
            hide_index=True,
        )
        st.caption(f"{len(display_df):,} customers require immediate review")
else:
    st.info("Risk engine has not yet evaluated customers. Waiting for data.")

# ── Hardship Breakdown Bar Chart ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Hardship Breakdown")
hardship = hardship_distribution(df)
if hardship:
    labels = [h.replace("_", " ").title() for h in hardship.keys()]
    values = list(hardship.values())
    colors = ["#E5484D", "#F59E0B", "#1F6FEB", "#6366F1", "#22C55E"]

    fig_bar = go.Figure(data=[go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker=dict(color=colors[:len(labels)], line=dict(width=0)),
        text=[f"{v:,}" for v in values],
        textposition="outside",
        textfont=dict(size=12, family="Inter, sans-serif", color="#0f172a"),
        hovertemplate="<b>%{y}</b><br>Count: %{x:,}<extra></extra>",
    )])
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color="#0f172a"),
        margin=dict(t=10, b=30, l=150, r=60),
        xaxis=dict(
            title="Number of Customers",
            gridcolor="#E2E8F0",
            title_font=dict(size=12, color="#64748b"),
        ),
        yaxis=dict(autorange="reversed"),
        height=max(200, len(labels) * 55 + 60),
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("No hardship classifications detected yet.")

# ── Risk Trend Line Chart (last 30 min) ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Risk Trend (Last 30 Minutes)")

import os as _os
trend_path = _os.path.join(
    _os.path.dirname(_os.path.abspath(__file__)), "pages", "risk_trend.csv"
)
if _os.path.isfile(trend_path):
    try:
        trend_df = pd.read_csv(trend_path)
        if "timestamp" in trend_df.columns:
            trend_df["timestamp"] = pd.to_datetime(trend_df["timestamp"], errors="coerce")
            cutoff = pd.Timestamp.now() - pd.Timedelta(minutes=30)
            trend_df = trend_df[trend_df["timestamp"] >= cutoff]

            if not trend_df.empty:
                fig_trend = go.Figure()
                for col, color, name in [
                    ("HIGH", "#E5484D", "High Risk"),
                    ("MEDIUM", "#F59E0B", "Medium Risk"),
                    ("LOW", "#22C55E", "Low Risk"),
                ]:
                    if col in trend_df.columns:
                        fig_trend.add_trace(go.Scatter(
                            x=trend_df["timestamp"],
                            y=pd.to_numeric(trend_df[col], errors="coerce").fillna(0),
                            name=name,
                            mode="lines+markers",
                            line=dict(color=color, width=2),
                            marker=dict(size=5),
                            hovertemplate=f"<b>{name}</b><br>Time: %{{x|%H:%M}}<br>Count: %{{y}}<extra></extra>",
                        ))
                fig_trend.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif", color="#0f172a"),
                    margin=dict(t=10, b=40, l=50, r=20),
                    xaxis=dict(
                        title="Time",
                        gridcolor="#E2E8F0",
                        title_font=dict(size=12, color="#64748b"),
                    ),
                    yaxis=dict(
                        title="Customer Count",
                        gridcolor="#E2E8F0",
                        title_font=dict(size=12, color="#64748b"),
                    ),
                    legend=dict(
                        orientation="h", yanchor="bottom", y=-0.25,
                        xanchor="center", x=0.5,
                        font=dict(size=12, color="#0f172a"),
                    ),
                    height=320,
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("No trend data available for the last 30 minutes.")
        else:
            st.info("Risk trend data not yet available.")
    except Exception:
        st.info("Risk trend data not yet available.")
else:
    st.info("Risk trend file not found. Trends will appear once the portfolio overview page has been visited.")

# ── Navigation Cards ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Operations Modules")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class="eq-feature-card">
        <div class="eq-feature-icon" style="background: linear-gradient(135deg, #1F6FEB, #0E2A5A);">P</div>
        <div class="eq-feature-title">Portfolio Overview</div>
        <p class="eq-feature-desc">Risk distribution, hardship breakdown, and trend analysis.</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="eq-feature-card">
        <div class="eq-feature-icon" style="background: linear-gradient(135deg, #E5484D, #B91C1C);">R</div>
        <div class="eq-feature-title">Risk Queue</div>
        <p class="eq-feature-desc">Prioritised queue for officer review and case management.</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="eq-feature-card">
        <div class="eq-feature-icon" style="background: linear-gradient(135deg, #F59E0B, #D97706);">C</div>
        <div class="eq-feature-title">Customer Profile</div>
        <p class="eq-feature-desc">Full customer detail with risk explainability.</p>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="eq-feature-card">
        <div class="eq-feature-icon" style="background: linear-gradient(135deg, #22C55E, #16A34A);">I</div>
        <div class="eq-feature-title">Intervention Center</div>
        <p class="eq-feature-desc">Policy-based communications and audit trail.</p>
    </div>
    """, unsafe_allow_html=True)

