"""
Risk Engine v5.0 — Continuous Risk Monitor
Re-evaluates all customer profiles every 5 seconds.
This process serves as a safety-net re-evaluator and distribution reporter.

The primary risk computation runs in customer_features.py per transaction.
This engine catches customers that may have drifted and ensures consistency.
"""
import redis
import json
import time
import os
from datetime import datetime

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# ── Load policy templates ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY_PATH = os.path.join(BASE_DIR, "risk", "policy_templates.json")

try:
    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        POLICIES = json.load(f)
except Exception:
    POLICIES = {}

print("=" * 60)
print("  EQUILIBRATE — Risk Monitor v5.0")
print("  Continuous risk evaluation + distribution reporting")
print("=" * 60)
print()


def evaluate_customer(customer_key):
    """Re-evaluate a customer's risk based on current Redis state.

    Mirrors the scoring logic in customer_features._compute_risk_score.
    """
    data = r.hgetall(customer_key)
    if not data:
        return None

    txn_count = int(data.get("txn_count", 0))
    withdrawals = int(data.get("withdrawals", 0))
    salary_count = int(data.get("salary_count", 0))
    total_spend = float(data.get("total_spend", 0))
    essential = float(data.get("essential_spend", 0))
    discretionary = float(data.get("discretionary_spend", 0))
    days_since_salary = int(data.get("days_since_salary", -1))
    atm_7d = int(data.get("atm_withdrawals_7d", 0))
    spending_change = float(data.get("spending_change_pct", 0))
    persona = data.get("persona", "UNKNOWN")

    score = 0.0

    if txn_count < 3:
        score = 0
    else:
        # ── Salary gap (0-3 points) ──
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

        # ── Persona factor ──
        if score >= 2:
            if persona == "INCOME_SHOCK" and salary_count == 0:
                score += 1
            elif persona == "SILENT_DRAIN" and txn_count < 10 and salary_count == 0:
                score += 0.5

    score = min(round(score), 10)

    # Classification
    if score >= 7:
        risk_level = "HIGH"
    elif score >= 4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # ── Hardship classification ──
    hardship = "NONE"

    if txn_count >= 3:
        if salary_count == 0 and txn_count >= 8 and persona in ("INCOME_SHOCK", "SILENT_DRAIN"):
            hardship = "INCOME_SHOCK"
        elif days_since_salary > 30 and atm_7d >= 3:
            hardship = "INCOME_SHOCK"
        elif atm_7d >= 5 and spending_change < -20:
            hardship = "LIQUIDITY_STRESS"
        elif atm_7d >= 10:
            hardship = "LIQUIDITY_STRESS"
        elif essential > 0 and discretionary == 0 and txn_count > 8:
            hardship = "EXPENSE_COMPRESSION"
        elif spending_change < -40 and essential > discretionary * 3 and txn_count > 10:
            hardship = "EXPENSE_COMPRESSION"
        elif discretionary > 0 and essential > 0 and discretionary > essential * 2.5 and discretionary > 8000:
            hardship = "OVERSPENDING"
        elif persona == "OVERSPENDER" and discretionary > essential * 2 and discretionary > 6000:
            hardship = "OVERSPENDING"

    # If LOW, clear hardship
    if risk_level == "LOW":
        hardship = "NONE"

    # ── Policy lookup ──
    hardship_key = hardship if hardship in POLICIES else "NONE"
    policy = POLICIES.get(hardship_key, {}).get(risk_level, {})
    recommended_action = policy.get("action", "Continue monitoring")

    # ── Write to Redis ──
    r.hset(customer_key, mapping={
        "risk_level": risk_level,
        "risk_score": str(score),
        "hardship_type": hardship,
        "recommended_action": recommended_action,
        "last_risk_eval": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    return risk_level


# ── Main Loop ──
cycle = 0
while True:
    cycle += 1
    customers = r.keys("customer:*")
    now = datetime.now().strftime("%H:%M:%S")

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    hardship_counts = {}

    for c in customers:
        level = evaluate_customer(c)
        if level:
            counts[level] = counts.get(level, 0) + 1

        # Count hardship types
        h = r.hget(c, "hardship_type") or "NONE"
        hardship_counts[h] = hardship_counts.get(h, 0) + 1

    total = len(customers)
    h_pct = 100 * counts["HIGH"] / total if total else 0
    m_pct = 100 * counts["MEDIUM"] / total if total else 0

    # Log distribution
    hardship_str = " | ".join(f"{k}:{v}" for k, v in sorted(hardship_counts.items()) if k != "NONE")

    print(
        f"[{now}] Scan #{cycle} | Total: {total} | "
        f"HIGH: {counts['HIGH']} ({h_pct:.1f}%) | "
        f"MEDIUM: {counts['MEDIUM']} ({m_pct:.1f}%) | "
        f"LOW: {counts['LOW']}"
    )
    if hardship_str:
        print(f"         Hardship: {hardship_str}")

    time.sleep(5)
