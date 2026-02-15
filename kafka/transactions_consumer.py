# transactions_consumer.py
# Kafka Consumer — reliably receives JSON transactions and writes to CSV in real time.
# Generates a unique consumer group on every run to avoid stale offset issues.

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable, KafkaError
import json
import csv
import os
import uuid
import time
import sys

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
KAFKA_BROKER = "127.0.0.1:9092"
TOPIC = "transactions"
GROUP_ID = f"txn-consumer-{uuid.uuid4()}"  # unique group every run

CSV_FIELDS = [
    "transaction_id",
    "customer_id",
    "timestamp",
    "amount",
    "transaction_type",
    "channel",
    "merchant_category",
    "is_salary",
]

# Resolve CSV path relative to project root (one level above /kafka)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "transactions_raw.csv")

# ──────────────────────────────────────────────
# KAFKA CONSUMER SETUP
# ──────────────────────────────────────────────
print(f"[INIT] Consumer Group ID : {GROUP_ID}")
print(f"[INIT] Broker            : {KAFKA_BROKER}")
print(f"[INIT] Topic             : {TOPIC}")
print(f"[INIT] CSV output        : {CSV_PATH}")
print()

try:
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="latest",        # only new messages from this run
        enable_auto_commit=True,
        auto_commit_interval_ms=1000,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        # Timeout per poll() call — lets us print heartbeat & avoids infinite block
        consumer_timeout_ms=5000,
        # Faster session/heartbeat so partition assignment happens quickly
        session_timeout_ms=10000,
        heartbeat_interval_ms=3000,
        request_timeout_ms=15000,
        # Fetch tuning
        max_poll_records=100,
        fetch_max_wait_ms=500,
    )
except NoBrokersAvailable:
    print("[ERROR] Could not connect to Kafka broker at", KAFKA_BROKER)
    print("        Make sure Kafka & Zookeeper are running.")
    sys.exit(1)
except KafkaError as e:
    print(f"[ERROR] Kafka error during consumer init: {e}")
    sys.exit(1)

print("[OK] Connected to Kafka broker.\n")

# ──────────────────────────────────────────────
# FORCE PARTITION ASSIGNMENT VIA POLL
# ──────────────────────────────────────────────
# On kafka-python, partitions are assigned lazily during poll().
# We explicitly call poll() in a loop until partitions are assigned.
print("[WAIT] Requesting partition assignment...")

MAX_ASSIGNMENT_WAIT = 30  # seconds
start = time.time()
while time.time() - start < MAX_ASSIGNMENT_WAIT:
    consumer.poll(timeout_ms=1000)   # triggers group join & rebalance
    assigned = consumer.assignment()
    if assigned:
        print(f"[OK] Partitions assigned: {assigned}")
        break
    print("  ... waiting for partition assignment", flush=True)
else:
    print("[WARN] Timed out waiting for partition assignment.")
    print("       Will continue anyway — assignment may happen on next poll.\n")

print()

# ──────────────────────────────────────────────
# CSV SETUP  (create header if file is new)
# ──────────────────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
file_exists = os.path.isfile(CSV_PATH) and os.path.getsize(CSV_PATH) > 0

if not file_exists:
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
    print("[CSV] Created new CSV with header row.")
else:
    print("[CSV] Appending to existing CSV file.")

# ──────────────────────────────────────────────
# MAIN CONSUMER LOOP
# ──────────────────────────────────────────────
print("\n🎧 Listening to Kafka transactions... (Ctrl+C to stop)\n")

message_count = 0

try:
    while True:
        # poll() returns a dict of {TopicPartition: [messages]}
        records = consumer.poll(timeout_ms=2000)

        if not records:
            # No messages in this poll window — just loop again
            continue

        for tp, messages in records.items():
            for message in messages:
                txn = message.value
                message_count += 1

                # ── Print to console ──
                print(f"[#{message_count}] {txn}")

                # ── Append to CSV (open-write-close to avoid Windows file locking) ──
                try:
                    with open(CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
                        writer.writerow(txn)
                        csvfile.flush()
                        os.fsync(csvfile.fileno())  # force OS-level flush
                except PermissionError:
                    print(f"[WARN] CSV file locked — retrying in 0.5s...")
                    time.sleep(0.5)
                    try:
                        with open(CSV_PATH, "a", newline="", encoding="utf-8") as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
                            writer.writerow(txn)
                            csvfile.flush()
                            os.fsync(csvfile.fileno())
                    except Exception as retry_err:
                        print(f"[ERROR] Failed to write after retry: {retry_err}")

except KeyboardInterrupt:
    print(f"\n\n[STOP] Consumer stopped by user.  Total messages received: {message_count}")
except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    raise
finally:
    consumer.close()
    print("[DONE] Consumer closed cleanly.")
