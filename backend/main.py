"""FastAPI entry point for Mortgage Renewal Intelligence."""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.agents.graph import run_graph
from backend.models.schemas import BorrowerInput, RecommendationOutput

app = FastAPI(title="Mortgage Renewal Intelligence", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendationOutput)
async def recommend(borrower: BorrowerInput) -> RecommendationOutput:
    """Run the full renewal analysis pipeline and return a recommendation.

    Accepts borrower parameters, fetches live rate data, runs quantitative
    analysis across all four renewal strategies, and returns Claude's
    borrower-specific recommendation with an evaluator-calibrated confidence score.
    """
    try:
        return await run_graph(borrower)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
