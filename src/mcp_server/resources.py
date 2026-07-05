"""MCP resources: read-only summaries under the bookiebreaker:// scheme."""

from mcp_server.server import get_backends, mcp
from mcp_server.tools.edges import render_edges
from mcp_server.tools.performance import render_performance
from mcp_server.tools.slate import render_slate


@mcp.resource("bookiebreaker://edges/current", mime_type="text/markdown")
async def current_edges_resource() -> str:
    """Summary of the freshest detected +EV edges."""
    edges = await get_backends().agent.list_edges(limit=25)
    return render_edges(edges)


@mcp.resource("bookiebreaker://performance/summary", mime_type="text/markdown")
async def performance_summary_resource() -> str:
    """All-time paper-trading performance snapshot."""
    perf = await get_backends().emulator.performance()
    return render_performance(perf, "all_time", None)


@mcp.resource("bookiebreaker://games/today", mime_type="text/markdown")
async def todays_games_resource() -> str:
    """Today's slate with predictions and edge counts."""
    slate = await get_backends().agent.get_slate()
    return render_slate(slate)
