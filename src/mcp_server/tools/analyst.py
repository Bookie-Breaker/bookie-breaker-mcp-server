"""ask_analyst tool -> agent POST /api/v1/agent/analysis."""

from typing import Annotated

from pydantic import Field

from mcp_server.server import get_backends, mcp


def infer_analysis_type(game_id: str | None, edge_id: str | None) -> str:
    if edge_id:
        return "EDGE_BREAKDOWN"
    if game_id:
        return "GAME_PREVIEW"
    return "PERFORMANCE_REVIEW"


@mcp.tool
async def ask_analyst(
    question: Annotated[str, Field(description="The question for the LLM analyst.")],
    game_id: Annotated[str | None, Field(description="Game UUID to scope the question to a game preview.")] = None,
    edge_id: Annotated[str | None, Field(description="Edge UUID to scope the question to an edge breakdown.")] = None,
    analysis_type: Annotated[
        str | None,
        Field(description="Override: GAME_PREVIEW, EDGE_BREAKDOWN, or PERFORMANCE_REVIEW. Inferred when omitted."),
    ] = None,
) -> str:
    """Ask the BookieBreaker LLM analyst about an edge, a game, or overall performance.

    Slow (LLM generation, up to ~2 minutes). Scope with edge_id or game_id
    for grounded answers.
    """
    resolved_type = analysis_type or infer_analysis_type(game_id, edge_id)
    analysis = await get_backends().agent.create_analysis(
        analysis_type=resolved_type, game_id=game_id, edge_id=edge_id, question=question
    )
    footer = f"\n\n---\n*{analysis.get('model_used')} — analysis {analysis.get('id')}*"
    return f"# {analysis.get('title')}\n\n{analysis.get('content')}{footer}"
