"""Read-only tools: request mapping and markdown rendering."""

from httpx import Response

from tests.unit.conftest import (
    AGENT_URL,
    LINES_URL,
    PREDICT_URL,
    SIM_URL,
    STATS_URL,
    edge_detail_payload,
    edge_payload,
    enveloped,
    text,
)


class TestGetEdges:
    async def test_lists_edges_as_markdown_table(self, client, upstream) -> None:
        route = upstream.get(f"{AGENT_URL}/api/v1/agent/edges").mock(
            return_value=Response(200, json=enveloped([edge_payload()]))
        )
        result = await client.call_tool(
            "get_edges", {"league": "NBA", "min_edge": 3.0, "market_type": "MONEYLINE", "limit": 10}
        )
        output = text(result)
        assert "| Edge ID |" in output
        assert "BOS @ LAL" in output
        assert "-140" in output
        assert "13.8%" in output
        params = route.calls[0].request.url.params
        assert params["league"] == "NBA"
        assert params["min_edge"] == "3.0"
        assert params["market_type"] == "MONEYLINE"
        assert params["limit"] == "10"

    async def test_empty_result_message(self, client, upstream) -> None:
        upstream.get(f"{AGENT_URL}/api/v1/agent/edges").mock(return_value=Response(200, json=enveloped([])))
        result = await client.call_tool("get_edges", {})
        assert "No active edges" in text(result)


class TestGetEdgeDetail:
    async def test_renders_sections(self, client, upstream) -> None:
        detail = edge_detail_payload()
        upstream.get(f"{AGENT_URL}/api/v1/agent/edges/{detail['id']}").mock(
            return_value=Response(200, json=enveloped(detail))
        )
        result = await client.call_tool("get_edge_detail", {"edge_id": detail["id"]})
        output = text(result)
        assert "## Edge: Los Angeles Lakers (BOS @ LAL)" in output
        assert "**Odds:** -140 at fanduel" in output
        assert "## Prediction" in output
        assert "## Paper Bet" not in output  # none placed


class TestGetSlate:
    async def test_renders_games(self, client, upstream) -> None:
        slate = {
            "date": "2026-07-04",
            "games": [
                {
                    "game_id": "g-1",
                    "league": "NBA",
                    "home_team": {"abbreviation": "LAL"},
                    "away_team": {"abbreviation": "BOS"},
                    "scheduled_start": "2026-07-04T22:00:00Z",
                    "status": "SCHEDULED",
                    "prediction": {"selection": "Los Angeles Lakers ML"},
                    "edges": [{"edge_percentage": 4.2}, {"edge_percentage": 2.0}],
                }
            ],
        }
        upstream.get(f"{AGENT_URL}/api/v1/agent/slate").mock(return_value=Response(200, json=enveloped(slate)))
        result = await client.call_tool("get_slate", {})
        output = text(result)
        assert "## Slate for 2026-07-04" in output
        assert "BOS @ LAL" in output
        assert "Los Angeles Lakers ML" in output
        assert "4.2%" in output


class TestGetPrediction:
    async def test_renders_predictions(self, client, upstream) -> None:
        payload = {
            "game_id": "g-1",
            "predictions": [
                {
                    "market_type": "TOTAL",
                    "selection": "Over 220.5",
                    "predicted_probability": 0.60,
                    "confidence_lower": 0.56,
                    "confidence_upper": 0.64,
                    "model_version_id": "abcdef1234567890",
                }
            ],
        }
        upstream.get(f"{PREDICT_URL}/api/v1/predict/games/g-1/latest").mock(
            return_value=Response(200, json=enveloped(payload))
        )
        result = await client.call_tool("get_prediction", {"game_id": "g-1"})
        output = text(result)
        assert "Over 220.5" in output
        assert "60.0%" in output
        assert "56.0% – 64.0%" in output


class TestGetLines:
    LINE = {
        "game_id": "ext-1",
        "sportsbook_key": "draftkings",
        "market_type": "SPREAD",
        "selection": "LAL -3.5",
        "line_value": -3.5,
        "odds_american": -110,
        "implied_probability": 0.524,
        "timestamp": "2026-07-04T12:00:00Z",
    }

    async def test_current_lines(self, client, upstream) -> None:
        route = upstream.get(f"{LINES_URL}/api/v1/lines/current").mock(
            return_value=Response(200, json=enveloped([self.LINE]))
        )
        result = await client.call_tool("get_lines", {"league": "NBA"})
        output = text(result)
        assert "## Current NBA Lines" in output
        assert "LAL -3.5" in output
        assert route.calls[0].request.url.params["league"] == "NBA"

    async def test_movement(self, client, upstream) -> None:
        upstream.get(f"{LINES_URL}/api/v1/lines/game/ext-1/movement").mock(
            return_value=Response(200, json=enveloped({"snapshots": [self.LINE]}))
        )
        result = await client.call_tool("get_lines", {"game_external_id": "ext-1", "include_movement": True})
        assert "## Line Movement — ext-1" in text(result)

    async def test_movement_requires_game_id(self, client) -> None:
        result = await client.call_tool("get_lines", {"include_movement": True})
        assert "requires game_external_id" in text(result)


class TestStatsTools:
    async def test_team_stats_generic_table(self, client, upstream) -> None:
        teams = [{"name": "Lakers", "wins": 52, "losses": 30, "pace": 101.2, "off_rating": 118.1}]
        route = upstream.get(f"{STATS_URL}/api/v1/stats/teams").mock(return_value=Response(200, json=enveloped(teams)))
        result = await client.call_tool("get_team_stats", {"league": "NBA", "team": "Lakers"})
        output = text(result)
        assert "## NBA Team Stats" in output
        assert "| Lakers | 52 | 30 |" in output
        assert route.calls[0].request.url.params["search"] == "Lakers"

    async def test_player_stats(self, client, upstream) -> None:
        players = [{"name": "L. James", "ppg": 25.1, "rpg": 7.8}]
        upstream.get(f"{STATS_URL}/api/v1/stats/players").mock(return_value=Response(200, json=enveloped(players)))
        result = await client.call_tool("get_player_stats", {"league": "NBA", "player": "James"})
        assert "L. James" in text(result)


class TestGetSimulation:
    async def test_renders_distribution_summary(self, client, upstream) -> None:
        run = {
            "simulation_run_id": "sim-1",
            "game_id": "g-1",
            "status": "completed",
            "iterations_completed": 10000,
            "converged": True,
            "completed_at": "2026-07-04T12:00:00Z",
            "result": {
                "home_win_probability": 0.68,
                "away_win_probability": 0.32,
                "mean_total": 222.3,
                "mean_margin": 6.1,
            },
        }
        upstream.get(f"{SIM_URL}/api/v1/sim/games/g-1/latest").mock(return_value=Response(200, json=enveloped(run)))
        result = await client.call_tool("get_simulation", {"game_id": "g-1"})
        output = text(result)
        assert "**Home win probability:** 68.0%" in output
        assert "**Iterations:** 10000" in output
