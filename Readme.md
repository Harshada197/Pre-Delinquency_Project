# Equilibrate — Pre-Delinquency Intervention Engine

> **Built for the Barclays Hack-O-Hire Hackathon**

A **real-time, AI-powered pre-delinquency detection system** for retail banking. Equilibrate identifies customers showing early signs of financial distress — before they miss a payment — and generates policy-compliant intervention recommendations.

Built on a streaming architecture using **Kafka → Feature Engine → Redis → Risk Engine → Dashboard**, the system processes live transactions, classifies customer hardship types, computes weighted risk scores, and delivers actionable intervention plans through a Streamlit operations console.

---

## Architecture

```
┌─────────────────┐     ┌───────────────┐     ┌──────────────────┐
│  Kafka Producer  │────▶│  Kafka Topic   │────▶│  Kafka Consumer  │
│  (Transactions)  │     │ "transactions" │     │  (Raw CSV Writer)│
└─────────────────┘     └───────────────┘     └──────────────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │  Feature Engine   │
                                              │  (Per-Txn Update) │
                                              └────────┬─────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │     Redis         │
                                              │  (Live Profiles)  │
                                              └────────┬─────────┘
                                                       │
                                          ┌────────────┼────────────┐
                                          ▼            ▼            ▼
                                   ┌────────────┐ ┌──────────┐ ┌───────────┐
                                   │Risk Engine │ │ Snapshot  │ │ Dashboard │
                                   │(5s cycles) │ │ Writer   │ │(Streamlit)│
                                   └────────────┘ └──────────┘ └───────────┘
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Persona-Driven Simulation** | 5,000 customers with 4 behavioural personas (Stable 70%, Overspender 15%, Income Shock 10%, Silent Drain 5%) |
| **Real-Time Feature Engineering** | Rolling 7-day windows for ATM withdrawals, spending change %, transaction frequency |
| **Dynamic Hardship Classification** | 5 types: Income Shock, Liquidity Stress, Expense Compression, Over-Leverage, Overspending |
| **Weighted Risk Scoring** | Multi-signal convergence model (salary gap, withdrawal spikes, spend drop, inactivity, persona factor) |
| **Policy-Bound Interventions** | Compliance-approved message templates mapped to hardship × risk level combinations |
| **Audit Trail** | Every intervention logged with timestamp, risk level, action taken, and message text |
| **Auto-Refresh Dashboard** | Live dashboard updates every 3 minutes with proof-of-realtime timestamps |

---

## Project Structure

```
Pre-Delinquecy/
│
├── kafka/
│   ├── transaction_producer.py      # Persona-driven transaction generator → Kafka
│   └── transactions_consumer.py     # Kafka consumer → data/transactions_raw.csv
│
├── features/
│   ├── feature_engine.py            # Kafka consumer → per-txn feature computation → Redis
│   └── customer_features.py         # Rolling windows, hardship classification, risk scoring
│
├── risk/
│   ├── risk_engine.py               # Continuous re-evaluation loop (every 5 seconds)
│   ├── policy_engine.py             # Policy lookup: hardship × risk → action + message
│   ├── policy_templates.json        # Compliance-approved intervention templates
│   └── alert_engine.py              # Alert generation
│
├── storage/
│   └── customer_snapshot_writer.py   # Periodic CSV snapshots of customer state
│
├── model/
│   ├── build_training_data.py       # Training data preparation
│   └── train_model.py               # XGBoost model training
│
├── dashboard/
│   ├── Home.py                      # Operations Hub — KPIs, live timestamps, risk donut
│   ├── utils.py                     # Redis access, CSV merge, sidebar, helpers
│   ├── audit_log.py                 # Intervention logging to CSV + Redis feedback
│   ├── styles/
│   │   └── theme.css                # Enterprise-grade dark/light CSS
│   └── pages/
│       ├── 1_Portfolio_Overview.py   # Charts: hardship × risk, trends over time
│       ├── 2_Risk_Queue.py          # Filterable risk table with Last Updated column
│       ├── 3_Customer_Profile.py    # Individual customer deep-dive
│       └── 4_Intervention_Center.py # Template messaging, send SMS, audit history
│
├── data/
│   ├── customers.csv                # Static customer master data (5,000 records)
│   ├── transactions_raw.csv         # Raw transaction log from Kafka consumer
│   ├── customer_history.csv         # Periodic behavioural snapshots
│   ├── intervention_log.csv         # Audit trail of all interventions
│   ├── features_dataset.csv         # Aggregated features for ML training
│   └── training_data.csv            # Labeled training data
│
├── alert/
│   └── intervention_engine.py       # Intervention logic
│
├── requirements.txt
└── Readme.md
```

---

## Prerequisites

- **Python 3.9+**
- **Apache Kafka** (installed at `C:\kafka` with KRaft or Zookeeper)
- **Redis Server** (installed at `C:\Redis`)
- **pip packages** — install via:

```bash
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Dashboard UI framework |
| `streamlit-autorefresh` | Auto-refresh every 3 minutes |
| `redis` | Real-time customer profile store |
| `kafka-python` | Kafka producer/consumer |
| `pandas` | Data manipulation |
| `plotly` | Interactive charts |
| `faker` | Synthetic transaction generation |
| `xgboost` | ML model (risk prediction) |
| `scikit-learn` | ML utilities |
| `joblib` | Model serialization |
| `gTTS` | Text-to-speech for audio messages |

