"""run_pipeline and get_pipeline_status tools."""

from typing import Annotated

from pydantic import Field

from mcp_server.formatting import kv_section
from mcp_server.server import get_backends, mcp


@mcp.tool
async def run_pipeline(
    league: Annotated[str | None, Field(description="League to run, e.g. NBA. Omit for all leagues.")] = None,
    auto_bet: Annotated[bool, Field(description="Auto-place paper bets on actionable edges.")] = True,
) -> str:
    """Trigger a prediction pipeline run (simulate -> predict -> detect edges -> auto-bet).

    Returns immediately; poll get_pipeline_status with the returned run id.
    """
    accepted = await get_backends().agent.run_pipeline(league=league, auto_bet=auto_bet)
    return kv_section(
        "Pipeline Run Accepted",
        [
            ("Run ID", str(accepted.get("pipeline_run_id"))),
            ("Status", str(accepted.get("status"))),
            ("League", str(accepted.get("league") or "ALL")),
            ("Games queued", str(accepted.get("games_queued"))),
            ("Started", str(accepted.get("started_at"))),
        ],
    )


@mcp.tool
async def get_pipeline_status(
    pipeline_run_id: Annotated[str, Field(description="Run UUID from run_pipeline.")],
) -> str:
    """Status and per-step outcome of a pipeline run."""
    run = await get_backends().agent.get_pipeline_run(pipeline_run_id)
    steps = run.get("steps", {})
    step_lines = "\n".join(
        f"- **{name}:** {detail.get('status', detail) if isinstance(detail, dict) else detail}"
        for name, detail in steps.items()
    )
    summary = kv_section(
        f"Pipeline Run {run.get('pipeline_run_id')}",
        [
            ("Status", str(run.get("status"))),
            ("Trigger", str(run.get("trigger"))),
            ("League", str(run.get("league") or "ALL")),
            ("Games processed", str(run.get("games_processed"))),
            ("Edges found", str(run.get("edges_found"))),
            ("Bets placed", str(run.get("bets_placed"))),
            ("Error", str(run.get("error") or "none")),
        ],
    )
    return f"{summary}\n\n## Steps\n\n{step_lines}" if step_lines else summary
