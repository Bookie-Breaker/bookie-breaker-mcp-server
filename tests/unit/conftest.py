"""Unit fixtures: in-memory MCP client + respx-mocked backends."""

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
import respx
from fastmcp import Client

from mcp_server import server
from mcp_server.settings import get_settings

AGENT_URL = "http://agent.test"
LINES_URL = "http://lines.test"
STATS_URL = "http://stats.test"
SIM_URL = "http://sim.test"
PREDICT_URL = "http://predict.test"
EMULATOR_URL = "http://emulator.test"

BACKEND_ENV = {
    "AGENT_URL": AGENT_URL,
    "LINES_SERVICE_URL": LINES_URL,
    "STATISTICS_SERVICE_URL": STATS_URL,
    "SIMULATION_ENGINE_URL": SIM_URL,
    "PREDICTION_ENGINE_URL": PREDICT_URL,
    "BOOKIE_EMULATOR_URL": EMULATOR_URL,
}


@pytest.fixture(autouse=True)
async def test_backends(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    for key, value in BACKEND_ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    await server.reset_backends()
    yield
    await server.reset_backends()
    get_settings.cache_clear()


@pytest.fixture
def upstream() -> Iterator[respx.MockRouter]:
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    async with Client(server.mcp) as mcp_client:
        yield mcp_client


def text(result: Any) -> str:
    return str(result.content[0].text)


def enveloped(data: Any) -> dict[str, Any]:
    return {"data": data, "meta": {"timestamp": "2026-07-04T12:00:00Z", "request_id": "req-test"}}


def error_enveloped(code: str, message: str) -> dict[str, Any]:
    return {
        "error": {"code": code, "message": message, "details": {}},
        "meta": {"timestamp": "2026-07-04T12:00:00Z", "request_id": "req-test"},
    }


def edge_payload(**overrides: Any) -> dict[str, Any]:
    edge = {
        "id": "0d4a5c1e-0000-4000-8000-000000000001",
        "game_id": "1d4a5c1e-0000-4000-8000-000000000002",
        "league": "NBA",
        "home_team": "LAL",
        "away_team": "BOS",
        "scheduled_start": "2026-07-04T22:00:00Z",
        "market_type": "MONEYLINE",
        "selection": "Los Angeles Lakers",
        "predicted_probability": 0.70,
        "implied_probability": 0.562,
        "edge_percentage": 13.8,
        "expected_value": 0.20,
        "odds_american": -140,
        "sportsbook_key": "fanduel",
        "kelly_fraction": 0.05,
        "recommended_stake": 5.0,
        "confidence": 0.78,
        "detected_at": "2026-07-04T12:00:00Z",
        "expires_at": "2026-07-04T22:00:00Z",
        "is_stale": False,
        "has_paper_bet": False,
        "paper_bet_id": None,
    }
    edge.update(overrides)
    return edge


def edge_detail_payload(**overrides: Any) -> dict[str, Any]:
    detail = edge_payload(
        game={
            "home_team": {"id": "h", "name": "Los Angeles Lakers", "abbreviation": "LAL"},
            "away_team": {"id": "a", "name": "Boston Celtics", "abbreviation": "BOS"},
            "scheduled_start": "2026-07-04T22:00:00Z",
            "status": "SCHEDULED",
        },
        game_external_id="ext-abc123",
        odds_decimal=1.714,
        sportsbook_id=None,
        prediction={"id": "pred-1", "model_version_id": "mv-1", "adjustment_magnitude": 0.02},
        betting_line={"id": "bl-1", "game_id": "ext-abc123", "sportsbook_key": "fanduel", "odds_american": -140},
        paper_bet=None,
        analysis=None,
    )
    detail.update(overrides)
    return detail
