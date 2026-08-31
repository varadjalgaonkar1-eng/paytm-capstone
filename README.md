# Paytm FinTech Analytics & AI Platform

This repository contains the complete submission for the Executive Certification Capstone Project.

## Project Structure
* `payments_fraud_analytics/`: Part 1 — Excel modeling, SQLite fraud queries, payment reconciliation engine, and 4-layer dashboard.
* `credit_risk_lending_ml/`: Part 2 — Credit risk classification, risk-based pricing, and behavioural anomaly detection.
* `ai_advisory_blockchain/`: Part 3 — CAPM advisory agent, disclosure extractor, debate simulator, DCF calculator, and crypto risk note.

## Setup & Execution
```bash
# 1. Environment Setup
pip install -r requirements.txt

# 2. Run Part 1
cd payments_fraud_analytics
python generate_data.py
python create_workbook.py
python schema_queries.py
python reconcile.py
python dashboard_generator.py
cd ..

# 3. Run Part 2
cd credit_risk_lending_ml
python generate_data.py
python credit_risk_pipeline.py
cd ..

# 4. Run Part 3 (Default MOCK_LLM=1 deterministic mode)
cd ai_advisory_blockchain
python advisory_agent.py
python extract_disclosure.py
python debate.py
python dcf_calculator.py
cd ..
```

## Design Decisions
* The fraud analytics workflow uses seeded, reproducible synthetic datasets with exact row counts and injection patterns for burner-account and velocity anomalies.
* Credit risk modeling follows leakage-safe preprocessing: feature engineering before split, train-only imputation, train-only scaling, and aligned one-hot encoding.
* The AI advisory layer keeps deterministic rule-based execution as the default mode, while leaving room for human escalation and external model review.

## Final Verification Checklist
* Part 1 generates reproducible CSVs, workbook, SQLite database, reconciliation output, and dashboard PNG images.
* Part 2 produces a valid credit-risk classification pipeline, pricing tiers, and behavioural anomaly detection metrics.
* Part 3 runs deterministic portfolio, disclosure, debate, and DCF analysis scripts without requiring external services.
