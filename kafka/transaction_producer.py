"""
Transaction Producer v4.0 — Persona-Driven Behaviour Simulation
Each customer is deterministically assigned a persona at startup.
Transactions are generated based on persona-specific patterns.

Personas:
  STABLE        (~70%)  Regular salary, normal spending
  OVERSPENDER   (~15%)  High discretionary, credit usage
  INCOME_SHOCK  (~10%)  Salary suddenly stops, ATM spikes, spending drops
  SILENT_DRAIN  (~5%)   No salary, low activity, slow drain
"""
from kafka import KafkaProducer
import pandas as pd
import json
import random
import time
import hashlib
import os
from datetime import datetime
from faker import Faker

fake = Faker()

# ── Kafka ──
producer = KafkaProducer(
    bootstrap_servers="127.0.0.1:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",
)

# ── Load customers ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
customer_path = os.path.join(BASE_DIR, "data", "customers.csv")
customers = pd.read_csv(customer_path)

# ── Persona Assignment (deterministic per customer_id) ──
PERSONA_WEIGHTS = {
    "STABLE": 0.70,
    "OVERSPENDER": 0.15,
    "INCOME_SHOCK": 0.10,
    "SILENT_DRAIN": 0.05,
}


def assign_persona(customer_id):
    """Deterministic persona: hash customer_id -> fixed persona."""
    h = int(hashlib.md5(str(customer_id).encode()).hexdigest(), 16) % 100
    if h < 70:
        return "STABLE"
    elif h < 85:
        return "OVERSPENDER"
    elif h < 95:
        return "INCOME_SHOCK"
    else:
        return "SILENT_DRAIN"


# Build persona map once at startup
persona_map = {}
persona_counts = {"STABLE": 0, "OVERSPENDER": 0, "INCOME_SHOCK": 0, "SILENT_DRAIN": 0}
for _, row in customers.iterrows():
    cid = int(row["customer_id"])
    p = assign_persona(cid)
    persona_map[cid] = p
    persona_counts[p] += 1

print("=" * 60)
print("  EQUILIBRATE — Transaction Producer v4.0 (Persona-Driven)")
print("=" * 60)
print(f"  Customers loaded: {len(customers)}")
for p, c in persona_counts.items():
    pct = 100 * c / len(customers)
    print(f"    {p:>15}: {c:>5} ({pct:.1f}%)")
print("=" * 60)
print()


# ── Transaction Categories ──
ESSENTIAL_CATEGORIES = ["GROCERY", "UTILITY", "RENT", "MEDICAL", "INSURANCE"]
DISCRETIONARY_CATEGORIES = ["SHOPPING", "TRAVEL", "DINING", "ENTERTAINMENT"]
ALL_CATEGORIES = ESSENTIAL_CATEGORIES + DISCRETIONARY_CATEGORIES
CHANNELS = ["UPI", "POS", "ATM", "AUTODEBIT", "NETBANKING"]


def generate_transaction(customer):
    """Generate a persona-driven transaction."""
    cid = int(customer["customer_id"])
    persona = persona_map.get(cid, "STABLE")
    salary = float(customer["salary"])
    emi = float(customer["emi_amount"])

    txn_type = "DEBIT"
    is_salary = 0
    channel = random.choice(CHANNELS)
    category = random.choice(ALL_CATEGORIES)
    amount = random.randint(100, 3000)

    # ─── STABLE: regular patterns ───
    if persona == "STABLE":
        # Salary credit: ~10% of transactions
        if random.random() < 0.10:
            txn_type = "CREDIT"
            amount = int(salary)
            category = "SALARY"
            channel = "BANK_TRANSFER"
            is_salary = 1
        # EMI auto-debit: ~5%
        elif random.random() < 0.05:
            amount = int(emi)
            category = "EMI"
            channel = "AUTODEBIT"
        else:
            # Balanced spending: 60% essential, 40% discretionary
            if random.random() < 0.60:
                category = random.choice(ESSENTIAL_CATEGORIES)
                amount = random.randint(100, 2500)
            else:
                category = random.choice(DISCRETIONARY_CATEGORIES)
                amount = random.randint(200, 3000)
            channel = random.choice(["UPI", "POS", "NETBANKING"])

    # ─── OVERSPENDER: high discretionary, credit-heavy ───
    elif persona == "OVERSPENDER":
        # Salary still comes: ~8%
        if random.random() < 0.08:
            txn_type = "CREDIT"
            amount = int(salary)
            category = "SALARY"
            channel = "BANK_TRANSFER"
            is_salary = 1
        # EMI: ~5%
        elif random.random() < 0.05:
            amount = int(emi)
            category = "EMI"
            channel = "AUTODEBIT"
        else:
            # 80% discretionary, high amounts
            if random.random() < 0.80:
                category = random.choice(DISCRETIONARY_CATEGORIES)
                amount = random.randint(800, 12000)
            else:
                category = random.choice(ESSENTIAL_CATEGORIES)
                amount = random.randint(100, 1500)
            channel = random.choice(["UPI", "POS", "NETBANKING"])

    # ─── INCOME_SHOCK: salary stops, ATM spikes ───
    elif persona == "INCOME_SHOCK":
        # NO salary credits (income stopped) — very rare accidental credit
        # High ATM withdrawals: ~40%
        if random.random() < 0.40:
            category = "ATM_WITHDRAWAL"
            channel = "ATM"
            amount = random.randint(1000, 8000)
        # Mostly essential spending, very little discretionary
        elif random.random() < 0.90:
            category = random.choice(ESSENTIAL_CATEGORIES)
            amount = random.randint(50, 1200)
            channel = random.choice(["UPI", "POS"])
        else:
            category = random.choice(DISCRETIONARY_CATEGORIES)
            amount = random.randint(50, 400)
            channel = "UPI"

    # ─── SILENT_DRAIN: no salary, low activity ───
    elif persona == "SILENT_DRAIN":
        # NO salary, very low spending
        if random.random() < 0.25:
            category = "ATM_WITHDRAWAL"
            channel = "ATM"
            amount = random.randint(200, 3000)
        else:
            category = random.choice(ESSENTIAL_CATEGORIES)
            amount = random.randint(50, 600)
            channel = random.choice(["UPI", "POS"])

    transaction = {
        "transaction_id": fake.uuid4(),
        "customer_id": cid,
        "timestamp": str(datetime.now()),
        "amount": int(amount),
        "transaction_type": txn_type,
        "channel": channel,
        "merchant_category": category,
        "is_salary": is_salary,
        "persona": persona,
    }

    return transaction


# ── Weighted customer selection: risky personas produce more transactions ──
persona_tx_weight = {
    "STABLE": 1.0,
    "OVERSPENDER": 1.8,
    "INCOME_SHOCK": 2.5,
    "SILENT_DRAIN": 0.4,
}

weights = [persona_tx_weight.get(persona_map.get(int(row["customer_id"]), "STABLE"), 1.0)
           for _, row in customers.iterrows()]
total_weight = sum(weights)
normalized_weights = [w / total_weight for w in weights]


# ── Infinite stream ──
txn_num = 0
while True:
    # Weighted random customer selection
    idx = random.choices(range(len(customers)), weights=normalized_weights, k=1)[0]
    customer = customers.iloc[idx]
    txn = generate_transaction(customer)

    producer.send("transactions", txn)
    txn_num += 1

    if txn_num % 50 == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent {txn_num} transactions | "
              f"Last: customer={txn['customer_id']} persona={txn['persona']} "
              f"type={txn['transaction_type']} amount={txn['amount']} "
              f"category={txn['merchant_category']}")

    time.sleep(random.uniform(0.3, 1.5))
