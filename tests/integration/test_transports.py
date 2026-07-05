"""Real-transport lifecycle tests: stdio subprocess and streamable HTTP.

Covers MCP initialization, capability negotiation (tools/list,
resources/list), tool invocation, and resource reads against a live stub
backend — no Docker required.
"""

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from tests.integration.conftest import backend_env

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TOOLS = {
    "ask_analyst",
    "get_bet_history",
    "get_edge_detail",
    "get_edges",
    "get_health",
    "get_lines",
    "get_performance",
    "get_pipeline_status",
    "get_player_stats",
    "get_prediction",
    "get_simulation",
    "get_slate",
    "get_team_stats",
    "place_bet",
    "run_pipeline",
}

EXPECTED_RESOURCES = {
    "bookiebreaker://edges/current",
    "bookiebreaker://performance/summary",
    "bookiebreaker://games/today",
}


class TestStdioTransport:
    @pytest.fixture
    def stdio_client(self, stub_backend_url: str) -> Client:
        env = os.environ | backend_env(stub_backend_url)
        env["MCP_TRANSPORT"] = "stdio"
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        transport = StdioTransport(command=sys.executable, args=["-m", "mcp_server"], env=env, cwd=str(REPO_ROOT))
        return Client(transport)

    async def test_lifecycle_tools_and_resources(self, stdio_client: Client) -> None:
        async with stdio_client:
            tools = await stdio_client.list_tools()
            assert {tool.name for tool in tools} == EXPECTED_TOOLS
            assert all(tool.description for tool in tools)

            resources = await stdio_client.list_resources()
            assert {str(resource.uri) for resource in resources} == EXPECTED_RESOURCES

            edges = await stdio_client.call_tool("get_edges", {"league": "NBA"})
            assert "BOS @ LAL" in edges.content[0].text

            bet = await stdio_client.call_tool(
                "place_bet", {"edge_id": "0d4a5c1e-0000-4000-8000-000000000001", "stake": 1.0}
            )
            assert "Paper bet placed" in bet.content[0].text

            contents = await stdio_client.read_resource("bookiebreaker://performance/summary")
            assert "**ROI:** 5.1%" in contents[0].text


class TestStreamableHttpTransport:
    @pytest.fixture
    def http_url(self, stub_backend_url: str) -> Iterator[str]:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = int(sock.getsockname()[1])
        env = os.environ | backend_env(stub_backend_url)
        env["MCP_TRANSPORT"] = "http"
        env["PORT"] = str(port)
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        process = subprocess.Popen(
            [sys.executable, "-m", "mcp_server"],
            env=env,
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 15.0
            while time.monotonic() < deadline:
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("streamable HTTP server did not start")
            yield f"http://127.0.0.1:{port}/mcp"
        finally:
            process.terminate()
            process.wait(timeout=10)

    async def test_lifecycle_over_http(self, http_url: str) -> None:
        async with Client(http_url) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools} == EXPECTED_TOOLS

            health = await client.call_tool("get_health", {})
            assert "All services healthy." in health.content[0].text

            edges = await client.call_tool("get_edges", {})
            assert "BOS @ LAL" in edges.content[0].text
