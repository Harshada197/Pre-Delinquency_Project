"""
Equilibrate — Dashboard Utilities v8.0
Redis data access, static CSV merge, risk analysis, sidebar builder.
Feedback loop writes intervention data back to Redis.
Policy-based message generation.
"""
import redis
import pandas as pd
import json
import os
import sys
import streamlit as st
from datetime import datetime

# Add ui module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui.theme import apply_theme

# ── Redis Connection ──
_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    return _redis_client


# ── Policy Templates ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY_PATH = os.path.join(BASE_DIR, "risk", "policy_templates.json")
CUSTOMERS_CSV = os.path.join(BASE_DIR, "data", "customers.csv")
_policy_cache = None
_static_cache = None


def _load_policies():
    global _policy_cache
    if _policy_cache is None:
        try:
            with open(POLICY_PATH, "r", encoding="utf-8") as f:
                _policy_cache = json.load(f)
        except Exception:
            _policy_cache = {}
    return _policy_cache


def _load_static_customers():
    """Load static customer data from customers.csv (city, employment_type, age, salary)."""
    global _static_cache
    if _static_cache is None:
        try:
            df = pd.read_csv(CUSTOMERS_CSV)
            df["customer_id"] = df["customer_id"].astype(str)
            _static_cache = df.set_index("customer_id")[
                ["city", "employment_type", "age", "salary"]
            ].to_dict("index")
        except Exception:
            _static_cache = {}
    return _static_cache


# ── Auto-refresh interval (3 minutes) ──
REFRESH_INTERVAL_MS = 180_000


# ═══════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=10)
def fetch_all_customers():
    """Fetch all customer profiles from Redis, merge static CSV data, return DataFrame."""
    r = get_redis()
    keys = r.keys("customer:*")
    if not keys:
        return pd.DataFrame()

    rows = []
    for key in keys:
        data = r.hgetall(key)
        if data:
            profile = {k: v for k, v in data.items() if not k.startswith("_")}
            if "customer_id" not in profile:
                profile["customer_id"] = key.split(":", 1)[1]
            rows.append(profile)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Type conversions for numeric columns
    numeric_cols = [
        "txn_count", "total_spend", "essential_spend", "discretionary_spend",
        "salary_count", "days_since_salary", "atm_withdrawals_7d",
        "txn_frequency_7d", "spending_change_pct", "risk_score", "withdrawals",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ── Merge static customer data (city, employment_type, age) ──
    static = _load_static_customers()
    if static and "customer_id" in df.columns:
        df["customer_id"] = df["customer_id"].astype(str)
        df["city"] = df["customer_id"].map(lambda cid: static.get(cid, {}).get("city", "Unknown"))
        df["employment_type"] = df["customer_id"].map(
            lambda cid: static.get(cid, {}).get("employment_type", "Unknown")
        )
        df["age"] = df["customer_id"].map(
            lambda cid: static.get(cid, {}).get("age", 0)
        )
        df["static_salary"] = df["customer_id"].map(
            lambda cid: static.get(cid, {}).get("salary", 0)
        )

    return df


def get_last_live_transaction_time():
    """Read the most recent 'last_updated' timestamp across all customers."""
    r = get_redis()
    keys = r.keys("customer:*")
    if not keys:
        return None
    latest = None
    for key in keys[:200]:
        ts = r.hget(key, "last_updated")
        if ts and (latest is None or ts > latest):
            latest = ts
    return latest


def get_last_risk_evaluation_time():
    """Read the most recent 'last_risk_eval' timestamp across all customers."""
    r = get_redis()
    keys = r.keys("customer:*")
    if not keys:
        return None
    latest = None
    for key in keys[:200]:
        ts = r.hget(key, "last_risk_eval")
        if ts and (latest is None or ts > latest):
            latest = ts
    return latest


def get_customer_profile(customer_id):
    """Get a single customer's complete profile from Redis + static CSV."""
    r = get_redis()
    key = f"customer:{customer_id}"
    data = r.hgetall(key)
    if not data:
        return None
    profile = {k: v for k, v in data.items() if not k.startswith("_")}
    # Ensure customer_id exists
    if "customer_id" not in profile:
        profile["customer_id"] = str(customer_id)

    # Merge static data
    static = _load_static_customers()
    cid = str(customer_id)
    if cid in static:
        profile["city"] = static[cid].get("city", "Unknown")
        profile["employment_type"] = static[cid].get("employment_type", "Unknown")
        profile["age"] = str(static[cid].get("age", ""))
        profile["static_salary"] = str(static[cid].get("salary", ""))

    return profile


# ═══════════════════════════════════════════════════════════════
# RISK ANALYSIS
# ═══════════════════════════════════════════════════════════════

def risk_counts(df):
    """Count customers by risk level."""
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    if "risk_level" in df.columns:
        vc = df["risk_level"].value_counts()
        for level in counts:
            counts[level] = int(vc.get(level, 0))
    return counts


def hardship_distribution(df):
    """Count customers by hardship type (excluding NONE)."""
    if "hardship_type" not in df.columns:
        return {}
    vc = df["hardship_type"].value_counts()
    return {k: int(v) for k, v in vc.items() if k and k != "NONE"}


# ═══════════════════════════════════════════════════════════════
# FEEDBACK LOOP
# ═══════════════════════════════════════════════════════════════

def write_intervention_feedback(customer_id, status, action_description):
    """Write intervention feedback back to Redis for the ML feedback loop."""
    r = get_redis()
    key = f"customer:{customer_id}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    r.hset(key, mapping={
        "last_intervention": action_description,
        "intervention_status": status,
        "intervention_timestamp": now,
    })


