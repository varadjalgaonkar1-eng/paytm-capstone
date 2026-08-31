import math
import os
from investor_profiles import INVESTOR_PROFILES
from stock_universe import MARKET_RETURN, RISK_FREE_RATE, STOCK_UNIVERSE

MOCK_LLM = os.getenv("MOCK_LLM", "1") == "1"

# 1. Tool Call Simulation
def get_stock_data(ticker: str) -> dict:
    if ticker not in STOCK_UNIVERSE:
        raise ValueError(f"Ticker {ticker} not found in STOCK_UNIVERSE")
    return STOCK_UNIVERSE[ticker]

# 2. Agent Execution Loop
def run_advisory_agent(investor: dict) -> dict:
    inv_id = investor["investor_id"]
    risk_tol = investor["risk_tolerance"]

    # Stage 1: Think (Prescribed Lookup Mapping)
    if risk_tol == "Conservative":
        tickers = ["PAYBOND", "PAYGOLD", "PAYRETAIL"]
    elif risk_tol == "Moderate":
        tickers = ["PAYRETAIL", "PAYINFRA", "PAYGOLD"]
    elif risk_tol == "Aggressive":
        tickers = ["PAYTECH", "PAYFIN", "PAYINFRA"]
    else:
        raise ValueError(f"Unknown risk tolerance: {risk_tol}")

    weights = [1 / 3, 1 / 3, 1 / 3]

    # Stage 2: Act (Tool Calls)
    stock_data = [get_stock_data(t) for t in tickers]

    # Stage 3: Observe & Decide
    # CAPM Expected Return per stock: E(R) = Rf + Beta * (Rm - Rf)
    capm_returns = [
        RISK_FREE_RATE + d["beta"] * (MARKET_RETURN - RISK_FREE_RATE)
        for d in stock_data
    ]
    portfolio_return = sum(w * r for w, r in zip(weights, capm_returns))

    # Portfolio Variance with pairwise rho = 0.3
    rho = 0.3
    stdevs = [d["std_dev"] for d in stock_data]
    var_p = sum((w**2) * (s**2) for w, s in zip(weights, stdevs))

    # Cross-terms: 2 * w_i * w_j * rho * s_i * s_j
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            var_p += 2 * weights[i] * weights[j] * rho * stdevs[i] * stdevs[j]

    portfolio_std = math.sqrt(var_p)

    # Human-in-the-Loop Escalation (> 20.0% threshold)
    escalation = portfolio_std > 0.20
    status = (
        "ESCALATED_TO_HUMAN_ADVISOR" if escalation else "RECOMMENDATION_FINALIZED"
    )

    # Gated Narrative Generation
    if MOCK_LLM:
        narrative = (
            f"For {risk_tol} investor {inv_id}, we recommend an equal-weighted"
            f" allocation across {', '.join(tickers)} with a CAPM-expected"
            f" portfolio return of {portfolio_return:.2%} and an annual volatility"
            f" of {portfolio_std:.2%}."
        )
    else:
        narrative = f"[LLM Mode] Evaluated {inv_id} ({risk_tol}): Recommended {tickers} with E(R) {portfolio_return:.2%} and StDev {portfolio_std:.2%}."

    return {
        "investor_id": inv_id,
        "risk_tolerance": risk_tol,
        "allocated_tickers": tickers,
        "capm_expected_return": portfolio_return,
        "portfolio_std_dev": portfolio_std,
        "status": status,
        "narrative": narrative,
    }


if __name__ == "__main__":
    print("=== Portfolio Advisory Agent Run Transcripts ===")
    for inv in INVESTOR_PROFILES:
        res = run_advisory_agent(inv)
        print(
            f"\n[{res['investor_id']}] {res['risk_tolerance']} | Status:"
            f" {res['status']}"
        )
        print(f"Allocations: {res['allocated_tickers']}")
        print(
            f"Expected Return: {res['capm_expected_return']:.2%} | Volatility:"
            f" {res['portfolio_std_dev']:.2%}"
        )
        print(f"Narrative: {res['narrative']}")
