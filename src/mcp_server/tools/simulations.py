"""get_simulation tool."""

from typing import Annotated, Any

from pydantic import Field

from mcp_server.formatting import kv_section, percent
from mcp_server.server import get_backends, mcp


def render_simulation(run: dict[str, Any]) -> str:
    result: dict[str, Any] = run.get("result") or {}
    return kv_section(
        f"Latest Simulation — game {run.get('game_id')}",
        [
            ("Run ID", str(run.get("simulation_run_id"))),
            ("Status", str(run.get("status"))),
            ("Iterations", str(run.get("iterations_completed"))),
            ("Converged", "yes" if run.get("converged") else "no"),
            ("Home win probability", percent(result.get("home_win_probability"))),
            ("Away win probability", percent(result.get("away_win_probability"))),
            ("Mean total", str(result.get("mean_total", "—"))),
            ("Mean margin (home)", str(result.get("mean_margin", "—"))),
            ("Completed", str(run.get("completed_at"))),
        ],
    )


@mcp.tool
async def get_simulation(
    game_id: Annotated[str, Field(description="statistics-service game UUID.")],
) -> str:
    """Latest Monte Carlo simulation results (win probabilities and score distributions) for a game."""
    run = await get_backends().simulation.latest_for_game(game_id)
    return render_simulation(run)
