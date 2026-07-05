"""Agent service client (port 8006): edges, slate, analysis, pipeline."""

from typing import Any

import httpx

from mcp_server.backends.base import BackendClient


class AgentBackend(BackendClient):
    service_name = "agent"
    health_path = "/api/v1/agent/health"

    def __init__(self, base_url: str, client: httpx.AsyncClient, analysis_timeout: float = 120.0) -> None:
        super().__init__(base_url, client)
        self._analysis_timeout = analysis_timeout

    async def list_edges(
        self,
        league: str | None = None,
        market_type: str | None = None,
        min_edge: float | None = None,
        date: str | None = None,
        include_stale: bool = False,
        limit: int = 25,
    ) -> Any:
        return await self.get_data(
            "/api/v1/agent/edges",
            {
                "league": league,
                "market_type": market_type,
                "min_edge": min_edge,
                "date": date,
                "is_stale": str(include_stale).lower() if include_stale else None,
                "limit": limit,
            },
        )

    async def get_edge(self, edge_id: str) -> Any:
        return await self.get_data(f"/api/v1/agent/edges/{edge_id}")

    async def get_slate(self, league: str | None = None, date: str | None = None) -> Any:
        return await self.get_data("/api/v1/agent/slate", {"league": league, "date": date})

    async def create_analysis(
        self,
        analysis_type: str,
        game_id: str | None,
        edge_id: str | None,
        question: str | None,
    ) -> Any:
        # LLM generation is slow; use the dedicated long timeout
        return await self.post_data(
            "/api/v1/agent/analysis",
            {"analysis_type": analysis_type, "game_id": game_id, "edge_id": edge_id, "question": question},
            timeout=self._analysis_timeout,
        )

    async def run_pipeline(self, league: str | None = None, auto_bet: bool = True) -> Any:
        return await self.post_data("/api/v1/agent/pipeline/run", {"league": league, "auto_bet": auto_bet})

    async def get_pipeline_run(self, pipeline_run_id: str) -> Any:
        return await self.get_data(f"/api/v1/agent/pipeline/runs/{pipeline_run_id}")
