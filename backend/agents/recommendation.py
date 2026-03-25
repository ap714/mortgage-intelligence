"""Recommendation agent — synthesizes research + analysis into borrower advice."""

import json
import logging
import os
from datetime import date

import anthropic

from backend.agents.state import GraphState
from backend.models.schemas import RecommendationOutput, RenewalStrategy, StrategyAnalysis

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"

_SYSTEM = (
    "You are a licensed Canadian mortgage advisor giving data-backed renewal advice "
    "to an independent mortgage broker. Be specific, reference the numbers, and be concise. "
    "Respond only with valid JSON matching the schema provided — no markdown fences."
)

_USER_TEMPLATE = """\
Borrower profile:
- Outstanding balance: ${balance:,.0f} CAD
- Current contract rate: {contract_rate:.2%} ({mortgage_type})
- Maturity date: {maturity_date}
- Amortization remaining: {amortization_years} years
- Risk tolerance: {risk_tolerance}

Rate environment:
{rate_summary}
BoC outlook: {boc_outlook}
{renewal_implication}

Quantitative analysis (5-year comparison, lower absolute NPV = more expensive):
{strategy_table}

Respond with a JSON object matching this exact schema:
{{
  "recommended_strategy": "<one of: renew_fixed | renew_variable | break_and_rewrite | blend_and_extend>",
  "rationale": "<3-4 sentences explaining why this strategy is optimal for this borrower>",
  "confidence_score": <float 0.0–1.0>
}}

Base your recommendation on the NPV analysis, the borrower's risk tolerance, and the rate outlook."""


def _format_strategy_table(strategies: list[StrategyAnalysis]) -> str:
    lines = []
    for s in sorted(strategies, key=lambda x: x.net_present_value, reverse=True):
        lines.append(
            f"  {s.strategy.value:<22} | payment ${s.estimated_monthly_payment:>8,.0f}/mo "
            f"| 5yr interest ${s.total_interest_5yr:>10,.0f} "
            f"| penalty ${s.break_penalty:>8,.0f} "
            f"| NPV ${s.net_present_value:>12,.0f}"
        )
    return "\n".join(lines)


async def recommendation_node(state: GraphState) -> dict:
    """Synthesise research context and quantitative analysis into a recommendation.

    Expects both `rate_context` and `strategy_analyses` to be populated (fan-in).
    Writes `recommendation` into the graph state.
    """
    rate_ctx = state.get("rate_context")
    analyses = state.get("strategy_analyses")
    borrower = state["borrower_input"]

    if os.getenv("MOCK_CLAUDE", "").lower() == "true":
        from backend.agents.mock import MOCK_RECOMMENDATION_PARSED
        logger.info("recommendation_node: using mock Claude response")
        parsed = MOCK_RECOMMENDATION_PARSED
        recommendation = RecommendationOutput(
            recommended_strategy=RenewalStrategy(parsed["recommended_strategy"]),
            rationale=parsed["rationale"],
            strategies=analyses or [],
            confidence_score=float(parsed["confidence_score"]),
            rate_environment_summary=rate_ctx["rate_environment_summary"] if rate_ctx else "",
            generated_at=date.today(),
        )
        return {"recommendation": recommendation}

    if rate_ctx is None or analyses is None:
        msg = "recommendation_node: missing rate_context or strategy_analyses"
        logger.error(msg)
        return {"errors": [msg]}

    strategy_table = _format_strategy_table(analyses)
    user_msg = _USER_TEMPLATE.format(
        balance=borrower.balance,
        contract_rate=borrower.contract_rate,
        mortgage_type=borrower.mortgage_type.value,
        maturity_date=borrower.maturity_date.isoformat(),
        amortization_years=borrower.amortization_years_remaining,
        risk_tolerance=borrower.risk_tolerance.value,
        rate_summary=rate_ctx["rate_environment_summary"],
        boc_outlook=rate_ctx["boc_outlook"],
        renewal_implication=rate_ctx["renewal_implication"],
        strategy_table=strategy_table,
    )

    try:
        client = anthropic.AsyncAnthropic()
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=1024,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        parsed = json.loads(message.content[0].text)
    except Exception as exc:
        logger.error("recommendation_node: Claude call failed: %s", exc)
        return {"errors": [f"recommendation_node: Claude call failed: {exc}"]}

    recommendation = RecommendationOutput(
        recommended_strategy=RenewalStrategy(parsed["recommended_strategy"]),
        rationale=parsed["rationale"],
        strategies=analyses,
        confidence_score=float(parsed["confidence_score"]),
        rate_environment_summary=rate_ctx["rate_environment_summary"],
        generated_at=date.today(),
    )
    return {"recommendation": recommendation}
