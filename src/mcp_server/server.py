"""FastMCP server definition and backend lifecycle.

Importing this module registers all tools and resources on ``mcp``.
Backends are created lazily from settings so the module imports cleanly
in any transport (stdio, streamable HTTP, in-memory test client).
"""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server.backends import Backends, create_backends
from mcp_server.settings import get_settings

mcp: FastMCP = FastMCP(
    "bookiebreaker",
    instructions=(
        "BookieBreaker is a sports prediction and paper-trading research system. "
        "Use these tools to inspect detected +EV edges, predictions, lines, and paper-trading "
        "performance, to place paper bets, run the prediction pipeline, and ask the LLM analyst. "
        "All money amounts are in units (1u = 1% of starting bankroll); no real money is involved."
    ),
)

_backends: Backends | None = None


def get_backends() -> Backends:
    global _backends
    if _backends is None:
        _backends = create_backends(get_settings())
    return _backends


async def reset_backends() -> None:
    """Close and drop the backend clients (test isolation helper)."""
    global _backends
    if _backends is not None:
        await _backends.aclose()
        _backends = None


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    """Container liveness for the bridge itself; use the get_health tool
    for backend status."""
    return JSONResponse({"status": "healthy", "service": "mcp-server"})


# Tool/resource registration happens via decorators at import time.
from mcp_server import resources  # noqa: E402,F401
from mcp_server.tools import (  # noqa: E402,F401
    analyst,
    betting,
    edges,
    health_tool,
    lines,
    performance,
    pipeline,
    predictions,
    simulations,
    slate,
    stats,
)
