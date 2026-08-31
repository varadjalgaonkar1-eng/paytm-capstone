import sqlite3
import pandas as pd

conn = sqlite3.connect("paytm_payments.db")
cursor = conn.cursor()

# 1. Normalized Schema Definition
cursor.executescript("""
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS merchants;

CREATE TABLE merchants (
    merchant_id INTEGER PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    category TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    signup_date TIMESTAMP NOT NULL
);

CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    merchant_id INTEGER NOT NULL,
    transaction_time TIMESTAMP NOT NULL,
    amount_inr INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(merchant_id) REFERENCES merchants(merchant_id)
);
""")

# Load CSVs
pd.read_csv("merchants.csv").to_sql(
    "merchants", conn, if_exists="append", index=False
)
pd.read_csv("users.csv").to_sql("users", conn, if_exists="append", index=False)
pd.read_csv("ledger.csv").to_sql(
    "transactions", conn, if_exists="append", index=False
)

print("--- Query 1: Top 5 Merchants by GMV (INNER JOIN, GROUP BY, ORDER BY, LIMIT) ---")
q1 = """
SELECT m.merchant_name, m.category, m.region, SUM(t.amount_inr) AS total_gmv
FROM transactions t
INNER JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.status = 'captured'
GROUP BY m.merchant_id, m.merchant_name, m.category, m.region
ORDER BY total_gmv DESC
LIMIT 5;
"""
print(pd.read_sql_query(q1, conn))

print("\n--- Query 2: High-Volume Users with Failed Txns (GROUP BY, HAVING) ---")
q2 = """
SELECT user_id, COUNT(*) AS failed_count, SUM(amount_inr) AS failed_amount
FROM transactions
WHERE status = 'failed'
GROUP BY user_id
HAVING COUNT(*) >= 3;
"""
print(pd.read_sql_query(q2, conn))

print("\n--- Query 3: Inactive Merchants Check (LEFT JOIN, DISTINCT) ---")
q3 = """
SELECT DISTINCT m.merchant_id, m.merchant_name, m.region
FROM merchants m
LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
WHERE t.transaction_id IS NULL;
"""
print(pd.read_sql_query(q3, conn))

print("\n--- Query 4: Total Chargeback Impact (Impact quantification) ---")
q4 = """
SELECT 
    COUNT(*) AS chargeback_count,
    COUNT(DISTINCT user_id) AS unique_users_affected,
    SUM(amount_inr) AS total_chargeback_inr
FROM transactions
WHERE status = 'chargeback';
"""
print(pd.read_sql_query(q4, conn))

print("\n--- Query 5: Burner Accounts Detection (Target: >= 15 rows) ---")
q5 = """
SELECT 
    t.transaction_id,
    t.user_id,
    u.signup_date,
    t.transaction_time,
    t.amount_inr,
    (julianday(t.transaction_time) - julianday(u.signup_date)) AS account_age_days
FROM transactions t
INNER JOIN users u ON t.user_id = u.user_id
WHERE t.status = 'chargeback'
  AND (julianday(t.transaction_time) - julianday(u.signup_date)) >= 0
  AND (julianday(t.transaction_time) - julianday(u.signup_date)) < 30
ORDER BY t.transaction_time;
"""
df_burner = pd.read_sql_query(q5, conn)
print(f"Burner accounts surfaced: {len(df_burner)}")
print(df_burner.head())

print("\n--- Query 6: Velocity Attack Detection (Target: 8 distinct clusters) ---")
q6 = """
SELECT 
    user_id,
    strftime('%Y-%m-%d %H:', transaction_time) || 
    substr('00' || (CAST(strftime('%M', transaction_time) AS INTEGER) / 10 * 10), -2, 2) AS time_bucket_10min,
    MIN(transaction_time) AS cluster_start_time,
    COUNT(*) AS txn_count,
    SUM(amount_inr) AS total_bucket_amount
FROM transactions
GROUP BY user_id, time_bucket_10min
HAVING COUNT(*) >= 3
ORDER BY cluster_start_time;
"""
df_velocity = pd.read_sql_query(q6, conn)
print(f"Velocity clusters surfaced: {len(df_velocity)}")
print(df_velocity)

conn.close()
