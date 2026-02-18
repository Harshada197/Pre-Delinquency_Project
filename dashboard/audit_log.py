"""
Equilibrate Dashboard — Audit Log v3.0
Maintains persistent CSV log + writes feedback to Redis.
"""
import csv
import os
import redis
import pandas as pd
from datetime import datetime

AUDIT_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_log.csv")

AUDIT_FIELDS = [
    "timestamp", "customer_id", "action_type", "message", "officer", "ref_id",
]

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def _ensure_log_exists():
    if not os.path.isfile(AUDIT_LOG_PATH) or os.path.getsize(AUDIT_LOG_PATH) == 0:
        with open(AUDIT_LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDS)
            writer.writeheader()


def log_audit_event(
    customer_id: str,
    action_type: str,
    message: str = "",
    officer: str = "System",
    ref_id: str = "",
):
    """Append an event to the audit CSV and write feedback to Redis."""
    _ensure_log_exists()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = {
        "timestamp": now,
        "customer_id": str(customer_id),
        "action_type": action_type,
        "message": message[:250],
        "officer": officer,
        "ref_id": ref_id,
    }
    with open(AUDIT_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDS)
        writer.writerow(row)

    # ── Write feedback to Redis (closes ML feedback loop) ──
    key = f"customer:{customer_id}"
    try:
        r.hset(key, mapping={
            "last_intervention": action_type,
            "intervention_status": action_type,
            "intervention_timestamp": now,
        })
    except Exception:
        pass

    print(f"[AUDIT] {now} | Customer {customer_id} | {action_type} | Ref: {ref_id}")
    return row


def load_audit_log():
    """Read the audit log CSV and return as DataFrame."""
    _ensure_log_exists()
    try:
        df = pd.read_csv(AUDIT_LOG_PATH)
        return df
    except Exception:
        return pd.DataFrame(columns=AUDIT_FIELDS)


# Backward compatibility aliases
def append_audit_log(customer_id, risk_level, action_taken, message_sent,
                     hardship_type="", officer_id="SYSTEM"):
    """Legacy alias for log_audit_event."""
    return log_audit_event(
        customer_id=customer_id,
        action_type=action_taken,
        message=message_sent,
        officer=officer_id,
    )


def read_audit_log():
    """Legacy alias for load_audit_log."""
    return load_audit_log()
