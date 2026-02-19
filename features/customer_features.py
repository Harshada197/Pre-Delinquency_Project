"""
Customer Features v4.0 — Time-Aware Behavioural Feature Computation
Processes transactions incrementally and computes time-based features.
Hardship classification and risk scoring run inside this module (not dashboard).

Redis key format: customer:{customer_id}

Stored fields:
  txn_count, total_spend, essential_spend, discretionary_spend,
  salary_count, last_salary_date, days_since_salary,
  atm_withdrawals_7d, txn_frequency_7d, spending_change_pct,
  hardship_type, risk_score, risk_level, recommended_action,
  persona, last_updated
"""
import redis
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "storage"))

from customer_snapshot_writer import write_customer_snapshot

# ── Policy templates ──
POLICY_PATH = os.path.join(BASE_DIR, "risk", "policy_templates.json")
_policy_cache = None


def _load_policies():
    global _policy_cache
    if _policy_cache is None:
        try:
            with open(POLICY_PATH, "r", encoding="utf-8") as f:
                _policy_cache = json.load(f)
        except Exception:
            _policy_cache = {}
    return _policy_cache


# ── Redis ──
r = redis.Redis(host="localhost", port=6379, decode_responses=True)


# ═══════════════════════════════════════════════════════════════
# FEATURE UPDATE
# ═══════════════════════════════════════════════════════════════

def update_customer_features(txn):
    """Process a single transaction and update customer profile in Redis."""
    cid = str(txn["customer_id"])
    key = f"customer:{cid}"

    amount = float(txn["amount"])
    category = txn["merchant_category"].upper()
    channel = txn.get("channel", "").upper()
    txn_type = txn["transaction_type"].upper()
    is_salary = int(txn.get("is_salary", 0))
    persona = txn.get("persona", "UNKNOWN")
    ts = txn.get("timestamp", str(datetime.now()))

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # ── Initialize profile if new ──
    if not r.exists(key):
        r.hset(key, mapping={
            "txn_count": 0,
            "total_spend": 0.0,
            "withdrawals": 0,
            "salary_count": 0,
            "last_salary_date": "",
            "essential_spend": 0.0,
            "discretionary_spend": 0.0,
            "atm_withdrawals_7d": 0,
            "txn_frequency_7d": 0,
            "spending_change_pct": 0.0,
            "days_since_salary": -1,
            "hardship_type": "NONE",
            "risk_score": 0,
            "risk_level": "LOW",
            "recommended_action": "Continue monitoring",
            "persona": persona,
            "last_updated": now_str,
            "first_seen": now_str,
            # Rolling window trackers (stored as JSON lists)
            "_txn_timestamps": "[]",
            "_atm_timestamps": "[]",
            "_spend_history": "[]",
        })

    # ── Transaction count ──
    r.hincrby(key, "txn_count", 1)

    # ── Salary detection ──
    if is_salary:
        r.hincrby(key, "salary_count", 1)
        r.hset(key, "last_salary_date", now_str)

    # ── Spending ──
    if txn_type == "DEBIT":
        r.hincrbyfloat(key, "total_spend", amount)

        essential_cats = {"GROCERY", "UTILITY", "RENT", "MEDICAL", "INSURANCE", "EMI"}
        if category in essential_cats:
            r.hincrbyfloat(key, "essential_spend", amount)
        else:
            r.hincrbyfloat(key, "discretionary_spend", amount)

    # ── ATM withdrawals ──
    if channel == "ATM":
        r.hincrby(key, "withdrawals", 1)

    # ── Update rolling window timestamps ──
    _update_rolling_windows(key, channel, amount, now)

    # ── Store persona (if not already set) ──
    current_persona = r.hget(key, "persona")
    if not current_persona or current_persona == "UNKNOWN":
        r.hset(key, "persona", persona)

    # ── Compute time-based features ──
    _compute_time_features(key, now)

    # ── Classify hardship ──
    _classify_hardship(key)

    # ── Compute risk score ──
    _compute_risk_score(key)

    # ── Update timestamp ──
    r.hset(key, "last_updated", now_str)

    # ── Snapshot to CSV ──
    write_customer_snapshot(cid)


# ═══════════════════════════════════════════════════════════════
# ROLLING WINDOW TRACKING
# ═══════════════════════════════════════════════════════════════

