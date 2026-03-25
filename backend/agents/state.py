"""LangGraph state definitions for the mortgage renewal agent graph."""

import operator
from typing import Annotated, TypedDict

from backend.models.schemas import BorrowerInput, RecommendationOutput, StrategyAnalysis


class RateContext(TypedDict):
    """Structured output from the research agent."""

    boc_rate: float
    goc_5yr_yield: float
    corra: float
    rate_environment_summary: str  # 2-sentence summary
    boc_outlook: str  # "cutting" | "holding" | "hiking" | "uncertain"
    renewal_implication: str  # what this means for a borrower renewing in 90 days


class EvaluationResult(TypedDict):
    """Structured output from the evaluator agent."""

    confidence_score: float  # 0.0 – 1.0
    passes_criteria: bool
    flags: list[str]  # issues found, empty if clean
    reasoning: str


class GraphState(TypedDict):
    """Shared state flowing through all nodes in the mortgage renewal graph.

    Parallel branches (research, analysis) write to disjoint keys so no
    reducer is needed beyond the list accumulator on `errors`.
    """

    # Input — set once by run_graph(), read-only for all nodes
    borrower_input: BorrowerInput

    # Research branch output
    rate_context: RateContext | None

    # Analysis branch output
    strategy_analyses: list[StrategyAnalysis] | None

    # Sequential outputs
    recommendation: RecommendationOutput | None
    evaluation: EvaluationResult | None

    # Errors from any node accumulate via reducer
    errors: Annotated[list[str], operator.add]
