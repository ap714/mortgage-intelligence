# Mortgage Renewal Intelligence MVP

## What This Is
An AI tool targeting the Canadian mortgage renewal wave (~1.2M renewals).
Takes borrower parameters (mortgage balance, current rate, term remaining,
risk tolerance) and market data (Bank of Canada overnight rate, GoC bond
yields, swap rates) to recommend optimal renewal timing and strategy.

The core insight: most borrowers renew passively at their lender's posted
rate 90 days before maturity. This tool identifies when breaking early,
shopping at renewal, or holding variable produces better outcomes.

## Target User
Independent mortgage brokers who need data-backed talking points for
client renewal conversations.

## Tech Stack
- Python 3.11+ with FastAPI
- LangGraph for multi-agent orchestration
- Anthropic SDK for Claude API calls
- React frontend (single page, minimal)
- uv for dependency management (pyproject.toml)
- ruff for formatting, mypy for type-checking

## Architecture
```
backend/
  main.py              — FastAPI entry point
  agents/
    research.py         — Fetches and summarizes current rate environment
    analysis.py         — Quantitative renewal timing model
    recommendation.py   — Synthesizes research + analysis into advice
    evaluator.py        — Scores recommendation quality
  services/
    rate_data.py        — Bank of Canada API, FRED API for yield curves
    mortgage_math.py    — Amortization, break penalty, IRD calculations
  models/
    schemas.py          — Pydantic models for borrower inputs and outputs
frontend/               — React app
data/
  raw/                  — Unprocessed source data
  processed/            — Cleaned/transformed data
evals/                  — Evaluation framework
```

## Agent Architecture
Supervisor pattern — a coordinator agent routes to specialists:
1. Research Agent: current rate environment, recent BoC decisions, market outlook
2. Analysis Agent: runs quantitative model (NPV comparison of renewal strategies)
3. Recommendation Agent: combines research + analysis into borrower-specific advice
4. Evaluation Agent: scores the recommendation against defined criteria

This mirrors a multi-agent orchestration pattern — supervisor handles
routing, fan-out to specialists, fan-in for final synthesis.

## Domain Logic
- Break penalty = max(IRD, 3-month interest) for fixed; usually 3-month for variable
- IRD = (contract rate - current posted rate) × balance × remaining term
- Renewal strategies to compare: renew fixed, renew variable, break early + rewrite, blend-and-extend
- Data sources: Bank of Canada overnight rate history, GoC 5yr bond yield (proxy for fixed rates), CORRA (Canadian Overnight Repo Rate Average)

## Conventions
- Type hints on everything
- Docstrings on public functions
- Tests in /tests, mirror the src structure
- pytest with async fixtures
- Environment variables via .env (never commit .env)
- Commit messages follow conventional commits
- Do not commit large binary files or PII

## Important
- All monetary values in CAD
- Rates expressed as decimals (0.05 not 5%)
- Dates in ISO 8601 format
- Run pytest before suggesting any PR