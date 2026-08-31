import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")

ledger = pd.read_csv("ledger.csv")
merchants = pd.read_csv("merchants.csv")
gateway = pd.read_csv("gateway_export.csv")

# Merge merchant details into ledger
df = ledger.merge(merchants, on="merchant_id", how="left")
df["transaction_time"] = pd.to_datetime(df["transaction_time"])
df["date"] = df["transaction_time"].dt.date

# -------------------------------------------------------------
# Layer 1: Headline Scorecards
# -------------------------------------------------------------
total_gmv = df[df["status"] == "captured"]["amount_inr"].sum()
overall_success_rate = (len(df[df["status"] == "captured"]) / len(df)) * 100

# Exact Match Rate: in both ledger & gateway with identical amount AND identical status
gw_set = set(zip(gateway["transaction_id"], gateway["amount_inr"], gateway["status"]))
matched_count = sum(
    1
    for _, row in ledger.iterrows()
    if (row["transaction_id"], row["amount_inr"], row["status"]) in gw_set
)
match_rate = (matched_count / len(ledger)) * 100

chargeback_ratio = (len(df[df["status"] == "chargeback"]) / len(df)) * 100

fig, ax = plt.subplots(figsize=(10, 3))
ax.axis("off")
scorecard_text = (
    f"PAYTM PAYMENTS HEALTH SCORECARD\n\n"
    f"Total GMV: INR {total_gmv:,.0f}   |   Overall Success Rate: {overall_success_rate:.1f}%\n"
    f"Reconciliation Match Rate: {match_rate:.1f}%   |   Platform Chargeback Ratio: {chargeback_ratio:.2f}%"
)
ax.text(
    0.5,
    0.5,
    scorecard_text,
    ha="center",
    va="center",
    fontsize=13,
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=1", facecolor="#E8F0FE", edgecolor="#1A73E8"),
)
plt.savefig("dashboard_layer1_headline.png", bbox_inches="tight", dpi=300)
plt.close()

# -------------------------------------------------------------
# Layer 2: Trends Layer (Daily GMV & Daily Chargebacks)
# -------------------------------------------------------------
daily_trends = (
    df.groupby("date")
    .agg(
        daily_gmv=(
            "amount_inr",
            lambda x: x[df.loc[x.index, "status"] == "captured"].sum(),
        ),
        daily_chargebacks=(
            "status",
            lambda x: (x == "chargeback").sum(),
        ),
    )
    .reset_index()
)

fig, ax1 = plt.subplots(figsize=(12, 5))
ax2 = ax1.twinx()

ax1.plot(
    daily_trends["date"],
    daily_trends["daily_gmv"],
    color="#1A73E8",
    marker="o",
    linewidth=2,
    label="Daily GMV (INR)",
)
ax2.bar(
    daily_trends["date"],
    daily_trends["daily_chargebacks"],
    color="#EA4335",
    alpha=0.4,
    label="Chargeback Count",
)

ax1.set_xlabel("Date")
ax1.set_ylabel("Daily GMV (INR)", color="#1A73E8")
ax2.set_ylabel("Daily Chargebacks", color="#EA4335")
plt.title("30-Day Daily GMV & Fraud Chargeback Trends", fontsize=14, fontweight="bold")
fig.autofmt_xdate()
plt.savefig("dashboard_layer2_trends.png", bbox_inches="tight", dpi=300)
plt.close()

# -------------------------------------------------------------
# Layer 3: Breakdown Layer (Payment Method & Category)
# -------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

gmv_by_method = (
    df[df["status"] == "captured"]
    .groupby("payment_method")["amount_inr"]
    .sum()
    .reset_index()
)
sns.barplot(
    data=gmv_by_method,
    x="payment_method",
    y="amount_inr",
    ax=axes[0],
    palette="Blues_d",
)
axes[0].set_title("GMV Breakdown by Payment Method", fontweight="bold")
axes[0].set_ylabel("Total GMV (INR)")

gmv_by_cat = (
    df[df["status"] == "captured"]
    .groupby("category")["amount_inr"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
sns.barplot(
    data=gmv_by_cat,
    y="category",
    x="amount_inr",
    ax=axes[1],
    palette="viridis",
)
axes[1].set_title("GMV Breakdown by Merchant Category", fontweight="bold")
axes[1].set_xlabel("Total GMV (INR)")

plt.tight_layout()
plt.savefig("dashboard_layer3_breakdown.png", bbox_inches="tight", dpi=300)
plt.close()

# -------------------------------------------------------------
# Layer 4: Details Layer (Top 10 Merchants Table Image)
# -------------------------------------------------------------
m_summary = (
    df.groupby(["merchant_id", "merchant_name", "category"])
    .agg(
        total_txns=("transaction_id", "count"),
        chargebacks=("status", lambda x: (x == "chargeback").sum()),
        captured_gmv=(
            "amount_inr",
            lambda x: x[df.loc[x.index, "status"] == "captured"].sum(),
        ),
    )
    .reset_index()
)

m_summary["chargeback_ratio_%"] = (
    m_summary["chargebacks"] / m_summary["total_txns"]
) * 100
m_summary["high_risk_flag"] = m_summary["chargeback_ratio_%"].apply(
    lambda x: "FLAG (>1%)" if x > 1.0 else "NORMAL"
)
top_10 = m_summary.sort_values(by="total_txns", ascending=False).head(10)

fig, ax = plt.subplots(figsize=(12, 4))
ax.axis("off")
table_data = [
    [
        "Merchant ID",
        "Name",
        "Category",
        "Total Txns",
        "Chargebacks",
        "Captured GMV (INR)",
        "CB Ratio (%)",
        "Risk Flag",
    ]
]
for _, r in top_10.iterrows():
    table_data.append([
        r["merchant_id"],
        r["merchant_name"],
        r["category"],
        r["total_txns"],
        r["chargebacks"],
        f"{r['captured_gmv']:,}",
        f"{r['chargeback_ratio_%']:.2f}%",
        r["high_risk_flag"],
    ])

table = ax.table(cellText=table_data, loc="center", cellLoc="center")
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.4)

# Format header & highlight flags
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_facecolor("#4285F4")
        cell.set_text_props(color="white", weight="bold")
    elif table_data[row][7] == "FLAG (>1%)":
        cell.set_facecolor("#FFEBEE")

plt.title(
    "Top 10 Merchants by Transaction Volume & Risk Status",
    fontweight="bold",
    pad=20,
)
plt.savefig("dashboard_layer4_details.png", bbox_inches="tight", dpi=300)
plt.close()

print("All 4 dashboard layer images generated successfully.")
