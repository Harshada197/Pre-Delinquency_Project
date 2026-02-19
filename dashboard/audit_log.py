"""
Equilibrate Dashboard — Intervention Log v4.0
Logs all interventions to data/intervention_log.csv.
Writes feedback to Redis for the ML feedback loop.
"""
import csv
import os
import redis
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERVENTION_LOG_PATH = os.path.join(BASE_DIR, "data", "intervention_log.csv")

INTERVENTION_FIELDS = [
    "timestamp", "customer_id", "risk_level", "action", "message",
]

# Keep old path as alias for backward compat
AUDIT_LOG_PATH = INTERVENTION_LOG_PATH
AUDIT_FIELDS = INTERVENTION_FIELDS

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def _ensure_log_exists():
    os.makedirs(os.path.dirname(INTERVENTION_LOG_PATH), exist_ok=True)
    if not os.path.isfile(INTERVENTION_LOG_PATH) or os.path.getsize(INTERVENTION_LOG_PATH) == 0:
        with open(INTERVENTION_LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=INTERVENTION_FIELDS)
            writer.writeheader()


def log_audit_event(
    customer_id: str,
    action_type: str,
    message: str = "",
    officer: str = "System",
    ref_id: str = "",
    risk_level: str = "",
):
    """Append an event to intervention_log.csv and write feedback to Redis."""
    _ensure_log_exists()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = {
        "timestamp": now,
        "customer_id": str(customer_id),
        "risk_level": risk_level,
        "action": action_type,
        "message": message[:250],
    }
    with open(INTERVENTION_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=INTERVENTION_FIELDS)
        writer.writerow(row)

    # Write feedback to Redis (closes ML feedback loop)
    key = f"customer:{customer_id}"
    try:
        r.hset(key, mapping={
            "last_intervention": action_type,
            "intervention_status": action_type,
            "intervention_timestamp": now,
        })
    except Exception:
        pass

    print(f"[INTERVENTION] {now} | Customer {customer_id} | {action_type}")
    return row


def load_audit_log():
    """Read the intervention log CSV and return as DataFrame."""
    _ensure_log_exists()
    try:
        df = pd.read_csv(INTERVENTION_LOG_PATH)
        return df
    except Exception:
        return pd.DataFrame(columns=INTERVENTION_FIELDS)


# Backward compatibility aliases
def append_audit_log(customer_id, risk_level, action_taken, message_sent,
                     hardship_type="", officer_id="SYSTEM"):
    return log_audit_event(
        customer_id=customer_id,
        action_type=action_taken,
        message=message_sent,
        officer=officer_id,
        risk_level=risk_level,
    )


def read_audit_log():
    return load_audit_log()
