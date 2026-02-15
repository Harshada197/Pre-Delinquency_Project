from kafka import KafkaConsumer
import json
import redis
import uuid

print("Connecting to Redis...")
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

print("Connecting to Kafka...")

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers="127.0.0.1:9092",
    auto_offset_reset="latest",
    enable_auto_commit=True,
    group_id="feature-engine-" + str(uuid.uuid4()),
    consumer_timeout_ms=1000,
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

print("Waiting for partition assignment...")

# FORCE Kafka to join group
while not consumer.assignment():
    consumer.poll(1000)

print("Partitions assigned:", consumer.assignment())
print("Feature Engine Started...\n")
