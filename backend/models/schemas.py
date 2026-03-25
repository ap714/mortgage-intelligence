"""Pydantic models for borrower inputs and outputs.

All monetary values in CAD. Rates as decimals. Dates in ISO 8601.
"""

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RiskTolerance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MortgageType(str, Enum):
    FIXED = "fixed"
    VARIABLE = "variable"


class BorrowerInput(BaseModel):
    """Input parameters provided by the broker / borrower."""

    balance: float = Field(..., gt=0, description="Outstanding mortgage balance in CAD.")
    contract_rate: float = Field(..., gt=0, lt=1, description="Current contract rate as a decimal.")
    mortgage_type: MortgageType
    maturity_date: date = Field(..., description="Mortgage maturity date (ISO 8601).")
    amortization_years_remaining: int = Field(..., gt=0, description="Years remaining on amortization.")
    risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM


class RenewalStrategy(str, Enum):
    RENEW_FIXED = "renew_fixed"
    RENEW_VARIABLE = "renew_variable"
    BREAK_AND_REWRITE = "break_and_rewrite"
    BLEND_AND_EXTEND = "blend_and_extend"


class StrategyAnalysis(BaseModel):
    """Quantitative analysis for a single renewal strategy."""

    strategy: RenewalStrategy
    estimated_monthly_payment: float
    total_interest_5yr: float
    break_penalty: float
    net_present_value: float
    notes: str = ""


class RecommendationOutput(BaseModel):
    """Final recommendation returned to the broker."""

    recommended_strategy: RenewalStrategy
    rationale: str
    strategies: list[StrategyAnalysis]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    rate_environment_summary: str
    generated_at: date