---

## Quick Start

Open **6 separate terminals** and run the commands in order:

### Terminal 1 — Redis Server
```bash
C:\Redis\redis-server.exe
```

### Terminal 2 — Kafka Broker
```bash
cd C:\kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

### Terminal 3 — Transaction Producer
```bash
cd Pre-Delinquecy
python kafka\transaction_producer.py
```

### Terminal 4 — Transaction Consumer
```bash
cd Pre-Delinquecy
python kafka\transactions_consumer.py
```

### Terminal 5 — Feature Engine
```bash
cd Pre-Delinquecy
python features\feature_engine.py
```

### Terminal 6 — Risk Engine
```bash
cd Pre-Delinquecy
python risk\risk_engine.py
```

### Terminal 7 — Dashboard
```bash
cd Pre-Delinquecy
streamlit run dashboard/Home.py
```

> **Note:** The Kafka topic `transactions` is auto-created on first message. If needed, create it manually:
> ```bash
> cd C:\kafka
> .\bin\windows\kafka-topics.bat --create --topic transactions --bootstrap-server 127.0.0.1:9092 --partitions 1 --replication-factor 1
> ```

---

## Dashboard Pages

### Home — Operations Hub
- KPI cards: Total Customers, High/Medium/Low Risk counts
- **Last Live Transaction** and **Last Risk Evaluation** timestamps (proof of real-time)
- High Risk Rate indicator with severity classification
- Risk distribution donut chart
- Immediate Attention table (HIGH risk customers)
- Hardship breakdown bar chart
- Risk trend line chart (last 30 minutes)

### Portfolio Overview
- Hardship type × Risk level stacked bar chart
- Risk levels over time (trend analysis)
- Persona distribution

### Risk Queue
- Filterable table: risk level, hardship type, search by customer ID
- Columns: Customer ID, Risk Level, Risk Score, Hardship Type, City, Employment, Recommended Action, **Last Updated**
- Sorted by risk score descending

### Customer Profile
- Search and select any customer
- Full profile: demographics, behavioural features, risk factors
- Risk explainability breakdown
- Transaction pattern analysis

### Intervention Center
- Select customer → view profile + risk assessment
- **Template-based message generation** from policy engine
- Edit and send SMS/email
- Full intervention audit history per customer
- All actions logged to `data/intervention_log.csv`

---

## Team CoreCapital

| # | Member |
|---|--------|
| 1 | Harshada Dhas |
| 2 | Anushree Surve |
| 3 | Srushti Kotgire |
| 4 | Zahara Bhori |
| 5 | Kasturi Deo |

---

## Hardship Classification Rules

| Type | Trigger Conditions |
|------|-------------------|
| **Income Shock** | No salary credits + ≥5 transactions + persona is INCOME_SHOCK or SILENT_DRAIN; OR days since salary >30 + ATM withdrawals ≥3 |
| **Over-Leverage** | Essential spending >70% of total spend + ≥5 transactions |
| **Liquidity Stress** | ATM withdrawals ≥5 + spending drop >20%; OR ATM withdrawals ≥8 |
| **Expense Compression** | Zero discretionary spending + ≥5 transactions; OR spending drop >40% + essential >3× discretionary |
| **Overspending** | Discretionary >2.5× essential + discretionary >₹3,000; OR OVERSPENDER persona + discretionary >2× essential |

---

## Risk Scoring (0–10 Scale)

| Signal | Points | Weight |
|--------|--------|--------|
| Salary gap (no salary + high txn count) | 0–3 | High |
| Withdrawal spike (ATM 7d) | 0–2 | Medium |
| Spending drop (% change) | 0–2 | Medium |
| Inactivity / survival mode | 0–1 | Low |
| Persona factor (supplemental) | 0–1 | Supplemental |

**Classification:** HIGH ≥ 5 · MEDIUM ≥ 3 · LOW < 3

---

## Verifying Real-Time Data

```bash
# Check Redis is running
redis-cli ping
# Expected: PONG

# Count customers in Redis
redis-cli keys "customer:*" | find /c ":"

# View a customer profile
redis-cli hgetall customer:100

# Check hardship distribution
python -c "import redis; from collections import Counter; r=redis.Redis(decode_responses=True); print(Counter(r.hget(k,'hardship_type') for k in r.keys('customer:*')))"
```

