"""Research agent — fetches and summarizes the current rate environment."""

import asyncio
import logging

import anthropic

from backend.agents.state import GraphState, RateContext
from backend.services.rate_data import (
    fetch_boc_overnight_rate,
    fetch_boc_overnight_rate_history,
    fetch_corra,
    fetch_goc_5yr_bond_yield,
)

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"

_SYSTEM = (
    "You are a Canadian mortgage rate analyst. Be concise and factual. "
    "Respond only in the JSON format requested — no markdown, no prose outside the JSON."
)

_USER_TEMPLATE = """\
Current rates (as of today):
- Bank of Canada overnight rate target: {boc_rate:.2%}
- GoC 5-year benchmark bond yield: {goc_5yr:.2%}
- CORRA: {corra:.2%}

Recent 12-month overnight rate history (date → rate):
{history_lines}

Respond with a JSON object containing exactly these keys:
{{
  "rate_environment_summary": "<2-sentence factual summary of the current rate environment>",
  "boc_outlook": "<one of: cutting | holding | hiking | uncertain>",
  "renewal_implication": "<1-2 sentences on what this means for a borrower renewing in the next 90 days>"
}}"""


async def research_node(state: GraphState) -> dict:
    """Fetch current rate data and call Claude for a market outlook summary.

    Writes `rate_context` into the graph state.
    """
    try:
        boc_rate, goc_5yr, corra, history = await asyncio.gather(
            fetch_boc_overnight_rate(),
            fetch_goc_5yr_bond_yield(),
            fetch_corra(),
            fetch_boc_overnight_rate_history(),
        )
    except Exception as exc:
        logger.error("research_node: rate fetch failed: %s", exc)
        return {"errors": [f"research_node: rate fetch failed: {exc}"]}

    # Summarise last 12 observations for the prompt (most recent first)
    recent = history[-12:]
    history_lines = "\n".join(
        f"  {obs['date']}: {float(obs['rate']):.2%}" for obs in recent
    )

    user_msg = _USER_TEMPLATE.format(
        boc_rate=boc_rate,
        goc_5yr=goc_5yr,
        corra=corra,
        history_lines=history_lines,
    )

    try:
        client = anthropic.AsyncAnthropic()
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=512,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        import json
        parsed = json.loads(message.content[0].text)
    except Exception as exc:
        logger.error("research_node: Claude call failed: %s", exc)
        return {"errors": [f"research_node: Claude call failed: {exc}"]}

    rate_context: RateContext = {
        "boc_rate": boc_rate,
        "goc_5yr_yield": goc_5yr,
        "corra": corra,
        "rate_environment_summary": parsed["rate_environment_summary"],
        "boc_outlook": parsed["boc_outlook"],
        "renewal_implication": parsed["renewal_implication"],
    }
    return {"rate_context": rate_context}
