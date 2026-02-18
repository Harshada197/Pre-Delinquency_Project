"""
Equilibrate — Global Enterprise Theme v5.0
Professional banking operations console.
Injected via st.markdown() — replaces external CSS files.
"""
import streamlit as st


def apply_theme():
    """Inject the full enterprise CSS theme. Call once per page after set_page_config."""
    st.markdown("""
    <style>
    /* ═══════════════════════════════════════════════════════════════
       EQUILIBRATE — Banking Operations Console Theme v5.0
       ═══════════════════════════════════════════════════════════════ */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── 1. GLOBAL ── */
    .stApp {
        background-color: #F4F7FB;
        font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
        color: #1A1A2E;
    }

    #MainMenu, footer, header { visibility: hidden; }

    /* Force readable text everywhere in main content */
    .stApp .main p, .stApp .main span, .stApp .main div,
    .stApp .main label, .stApp .main li, .stApp .main td {
        color: #1A1A2E;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }


    /* ── 2. HEADINGS ── */
    .stApp .main h1 {
        color: #0A1F44 !important;
        font-weight: 700 !important;
        font-size: 1.65rem !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: -0.01em;
        padding-bottom: 8px;
        margin-bottom: 18px !important;
        border-bottom: 2px solid #E2E8F0;
    }

    .stApp .main h2 {
        color: #0E2A5A !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        font-family: 'Inter', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1.1px;
        margin-top: 22px !important;
        margin-bottom: 12px !important;
    }

    .stApp .main h3 {
        color: #0A1F44 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stApp .main h4, .stApp .main h5, .stApp .main h6 {
        color: #0A1F44 !important;
        font-weight: 600 !important;
    }


    /* ── 3. SIDEBAR — Dark navy, white text ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A1F44 0%, #0E2A5A 50%, #122F60 100%);
        border-right: none;
        box-shadow: 3px 0 15px rgba(0, 0, 0, 0.12);
    }

    /* Force ALL sidebar content white */
    section[data-testid="stSidebar"] *,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5 {
        color: #FFFFFF !important;
        opacity: 1 !important;
    }

    /* Sidebar nav links */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] div,
    section[data-testid="stSidebar"] .stPageLink a,
    section[data-testid="stSidebar"] a span {
        color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover span {
        color: #7FB5F5 !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.1);
        margin: 14px 0;
    }

    /* Sidebar captions */
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {
        color: #8BAAC4 !important;
    }


    /* ── 4. SIDEBAR COMPONENTS ── */
    .sidebar-brand {
        background: linear-gradient(135deg, rgba(31, 111, 235, 0.15), rgba(31, 111, 235, 0.05));
        border: 1px solid rgba(31, 111, 235, 0.2);
        border-radius: 10px;
        padding: 18px 14px;
        margin-bottom: 18px;
        text-align: center;
    }

    .sidebar-brand-name {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        font-weight: 800;
        letter-spacing: 2.5px;
        color: #FFFFFF !important;
        margin: 0;
        text-transform: uppercase;
    }

    .sidebar-brand-sub {
        font-size: 0.72rem;
        color: #7FB5F5 !important;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin: 5px 0 0 0;
        font-weight: 500;
    }

    .sys-status-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 5px 0;
        font-size: 0.85rem;
        color: #FFFFFF !important;
    }

    .dot-green {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #22C55E;
        display: inline-block;
        box-shadow: 0 0 5px rgba(34, 197, 94, 0.5);
    }

    .dot-red {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #E5484D;
        display: inline-block;
    }

    .dot-amber {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #F59E0B;
        display: inline-block;
    }

    .sys-stat-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
        line-height: 1;
    }

    .sys-stat-label {
        font-size: 0.68rem;
        color: #8BAAC4 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 500;
    }


    /* ── 5. HEADER BANNER ── */
    .eq-header {
        background: linear-gradient(135deg, #0A1F44 0%, #0E2A5A 40%, #14375E 75%, #1A4A7A 100%);
        padding: 24px 32px;
        border-radius: 10px;
        margin-bottom: 24px;
        box-shadow: 0 3px 16px rgba(10, 31, 68, 0.2);
        position: relative;
        overflow: hidden;
    }

    .eq-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image:
            radial-gradient(circle at 20% 50%, rgba(31, 111, 235, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(34, 197, 94, 0.04) 0%, transparent 40%);
        pointer-events: none;
    }

    /* Force white on ALL header children */
    .eq-header, .eq-header *,
    .eq-header .eq-header-title,
    .eq-header .eq-header-subtitle,
    .eq-header span, .eq-header div, .eq-header p {
        color: #FFFFFF !important;
    }

    .eq-header-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: 2.5px;
        margin: 0;
        color: #FFFFFF !important;
        position: relative;
        text-transform: uppercase;
    }

    .eq-header-divider {
        width: 45px; height: 3px;
        background: #1F6FEB;
        border-radius: 2px;
        margin: 10px 0 0 0;
        position: relative;
    }

    .eq-header-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.85) !important;
        letter-spacing: 0.5px;
        margin: 6px 0 0 0;
        position: relative;
    }


    /* ── 6. METRIC CARDS ── */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px 18px 14px 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
        border-left: 4px solid #1F6FEB;
    }

    div[data-testid="stMetric"]:hover {
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.07);
        transform: translateY(-1px);
    }

    div[data-testid="stMetric"] label,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] div,
    [data-testid="stMetricLabel"] p {
        color: #4A5568 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] div {
        color: #0A1F44 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1.85rem !important;
        font-weight: 700;
    }

    /* Color-coded borders */
    div[data-testid="column"]:nth-child(1) div[data-testid="stMetric"] { border-left-color: #1F6FEB; }
    div[data-testid="column"]:nth-child(2) div[data-testid="stMetric"] { border-left-color: #E5484D; }
    div[data-testid="column"]:nth-child(3) div[data-testid="stMetric"] { border-left-color: #F59E0B; }
    div[data-testid="column"]:nth-child(4) div[data-testid="stMetric"] { border-left-color: #22C55E; }


    /* ── 7. CARDS ── */
    .eq-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 22px 26px;
        margin-bottom: 14px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        transition: box-shadow 0.2s ease;
    }

    .eq-card:hover {
        box-shadow: 0 5px 18px rgba(0, 0, 0, 0.07);
    }

    .eq-card * {
        color: #1A1A2E !important;
    }

    .eq-card-header {
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.1px;
        color: #0E2A5A !important;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid #F0F2F5;
    }

    .eq-stat-value {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #0A1F44 !important;
        line-height: 1.2;
    }

    .eq-stat-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #4A5568 !important;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        margin-top: 3px;
        font-weight: 500;
    }


    /* ── 8. FEATURE CARDS (Home) ── */
    .eq-feature-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        transition: all 0.25s ease;
        height: 100%;
        border-top: 3px solid #1F6FEB;
    }

    .eq-feature-card:hover {
        box-shadow: 0 6px 22px rgba(0, 0, 0, 0.07);
        transform: translateY(-2px);
    }

    .eq-feature-card * {
        color: #1A1A2E !important;
    }

    .eq-feature-icon {
        width: 44px; height: 44px;
        border-radius: 10px;
        display: flex;
        align-items: center; justify-content: center;
        font-size: 1.2rem;
        margin-bottom: 14px;
        font-weight: 700;
        color: #FFFFFF !important;
    }

    .eq-feature-title {
        font-family: 'Inter', sans-serif;
        font-size: 0.98rem;
        font-weight: 700;
        color: #0A1F44 !important;
        margin-bottom: 6px;
    }

    .eq-feature-desc {
        font-size: 0.86rem;
        color: #4A5568 !important;
        line-height: 1.55;
        margin: 0;
    }


    /* ── 9. RISK BADGES ── */
    .badge-high {
        background: #E5484D; color: #FFFFFF !important;
        padding: 5px 14px; border-radius: 4px;
        font-family: 'Inter', sans-serif; font-weight: 700;
        font-size: 0.78rem; letter-spacing: 0.6px;
        display: inline-block; text-transform: uppercase;
    }
    .badge-medium {
        background: #F59E0B; color: #FFFFFF !important;
        padding: 5px 14px; border-radius: 4px;
        font-family: 'Inter', sans-serif; font-weight: 700;
        font-size: 0.78rem; letter-spacing: 0.6px;
        display: inline-block; text-transform: uppercase;
    }
    .badge-low {
        background: #22C55E; color: #FFFFFF !important;
        padding: 5px 14px; border-radius: 4px;
        font-family: 'Inter', sans-serif; font-weight: 700;
        font-size: 0.78rem; letter-spacing: 0.6px;
        display: inline-block; text-transform: uppercase;
    }
    .badge-unknown {
        background: #94A3B8; color: #FFFFFF !important;
        padding: 5px 14px; border-radius: 4px;
        font-family: 'Inter', sans-serif; font-weight: 700;
        font-size: 0.78rem; letter-spacing: 0.6px;
        display: inline-block; text-transform: uppercase;
    }

    /* Large badges */
    .badge-high-lg {
        background: #E5484D; color: #FFFFFF !important;
        padding: 10px 30px; border-radius: 6px;
        font-family: 'Inter', sans-serif; font-weight: 700;
        font-size: 1.0rem; letter-spacing: 1px;
        display: inline-block; text-transform: uppercase;
        box-shadow: 0 2px 8px rgba(229, 72, 77, 0.3);
    }
    .badge-medium-lg {
        background: #F59E0B; color: #FFFFFF !important;
        padding: 10px 30px; border-radius: 6px;
        font-family: 'Inter', sans-serif; font-weight: 700;
        font-size: 1.0rem; letter-spacing: 1px;
        display: inline-block; text-transform: uppercase;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
    }
    .badge-low-lg {
        background: #22C55E; color: #FFFFFF !important;
        padding: 10px 30px; border-radius: 6px;
        font-family: 'Inter', sans-serif; font-weight: 700;
        font-size: 1.0rem; letter-spacing: 1px;
        display: inline-block; text-transform: uppercase;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
    }


    /* ── 10. DETAIL ROWS ── */
    .eq-detail-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #F0F2F5;
    }
    .eq-detail-label {
        color: #4A5568 !important;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
    }
    .eq-detail-value {
        color: #0A1F44 !important;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
    }


    /* ── 11. RISK FACTORS ── */
    .eq-risk-factor {
        background: #FFFBF0;
        border-left: 3px solid #F59E0B;
        padding: 12px 18px;
        margin-bottom: 6px;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
        color: #1A1A2E !important;
        font-family: 'Inter', sans-serif;
        line-height: 1.5;
    }
    .eq-risk-factor-ok {
        background: #F0FFF4;
        border-left: 3px solid #22C55E;
        padding: 12px 18px;
        margin-bottom: 6px;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
        color: #1A1A2E !important;
        font-family: 'Inter', sans-serif;
    }
    .eq-risk-factor-critical {
        background: #FFF5F5;
        border-left: 3px solid #E5484D;
        padding: 12px 18px;
        margin-bottom: 6px;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
        color: #1A1A2E !important;
        font-family: 'Inter', sans-serif;
    }


    /* ── 12. DATAFRAMES ── */
    [data-testid="stDataFrame"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 6px rgba(0, 0, 0, 0.03);
    }
    [data-testid="stDataFrame"] td,
    [data-testid="stDataFrame"] td div,
    [data-testid="stDataFrame"] td span {
        color: #1A1A2E !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stDataFrame"] th,
    [data-testid="stDataFrame"] th div,
    [data-testid="stDataFrame"] th span {
        background-color: #F1F5F9 !important;
        color: #0A1F44 !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
    }


    /* ── 13. DIVIDERS ── */
    .eq-section-divider {
        border-top: 1px solid #E2E8F0;
        margin: 24px 0 18px 0;
    }
    hr {
        border: none;
        border-top: 1px solid #E2E8F0;
        margin: 14px 0;
    }


    /* ── 14. BUTTONS ── */
    .stButton>button {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #0E2A5A, #1F6FEB);
        color: #FFFFFF !important;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.86rem;
        transition: all 0.25s ease;
        box-shadow: 0 2px 6px rgba(14, 42, 90, 0.15);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1F6FEB, #3B82F6);
        box-shadow: 0 3px 12px rgba(31, 111, 235, 0.3);
        transform: translateY(-1px);
        color: #FFFFFF !important;
    }


    /* ── 15. INPUTS ── */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        font-family: 'Inter', sans-serif;
        background: #FFFFFF;
        border: 1px solid #D1D9E6;
        border-radius: 8px;
        font-size: 0.9rem;
        color: #1A1A2E !important;
    }
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #1F6FEB;
        box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.08);
    }
    .stSelectbox>div>div {
        font-family: 'Inter', sans-serif;
        background: #FFFFFF;
        border-radius: 8px;
    }

    /* Widget labels */
    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stNumberInput label, .stCheckbox label, .stRadio label {
        color: #1A1A2E !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
    }


    /* ── 16. ALERTS & EXPANDERS ── */
    .stAlert {
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
    }
    .streamlit-expanderHeader {
        font-family: 'Inter', sans-serif;
        background: #FFFFFF;
        border-radius: 8px;
        font-weight: 600;
        color: #0E2A5A !important;
        font-size: 0.9rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.86rem;
    }


    /* ── 17. LIVE INDICATOR ── */
    .live-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #22C55E !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-family: 'Inter', sans-serif;
    }
    .live-tag-dot {
        width: 6px; height: 6px;
        background: #22C55E;
        border-radius: 50%;
        display: inline-block;
        animation: livepulse 2s infinite;
    }
    @keyframes livepulse {
        0%  { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.5); }
        70% { box-shadow: 0 0 0 5px rgba(34, 197, 94, 0); }
        100%{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }


    /* ── 18. SCROLLBAR ── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #F4F7FB; }
    ::-webkit-scrollbar-thumb { background: #C1C9D4; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #A0AEBF; }


    /* ── 19. PLOTLY ── */
    .js-plotly-plot .plotly .gtitle { fill: #0A1F44 !important; }
    .js-plotly-plot .plotly .xtick text,
    .js-plotly-plot .plotly .ytick text { fill: #4A5568 !important; }

    </style>
    """, unsafe_allow_html=True)
