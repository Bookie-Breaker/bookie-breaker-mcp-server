"""get_health tool: fan-out liveness across all backends."""

import asyncio

from mcp_server.formatting import table
from mcp_server.server import get_backends, mcp


@mcp.tool
async def get_health() -> str:
    """Health of every BookieBreaker backend service this server bridges to."""
    backends = get_backends()
    named = [
        ("agent", backends.agent),
        ("lines-service", backends.lines),
        ("statistics-service", backends.statistics),
        ("simulation-engine", backends.simulation),
        ("prediction-engine", backends.prediction),
        ("bookie-emulator", backends.emulator),
    ]
    results = await asyncio.gather(*(backend.is_healthy() for _, backend in named))
    rows = [
        [name, "healthy" if ok else "unhealthy", backend.base_url]
        for (name, backend), ok in zip(named, results, strict=True)
    ]
    status = "All services healthy." if all(results) else "Some services are degraded."
    return f"## Backend Health\n\n{status}\n\n" + table(["Service", "Status", "URL"], rows)