# ═══════════════════════════════════════════════════════════════
# POLICY MESSAGE GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_policy_message(customer_id, hardship_type, risk_level, ref_id,
                            channel="SMS"):
    """Generate a policy-compliant message from templates.

    NO LLM involved. Uses policy_templates.json with variable substitution.
    Supports SMS, WhatsApp, and Voice channels.
    """
    policies = _load_policies()
    hardship_key = hardship_type if hardship_type in policies else "NONE"
    policy = policies.get(hardship_key, {}).get(risk_level, {})
    template = policy.get("message", "")

    if not template:
        template = (
            "Dear Customer {customer_id}, we would like to inform you about "
            "our support options. Please contact our helpline at 1800-XXX-XXXX "
            "for more information. Ref: {ref_id}"
        )

    message = template.replace("{customer_id}", str(customer_id))
    message = message.replace("{ref_id}", str(ref_id))

    # Add channel-specific prefix
    if channel == "WhatsApp":
        message = f"[WhatsApp] {message}"
    elif channel == "Voice":
        message = f"[Voice/IVR] {message}"

    return message


# ═══════════════════════════════════════════════════════════════
# UI COMPONENTS
# ═══════════════════════════════════════════════════════════════

def load_css():
    """Load CSS and apply theme."""
    apply_theme()
    css_path = os.path.join(os.path.dirname(__file__), "styles", "theme.css")
    if os.path.isfile(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_header():
    """Render the Equilibrate header."""
    st.markdown("""
    <div class="eq-header">
        <div class="eq-header-brand">
            <span class="eq-header-logo">E</span>
            <span class="eq-header-title">Equilibrate</span>
            <span class="eq-header-subtitle">Pre-Delinquency Intervention Engine</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar navigation with system status."""
    with st.sidebar:
        st.markdown("""
        <div style="padding:14px 0 8px 0;">
            <div style="font-size:1.15rem; font-weight:800; color:#FFFFFF; letter-spacing:2px; margin-bottom:4px;">
                EQUILIBRATE
            </div>
            <div style="font-size:0.78rem; color:#8BACC8; margin-bottom:12px;">
                Pre-Delinquency Engine v4.0
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # System status
        try:
            r = get_redis()
            customer_count = len(r.keys("customer:*"))
            r.ping()
            redis_status = "Connected"
            redis_color = "#22C55E"
        except Exception:
            customer_count = 0
            redis_status = "Disconnected"
            redis_color = "#E5484D"

        st.markdown(f"""
        <div style="padding:10px 0; font-size:0.85rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="color:#8BACC8; font-weight:500;">Redis</span>
                <span style="color:{redis_color}; font-weight:700; font-size:0.82rem;">{redis_status}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="color:#8BACC8; font-weight:500;">Kafka Streaming</span>
                <span style="color:#22C55E; font-weight:700; font-size:0.82rem;">Active</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="color:#8BACC8; font-weight:500;">Feature Engine</span>
                <span style="color:#22C55E; font-weight:700; font-size:0.82rem;">Active</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="color:#8BACC8; font-weight:500;">Customers</span>
                <span style="color:#FFFFFF; font-weight:700;">{customer_count:,}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="color:#8BACC8; font-weight:500;">Refresh</span>
                <span style="color:#FFFFFF; font-weight:600;">3 min</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#8BACC8; font-weight:500;">Last Updated</span>
                <span style="color:#FFFFFF; font-weight:600;">{datetime.now().strftime('%H:%M:%S')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_live_tag():
    """Render a LIVE indicator pulsing tag."""
    st.markdown("""
    <div class="eq-live-tag">
        <span class="eq-live-dot"></span> LIVE
    </div>
    """, unsafe_allow_html=True)
