"""get_performance tool."""

from typing import Annotated, Any

from pydantic import Field

from mcp_server.formatting import kv_section, percent, units
from mcp_server.server import get_backends, mcp


def render_performance(perf: dict[str, Any], window: str, league: str | None) -> str:
    scope = f"{league} " if league else ""
    return kv_section(
        f"{scope}Performance ({window})",
        [
            (
                "Bets",
                f"{perf.get('total_bets', 0)} ({perf.get('total_wins', 0)}W-"
                f"{perf.get('total_losses', 0)}L-{perf.get('total_pushes', 0)}P)",
            ),
            ("Win rate", percent(perf.get("win_rate"))),
            ("ROI", percent(perf.get("roi"))),
            ("Profit", units(perf.get("total_profit_units"))),
            ("Wagered", f"{perf.get('total_wagered_units', 0)}u"),
            ("Avg edge at placement", f"{perf.get('avg_edge_percentage', 0)}%"),
            ("Avg CLV", percent(perf.get("avg_clv"), 2)),
        ],
    )


@mcp.tool
async def get_performance(
    window: Annotated[str, Field(description="daily, weekly, monthly, or all_time.")] = "all_time",
    league: Annotated[str | None, Field(description="Filter by league.")] = None,
) -> str:
    """Paper-trading performance: ROI, win rate, profit, and closing-line value."""
    perf = await get_backends().emulator.performance(window=window, league=league)
    return render_performance(perf, window, league)
