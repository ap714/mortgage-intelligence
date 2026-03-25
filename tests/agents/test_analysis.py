"""Tests for the deterministic analysis agent node."""

from datetime import date, timedelta

import pytest

from backend.models.schemas import BorrowerInput, MortgageType, RenewalStrategy, RiskTolerance
from backend.agents.state import GraphState


def _make_borrower(
    balance: float = 400_000,
    contract_rate: float = 0.05,
    mortgage_type: MortgageType = MortgageType.FIXED,
    months_to_maturity: int = 18,
    amortization_years: int = 20,
    risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM,
) -> BorrowerInput:
    return BorrowerInput(
        balance=balance,
        contract_rate=contract_rate,
        mortgage_type=mortgage_type,
        maturity_date=date.today() + timedelta(days=months_to_maturity * 30),
        amortization_years_remaining=amortization_years,
        risk_tolerance=risk_tolerance,
    )


def _make_state(borrower: BorrowerInput) -> GraphState:
    return {
        "borrower_input": borrower,
        "rate_context": None,
        "strategy_analyses": None,
        "recommendation": None,
        "evaluation": None,
        "errors": [],
    }


def _patch_rates(monkeypatch: pytest.MonkeyPatch, boc: float = 0.045, goc: float = 0.035) -> None:
    async def fake_boc() -> float:
        return boc

    async def fake_goc() -> float:
        return goc

    monkeypatch.setattr("backend.agents.analysis.fetch_boc_overnight_rate", fake_boc)
    monkeypatch.setattr("backend.agents.analysis.fetch_goc_5yr_bond_yield", fake_goc)


@pytest.mark.asyncio
async def test_analysis_returns_all_four_strategies(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_rates(monkeypatch)
    from backend.agents.analysis import analysis_node

    result = await analysis_node(_make_state(_make_borrower()))
    analyses = result["strategy_analyses"]
    assert len(analyses) == 4
    strategies = {s.strategy for s in analyses}
    assert strategies == {
        RenewalStrategy.RENEW_FIXED,
        RenewalStrategy.RENEW_VARIABLE,
        RenewalStrategy.BREAK_AND_REWRITE,
        RenewalStrategy.BLEND_AND_EXTEND,
    }


@pytest.mark.asyncio
async def test_renew_fixed_has_no_break_penalty(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_rates(monkeypatch)
    from backend.agents.analysis import analysis_node

    result = await analysis_node(_make_state(_make_borrower()))
    fixed = next(s for s in result["strategy_analyses"] if s.strategy == RenewalStrategy.RENEW_FIXED)
    assert fixed.break_penalty == 0.0


@pytest.mark.asyncio
async def test_break_and_rewrite_has_positive_penalty_for_fixed(monkeypatch: pytest.MonkeyPatch) -> None:
    # contract_rate (5%) > new posted rate (2.5% + 1.25% = 3.75%) → IRD is positive
    _patch_rates(monkeypatch, boc=0.025, goc=0.025)
    from backend.agents.analysis import analysis_node

    borrower = _make_borrower(contract_rate=0.05, mortgage_type=MortgageType.FIXED, months_to_maturity=24)
    result = await analysis_node(_make_state(borrower))
    brw = next(s for s in result["strategy_analyses"] if s.strategy == RenewalStrategy.BREAK_AND_REWRITE)
    assert brw.break_penalty > 0.0


@pytest.mark.asyncio
async def test_blend_and_extend_has_no_break_penalty(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_rates(monkeypatch)
    from backend.agents.analysis import analysis_node

    result = await analysis_node(_make_state(_make_borrower()))
    blend = next(s for s in result["strategy_analyses"] if s.strategy == RenewalStrategy.BLEND_AND_EXTEND)
    assert blend.break_penalty == 0.0


@pytest.mark.asyncio
async def test_npv_is_negative(monkeypatch: pytest.MonkeyPatch) -> None:
    """NPV is a cost — all values should be negative."""
    _patch_rates(monkeypatch)
    from backend.agents.analysis import analysis_node

    result = await analysis_node(_make_state(_make_borrower()))
    for s in result["strategy_analyses"]:
        assert s.net_present_value < 0, (
            f"{s.strategy} NPV should be negative, got {s.net_present_value}"
        )


@pytest.mark.asyncio
async def test_variable_rate_lower_payment_when_rates_low(monkeypatch: pytest.MonkeyPatch) -> None:
    """When BoC rate is well below GoC 5yr, variable payment should be lower than fixed."""
    _patch_rates(monkeypatch, boc=0.03, goc=0.05)
    from backend.agents.analysis import analysis_node

    result = await analysis_node(_make_state(_make_borrower()))
    analyses = {s.strategy: s for s in result["strategy_analyses"]}
    assert (
        analyses[RenewalStrategy.RENEW_VARIABLE].estimated_monthly_payment
        < analyses[RenewalStrategy.RENEW_FIXED].estimated_monthly_payment
    )
