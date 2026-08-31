import numpy as np
import pandas as pd

np.random.seed(42)
N = 400

age = np.random.randint(21, 60, N)
monthly_income_inr = np.random.randint(15000, 150000, N)
existing_loans_count = np.random.randint(0, 5, N)
credit_utilization_ratio = np.round(np.random.uniform(0.05, 0.95, N), 2)
upi_monthly_inflow_inr = np.random.randint(2000, 120000, N)
bounced_payments_count = np.random.poisson(1.2, N)
employment_type = np.random.choice(
    ["salaried", "self_employed", "gig"], N, p=[0.55, 0.30, 0.15]
)
credit_bureau_score = np.random.randint(300, 900, N).astype(float)

# 20% thin-file applicants (missing bureau score)
thin_file_idx = np.random.choice(N, size=int(0.20 * N), replace=False)
credit_bureau_score[thin_file_idx] = np.nan

# Alternate-data risk formula
z_income = (
    monthly_income_inr - monthly_income_inr.mean()
) / monthly_income_inr.std()
z_bounced = (
    bounced_payments_count - bounced_payments_count.mean()
) / (bounced_payments_count.std() + 1e-9)
z_util = (
    credit_utilization_ratio - credit_utilization_ratio.mean()
) / credit_utilization_ratio.std()
z_upi = (
    upi_monthly_inflow_inr - upi_monthly_inflow_inr.mean()
) / upi_monthly_inflow_inr.std()

risk_score = (
    -2.25
    + (-0.9 * z_income)
    + (0.8 * z_bounced)
    + (0.7 * z_util)
    + (-0.5 * z_upi)
    + np.random.normal(0, 0.6, N)
)
default_prob = 1 / (1 + np.exp(-risk_score))
default = (np.random.uniform(0, 1, N) < default_prob).astype(int)

df = pd.DataFrame({
    "applicant_id": [f"APP{1000 + i}" for i in range(N)],
    "age": age,
    "monthly_income_inr": monthly_income_inr,
    "existing_loans_count": existing_loans_count,
    "credit_utilization_ratio": credit_utilization_ratio,
    "upi_monthly_inflow_inr": upi_monthly_inflow_inr,
    "bounced_payments_count": bounced_payments_count,
    "credit_bureau_score": credit_bureau_score,
    "employment_type": employment_type,
    "default": default,
})
df.to_csv("credit_applicants.csv", index=False)
print("Applicant Default Distribution:")
print(df["default"].value_counts(normalize=True))

# 2. Anomaly detection behavioral dataset
M = 250
behaviour = pd.DataFrame({
    "txn_id": [f"BTXN{5000 + i}" for i in range(M)],
    "applicant_id": np.random.choice(df["applicant_id"], M),
    "txn_hour": np.random.randint(6, 23, M),
    "is_new_device": np.random.choice([0, 1], M, p=[0.9, 0.1]),
    "txn_amount_inr": np.random.choice(
        [199, 499, 999, 1999, 3999], M, p=[0.30, 0.28, 0.22, 0.13, 0.07]
    ),
    "channel": np.random.choice(["P2P", "P2M"], M, p=[0.4, 0.6]),
})

anomalies = pd.DataFrame({
    "txn_id": [f"BTXNA{i}" for i in range(15)],
    "applicant_id": np.random.choice(df["applicant_id"], 15),
    "txn_hour": np.random.randint(1, 5, 15),
    "is_new_device": 1,
    "txn_amount_inr": np.random.choice([14999, 19999, 24999], 15),
    "channel": "P2P",
})

behaviour = pd.concat([behaviour, anomalies], ignore_index=True)
behaviour.to_csv("txn_behaviour.csv", index=False)
