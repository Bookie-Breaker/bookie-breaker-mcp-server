"""Simulation engine client (port 8003): latest simulation per game."""

from typing import Any

from mcp_server.backends.base import BackendClient


class SimulationBackend(BackendClient):
    service_name = "simulation-engine"
    health_path = "/api/v1/sim/health"

    async def latest_for_game(self, game_id: str) -> Any:
        return await self.get_data(f"/api/v1/sim/games/{game_id}/latest")
