import pandas as pd

print("Building training dataset...")

df = pd.read_csv("data/transactions_raw.csv")

# aggregate customer behaviour
features = df.groupby("customer_id").agg({
    "amount": ["count", "sum"],
    "is_salary": "sum"
})

features.columns = ["txn_count", "total_amount", "salary_count"]
features = features.reset_index()

# create withdrawals
withdrawals = df[df["merchant_category"] == "atm"].groupby("customer_id").size()
features["withdrawals"] = features["customer_id"].map(withdrawals).fillna(0)

# simulate delinquency label
def assign_label(row):
    if row["salary_count"] == 0 and row["withdrawals"] > 5:
        return 1   # delinquent
    if row["total_amount"] < 2000:
        return 1
    return 0

features["delinquent"] = features.apply(assign_label, axis=1)

features.to_csv("data/training_data.csv", index=False)

print("training_data.csv created!")
