"""Mock Claude responses for local development without an API key.

Set MOCK_CLAUDE=true in .env to activate.
"""

from backend.agents.state import RateContext, EvaluationResult

MOCK_RATE_CONTEXT: RateContext = {
    "boc_rate": 0.0295,
    "goc_5yr_yield": 0.0318,
    "corra": 0.0290,
    "rate_environment_summary": (
        "The Bank of Canada has held its overnight rate at 2.95% following a prolonged easing cycle, "
        "with GoC 5-year bond yields at 3.18% reflecting market expectations of a soft landing. "
        "Inflation has returned close to the 2% target and the labour market is moderating."
    ),
    "boc_outlook": "holding",
    "renewal_implication": (
        "Borrowers renewing in the next 90 days are entering a more favourable rate environment than "
        "two years ago — locking into a 5-year fixed now captures near-cycle-low fixed rates, "
        "while variable offers limited additional upside given the BoC's neutral stance."
    ),
}

MOCK_RECOMMENDATION_PARSED = {
    "recommended_strategy": "renew_fixed",
    "rationale": (
        "With the Bank of Canada holding at 2.95% and fixed rates near cycle lows, locking into a "
        "5-year fixed eliminates rate risk at an attractive level. The borrower's medium risk tolerance "
        "supports payment certainty over variable upside. The break-and-rewrite penalty erodes most of "
        "the rate advantage, and blend-and-extend offers a blended rate that is materially worse than "
        "the current posted renewal rate."
    ),
    "confidence_score": 0.81,
}

MOCK_EVALUATION: EvaluationResult = {
    "confidence_score": 0.79,
    "passes_criteria": True,
    "flags": [],
    "reasoning": (
        "The recommended strategy aligns with the best NPV outcome and is consistent with medium risk "
        "tolerance. The rationale addresses both the rate environment and the break penalty cost. "
        "Confidence trimmed slightly to reflect uncertainty in the BoC's next move."
    ),
}
