# transaction_consumer.py
# This file will capture the stream and create your dataset.

from kafka import KafkaConsumer
import json
import csv
import os
import uuid
import time

# give unique group every run (prevents Kafka offset problems)
GROUP_ID = "txn-consumer-" + str(uuid.uuid4())

try:
    consumer = KafkaConsumer(
        "transactions",
        bootstrap_servers="127.0.0.1:9092",
        group_id=GROUP_ID,                # ⭐ VERY IMPORTANT
        auto_offset_reset="earliest",     # read old messages also
        enable_auto_commit=True,

        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
except Exception as e:
    print(f"Error connecting to Kafka: {e}")
    exit(1)

print("Connected to Kafka")
print("Waiting for partition assignment...")

# wait until Kafka assigns partitions (with timeout)
timeout_counter = 0
while not consumer.assignment() and timeout_counter < 30:
    print(".", end="", flush=True)
    timeout_counter += 1
    time.sleep(0.1)

print("Partitions assigned:", consumer.assignment())

# locate dataset path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(BASE_DIR, "data", "transactions_raw.csv")

file_exists = os.path.exists(data_path)

with open(data_path, "a", newline="", encoding="utf-8") as csvfile:

    fieldnames = [
        "transaction_id",
        "customer_id",
        "timestamp",
        "amount",
        "transaction_type",
        "channel",
        "merchant_category",
        "is_salary"
    ]

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    if not file_exists:
        writer.writeheader()

    print("Listening to Kafka transactions...\n")

    try:
        for message in consumer:
            txn = message.value

            writer.writerow(txn)
            csvfile.flush()

            print("Saved transaction:", txn)
    except KeyboardInterrupt:
        print("\nConsumer stopped by user")
    except Exception as e:
        print(f"Error processing message: {e}")
        raise
