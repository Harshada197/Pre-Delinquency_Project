# generate_customers.py
from faker import Faker
import pandas as pd
import random
from datetime import datetime, timedelta

fake = Faker()

customers = []

NUM_CUSTOMERS = 5000   # you can later increase to 5000

employment_types = ["SALARIED", "SELF_EMPLOYED", "GIG_WORKER","UNEMPLOYED"]

for i in range(NUM_CUSTOMERS):

    employment = random.choice(employment_types)

    # income based on employment
    if employment == "SALARIED":
        salary = random.randint(25000, 120000)
        expected_salary_day = random.randint(1, 7)  # salary usually early month
    elif employment == "SELF_EMPLOYED":
        salary = random.randint(20000, 100000)
        expected_salary_day = random.randint(5, 20)
    else:  # GIG_WORKER
        salary = random.randint(15000, 60000)
        expected_salary_day = random.randint(10, 28)

    # loan simulation
    loan_amount = random.randint(50000, 500000)

    tenure_months = random.choice([12, 24, 36, 48])

    # simple EMI approximation
    emi_amount = int((loan_amount / tenure_months) * 1.08)  # 8% interest approx

    # loan start date sometime in past year
    loan_start_date = fake.date_between(start_date="-365d", end_date="-30d")

    # starting balance
    balance = random.randint(5000, 90000)

    customers.append({
        "customer_id": i + 1,
        "age": random.randint(21, 60),
        "city": fake.city(),
        "employment_type": employment,
        "salary": salary,
        "expected_salary_day": expected_salary_day,
        "loan_amount": loan_amount,
        "loan_tenure_months": tenure_months,
        "emi_amount": emi_amount,
        "loan_start_date": loan_start_date,
        "initial_balance": balance
    })

df = pd.DataFrame(customers)
df.to_csv("customers.csv", index=False)

print("customers.csv generated successfully!")
