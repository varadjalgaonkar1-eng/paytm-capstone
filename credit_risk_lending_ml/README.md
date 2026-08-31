# Part 2: Credit Risk & Lending ML

## Preprocessing & Thin-File Strategy
* **Thin-File Handling:** To preserve all new-to-credit applicants without introducing data leakage, the `is_thin_file` binary flag was engineered directly from the raw dataset prior to splitting.
* **Leakage-Free Imputation:** The median bureau score was calculated exclusively on the training partition (`X_train`) and subsequently used to impute missing values across both `X_train` and `X_test`. All continuous scaling via `StandardScaler` was strictly fitted on `X_train` only.

## Classifier Performance & Anomaly Detection Summary

| Metric | Logistic Regression | Decision Tree | Isolation Forest (Anomaly) |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 0.7600 | 0.6500 | N/A |
| **Precision** | 0.3889 | 0.2222 | N/A |
| **Recall** | 0.3500 | 0.3000 | 73.33% (11/15 BTXNA*) |
| **F1-Score** | 0.3684 | 0.2553 | N/A |
| **ROC-AUC** | 0.7188 | 0.5188 | N/A |

## Risk-Based Pricing Structure
Applicants are assigned to 4 distinct risk tiers based on Logistic Regression predicted default probabilities, demonstrating a monotonic increase in observed default rates across tiers to ensure risk-calibrated interest margins.

## Bias-Awareness Note & Model Governance (Part D)
Even in the absence of explicit protected demographic attributes (e.g., gender, caste, religion), variables such as `monthly_income_inr`, `employment_type`, and `credit_bureau_score` can serve as correlated proxies for socioeconomic status and regional financial exclusion. For instance, gig workers and self-employed applicants frequently lack formal credit bureau scores and experience irregular cash flow profiles, which risks systemic credit suppression if penalized by traditional scoring criteria.

**Governance Workflow:**
1. **Dual-Track Evaluation:** Applications categorized as thin-file (`is_thin_file = 1`) are scored using alternate cash-flow signals (`upi_monthly_inflow_inr` and `bounced_payments_count`) rather than purely bureau-based models.
2. **Maker-Checker Human Escalation:** Any borderline decline for thin-file or gig-economy applicants within Tier 3 is routed to a human credit officer for secondary review of alternate banking telemetry before final rejection.

## Model Deployment Verdict
Logistic Regression is selected for deployment in Paytm Postpaid over the Decision Tree classifier. It provides smooth, well-calibrated default probability outputs that support granular risk-based pricing tiers, delivers higher generalization stability (ROC-AUC), and provides linear coefficient interpretability required for regulatory credit compliance.
