"""Thin typed clients over the BookieBreaker REST services."""

from dataclasses import dataclass

import httpx

from mcp_server.backends.agent import AgentBackend
from mcp_server.backends.base import BackendClient
from mcp_server.backends.emulator import EmulatorBackend
from mcp_server.backends.lines import LinesBackend
from mcp_server.backends.prediction import PredictionBackend
from mcp_server.backends.simulation import SimulationBackend
from mcp_server.backends.statistics import StatisticsBackend
from mcp_server.settings import Settings


@dataclass(frozen=True)
class Backends:
    agent: AgentBackend
    lines: LinesBackend
    emulator: EmulatorBackend
    prediction: PredictionBackend
    simulation: SimulationBackend
    statistics: StatisticsBackend
    http_client: httpx.AsyncClient

    async def aclose(self) -> None:
        await self.http_client.aclose()


def create_backends(settings: Settings) -> Backends:
    client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)
    return Backends(
        agent=AgentBackend(settings.agent_url, client, analysis_timeout=settings.analysis_timeout_seconds),
        lines=LinesBackend(settings.lines_service_url, client),
        emulator=EmulatorBackend(settings.bookie_emulator_url, client),
        prediction=PredictionBackend(settings.prediction_engine_url, client),
        simulation=SimulationBackend(settings.simulation_engine_url, client),
        statistics=StatisticsBackend(settings.statistics_service_url, client),
        http_client=client,
    )


__all__ = ["BackendClient", "Backends", "create_backends"]
