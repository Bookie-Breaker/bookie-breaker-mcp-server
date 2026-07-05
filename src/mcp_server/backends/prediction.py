"""Prediction engine client (port 8004): latest predictions per game."""

from typing import Any

from mcp_server.backends.base import BackendClient


class PredictionBackend(BackendClient):
    service_name = "prediction-engine"
    health_path = "/api/v1/predict/health"

    async def latest_for_game(self, game_id: str, market_type: str | None = None) -> Any:
        return await self.get_data(f"/api/v1/predict/games/{game_id}/latest", {"market_type": market_type})
