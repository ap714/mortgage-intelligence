# Mortgage Renewal Intelligence

Multi-agent AI tool for Canadian mortgage renewal timing analysis.
Stack: Python, FastAPI, LangGraph, Claude API.

## Project Structure

```
backend/     FastAPI app, LangGraph agents, business logic, API routes
frontend/    UI layer
data/        Raw and processed datasets (rate history, scraped data, etc.)
evals/       Evaluation scripts, test cases, benchmarks for agent quality
```

## Backend

- Entry point: `backend/main.py`
- Agents defined with LangGraph; each agent in its own module under `backend/agents/`
- Use the Anthropic SDK for Claude API calls

## Data

- `data/raw/` for unprocessed source data
- `data/processed/` for cleaned/transformed data
- Do not commit large binary files or sensitive PII

## Evals

- Evaluation harness goes in `evals/`
- Each eval should be runnable independently
- Track agent accuracy, latency, and reasoning quality

## Conventions

- Python 3.11+
- Use `uv` for dependency management (`pyproject.toml`)
- Format with `ruff`; type-check with `mypy`
- Environment variables via `.env` (never commit `.env`)
