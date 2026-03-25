"""Tests for mortgage_math service."""

import pytest
from backend.services.mortgage_math import (
    calculate_break_penalty,
    calculate_ird,
    calculate_three_month_interest,
    monthly_payment,
)


def test_ird_basic() -> None:
    penalty = calculate_ird(
        balance=400_000,
        contract_rate=0.05,
        current_posted_rate=0.03,
        remaining_term_years=3.0,
    )
    assert penalty == pytest.approx(24_000.0)


def test_three_month_interest() -> None:
    penalty = calculate_three_month_interest(balance=400_000, contract_rate=0.05)
    assert penalty == pytest.approx(5_000.0)


def test_break_penalty_fixed_uses_max() -> None:
    # IRD > 3-month interest → should return IRD
    penalty = calculate_break_penalty(
        balance=400_000,
        contract_rate=0.05,
        current_posted_rate=0.03,
        remaining_term_years=3.0,
        mortgage_type="fixed",
    )
    assert penalty == pytest.approx(24_000.0)


def test_break_penalty_variable_uses_three_month() -> None:
    penalty = calculate_break_penalty(
        balance=400_000,
        contract_rate=0.05,
        current_posted_rate=0.03,
        remaining_term_years=3.0,
        mortgage_type="variable",
    )
    assert penalty == pytest.approx(5_000.0)


def test_monthly_payment_zero_rate() -> None:
    payment = monthly_payment(balance=240_000, annual_rate=0.0, amortization_years=20)
    assert payment == pytest.approx(1_000.0)
