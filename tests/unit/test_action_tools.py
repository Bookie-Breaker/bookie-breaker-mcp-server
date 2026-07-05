"""Action tools: place_bet, pipeline, ask_analyst, performance, history."""

import json

import pytest
from fastmcp.exceptions import ToolError
from httpx import Response

from tests.unit.conftest import AGENT_URL, EMULATOR_URL, edge_detail_payload, enveloped, text


class TestPlaceBet:
    async def test_builds_bet_from_edge_and_is_idempotent(self, client, upstream) -> None:
        detail = edge_detail_payload()
        upstream.get(f"{AGENT_URL}/api/v1/agent/edges/{detail['id']}").mock(
            return_value=Response(200, json=enveloped(detail))
        )
        bet_route = upstream.post(f"{EMULATOR_URL}/api/v1/emulator/bets").mock(
            return_value=Response(
                201,
                json=enveloped(
                    {
                        "id": "bet-1",
                        "selection": detail["selection"],
                        "odds_american": -140,
                        "sportsbook_key": "fanduel",
                        "stake": 2.0,
                        "result": "PENDING",
                        "placed_at": "2026-07-04T12:00:00Z",
                    }
                ),
            )
        )
        result = await client.call_tool("place_bet", {"edge_id": detail["id"], "stake": 2.0})
        output = text(result)
        assert "Paper bet placed" in output
        assert "bet-1" in output

        request = bet_route.calls[0].request
        body = json.loads(request.content)
        assert body["edge_id"] == detail["id"]
        assert body["game_external_id"] == "ext-abc123"
        assert body["prediction_id"] == "pred-1"
        assert body["stake"] == 2.0
        assert body["sportsbook_key"] == "fanduel"
        first_key = request.headers["X-Idempotency-Key"]

        await client.call_tool("place_bet", {"edge_id": detail["id"], "stake": 2.0})
        assert bet_route.calls[1].request.headers["X-Idempotency-Key"] == first_key
        # different stake -> different idempotency key
        await client.call_tool("place_bet", {"edge_id": detail["id"], "stake": 3.0})
        assert bet_route.calls[2].request.headers["X-Idempotency-Key"] != first_key

    async def test_stale_edge_rejected(self, client, upstream) -> None:
        detail = edge_detail_payload(is_stale=True)
        upstream.get(f"{AGENT_URL}/api/v1/agent/edges/{detail['id']}").mock(
            return_value=Response(200, json=enveloped(detail))
        )
        with pytest.raises(ToolError, match="stale"):
            await client.call_tool("place_bet", {"edge_id": detail["id"], "stake": 1.0})


class TestBetHistoryAndPerformance:
    async def test_bet_history_table(self, client, upstream) -> None:
        bets = [
            {
                "id": "bet-1",
                "selection": "Over 220.5",
                "market_type": "TOTAL",
                "odds_american": -108,
                "sportsbook_key": "fanduel",
                "stake": 1.5,
                "result": "WON",
                "profit_loss": 1.39,
                "placed_at": "2026-07-03T18:00:00Z",
            }
        ]
        route = upstream.get(f"{EMULATOR_URL}/api/v1/emulator/bets").mock(
            return_value=Response(200, json=enveloped(bets))
        )
        result = await client.call_tool("get_bet_history", {"status": "won", "limit": 10})
        output = text(result)
        assert "Over 220.5" in output
        assert "+1.39u" in output
        assert route.calls[0].request.url.params["status"] == "won"

    async def test_performance_summary(self, client, upstream) -> None:
        perf = {
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
        upstream.get(f"{EMULATOR_URL}/api/v1/emulator/performance").mock(
            return_value=Response(200, json=enveloped(perf))
        )
        result = await client.call_tool("get_performance", {})
        output = text(result)
        assert "42 (25W-16L-1P)" in output
        assert "**ROI:** 5.1%" in output
        assert "+3.10u" in output


class TestAskAnalyst:
    ANALYSIS = {
        "id": "an-1",
        "title": "Edge Analysis: Over 220.5",
        "content": "## Summary\n\nSolid edge.",
        "model_used": "claude-opus-4-8",
    }

    async def test_type_inference(self, client, upstream) -> None:
        route = upstream.post(f"{AGENT_URL}/api/v1/agent/analysis").mock(
            return_value=Response(201, json=enveloped(self.ANALYSIS))
        )

        await client.call_tool("ask_analyst", {"question": "Why?", "edge_id": "e-1", "game_id": "g-1"})
        assert json.loads(route.calls[-1].request.content)["analysis_type"] == "EDGE_BREAKDOWN"

        await client.call_tool("ask_analyst", {"question": "Preview?", "game_id": "g-1"})
        assert json.loads(route.calls[-1].request.content)["analysis_type"] == "GAME_PREVIEW"

        await client.call_tool("ask_analyst", {"question": "How are we doing?"})
        assert json.loads(route.calls[-1].request.content)["analysis_type"] == "PERFORMANCE_REVIEW"

        await client.call_tool("ask_analyst", {"question": "?", "game_id": "g-1", "analysis_type": "EDGE_BREAKDOWN"})
        assert json.loads(route.calls[-1].request.content)["analysis_type"] == "EDGE_BREAKDOWN"

    async def test_renders_title_content_and_model(self, client, upstream) -> None:
        upstream.post(f"{AGENT_URL}/api/v1/agent/analysis").mock(
            return_value=Response(201, json=enveloped(self.ANALYSIS))
        )
        result = await client.call_tool("ask_analyst", {"question": "Why the over?"})
        output = text(result)
        assert output.startswith("# Edge Analysis: Over 220.5")
        assert "Solid edge." in output
        assert "claude-opus-4-8" in output


class TestPipelineTools:
    async def test_run_pipeline(self, client, upstream) -> None:
        accepted = {
            "pipeline_run_id": "run-1",
            "status": "RUNNING",
            "league": "NBA",
            "games_queued": 4,
            "started_at": "2026-07-04T12:00:00Z",
        }
        route = upstream.post(f"{AGENT_URL}/api/v1/agent/pipeline/run").mock(
            return_value=Response(202, json=enveloped(accepted))
        )
        result = await client.call_tool("run_pipeline", {"league": "NBA", "auto_bet": False})
        output = text(result)
        assert "**Run ID:** run-1" in output
        assert json.loads(route.calls[0].request.content) == {"league": "NBA", "auto_bet": False}

    async def test_pipeline_status_with_steps(self, client, upstream) -> None:
        run = {
            "pipeline_run_id": "run-1",
            "status": "COMPLETED",
            "trigger": "MANUAL",
            "league": "NBA",
            "games_processed": 4,
            "edges_found": 3,
            "bets_placed": 2,
            "error": None,
            "steps": {"simulation": {"status": "completed"}, "prediction": {"status": "completed"}},
        }
        upstream.get(f"{AGENT_URL}/api/v1/agent/pipeline/runs/run-1").mock(
            return_value=Response(200, json=enveloped(run))
        )
        result = await client.call_tool("get_pipeline_status", {"pipeline_run_id": "run-1"})
        output = text(result)
        assert "**Status:** COMPLETED" in output
        assert "**simulation:** completed" in output
