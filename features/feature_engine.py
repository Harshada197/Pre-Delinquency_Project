"""
Feature Engine v4.0 — Behaviour-Driven Feature Pipeline
Consumes transactions from Kafka and computes time-aware customer features.
Hardship classification and risk scoring run inline per transaction.

Run:  python features/feature_engine.py
"""
from kafka import KafkaConsumer
import json
import uuid
from datetime import datetime
from customer_features import update_customer_features

print("=" * 60)
print("  EQUILIBRATE — Feature Engine v4.0 (Behaviour-Driven)")
print("  Consumes from Kafka -> computes features -> writes Redis")
print("=" * 60)
print()

# Unique consumer group per run ensures fresh consumption
GROUP_ID = f"feature-engine-{uuid.uuid4().hex[:8]}"

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers="127.0.0.1:9092",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="latest",
    enable_auto_commit=True,
    group_id=GROUP_ID,
    consumer_timeout_ms=5000,
)

print(f"  Consumer group:  {GROUP_ID}")
print(f"  Topic:           transactions")
print(f"  Offset:          latest")
print("-" * 60)

processed = 0

while True:
    try:
        records = consumer.poll(timeout_ms=2000)
        if not records:
            continue

        for tp, messages in records.items():
            for msg in messages:
                txn = msg.value
                update_customer_features(txn)
                processed += 1

                if processed % 25 == 0:
                    cid = txn.get("customer_id", "?")
                    persona = txn.get("persona", "?")
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"  [{ts}] Processed {processed} transactions | "
                          f"Last: Customer {cid} (Persona: {persona})")

    except KeyboardInterrupt:
        print(f"\n  Feature Engine stopped. Total processed: {processed}")
        break
    except Exception as e:
        print(f"  [ERROR] {e}")
        continue

consumer.close()
