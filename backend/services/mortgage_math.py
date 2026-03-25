"""Mortgage math — amortization, break penalty, and IRD calculations.

All monetary values in CAD. Rates as decimals (0.05, not 5%).
"""


def calculate_ird(
    balance: float,
    contract_rate: float,
    current_posted_rate: float,
    remaining_term_years: float,
) -> float:
    """Calculate the Interest Rate Differential (IRD) penalty.

    IRD = (contract_rate - current_posted_rate) * balance * remaining_term_years

    Args:
        balance: Outstanding mortgage balance in CAD.
        contract_rate: Original contract interest rate as a decimal.
        current_posted_rate: Current posted rate for equivalent term as a decimal.
        remaining_term_years: Years remaining in the current term.

    Returns:
        IRD penalty amount in CAD.
    """
    return (contract_rate - current_posted_rate) * balance * remaining_term_years


def calculate_three_month_interest(balance: float, contract_rate: float) -> float:
    """Calculate the 3-month interest penalty.

    Args:
        balance: Outstanding mortgage balance in CAD.
        contract_rate: Contract interest rate as a decimal.

    Returns:
        3-month interest penalty in CAD.
    """
    return balance * contract_rate * (3 / 12)


def calculate_break_penalty(
    balance: float,
    contract_rate: float,
    current_posted_rate: float,
    remaining_term_years: float,
    mortgage_type: str,
) -> float:
    """Calculate the break penalty for a mortgage.

    For fixed-rate: max(IRD, 3-month interest).
    For variable-rate: 3-month interest.

    Args:
        balance: Outstanding mortgage balance in CAD.
        contract_rate: Original contract interest rate as a decimal.
        current_posted_rate: Current posted rate for equivalent term as a decimal.
        remaining_term_years: Years remaining in the current term.
        mortgage_type: "fixed" or "variable".

    Returns:
        Break penalty amount in CAD.
    """
    three_month = calculate_three_month_interest(balance, contract_rate)
    if mortgage_type == "variable":
        return three_month
    ird = calculate_ird(balance, contract_rate, current_posted_rate, remaining_term_years)
    return max(ird, three_month)


def calculate_strategy_npv(
    monthly_payment_amount: float,
    break_penalty: float,
    annual_discount_rate: float,
    months: int = 60,
) -> float:
    """Calculate the net present value of a mortgage renewal strategy.

    NPV is expressed as a negative number (total cost in present-value terms).
    Higher (less negative) NPV means the strategy is cheaper.

    Args:
        monthly_payment_amount: Fixed monthly payment in CAD.
        break_penalty: Upfront break cost at t=0 in CAD (0 if no break required).
        annual_discount_rate: Annual discount rate as a decimal (use BoC overnight rate).
        months: Number of months in the comparison window (default 60 = 5 years).

    Returns:
        NPV as a negative float. Less negative = better.
    """
    monthly_rate = annual_discount_rate / 12
    if monthly_rate == 0:
        pv_payments = monthly_payment_amount * months
    else:
        pv_payments = monthly_payment_amount * (1 - (1 + monthly_rate) ** -months) / monthly_rate
    return -(pv_payments + break_penalty)


def monthly_payment(
    balance: float, annual_rate: float, amortization_years: int
) -> float:
    """Calculate monthly mortgage payment.

    Args:
        balance: Mortgage principal in CAD.
        annual_rate: Annual interest rate as a decimal.
        amortization_years: Total amortization period in years.

    Returns:
        Monthly payment amount in CAD.
    """
    monthly_rate = annual_rate / 12
    n = amortization_years * 12
    if monthly_rate == 0:
        return balance / n
    return balance * monthly_rate / (1 - (1 + monthly_rate) ** -n)
