"""
Page 1 — Portfolio Overview
Donut chart (risk), stacked bar (hardship by risk level),
trend line (risk over time), persona distribution donut.
All data from Redis. Auto-refreshes every 3 minutes.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os, sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import (
    load_css, render_header, render_sidebar, render_live_tag,
    fetch_all_customers, risk_counts, hardship_distribution,
    REFRESH_INTERVAL_MS,
)

st.set_page_config(page_title="Portfolio Overview — Equilibrate", page_icon="E", layout="wide")
load_css()

from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=REFRESH_INTERVAL_MS, limit=None, key="portfolio_refresh")

render_sidebar()
render_header()

title_col, live_col = st.columns([4, 1])
with title_col:
    st.markdown("# Portfolio Overview")
with live_col:
    st.markdown("<br>", unsafe_allow_html=True)
    render_live_tag()

df = fetch_all_customers()
if df.empty:
    st.warning("No customer data available.")
    st.stop()

counts = risk_counts(df)
total = len(df)

# ── KPI ──
st.markdown("## Key Risk Indicators")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Customers", f"{total:,}")
with c2:
    st.metric("High Risk", f"{counts['HIGH']:,}")
with c3:
    st.metric("Medium Risk", f"{counts['MEDIUM']:,}")
with c4:
    st.metric("Low Risk", f"{counts['LOW']:,}")

# ── Chart styling ──
CHART_FONT = dict(family="Inter, Segoe UI, sans-serif", color="#0f172a")
CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=CHART_FONT,
    margin=dict(t=30, b=40, l=40, r=30),
)

# ── Row 1: Risk Donut + Hardship Donut ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
chart1, chart2 = st.columns(2)

with chart1:
    st.markdown("## Risk Distribution")
    fig_donut = go.Figure(data=[go.Pie(
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
    fig_donut.update_layout(
        **CHART_LAYOUT,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5,
            font=dict(size=12, family="Inter, sans-serif", color="#0f172a"),
        ),
        annotations=[dict(
            text=f"<b>{total:,}</b><br><span style='font-size:11px;color:#64748b'>Total</span>",
            x=0.5, y=0.5, font_size=20, font_family="Inter, sans-serif",
            showarrow=False, font_color="#0f172a",
        )],
        height=350,
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with chart2:
    st.markdown("## Hardship Classification")
    hardship = hardship_distribution(df)
    if hardship:
        h_labels = [h.replace("_", " ").title() for h in hardship.keys()]
        h_values = list(hardship.values())
        h_colors = ["#0E2A5A", "#1F6FEB", "#E5484D", "#F59E0B", "#6366F1"][:len(h_labels)]

        fig_hardship_donut = go.Figure(data=[go.Pie(
            labels=h_labels,
            values=h_values,
            marker=dict(
                colors=h_colors,
                line=dict(color="#FFFFFF", width=2),
            ),
            hole=0.55,
            textinfo="label+value",
            textfont=dict(size=11, family="Inter, sans-serif", color="#0f172a"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
        )])
        fig_hardship_donut.update_layout(
            **CHART_LAYOUT,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                font=dict(size=11, family="Inter", color="#334155"),
            ),
            annotations=[dict(
                text=f"<b>{sum(h_values):,}</b><br><span style='font-size:10px;color:#64748b'>Flagged</span>",
                x=0.5, y=0.5, font_size=16, font_family="Inter, sans-serif",
                showarrow=False, font_color="#0f172a",
            )],
            height=350,
        )
        st.plotly_chart(fig_hardship_donut, use_container_width=True)
    else:
        st.info("Hardship data will appear once the risk engine processes customer profiles.")

# ── Row 2: Hardship by Risk Level (Stacked Bar) ──
if "hardship_type" in df.columns and "risk_level" in df.columns:
    hardship_risk = df[df["hardship_type"] != "NONE"].copy()
    if not hardship_risk.empty:
        st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
        st.markdown("## Hardship by Risk Level")

        pivot = hardship_risk.groupby(["hardship_type", "risk_level"]).size().reset_index(name="count")
        risk_colors = {"HIGH": "#E5484D", "MEDIUM": "#F59E0B", "LOW": "#22C55E"}

        fig_stacked = go.Figure()
        for rl in ["HIGH", "MEDIUM", "LOW"]:
            rl_data = pivot[pivot["risk_level"] == rl]
            if not rl_data.empty:
                fig_stacked.add_trace(go.Bar(
                    x=[h.replace("_", " ").title() for h in rl_data["hardship_type"]],
                    y=rl_data["count"],
                    name=rl,
                    marker_color=risk_colors[rl],
                    text=rl_data["count"],
                    textposition="inside",
                    textfont=dict(size=12, color="white", family="Inter"),
                    hovertemplate="<b>%{x}</b><br>Risk: " + rl + "<br>Count: %{y}<extra></extra>",
                ))

        fig_stacked.update_layout(
            **CHART_LAYOUT,
            barmode="stack",
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5,
                font=dict(size=12, family="Inter", color="#334155"),
            ),
            xaxis=dict(title="Hardship Type", showgrid=False,
                       tickfont=dict(size=12, family="Inter", color="#334155"),
                       titlefont=dict(size=12, family="Inter", color="#64748b")),
            yaxis=dict(title="Customers", showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                       tickfont=dict(size=11, family="Inter", color="#334155"),
                       titlefont=dict(size=12, family="Inter", color="#64748b")),
            height=380,
            bargap=0.3,
        )
        st.plotly_chart(fig_stacked, use_container_width=True)

# ── Row 3: Risk Levels Over Time ──
st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Risk Levels Over Time")

TREND_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "risk_trend.csv")
now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
try:
    if os.path.isfile(TREND_CSV):
        trend_df = pd.read_csv(TREND_CSV)
    else:
        trend_df = pd.DataFrame(columns=["timestamp", "high", "medium", "low"])

    new_row = pd.DataFrame([{
        "timestamp": now_str,
        "high": counts["HIGH"],
        "medium": counts["MEDIUM"],
        "low": counts["LOW"],
    }])
    trend_df = pd.concat([trend_df, new_row], ignore_index=True).tail(500)
    trend_df.to_csv(TREND_CSV, index=False)
except Exception:
    trend_df = pd.DataFrame(columns=["timestamp", "high", "medium", "low"])

if len(trend_df) >= 2:
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=trend_df["timestamp"], y=trend_df["high"],
        mode="lines+markers", name="High Risk",
        line=dict(color="#E5484D", width=2.5), marker=dict(size=5),
        hovertemplate="<b>High Risk</b><br>Time: %{x}<br>Count: %{y}<extra></extra>",
    ))
    fig_line.add_trace(go.Scatter(
        x=trend_df["timestamp"], y=trend_df["medium"],
        mode="lines", name="Medium Risk",
        line=dict(color="#F59E0B", width=2, dash="dot"),
        hovertemplate="<b>Medium Risk</b><br>Time: %{x}<br>Count: %{y}<extra></extra>",
    ))
    fig_line.add_trace(go.Scatter(
        x=trend_df["timestamp"], y=trend_df["low"],
        mode="lines", name="Low Risk",
        line=dict(color="#22C55E", width=2, dash="dot"),
        hovertemplate="<b>Low Risk</b><br>Time: %{x}<br>Count: %{y}<extra></extra>",
    ))
    fig_line.update_layout(
        **CHART_LAYOUT,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5,
            font=dict(size=12, family="Inter", color="#334155"),
        ),
        xaxis=dict(title="Time", showgrid=False,
                   tickfont=dict(size=10, color="#334155"), tickangle=-45,
                   titlefont=dict(size=12, family="Inter", color="#64748b")),
        yaxis=dict(title="Customers", showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                   tickfont=dict(size=11, color="#334155"),
                   titlefont=dict(size=12, family="Inter", color="#64748b")),
        height=370,
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Trend data is being collected. Chart appears after multiple refresh cycles.")

# ── Row 4: Persona Distribution ──
if "persona" in df.columns:
    st.markdown('<div class="eq-section-divider"></div>', unsafe_allow_html=True)
    st.markdown("## Customer Persona Distribution")

    persona_counts = df["persona"].value_counts().to_dict()
    if persona_counts:
        p_labels = [p.replace("_", " ").title() for p in persona_counts.keys()]
        p_values = list(persona_counts.values())
        p_colors = ["#22C55E", "#1F6FEB", "#E5484D", "#F59E0B", "#6366F1"][:len(p_labels)]

        fig_persona = go.Figure(data=[go.Pie(
            labels=p_labels, values=p_values,
            marker=dict(colors=p_colors, line=dict(color="#FFFFFF", width=2)),
            hole=0.5,
            textinfo="label+percent",
            textfont=dict(size=12, family="Inter", color="#0f172a"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
        )])
        fig_persona.update_layout(
            **CHART_LAYOUT,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5,
                font=dict(size=12, color="#334155"),
            ),
            height=350,
        )
        st.plotly_chart(fig_persona, use_container_width=True)
