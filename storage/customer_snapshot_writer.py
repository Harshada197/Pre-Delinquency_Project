"""
Customer Snapshot Writer — Behavioural Monitoring Database Writer
Appends one row per customer to data/customer_history.csv after each
transaction is processed. Acts as the bank's behavioural snapshot store.

Deduplication: Prevents duplicate writes within 5 minutes per customer.
"""
import os
import csv
import time
import pandas as pd
import redis
from datetime import datetime

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_CSV = os.path.join(BASE_DIR, "data", "customer_history.csv")
CUSTOMERS_CSV = os.path.join(BASE_DIR, "data", "customers.csv")

# ── CSV Headers ──
SNAPSHOT_FIELDS = [
    "customer_id",
    "timestamp",
    "risk_level",
    "risk_score",
    "txn_count_7d",
    "salary_credits_30d",
    "withdrawals_7d",
    "total_spend_30d",
    "essential_spend_ratio",
    "discretionary_spend_ratio",
    "days_since_salary",
    "hardship_type",
    "account_balance",
    "emi_amount",
    "previous_defaults",
    "loan_from_other_banks",
]

# ── Redis connection ──
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# ── In-memory deduplication cache: { customer_id: last_write_timestamp } ──
_last_write_time = {}

# ── Cooldown in seconds (5 minutes) ──
WRITE_COOLDOWN = 300

# ── Load static customer data (once at startup) ──
_customer_static = {}


def _load_static_data():
    """Load static customer attributes from customers.csv into memory."""
    global _customer_static
    try:
        df = pd.read_csv(CUSTOMERS_CSV)
        for _, row in df.iterrows():
            cid = str(int(row["customer_id"]))
            _customer_static[cid] = {
                "emi_amount": float(row.get("emi_amount", 0)),
                "initial_balance": float(row.get("initial_balance", 0)),
            }
        print(f"  [SnapshotWriter] Loaded static data for {len(_customer_static)} customers")
    except Exception as e:
        print(f"  [SnapshotWriter] Warning: Could not load customers.csv — {e}")


# Load on import
_load_static_data()


def _ensure_csv_exists():
    """Create the CSV file with headers if it doesn't exist."""
    if not os.path.exists(HISTORY_CSV):
        os.makedirs(os.path.dirname(HISTORY_CSV), exist_ok=True)
        with open(HISTORY_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(SNAPSHOT_FIELDS)
        print(f"  [SnapshotWriter] Created {HISTORY_CSV}")


def _is_duplicate(customer_id):
    """Check if a write for this customer occurred within the last 5 minutes."""
    cid = str(customer_id)
    now = time.time()
    last = _last_write_time.get(cid, 0)
    return (now - last) < WRITE_COOLDOWN


def _mark_written(customer_id):
    """Record the timestamp of the latest write for this customer."""
    _last_write_time[str(customer_id)] = time.time()


def write_customer_snapshot(customer_id):
    """
    Build and append a behavioural snapshot row for a customer.
    Pulls real-time features from Redis + static data from customers.csv.
    Skips if the same customer was written within the last 5 minutes.
    """
    cid = str(customer_id)

    # ── Deduplication check ──
    if _is_duplicate(cid):
        return False

    # ── Ensure CSV exists ──
    _ensure_csv_exists()

    # ── Pull real-time data from Redis ──
    key = f"customer:{cid}"
    profile = r.hgetall(key)

    if not profile:
        return False

    # Real-time features
    txn_count = int(profile.get("txn_count", 0))
    salary_count = int(profile.get("salary_count", 0))
    withdrawals = int(profile.get("withdrawals", 0))
    total_spend = float(profile.get("total_spend", 0))
    essential_spend = float(profile.get("essential_spend", 0))
    discretionary_spend = float(profile.get("discretionary_spend", 0))
    risk_level = profile.get("risk_level", "UNKNOWN")
    risk_score = profile.get("risk_score", "0")
    hardship_type = profile.get("hardship_type", "NONE")
    last_salary_ts = profile.get("last_salary_ts", "")

    # ── Compute derived features ──
    # Essential & discretionary spend ratios
    total_categorized = essential_spend + discretionary_spend
    essential_ratio = round(essential_spend / total_categorized, 4) if total_categorized > 0 else 0.0
    discretionary_ratio = round(discretionary_spend / total_categorized, 4) if total_categorized > 0 else 0.0

    # Days since last salary
    days_since_salary = -1  # -1 means no salary ever received
    if last_salary_ts and last_salary_ts.strip():
        try:
            last_salary_dt = datetime.strptime(last_salary_ts.split(".")[0], "%Y-%m-%d %H:%M:%S")
            days_since_salary = (datetime.now() - last_salary_dt).days
        except (ValueError, IndexError):
            days_since_salary = -1

    # ── Static data from customers.csv ──
    static = _customer_static.get(cid, {})
    emi_amount = static.get("emi_amount", 0)
    account_balance = static.get("initial_balance", 0)

    # ── Simulated fields (not available in current pipeline — placeholder) ──
    previous_defaults = 0
    loan_from_other_banks = 0

    # ── Build the row ──
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        cid,                        # customer_id
        now,                        # timestamp
        risk_level,                 # risk_level
        risk_score,                 # risk_score
        txn_count,                  # txn_count_7d (using total as approximation)
        salary_count,               # salary_credits_30d
        withdrawals,                # withdrawals_7d
        round(total_spend, 2),      # total_spend_30d
        essential_ratio,            # essential_spend_ratio
        discretionary_ratio,        # discretionary_spend_ratio
        days_since_salary,          # days_since_salary
        hardship_type,              # hardship_type
        round(account_balance, 2),  # account_balance
        round(emi_amount, 2),       # emi_amount
        previous_defaults,          # previous_defaults
        loan_from_other_banks,      # loan_from_other_banks
    ]

    # ── Append to CSV ──
    try:
        with open(HISTORY_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        _mark_written(cid)
        print(f"  [Snapshot] Wrote snapshot for customer {cid} | Risk: {risk_level} | Score: {risk_score}")
        return True

    except Exception as e:
        print(f"  [SnapshotWriter] Error writing snapshot for {cid}: {e}")
        return False