def _update_rolling_windows(key, channel, amount, now):
    """Maintain rolling 7-day windows for txn frequency and ATM withdrawals."""
    now_iso = now.isoformat()
    cutoff = (now - timedelta(days=7)).isoformat()

    # Transaction timestamps (7-day window)
    try:
        txn_ts_raw = r.hget(key, "_txn_timestamps") or "[]"
        txn_ts = json.loads(txn_ts_raw)
    except (json.JSONDecodeError, TypeError):
        txn_ts = []
    txn_ts.append(now_iso)
    txn_ts = [t for t in txn_ts if t >= cutoff]
    # Limit to prevent unbounded growth
    txn_ts = txn_ts[-200:]
    r.hset(key, "_txn_timestamps", json.dumps(txn_ts))
    r.hset(key, "txn_frequency_7d", len(txn_ts))

    # ATM timestamps (7-day window)
    if channel == "ATM":
        try:
            atm_ts_raw = r.hget(key, "_atm_timestamps") or "[]"
            atm_ts = json.loads(atm_ts_raw)
        except (json.JSONDecodeError, TypeError):
            atm_ts = []
        atm_ts.append(now_iso)
        atm_ts = [t for t in atm_ts if t >= cutoff]
        atm_ts = atm_ts[-100:]
        r.hset(key, "_atm_timestamps", json.dumps(atm_ts))
        r.hset(key, "atm_withdrawals_7d", len(atm_ts))

    # Spend history (track last 30 spend amounts for change detection)
    try:
        spend_raw = r.hget(key, "_spend_history") or "[]"
        spend_hist = json.loads(spend_raw)
    except (json.JSONDecodeError, TypeError):
        spend_hist = []
    spend_hist.append(float(amount))
    spend_hist = spend_hist[-30:]
    r.hset(key, "_spend_history", json.dumps(spend_hist))


# ═══════════════════════════════════════════════════════════════
# TIME-BASED FEATURE COMPUTATION
# ═══════════════════════════════════════════════════════════════

def _compute_time_features(key, now):
    """Compute days_since_salary and spending_change_pct."""
    # Days since salary
    last_salary = r.hget(key, "last_salary_date") or ""
    if last_salary and last_salary.strip():
        try:
            salary_dt = datetime.strptime(last_salary.split(".")[0], "%Y-%m-%d %H:%M:%S")
            days = (now - salary_dt).days
            r.hset(key, "days_since_salary", days)
        except (ValueError, IndexError):
            r.hset(key, "days_since_salary", -1)
    else:
        r.hset(key, "days_since_salary", -1)

    # Spending change percentage (compare recent 5 vs previous 5 transactions)
    try:
        spend_raw = r.hget(key, "_spend_history") or "[]"
        spend_hist = json.loads(spend_raw)
    except (json.JSONDecodeError, TypeError):
        spend_hist = []

    if len(spend_hist) >= 10:
        recent = sum(spend_hist[-5:])
        previous = sum(spend_hist[-10:-5])
        if previous > 0:
            change_pct = round(((recent - previous) / previous) * 100, 1)
        else:
            change_pct = 0.0
        r.hset(key, "spending_change_pct", change_pct)


# ═══════════════════════════════════════════════════════════════
# HARDSHIP CLASSIFICATION (computed in feature engine, NOT dashboard)
# ═══════════════════════════════════════════════════════════════

def _classify_hardship(key):
    """Deterministic hardship classification based on behavioral signals.

    Rules (priority order):
      1. INCOME_SHOCK  — no salary for extended period + withdrawal spikes
      2. LIQUIDITY_STRESS — high ATM withdrawals + spending drops
      3. EXPENSE_COMPRESSION — discretionary spending drops > 40%
      4. OVERSPENDING — high discretionary relative to essential + credit usage
    """
    data = r.hgetall(key)

    salary_count = int(data.get("salary_count", 0))
    days_since_salary = int(data.get("days_since_salary", -1))
    atm_7d = int(data.get("atm_withdrawals_7d", 0))
    txn_count = int(data.get("txn_count", 0))
    essential = float(data.get("essential_spend", 0))
    discretionary = float(data.get("discretionary_spend", 0))
    spending_change = float(data.get("spending_change_pct", 0))
    persona = data.get("persona", "UNKNOWN")

    hardship = "NONE"

    # Need minimum transaction history to classify
    if txn_count < 3:
        r.hset(key, "hardship_type", hardship)
        return

    total_spend = float(data.get("total_spend", 0))

    # ── Income Shock: no salary for extended period + withdrawal spikes ──
    if salary_count == 0 and txn_count >= 5 and persona in ("INCOME_SHOCK", "SILENT_DRAIN"):
        hardship = "INCOME_SHOCK"
    elif days_since_salary > 30 and atm_7d >= 3:
        hardship = "INCOME_SHOCK"

    # ── Over-Leverage: high essential spend ratio (EMI/loans heavy) ──
    elif essential > 0 and total_spend > 0 and (essential / total_spend) > 0.70 and txn_count >= 5:
        hardship = "OVER_LEVERAGE"

    # ── Liquidity Stress: high ATM + spending drops ──
    elif atm_7d >= 5 and spending_change < -20:
        hardship = "LIQUIDITY_STRESS"
    elif atm_7d >= 8:
        hardship = "LIQUIDITY_STRESS"

    # ── Expense Compression: discretionary drops sharply ──
    elif essential > 0 and discretionary == 0 and txn_count > 5:
        hardship = "EXPENSE_COMPRESSION"
    elif spending_change < -40 and essential > discretionary * 3 and txn_count > 5:
        hardship = "EXPENSE_COMPRESSION"

    # ── Overspending: high discretionary relative to essential ──
    elif discretionary > 0 and essential > 0 and discretionary > essential * 2.5 and discretionary > 3000:
        hardship = "OVERSPENDING"
    elif persona == "OVERSPENDER" and discretionary > essential * 2 and discretionary > 2000:
        hardship = "OVERSPENDING"

    r.hset(key, "hardship_type", hardship)


