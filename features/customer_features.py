import redis
import json
from kafka import KafkaConsumer
from datetime import datetime

print("Connecting Redis...")
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

print("Connecting Kafka...")

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers="127.0.0.1:9092",
    auto_offset_reset="latest",
    group_id=None,
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

print("Feature Engine Started...")

def update_customer_features(txn):
    cid = txn["customer_id"]
    key = f"customer:{cid}"

    amount = float(txn["amount"])
    category = txn["merchant_category"]
    is_salary = txn["is_salary"]

    # initialize profile if new
    if not r.exists(key):
        r.hset(key, mapping={
            "txn_count": 0,
            "total_spend": 0,
            "withdrawals": 0,
            "salary_count": 0,
            "last_salary_ts": "",
            "essential_spend": 0,
            "discretionary_spend": 0
        })

    # transaction count
    r.hincrby(key, "txn_count", 1)

    # salary detection
    if is_salary:
        r.hincrby(key, "salary_count", 1)
        r.hset(key, "last_salary_ts", txn["timestamp"])

    # spending
    if txn["transaction_type"] == "debit":
        r.hincrbyfloat(key, "total_spend", amount)

        if category in ["grocery", "utilities", "rent"]:
            r.hincrbyfloat(key, "essential_spend", amount)
        else:
            r.hincrbyfloat(key, "discretionary_spend", amount)

    # withdrawals
    if category == "atm":
        r.hincrby(key, "withdrawals", 1)

    print(f"Updated profile for customer {cid}")


for message in consumer:
    txn = message.value
    update_customer_features(txn)
