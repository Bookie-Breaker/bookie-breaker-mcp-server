"""Lines service client (port 8001): current lines and movement."""

from typing import Any

from mcp_server.backends.base import BackendClient


class LinesBackend(BackendClient):
    service_name = "lines-service"
    health_path = "/api/v1/lines/health"

    async def current_lines(
        self,
        league: str = "NBA",
        game_id: str | None = None,
        market_type: str | None = None,
        limit: int = 50,
    ) -> Any:
        return await self.get_data(
            "/api/v1/lines/current",
            {"league": league, "game_id": game_id, "market_type": market_type, "limit": limit},
        )

    async def movement(self, game_external_id: str, market_type: str | None = None) -> Any:
        return await self.get_data(f"/api/v1/lines/game/{game_external_id}/movement", {"market_type": market_type})
