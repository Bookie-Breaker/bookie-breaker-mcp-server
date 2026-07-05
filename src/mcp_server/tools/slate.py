"""get_slate tool."""

from typing import Annotated, Any

from pydantic import Field

from mcp_server.formatting import points, table
from mcp_server.server import get_backends, mcp


def render_slate(slate: dict[str, Any]) -> str:
    games = slate.get("games", [])
    if not games:
        return f"No games on the slate for {slate.get('date', 'today')}."
    rows = []
    for game in games:
        home = (game.get("home_team") or {}).get("abbreviation", "?")
        away = (game.get("away_team") or {}).get("abbreviation", "?")
        prediction = game.get("prediction")
        edges = game.get("edges", [])
        best_edge = max((e.get("edge_percentage", 0.0) for e in edges), default=None)
        rows.append(
            [
                f"{away} @ {home}",
                str(game.get("scheduled_start", "")),
                str(game.get("status", "")),
                prediction.get("selection", "—") if prediction else "—",
                str(len(edges)),
                points(best_edge) if best_edge is not None else "—",
            ]
        )
    return f"## Slate for {slate.get('date', 'today')}\n\n" + table(
        ["Game", "Start", "Status", "Model Pick", "Edges", "Best Edge"], rows
    )


@mcp.tool
async def get_slate(
    league: Annotated[str | None, Field(description="Filter by league, e.g. NBA.")] = None,
    date: Annotated[str | None, Field(description="Slate date (YYYY-MM-DD); defaults to today.")] = None,
) -> str:
    """Today's (or a given date's) games with prediction summaries and active edge counts."""
    slate = await get_backends().agent.get_slate(league=league, date=date)
    return render_slate(slate)
