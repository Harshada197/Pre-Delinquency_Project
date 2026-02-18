"""
Alert Engine v3.0 — Policy-Aligned Risk Alerts
Reads risk levels from Redis (as computed by the feature engine)
and generates console alerts. No emojis, production-grade output.

This is a simplified version of the intervention engine.
For full intervention logic, use alert/intervention_engine.py.
"""
import redis
import time
from datetime import datetime

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

print("=" * 60)
print("   EQUILIBRATE — Alert Engine v3.0")
print("   Monitoring customer risk levels...")
print("=" * 60)
print()

while True:
    customers = r.keys("customer:*")
    now = datetime.now().strftime("%H:%M:%S")

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for c in customers:
        data = r.hgetall(c)
        level = data.get("risk_level", "LOW")
        score = data.get("risk_score", "0")
        hardship = data.get("hardship_type", "NONE")
        action = data.get("recommended_action", "Continue monitoring")

        counts[level] = counts.get(level, 0) + 1

        if level == "HIGH":
            print(f"  [ALERT] {c} | HIGH RISK (Score: {score}/10) | "
                  f"Hardship: {hardship.replace('_', ' ').title()} | "
                  f"Action: {action}")
        elif level == "MEDIUM":
            print(f"  [WARN]  {c} | MEDIUM (Score: {score}/10) | "
                  f"Hardship: {hardship.replace('_', ' ').title()}")

    total = len(customers)
    h_pct = 100 * counts["HIGH"] / total if total else 0
    print(f"\n  [{now}] Total: {total} | HIGH: {counts['HIGH']} ({h_pct:.1f}%) | "
          f"MEDIUM: {counts['MEDIUM']} | LOW: {counts['LOW']}")
    print(f"  Checking again in 10 seconds...\n")
    time.sleep(10)
