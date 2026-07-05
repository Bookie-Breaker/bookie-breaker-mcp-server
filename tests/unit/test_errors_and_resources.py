"""ToolError mapping, health fan-out, resources, and the /health route."""

import httpx
import pytest
from fastmcp.exceptions import ToolError
from httpx import Response

from mcp_server.main import app
from tests.unit.conftest import AGENT_URL, EMULATOR_URL, edge_payload, enveloped, error_enveloped, text


class TestErrorMapping:
    async def test_backend_error_envelope_becomes_actionable_tool_error(self, client, upstream) -> None:
        upstream.get(f"{AGENT_URL}/api/v1/agent/edges/e-404").mock(
            return_value=Response(404, json=error_enveloped("RESOURCE_NOT_FOUND", "Edge e-404 not found"))
        )
        with pytest.raises(ToolError, match="agent returned 404: Edge e-404 not found"):
            await client.call_tool("get_edge_detail", {"edge_id": "e-404"})

    async def test_unreachable_backend_names_service_and_url(self, client, upstream) -> None:
        upstream.get(f"{AGENT_URL}/api/v1/agent/edges").mock(side_effect=httpx.ConnectError("boom"))
        with pytest.raises(ToolError, match="agent unreachable at http://agent.test"):
            await client.call_tool("get_edges", {})


class TestGetHealth:
    async def test_mixed_statuses(self, client, upstream) -> None:
        upstream.get(f"{AGENT_URL}/api/v1/agent/health").mock(return_value=Response(200, json=enveloped({})))
        upstream.get(f"{EMULATOR_URL}/api/v1/emulator/health").mock(return_value=Response(200, json=enveloped({})))
        # all other backends unmocked -> connect errors -> unhealthy
        upstream.route(host="lines.test").mock(side_effect=httpx.ConnectError("down"))
        upstream.route(host="stats.test").mock(side_effect=httpx.ConnectError("down"))
        upstream.route(host="sim.test").mock(side_effect=httpx.ConnectError("down"))
        upstream.route(host="predict.test").mock(side_effect=httpx.ConnectError("down"))

        result = await client.call_tool("get_health", {})
        output = text(result)
        assert "Some services are degraded." in output
        assert "| agent | healthy |" in output
        assert "| lines-service | unhealthy |" in output


class TestResources:
    async def test_current_edges_resource(self, client, upstream) -> None:
        upstream.get(f"{AGENT_URL}/api/v1/agent/edges").mock(
            return_value=Response(200, json=enveloped([edge_payload()]))
        )
        contents = await client.read_resource("bookiebreaker://edges/current")
        assert "BOS @ LAL" in contents[0].text

    async def test_performance_resource(self, client, upstream) -> None:
        upstream.get(f"{EMULATOR_URL}/api/v1/emulator/performance").mock(
            return_value=Response(200, json=enveloped({"total_bets": 10, "win_rate": 0.6, "roi": 0.05}))
        )
        contents = await client.read_resource("bookiebreaker://performance/summary")
        assert "**ROI:** 5.0%" in contents[0].text

    async def test_todays_games_resource(self, client, upstream) -> None:
        upstream.get(f"{AGENT_URL}/api/v1/agent/slate").mock(
            return_value=Response(200, json=enveloped({"date": "2026-07-04", "games": []}))
        )
        contents = await client.read_resource("bookiebreaker://games/today")
        assert "No games on the slate" in contents[0].text


class TestHealthRoute:
    async def test_liveness_route(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://mcp.test") as http:
            response = await http.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "mcp-server"}
