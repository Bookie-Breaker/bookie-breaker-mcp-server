"""Integration fixtures: a canned-JSON stub backend served over real HTTP.

The stub stands in for every BookieBreaker service so the MCP server can
be exercised end-to-end over real transports (stdio subprocess and
streamable HTTP) without Docker.
"""

import socket
import threading
import time
from collections.abc import Iterator
from typing import Any

import pytest
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

META = {"timestamp": "2026-07-04T12:00:00Z", "request_id": "req-stub"}

EDGE = {
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

PERFORMANCE = {
    "total_bets": 42,
    "total_wins": 25,
    "total_losses": 16,
    "total_pushes": 1,
    "win_rate": 0.5952,
    "roi": 0.051,
    "total_wagered_units": 60.0,
    "total_profit_units": 3.1,
    "avg_edge_percentage": 4.0,
    "avg_clv": 0.011,
}


def enveloped(data: Any) -> dict[str, Any]:
    return {"data": data, "meta": META}


def build_stub_app() -> Starlette:
    async def edges(_request: Request) -> JSONResponse:
        return JSONResponse(enveloped([EDGE]))

    async def edge_detail(request: Request) -> JSONResponse:
        detail = dict(EDGE)
        detail["id"] = request.path_params["edge_id"]
        detail.update(
            {
                "game": None,
                "game_external_id": "ext-abc123",
                "odds_decimal": 1.714,
                "sportsbook_id": None,
                "prediction": None,
                "betting_line": None,
                "paper_bet": None,
                "analysis": None,
            }
        )
        return JSONResponse(enveloped(detail))

    async def place_bet(_request: Request) -> JSONResponse:
        return JSONResponse(
            enveloped(
                {
                    "id": "bet-stub-1",
                    "selection": EDGE["selection"],
                    "odds_american": -140,
                    "sportsbook_key": "fanduel",
                    "stake": 1.0,
                    "result": "PENDING",
                    "placed_at": "2026-07-04T12:00:00Z",
                }
            ),
            status_code=201,
        )

    async def performance(_request: Request) -> JSONResponse:
        return JSONResponse(enveloped(PERFORMANCE))

    async def health(_request: Request) -> JSONResponse:
        return JSONResponse(enveloped({"status": "healthy"}))

    return Starlette(
        routes=[
            Route("/api/v1/agent/edges", edges),
            Route("/api/v1/agent/edges/{edge_id}", edge_detail),
            Route("/api/v1/emulator/bets", place_bet, methods=["POST"]),
            Route("/api/v1/emulator/performance", performance),
            Route("/api/v1/agent/health", health),
            Route("/api/v1/emulator/health", health),
            Route("/api/v1/lines/health", health),
            Route("/api/v1/stats/health", health),
            Route("/api/v1/sim/health", health),
            Route("/api/v1/predict/health", health),
        ]
    )


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def stub_backend_url() -> Iterator[str]:
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(build_stub_app(), host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10.0
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("stub backend failed to start")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5.0)


def backend_env(stub_url: str) -> dict[str, str]:
    return {
        "AGENT_URL": stub_url,
        "LINES_SERVICE_URL": stub_url,
        "STATISTICS_SERVICE_URL": stub_url,
        "SIMULATION_ENGINE_URL": stub_url,
        "PREDICTION_ENGINE_URL": stub_url,
        "BOOKIE_EMULATOR_URL": stub_url,
    }
