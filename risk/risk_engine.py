import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

print("Risk Engine Started...\n")

def calculate_risk(customer_key):
    data = r.hgetall(customer_key)

    txn_count = int(data.get("txn_count", 0))
    withdrawals = int(data.get("withdrawals", 0))
    salary_count = int(data.get("salary_count", 0))
    essential = float(data.get("essential_spend", 0))
    discretionary = float(data.get("discretionary_spend", 0))

    risk = 0

    # Rule 1: no salary
    if salary_count == 0:
        risk += 3

    # Rule 2: high withdrawals
    if withdrawals > 5:
        risk += 2

    # Rule 3: essential > discretionary (financial pressure)
    if essential > discretionary:
        risk += 2

    # classify
    if risk >= 5:
        return "HIGH RISK"
    elif risk >= 3:
        return "MEDIUM RISK"
    else:
        return "LOW RISK"

while True:
    customers = r.keys("customer:*")

    for c in customers:
        level = calculate_risk(c)
        print(c, "→", level)

    print("------")
