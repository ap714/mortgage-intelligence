"""Evaluator agent — scores recommendation quality against defined criteria."""

import json
import logging
import os

import anthropic

from backend.agents.state import EvaluationResult, GraphState
from backend.models.schemas import RenewalStrategy

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"

_SYSTEM = (
    "You are a quality-control reviewer for mortgage renewal recommendations. "
    "Evaluate rigorously and flag any inconsistencies. "
    "Respond only with valid JSON matching the schema provided — no markdown fences."
)

_USER_TEMPLATE = """\
Evaluate the following mortgage renewal recommendation against these criteria:
1. Mathematical consistency — does the recommended strategy match or justify deviation from the best NPV?
2. Risk alignment — is the strategy consistent with the borrower's stated risk tolerance ({risk_tolerance})?
3. Completeness — does the rationale address both the rate environment and the penalty cost?
4. Confidence calibration — is the confidence score ({confidence:.0%}) defensible given the NPV spread between strategies?

Recommendation:
- Recommended strategy: {strategy}
- Confidence: {confidence:.0%}
- Rationale: {rationale}

Strategy NPVs (higher = cheaper):
{npv_lines}

Rate environment context:
{rate_summary}
BoC outlook: {boc_outlook}

Respond with a JSON object:
{{
  "passes_criteria": <true | false>,
  "confidence_score": <revised float 0.0–1.0 reflecting your assessment>,
  "flags": [<list of specific issues found, empty array if none>],
  "reasoning": "<2-3 sentences summarising your evaluation>"
}}"""


async def evaluator_node(state: GraphState) -> dict:
    """Score the recommendation against quality criteria.

    Writes `evaluation` into the graph state.
    """
    recommendation = state.get("recommendation")
    rate_ctx = state.get("rate_context")

    if os.getenv("MOCK_CLAUDE", "").lower() == "true":
        from backend.agents.mock import MOCK_EVALUATION
        logger.info("evaluator_node: using mock Claude response")
        if recommendation:
            recommendation.confidence_score = MOCK_EVALUATION["confidence_score"]
        return {"evaluation": MOCK_EVALUATION}

    if recommendation is None:
        msg = "evaluator_node: no recommendation to evaluate"
        logger.error(msg)
        return {"errors": [msg]}

    npv_lines = "\n".join(
        f"  {s.strategy.value:<22}: ${s.net_present_value:>12,.0f}"
        for s in sorted(recommendation.strategies, key=lambda x: x.net_present_value, reverse=True)
    )

    user_msg = _USER_TEMPLATE.format(
        risk_tolerance=state["borrower_input"].risk_tolerance.value,
        strategy=recommendation.recommended_strategy.value,
        confidence=recommendation.confidence_score,
        rationale=recommendation.rationale,
        npv_lines=npv_lines,
        rate_summary=recommendation.rate_environment_summary,
        boc_outlook=rate_ctx["boc_outlook"] if rate_ctx else "unknown",
    )

    try:
        client = anthropic.AsyncAnthropic()
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=512,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        parsed = json.loads(message.content[0].text)
    except Exception as exc:
        logger.error("evaluator_node: Claude call failed: %s", exc)
        return {"errors": [f"evaluator_node: Claude call failed: {exc}"]}

    evaluation: EvaluationResult = {
        "confidence_score": float(parsed["confidence_score"]),
        "passes_criteria": bool(parsed["passes_criteria"]),
        "flags": parsed.get("flags", []),
        "reasoning": parsed["reasoning"],
    }

    # Propagate the evaluator's calibrated confidence back to the recommendation
    recommendation.confidence_score = evaluation["confidence_score"]

    return {"evaluation": evaluation}