# ═══════════════════════════════════════════════════════════════
# RISK SCORING (weighted, behavior-driven)
# Only ~1-2% should reach HIGH (7-10)
# ═══════════════════════════════════════════════════════════════

def _compute_risk_score(key):
    """Weighted risk scoring: 0-10 scale.

    Structure:
      Salary gap      0-3 points  (weight: high)
      Withdrawal spike 0-2 points  (weight: medium)
      Spend drop      0-2 points  (weight: medium)
      Inactivity      0-1 points  (weight: low)
      Persona factor  0-1 points  (weight: supplemental, never standalone)

    HIGH requires convergence of MULTIPLE signals.
    A single signal alone should NOT push to HIGH.
    """
    data = r.hgetall(key)

    salary_count = int(data.get("salary_count", 0))
    days_since_salary = int(data.get("days_since_salary", -1))
    atm_7d = int(data.get("atm_withdrawals_7d", 0))
    txn_count = int(data.get("txn_count", 0))
    total_spend = float(data.get("total_spend", 0))
    essential = float(data.get("essential_spend", 0))
    discretionary = float(data.get("discretionary_spend", 0))
    spending_change = float(data.get("spending_change_pct", 0))
    persona = data.get("persona", "UNKNOWN")
    hardship = data.get("hardship_type", "NONE")
    withdrawals = int(data.get("withdrawals", 0))

    score = 0.0

    # ── Need minimum history to score meaningfully ──
    if txn_count < 3:
        score = 0
    else:
        # ── Salary gap (0-3 points) ──
        # Only penalize heavily if there is enough transaction history to judge
        if salary_count == 0 and txn_count >= 15:
            score += 3
        elif salary_count == 0 and txn_count >= 8:
            score += 2
        elif salary_count == 0 and txn_count >= 4:
            score += 1
        elif days_since_salary > 45:
            score += 2
        elif days_since_salary > 30:
            score += 1

        # ── Withdrawal spike (0-2 points) ──
        if atm_7d >= 12:
            score += 2
        elif atm_7d >= 6:
            score += 1.5
        elif atm_7d >= 4:
            score += 1

        # ── Spend drop (0-2 points) ──
        if spending_change < -60:
            score += 2
        elif spending_change < -35:
            score += 1

        # ── Inactivity / survival mode (0-1 point) ──
        if essential > 0 and discretionary == 0 and txn_count > 10:
            score += 1
        elif essential > 0 and discretionary > 0 and essential > discretionary * 4:
            score += 0.5

        # ── Persona factor (supplemental, never adds more than 1 point) ──
        # Only adds if there are ALREADY other signals present
        if score >= 2:
            if persona == "INCOME_SHOCK" and salary_count == 0:
                score += 1
            elif persona == "SILENT_DRAIN" and txn_count < 10 and salary_count == 0:
                score += 0.5

    # Round and cap at 10
    score = min(round(score), 10)

    # ── Classification (calibrated for streaming demo) ──
    if score >= 5:
        risk_level = "HIGH"
    elif score >= 3:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # ── Policy-bound recommendation (via policy_engine) ──
    import sys as _sys
    _sys.path.insert(0, os.path.join(BASE_DIR, "risk"))
    from policy_engine import get_recommended_action
    recommended_action = get_recommended_action(hardship, risk_level)

    # ── Write to Redis ──
    r.hset(key, mapping={
        "risk_score": str(score),
        "risk_level": risk_level,
        "recommended_action": recommended_action,
    })
