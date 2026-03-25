"""LangGraph supervisor graph for mortgage renewal intelligence.

Topology:
    START → supervisor
              ├── research_node  (parallel)
              └── analysis_node  (parallel)
                        └── recommendation_node
                                  └── evaluator_node → END

The supervisor node is a lightweight pass-through that validates input and
initialises state. The graph structure itself handles fan-out and fan-in.
"""

import logging

from langgraph.graph import END, START, StateGraph

from backend.agents.analysis import analysis_node
from backend.agents.evaluator import evaluator_node
from backend.agents.recommendation import recommendation_node
from backend.agents.research import research_node
from backend.agents.state import GraphState
from backend.models.schemas import BorrowerInput, RecommendationOutput

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Supervisor node
# ---------------------------------------------------------------------------

async def supervisor_node(state: GraphState) -> dict:
    """Validate input and log the start of a renewal analysis run.

    Acts as the entry point before fanning out to research and analysis.
    """
    borrower = state["borrower_input"]
    logger.info(
        "Starting renewal analysis | balance=$%.0f | rate=%.2f%% | maturity=%s",
        borrower.balance,
        borrower.contract_rate * 100,
        borrower.maturity_date.isoformat(),
    )
    return {}  # no state mutation — just routing


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Assemble and return the compiled mortgage renewal graph."""
    builder = StateGraph(GraphState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("research", research_node)
    builder.add_node("analysis", analysis_node)
    builder.add_node("recommendation", recommendation_node)
    builder.add_node("evaluator", evaluator_node)

    # Supervisor receives input from START
    builder.add_edge(START, "supervisor")

    # Fan-out: supervisor dispatches research and analysis in parallel
    builder.add_edge("supervisor", "research")
    builder.add_edge("supervisor", "analysis")

    # Fan-in: recommendation waits for both parallel branches to complete
    builder.add_edge(["research", "analysis"], "recommendation")

    # Sequential: evaluator follows recommendation
    builder.add_edge("recommendation", "evaluator")
    builder.add_edge("evaluator", END)

    return builder


# Compiled once at import time — reused across requests
_compiled_graph = build_graph().compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_graph(borrower_input: BorrowerInput) -> RecommendationOutput:
    """Run the full mortgage renewal analysis pipeline.

    Args:
        borrower_input: Validated borrower parameters.

    Returns:
        Final RecommendationOutput with evaluator-calibrated confidence score.

    Raises:
        RuntimeError: If any agent node fails or no recommendation is produced.
    """
    initial_state: GraphState = {
        "borrower_input": borrower_input,
        "rate_context": None,
        "strategy_analyses": None,
        "recommendation": None,
        "evaluation": None,
        "errors": [],
    }

    final_state: GraphState = await _compiled_graph.ainvoke(initial_state)  # type: ignore[assignment]

    if final_state["errors"]:
        raise RuntimeError(
            "Mortgage analysis pipeline failed: " + "; ".join(final_state["errors"])
        )

    recommendation = final_state.get("recommendation")
    if recommendation is None:
        raise RuntimeError("Pipeline completed but produced no recommendation.")

    return recommendation
