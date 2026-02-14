from kafka import KafkaProducer
import pandas as pd
import json, random, time, datetime
from faker import Faker

fake = Faker()

# connect to kafka
producer = KafkaProducer(
    bootstrap_servers='127.0.0.1:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all'
)

# load customers
customers = pd.read_csv("../data/customers.csv")

channels = ["UPI", "POS", "ATM", "AUTODEBIT" , "NETBANKING"]
categories = ["GROCERY","FOOD","SHOPPING","UTILITY","TRAVEL","LOANAPP"]

def generate_transaction(customer):

    txn_type = random.choice(["DEBIT","CREDIT"])

    # salary credit (once in a while)
    is_salary = 0
    if txn_type == "CREDIT" and random.random() < 0.08:
        amount = customer["salary"]
        category = "SALARY"
        channel = "BANK_TRANSFER"
        is_salary = 1

    # EMI auto debit
    elif random.random() < 0.05:
        amount = customer["emi_amount"]
        category = "EMI"
        channel = "AUTODEBIT"
        txn_type = "DEBIT"

    else:
        amount = random.randint(50, 4000)
        category = random.choice(categories)
        channel = random.choice(channels)

    transaction = {
        "transaction_id": fake.uuid4(),
        "customer_id": int(customer["customer_id"]),
        "timestamp": str(datetime.datetime.now()),
        "amount": int(amount),
        "transaction_type": txn_type,
        "channel": channel,
        "merchant_category": category,
        "is_salary": is_salary
    }

    return transaction


# infinite stream
while True:

    customer = customers.sample(1).iloc[0]
    txn = generate_transaction(customer)

    producer.send("transactions", txn)
    print("Sent:", txn)

    time.sleep(random.uniform(0.5, 2.0))
