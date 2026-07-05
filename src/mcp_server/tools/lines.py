"""get_lines tool."""

from typing import Annotated, Any

from pydantic import Field

from mcp_server.formatting import american_odds, percent, table
from mcp_server.server import get_backends, mcp


def render_lines(lines: list[dict[str, Any]], title: str) -> str:
    if not lines:
        return "No lines found."
    rows = [
        [
            str(line.get("game_id", "")),
            str(line.get("sportsbook_key", "")),
            str(line.get("market_type", "")),
            str(line.get("selection", "")),
            str(line.get("line_value")) if line.get("line_value") is not None else "—",
            american_odds(line.get("odds_american")),
            percent(line.get("implied_probability")),
            str(line.get("timestamp", "")),
        ]
        for line in lines
    ]
    return f"## {title}\n\n" + table(["Game", "Book", "Market", "Selection", "Line", "Odds", "Implied", "As Of"], rows)


@mcp.tool
async def get_lines(
    league: Annotated[str, Field(description="League, e.g. NBA.")] = "NBA",
    game_external_id: Annotated[str | None, Field(description="lines-service game id to focus on one game.")] = None,
    market_type: Annotated[str | None, Field(description="SPREAD, TOTAL, or MONEYLINE.")] = None,
    include_movement: Annotated[
        bool,
        Field(description="Return the line movement history instead of current lines (requires game_external_id)."),
    ] = False,
    limit: Annotated[int, Field(ge=1, le=200, description="Max snapshots for current lines.")] = 50,
) -> str:
    """Current betting lines across sportsbooks, or one game's line movement history."""
    backends = get_backends()
    if include_movement:
        if not game_external_id:
            return "Line movement requires game_external_id (see the Game column of get_lines output)."
        movement = await backends.lines.movement(game_external_id, market_type=market_type)
        snapshots = movement.get("snapshots", movement) if isinstance(movement, dict) else movement
        return render_lines(snapshots, f"Line Movement — {game_external_id}")
    lines = await backends.lines.current_lines(
        league=league, game_id=game_external_id, market_type=market_type, limit=limit
    )
    return render_lines(lines, f"Current {league} Lines")
