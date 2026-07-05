"""Statistics service client (port 8002): team and player stats."""

from typing import Any

from mcp_server.backends.base import BackendClient


class StatisticsBackend(BackendClient):
    service_name = "statistics-service"
    health_path = "/api/v1/stats/health"

    async def team_stats(self, league: str = "NBA", team: str | None = None) -> Any:
        return await self.get_data("/api/v1/stats/teams", {"league": league, "search": team})

    async def player_stats(self, league: str = "NBA", player: str | None = None, team_id: str | None = None) -> Any:
        return await self.get_data("/api/v1/stats/players", {"league": league, "search": player, "team_id": team_id})
