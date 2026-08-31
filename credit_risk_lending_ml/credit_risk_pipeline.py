import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

# -------------------------------------------------------------
# Part A: EDA & Leakage-Free Preprocessing
# -------------------------------------------------------------
df = pd.read_csv("credit_applicants.csv")

# 1. Report Baseline Stats
measured_default_rate = df["default"].mean() * 100
missing_bureau_pct = (df["credit_bureau_score"].isna().sum() / len(df)) * 100
print(f"Dataset Shape: {df.shape}")
print(f"Measured Default Rate: {measured_default_rate:.2f}% (Target: 15-25%)")
print(
    f"Missing Bureau Scores: {missing_bureau_pct:.2f}% (Target: exactly 20.0%)"
)

# 2. Engineer is_thin_file Flag BEFORE train/test split
# (Direct indicator from raw data; does not depend on fitted statistics)
df["is_thin_file"] = df["credit_bureau_score"].isna().astype(int)

# Separate features and target
X = df.drop(columns=["applicant_id", "default"])
y = df["default"]

# 3. Stratified Train/Test Split (75/25, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

# 4. Impute Missing Bureau Scores strictly using Train-Set Median
train_bureau_median = X_train["credit_bureau_score"].dropna().median()
print(f"Training Bureau Median: {train_bureau_median:.2f}")

X_train["credit_bureau_score"] = X_train["credit_bureau_score"].fillna(
    train_bureau_median
)
X_test["credit_bureau_score"] = X_test["credit_bureau_score"].fillna(
    train_bureau_median
)

# 5. One-Hot Encode Categorical Features
X_train = pd.get_dummies(
    X_train, columns=["employment_type"], drop_first=True, dtype=int
)
X_test = pd.get_dummies(
    X_test, columns=["employment_type"], drop_first=True, dtype=int
)
# Ensure aligned columns between train and test
X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

# 6. Scale Numeric Features (Fit on Train ONLY)
numeric_cols = [
    "age",
    "monthly_income_inr",
    "existing_loans_count",
    "credit_utilization_ratio",
    "upi_monthly_inflow_inr",
    "bounced_payments_count",
    "credit_bureau_score",
]

scaler = StandardScaler()
X_train[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
X_test[numeric_cols] = scaler.transform(X_test[numeric_cols])

# -------------------------------------------------------------
# Part B: Classification Models & Evaluation
# -------------------------------------------------------------
# Train Logistic Regression
lr_model = LogisticRegression(random_state=42, max_iter=1000)
lr_model.fit(X_train, y_train)
lr_preds = lr_model.predict(X_test)
lr_probs = lr_model.predict_proba(X_test)[:, 1]

# Train Decision Tree
dt_model = DecisionTreeClassifier(random_state=42)
dt_model.fit(X_train, y_train)
dt_preds = dt_model.predict(X_test)
dt_probs = dt_model.predict_proba(X_test)[:, 1]


def evaluate_model(name, y_true, y_pred, y_prob):
    cm = confusion_matrix(y_true, y_pred)
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_prob)
    return {
        "Model": name,
        "Confusion Matrix [TN, FP / FN, TP]": f"[{cm[0,0]}, {cm[0,1]} / {cm[1,0]}, {cm[1,1]}]",
        "Accuracy": f"{acc:.4f}",
        "Precision": f"{prec:.4f}",
        "Recall": f"{rec:.4f}",
        "F1-Score": f"{f1:.4f}",
        "ROC-AUC": f"{auc:.4f}",
    }


metrics_table = pd.DataFrame([
    evaluate_model("Logistic Regression", y_test, lr_preds, lr_probs),
    evaluate_model("Decision Tree", y_test, dt_preds, dt_probs),
])
print("\n=== Classifier Comparison Table ===")
print(metrics_table.to_string(index=False))

# -------------------------------------------------------------
# Part B.3: Risk-Based Pricing Table
# -------------------------------------------------------------
# Bucket test set into 4 probability quartiles
test_eval_df = pd.DataFrame({
    "actual_default": y_test.values,
    "pred_prob": lr_probs,
})

test_eval_df["risk_tier"] = pd.qcut(
    test_eval_df["pred_prob"],
    q=4,
    labels=["Tier 1 (Low)", "Tier 2 (Medium)", "Tier 3 (High)", "Tier 4 (Very High)"],
)

pricing_grid = {
    "Tier 1 (Low)": "12.0% - 15.0%",
    "Tier 2 (Medium)": "16.0% - 19.0%",
    "Tier 3 (High)": "20.0% - 24.0%",
    "Tier 4 (Very High)": "25.0% - 30.0%",
}

pricing_table = (
    test_eval_df.groupby("risk_tier", observed=False)
    .agg(
        applicant_count=("actual_default", "count"),
        min_pred_prob=("pred_prob", "min"),
        max_pred_prob=("pred_prob", "max"),
        observed_defaults=("actual_default", "sum"),
        observed_default_rate=("actual_default", "mean"),
    )
    .reset_index()
)

pricing_table["interest_rate_range"] = pricing_table["risk_tier"].map(
    pricing_grid
)
pricing_table["observed_default_rate_%"] = (
    pricing_table["observed_default_rate"] * 100
).round(2)
pricing_table["min_pred_prob"] = pricing_table["min_pred_prob"].round(4)
pricing_table["max_pred_prob"] = pricing_table["max_pred_prob"].round(4)

print("\n=== Risk-Based Pricing Table ===")
print(
    pricing_table[[
        "risk_tier",
        "min_pred_prob",
        "max_pred_prob",
        "applicant_count",
        "observed_default_rate_%",
        "interest_rate_range",
    ]].to_string(index=False)
)

# -------------------------------------------------------------
# Part C: Transaction Behaviour Anomaly Detection
# -------------------------------------------------------------
behaviour_df = pd.read_csv("txn_behaviour.csv")
features = ["txn_hour", "is_new_device", "txn_amount_inr"]

X_beh = behaviour_df[features].copy()
scaler_beh = StandardScaler()
X_beh_scaled = scaler_beh.fit_transform(X_beh)

# Contamination matching seeded rate: 15 / 265
contamination_rate = 15 / 265
iso_forest = IsolationForest(
    contamination=contamination_rate, random_state=42
)
behaviour_df["anomaly_flag"] = iso_forest.fit_predict(X_beh_scaled)
# IsolationForest returns -1 for anomalies, 1 for normal instances
behaviour_df["is_anomaly"] = (behaviour_df["anomaly_flag"] == -1).astype(int)

# Check Recall against injected 'BTXNA*' IDs
seeded_anomalies = behaviour_df[
    behaviour_df["txn_id"].str.startswith("BTXNA")
]
flagged_seeded = seeded_anomalies["is_anomaly"].sum()
total_seeded = len(seeded_anomalies)
recall_seeded = (flagged_seeded / total_seeded) * 100

print("\n=== Isolation Forest Anomaly Detection Results ===")
print(f"Total Transactions: {len(behaviour_df)}")
print(f"Total Flagged as Anomalies: {behaviour_df['is_anomaly'].sum()}")
print(
    f"Injected Anomalies (BTXNA*) Detected: {flagged_seeded} / {total_seeded}"
)
print(f"Seeded Anomaly Recall: {recall_seeded:.2f}%")
