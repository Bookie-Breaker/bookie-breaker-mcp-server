"""Bookie-emulator client (port 8005): paper bets and performance."""

from typing import Any

from mcp_server.backends.base import BackendClient


class EmulatorBackend(BackendClient):
    service_name = "bookie-emulator"
    health_path = "/api/v1/emulator/health"

    async def place_bet(self, body: dict[str, Any], idempotency_key: str | None = None) -> Any:
        headers = {"X-Idempotency-Key": idempotency_key} if idempotency_key else None
        return await self.post_data("/api/v1/emulator/bets", body, headers=headers)

    async def list_bets(
        self,
        status: str | None = None,
        league: str | None = None,
        market_type: str | None = None,
        limit: int = 25,
    ) -> Any:
        return await self.get_data(
            "/api/v1/emulator/bets",
            {"status": status, "league": league, "market_type": market_type, "limit": limit},
        )

    async def performance(self, window: str = "all_time", league: str | None = None) -> Any:
        return await self.get_data("/api/v1/emulator/performance", {"window": window, "league": league})
