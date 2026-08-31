import pandas as pd


def reconcile_payments(ledger_df: pd.DataFrame, gateway_df: pd.DataFrame):
    # 1. Missing in Gateway
    missing_in_gateway = ledger_df[
        ~ledger_df["transaction_id"].isin(gateway_df["transaction_id"])
    ].copy()

    # 2. Missing in Ledger (Extra in Gateway)
    missing_in_ledger = gateway_df[
        ~gateway_df["transaction_id"].isin(ledger_df["transaction_id"])
    ].copy()

    # Common transactions
    common_ids = set(ledger_df["transaction_id"]).intersection(
        set(gateway_df["transaction_id"])
    )
    l_common = ledger_df[ledger_df["transaction_id"].isin(common_ids)].set_index(
        "transaction_id"
    )
    g_common = gateway_df[
        gateway_df["transaction_id"].isin(common_ids)
    ].set_index("transaction_id")

    # 3. Amount Mismatches
    merged = l_common.join(
        g_common, lsuffix="_ledger", rsuffix="_gateway", how="inner"
    )
    amt_diff = merged[
        merged["amount_inr_ledger"] != merged["amount_inr_gateway"]
    ].copy()
    amt_diff["difference_inr"] = (
        amt_diff["amount_inr_gateway"] - amt_diff["amount_inr_ledger"]
    )

    # 4. Status Mismatches
    status_diff = merged[
        merged["status_ledger"] != merged["status_gateway"]
    ].copy()

    return missing_in_gateway, missing_in_ledger, amt_diff, status_diff


if __name__ == "__main__":
    ledger = pd.read_csv("ledger.csv")
    gateway = pd.read_csv("gateway_export.csv")

    missing_gw, missing_led, amt_mismatch, status_mismatch = reconcile_payments(
        ledger, gateway
    )

    print("=== Payment Reconciliation Report ===")
    print(
        f"1. Missing in Gateway: {len(missing_gw)} (Expected ~5% of"
        f" {len(ledger)}: {round(0.05 * len(ledger))})"
    )
    print(
        f"2. Missing in Ledger (Extra in GW): {len(missing_led)} (Expected ~2% of"
        f" {len(ledger)}: {round(0.02 * len(ledger))})"
    )
    print(
        f"3. Amount Mismatches: {len(amt_mismatch)} (Expected ~3% of"
        f" {len(ledger)}: {round(0.03 * len(ledger))})"
    )
    print(
        f"4. Status Mismatches: {len(status_mismatch)} (Expected ~2% of"
        f" {len(ledger)}: {round(0.02 * len(ledger))})"
    )
