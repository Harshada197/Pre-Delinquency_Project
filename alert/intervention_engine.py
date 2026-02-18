"""
Intervention Engine v3.0 — Policy-Aligned Risk Monitor
Scans all customers and prints prioritised intervention recommendations.
Compliant, no emojis, production-grade console output.

Reads from Redis (populated by feature_engine) and uses policy_templates.json.
"""
import redis
import json
import time
import os
from datetime import datetime

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY_PATH = os.path.join(BASE_DIR, "risk", "policy_templates.json")

try:
    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        POLICIES = json.load(f)
except Exception:
    POLICIES = {}

print("=" * 60)
print("   EQUILIBRATE — Intervention Engine v3.0")
print("   Monitoring customer risk in real-time...")
print("=" * 60)
print()


def get_risk_factors(profile):
    """Generate structured risk factors from customer data."""
    factors = []
    salary_count = int(profile.get("salary_count", 0))
    withdrawals = int(profile.get("withdrawals", 0))
    atm_7d = int(profile.get("atm_withdrawals_7d", 0))
    total_spend = float(profile.get("total_spend", 0))
    essential = float(profile.get("essential_spend", 0))
    discretionary = float(profile.get("discretionary_spend", 0))
    days_since = int(profile.get("days_since_salary", -1))
    spend_change = float(profile.get("spending_change_pct", 0))
    persona = profile.get("persona", "UNKNOWN")
    txn_count = int(profile.get("txn_count", 0))

    if salary_count == 0 and txn_count > 5:
        factors.append("No salary credit detected — possible income disruption")
    elif days_since > 30:
        factors.append(f"Last salary was {days_since} days ago — extended income gap")

    if atm_7d >= 10:
        factors.append(f"Very high ATM withdrawals in 7d ({atm_7d}) — panic liquidity behaviour")
    elif atm_7d >= 5:
        factors.append(f"Elevated ATM withdrawals in 7d ({atm_7d}) — above normal threshold")

    if spend_change < -40:
        factors.append(f"Spending dropped {abs(spend_change):.0f}% — significant contraction")
    elif spend_change < -20:
        factors.append(f"Spending declined {abs(spend_change):.0f}% — early contraction signal")

    if essential > 0 and discretionary == 0 and txn_count > 5:
        factors.append("Zero discretionary spending — customer in survival mode")
    elif essential > 0 and discretionary > 0 and essential > discretionary * 3:
        ratio = round(essential / max(discretionary, 1), 1)
        factors.append(f"Essential-to-discretionary ratio is {ratio}x — financial stress indicator")

    if discretionary > essential * 2 and discretionary > 5000:
        factors.append(f"High discretionary spending (Rs. {discretionary:,.0f}) — possible overspending")

    return factors


def get_policy_action(hardship_type, risk_level):
    """Look up the approved action from policy templates."""
    hardship_key = hardship_type if hardship_type in POLICIES else "NONE"
    policy = POLICIES.get(hardship_key, {}).get(risk_level, {})
    return policy.get("action", "Continue monitoring")


cycle = 0

while True:
    cycle += 1
    customers = r.keys("customer:*")
    now = datetime.now().strftime("%H:%M:%S")

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    hardship_counts = {}

    print(f"\n{'=' * 60}")
    print(f"   SCAN #{cycle} | Time: {now} | Customers: {len(customers)}")
    print(f"{'=' * 60}")

    for cust in customers:
        profile = r.hgetall(cust)
        if not profile:
            continue

        risk_level = profile.get("risk_level", "LOW")
        risk_score = int(profile.get("risk_score", 0))
        hardship = profile.get("hardship_type", "NONE")
        persona = profile.get("persona", "UNKNOWN")

        counts[risk_level] = counts.get(risk_level, 0) + 1

        if hardship != "NONE":
            hardship_counts[hardship] = hardship_counts.get(hardship, 0) + 1

        # Only print details for HIGH and MEDIUM risk customers
        if risk_level in ("HIGH", "MEDIUM"):
            factors = get_risk_factors(profile)
            action = get_policy_action(hardship, risk_level)

            level_tag = f"[{risk_level}]"
            print(f"\n  +--- {level_tag:>8} | {cust} | Score: {risk_score}/10 | "
                  f"Hardship: {hardship.replace('_', ' ').title()}")
            print(f"  |  Persona: {persona.replace('_', ' ').title()}")

            if factors:
                print(f"  |  Risk Factors:")
                for f_text in factors:
                    print(f"  |    - {f_text}")

            print(f"  |  Recommended Action: {action}")
            print(f"  +{'─' * 55}")

    total = len(customers)
    h_pct = 100 * counts.get("HIGH", 0) / total if total else 0
    m_pct = 100 * counts.get("MEDIUM", 0) / total if total else 0
    l_pct = 100 * counts.get("LOW", 0) / total if total else 0

    print(f"\n  +{'=' * 44}+")
    print(f"  |  HIGH:   {counts.get('HIGH', 0):>4}  ({h_pct:.1f}%)  |  "
          f"MEDIUM: {counts.get('MEDIUM', 0):>4}  ({m_pct:.1f}%)  |")
    print(f"  |  LOW:    {counts.get('LOW', 0):>4}  ({l_pct:.1f}%)  |  "
          f"TOTAL:  {total:>4}           |")
    print(f"  +{'=' * 44}+")

    if hardship_counts:
        h_str = " | ".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in sorted(hardship_counts.items()))
        print(f"  Hardship: {h_str}")

    time.sleep(10)
