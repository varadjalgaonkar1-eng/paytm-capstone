import pandas as pd
from stock_universe import MARKET_RETURN, RISK_FREE_RATE, STOCK_UNIVERSE

# 1. Base Assumptions (Hypothetical Paytm Business Line)
ebit_0 = 1000.0  # INR Cr
tax_rate = 0.25
da_0 = 120.0  # INR Cr
capex_0 = 150.0  # INR Cr
delta_nwc_0 = 40.0  # INR Cr

# Unlevered FCFF Base Formula: EBIT*(1-t) + D&A - CapEx - Delta_NWC
base_fcff = ebit_0 * (1 - tax_rate) + da_0 - capex_0 - delta_nwc_0  # 680 INR Cr

growth_rates = [0.15, 0.12, 0.10, 0.08, 0.06]  # 5-year fade
base_terminal_growth = 0.04  # 4.0%

# 2. WACC Calculation
# Cost of Equity (CAPM using PAYINFRA beta = 1.10)
beta = STOCK_UNIVERSE["PAYINFRA"]["beta"]
cost_of_equity = RISK_FREE_RATE + beta * (MARKET_RETURN - RISK_FREE_RATE)  # 13.6%
cost_of_debt_pretax = 0.09
cost_of_debt_aftertax = cost_of_debt_pretax * (1 - tax_rate)  # 6.75%
weight_equity = 0.80
weight_debt = 0.20

base_wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt_aftertax)  # 12.23%


def compute_dcf(wacc: float, g: float):
    # 5-year projections
    fcffs = []
    current_fcff = base_fcff
    for gr in growth_rates:
        current_fcff *= (1 + gr)
        fcffs.append(current_fcff)

    # Discount FCFFs
    pvs = [f / ((1 + wacc) ** t) for t, f in enumerate(fcffs, 1)]
    pv_explicit = sum(pvs)

    # Terminal Value
    tv = (fcffs[-1] * (1 + g)) / (wacc - g)
    pv_tv = tv / ((1 + wacc) ** 5)

    enterprise_value = pv_explicit + pv_tv
    return enterprise_value


# 3. Build 3x3 Sensitivity Matrix (WACC +- 1%, Growth +- 1%)
wacc_range = [base_wacc - 0.01, base_wacc, base_wacc + 0.01]
g_range = [base_terminal_growth - 0.01, base_terminal_growth, base_terminal_growth + 0.01]

grid = {}
for g in g_range:
    row_vals = []
    for w in wacc_range:
        val = compute_dcf(w, g)
        row_vals.append(round(val, 2))
    grid[f"g = {g:.1%}"] = row_vals

sensitivity_df = pd.DataFrame(
    grid, index=[f"WACC = {w:.2%}" for w in wacc_range]
).T

# 4. EV/EBITDA Cross-Check
ebitda_0 = ebit_0 + da_0  # 1120 INR Cr
target_multiple = 8.5
ev_multiple = ebitda_0 * target_multiple  # 9520 INR Cr
base_ev_dcf = compute_dcf(base_wacc, base_terminal_growth)

if __name__ == "__main__":
    print("=== DCF Valuation Summary ===")
    print(f"Base FCFF: INR {base_fcff:.2f} Cr")
    print(f"Base Cost of Equity: {cost_of_equity:.2%}")
    print(f"Base WACC: {base_wacc:.2%}")
    print(f"Base Terminal Growth Rate: {base_terminal_growth:.2%}")
    print(
        f"Worst-Case Sensitivity Spread (min WACC - max g): "
        f"{(base_wacc - 0.01) - (base_terminal_growth + 0.01):.2%} (Target >= 1.0%)"
    )
    print(f"\nBase Enterprise Value (DCF): INR {base_ev_dcf:,.2f} Cr")
    print(f"EV / EBITDA Implied Valuation (8.5x on {ebitda_0} Cr EBITDA): INR {ev_multiple:,.2f} Cr")
    print(f"DCF vs Multiple Variance: {((base_ev_dcf - ev_multiple) / ev_multiple):.2%}")

    print("\n=== 3x3 DCF Enterprise Value Sensitivity Table (INR Cr) ===")
    print(sensitivity_df.to_string())
