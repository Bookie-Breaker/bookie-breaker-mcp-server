"""get_team_stats and get_player_stats tools."""

from typing import Annotated, Any

from pydantic import Field

from mcp_server.formatting import table
from mcp_server.server import get_backends, mcp

MAX_COLUMNS = 10


def render_records(records: Any, title: str) -> str:
    """Generic renderer for stat payloads: list of dicts -> capped table."""
    if isinstance(records, dict):
        records = records.get("teams") or records.get("players") or [records]
    if not records:
        return f"No {title.lower()} found."
    columns: list[str] = []
    for record in records:
        for key in record:
            if key not in columns and not isinstance(record[key], dict | list):
                columns.append(key)
    columns = columns[:MAX_COLUMNS]
    rows = [[str(record.get(column, "—")) for column in columns] for record in records]
    return f"## {title}\n\n" + table(columns, rows)


@mcp.tool
async def get_team_stats(
    league: Annotated[str, Field(description="League, e.g. NBA.")] = "NBA",
    team: Annotated[str | None, Field(description="Team name or abbreviation to filter on.")] = None,
) -> str:
    """Current team statistics (pace, ratings, records) from the statistics service."""
    payload = await get_backends().statistics.team_stats(league=league, team=team)
    return render_records(payload, f"{league} Team Stats")


@mcp.tool
async def get_player_stats(
    league: Annotated[str, Field(description="League, e.g. NBA.")] = "NBA",
    player: Annotated[str | None, Field(description="Player name to filter on.")] = None,
    team_id: Annotated[str | None, Field(description="Filter to one team's roster.")] = None,
) -> str:
    """Current player statistics from the statistics service."""
    payload = await get_backends().statistics.player_stats(league=league, player=player, team_id=team_id)
    return render_records(payload, f"{league} Player Stats")
