"""Analysis agent — quantitative NPV comparison of renewal strategies."""

import asyncio
import logging
from datetime import date

from backend.agents.state import GraphState
from backend.models.schemas import MortgageType, RenewalStrategy, StrategyAnalysis
from backend.services.mortgage_math import (
    calculate_break_penalty,
    calculate_strategy_npv,
    monthly_payment,
)
from backend.services.rate_data import fetch_boc_overnight_rate, fetch_goc_5yr_bond_yield

logger = logging.getLogger(__name__)

# Typical lender spread assumptions (Canadian market)
_FIXED_RENEWAL_SPREAD = 0.0150   # 150 bps over GoC 5yr — posted renewal rate
_FIXED_REWRITE_SPREAD = 0.0125   # 125 bps — borrower actively shopping
_VARIABLE_SPREAD = 0.0100        # 100 bps over overnight — typical variable pricing
_COMPARISON_MONTHS = 60          # 5-year comparison window


async def analysis_node(state: GraphState) -> dict:
    """Run quantitative NPV analysis for all four renewal strategies.

    Fetches current market rates independently (runs in parallel with research_node).
    Writes `strategy_analyses` into the graph state.
    """
    borrower = state["borrower_input"]

    try:
        boc_rate, goc_5yr = await asyncio.gather(
            fetch_boc_overnight_rate(),
            fetch_goc_5yr_bond_yield(),
        )
    except Exception as exc:
        logger.error("analysis_node: rate fetch failed: %s", exc)
        return {"errors": [f"analysis_node: rate fetch failed: {exc}"]}

    remaining_term_years = max(
        (borrower.maturity_date - date.today()).days / 365.25, 0.0
    )

    fixed_renewal_rate = goc_5yr + _FIXED_RENEWAL_SPREAD
    fixed_rewrite_rate = goc_5yr + _FIXED_REWRITE_SPREAD
    variable_rate = boc_rate + _VARIABLE_SPREAD

    analyses: list[StrategyAnalysis] = [
        _renew_fixed(borrower, fixed_renewal_rate, boc_rate),
        _renew_variable(borrower, variable_rate, boc_rate),
        _break_and_rewrite(borrower, fixed_rewrite_rate, boc_rate, remaining_term_years),
        _blend_and_extend(
            borrower, fixed_renewal_rate, boc_rate, remaining_term_years
        ),
    ]

    return {"strategy_analyses": analyses}


def _renew_fixed(borrower, rate: float, discount_rate: float) -> StrategyAnalysis:
    """Renew at maturity into a new 5-year fixed."""
    payment = monthly_payment(borrower.balance, rate, borrower.amortization_years_remaining)
    total_interest = payment * _COMPARISON_MONTHS - _principal_paid(
        borrower.balance, rate, _COMPARISON_MONTHS
    )
    npv = calculate_strategy_npv(payment, 0.0, discount_rate, _COMPARISON_MONTHS)
    return StrategyAnalysis(
        strategy=RenewalStrategy.RENEW_FIXED,
        estimated_monthly_payment=round(payment, 2),
        total_interest_5yr=round(total_interest, 2),
        break_penalty=0.0,
        net_present_value=round(npv, 2),
        notes=f"New rate: {rate:.2%} (GoC 5yr + 150 bps). No break penalty.",
    )


def _renew_variable(borrower, rate: float, discount_rate: float) -> StrategyAnalysis:
    """Renew at maturity into a variable rate."""
    payment = monthly_payment(borrower.balance, rate, borrower.amortization_years_remaining)
    total_interest = payment * _COMPARISON_MONTHS - _principal_paid(
        borrower.balance, rate, _COMPARISON_MONTHS
    )
    npv = calculate_strategy_npv(payment, 0.0, discount_rate, _COMPARISON_MONTHS)
    return StrategyAnalysis(
        strategy=RenewalStrategy.RENEW_VARIABLE,
        estimated_monthly_payment=round(payment, 2),
        total_interest_5yr=round(total_interest, 2),
        break_penalty=0.0,
        net_present_value=round(npv, 2),
        notes=(
            f"New rate: {rate:.2%} (overnight + 100 bps). "
            "NPV assumes rate holds flat — actual payments will vary with BoC decisions."
        ),
    )


def _break_and_rewrite(
    borrower, rate: float, discount_rate: float, remaining_term_years: float
) -> StrategyAnalysis:
    """Break the current mortgage early and rewrite at today's best rate."""
    penalty = calculate_break_penalty(
        balance=borrower.balance,
        contract_rate=borrower.contract_rate,
        current_posted_rate=rate,
        remaining_term_years=remaining_term_years,
        mortgage_type=borrower.mortgage_type.value,
    )
    payment = monthly_payment(borrower.balance, rate, borrower.amortization_years_remaining)
    total_interest = payment * _COMPARISON_MONTHS - _principal_paid(
        borrower.balance, rate, _COMPARISON_MONTHS
    )
    npv = calculate_strategy_npv(payment, penalty, discount_rate, _COMPARISON_MONTHS)
    return StrategyAnalysis(
        strategy=RenewalStrategy.BREAK_AND_REWRITE,
        estimated_monthly_payment=round(payment, 2),
        total_interest_5yr=round(total_interest, 2),
        break_penalty=round(penalty, 2),
        net_present_value=round(npv, 2),
        notes=(
            f"New rate: {rate:.2%} (GoC 5yr + 125 bps, shopping discount). "
            f"Break penalty: ${penalty:,.0f}. "
            f"{remaining_term_years:.1f} years remaining on current term."
        ),
    )


def _blend_and_extend(
    borrower, renewal_rate: float, discount_rate: float, remaining_term_years: float
) -> StrategyAnalysis:
    """Blend current contract rate with renewal rate and extend to a new 5-year term."""
    extension_years = max(5.0 - remaining_term_years, 0.0)
    if remaining_term_years + extension_years > 0:
        blended_rate = (
            borrower.contract_rate * remaining_term_years
            + renewal_rate * extension_years
        ) / (remaining_term_years + extension_years)
    else:
        blended_rate = renewal_rate

    payment = monthly_payment(borrower.balance, blended_rate, borrower.amortization_years_remaining)
    total_interest = payment * _COMPARISON_MONTHS - _principal_paid(
        borrower.balance, blended_rate, _COMPARISON_MONTHS
    )
    npv = calculate_strategy_npv(payment, 0.0, discount_rate, _COMPARISON_MONTHS)
    return StrategyAnalysis(
        strategy=RenewalStrategy.BLEND_AND_EXTEND,
        estimated_monthly_payment=round(payment, 2),
        total_interest_5yr=round(total_interest, 2),
        break_penalty=0.0,
        net_present_value=round(npv, 2),
        notes=(
            f"Blended rate: {blended_rate:.2%} "
            f"({remaining_term_years:.1f}yr at {borrower.contract_rate:.2%} + "
            f"{extension_years:.1f}yr at {renewal_rate:.2%}). "
            "Available through existing lender only — limited rate negotiation."
        ),
    )


def _principal_paid(balance: float, annual_rate: float, months: int) -> float:
    """Approximate principal paid over `months` months."""
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return balance  # all payment is principal
    payment = balance * monthly_rate / (1 - (1 + monthly_rate) ** -(months))
    remaining = balance * (1 + monthly_rate) ** months - payment * (
        (1 + monthly_rate) ** months - 1
    ) / monthly_rate
    return max(balance - remaining, 0.0)
