from stock_universe import MARKET_RETURN, RISK_FREE_RATE, STOCK_UNIVERSE


def run_debate(ticker: str = "PAYFIN"):
    stock = STOCK_UNIVERSE[ticker]
    beta = stock["beta"]
    stdev = stock["std_dev"]
    exp_ret = RISK_FREE_RATE + beta * (MARKET_RETURN - RISK_FREE_RATE)
    analyst_ret = stock["analyst_expected_return"]

    # Agent 1: Bull
    bull_arg = (
        f"[Bull Agent]: {ticker} demonstrates substantial capital upside with an expected return of {exp_ret:.1%} "
        f"(analyst target: {analyst_ret:.1%}) and a high beta of {beta:.2f}, positioning it as a prime vehicle to capture economic expansion."
    )

    # Agent 2: Bear
    bear_arg = (
        f"[Bear Agent]: {ticker} presents severe volatility risk with an annualized standard deviation of {stdev:.1%}. "
        f"Its beta of {beta:.2f} amplifies systematic downside shocks, creating unhedged downside vulnerability during market corrections."
    )

    # Agent 3: Synthesizer
    synthesizer = (
        f"[Synthesizer Agent]: While {ticker} offers strong upside beta ({beta:.2f}) aligned with high expected returns ({exp_ret:.1%}), "
        f"its {stdev:.1%} volatility profile necessitates strict portfolio sizing. We recommend limiting exposure to aggressive portfolios and pairing it with low-beta stabilizers."
    )

    return bull_arg, bear_arg, synthesizer


if __name__ == "__main__":
    print("=== Multi-Agent Debate Demo (PAYFIN) ===")
    bull, bear, syn = run_debate("PAYFIN")
    print(bull)
    print("\n" + bear)
    print("\n" + syn)
