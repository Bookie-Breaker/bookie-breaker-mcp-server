"""place_bet and get_bet_history tools."""

import uuid
from typing import Annotated, Any

from fastmcp.exceptions import ToolError
from pydantic import Field

from mcp_server.formatting import american_odds, table, units
from mcp_server.server import get_backends, mcp

# Fixed namespace: retrying the same edge+stake never double-bets.
BET_IDEMPOTENCY_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "bets.mcp-server.bookie-breaker")


def render_bets(bets: list[dict[str, Any]]) -> str:
    if not bets:
        return "No paper bets found."
    rows = [
        [
            str(bet.get("id", "")),
            str(bet.get("selection", "")),
            str(bet.get("market_type", "")),
            american_odds(bet.get("odds_american")),
            str(bet.get("sportsbook_key", "")),
            f"{bet.get('stake')}u",
            str(bet.get("result", "")),
            units(bet.get("profit_loss")) if bet.get("profit_loss") is not None else "—",
            str(bet.get("placed_at", "")),
        ]
        for bet in bets
    ]
    return f"## Paper Bets ({len(bets)})\n\n" + table(
        ["Bet ID", "Selection", "Market", "Odds", "Book", "Stake", "Result", "P/L", "Placed"], rows
    )


@mcp.tool
async def place_bet(
    edge_id: Annotated[str, Field(description="The edge UUID to bet (from get_edges).")],
    stake: Annotated[float, Field(gt=0, le=100, description="Stake in units (1u = 1% of starting bankroll).")],
    reasoning: Annotated[str | None, Field(description="Why this bet is being placed.")] = None,
) -> str:
    """Place a paper bet on a detected edge at its current recorded odds.

    Idempotent per (edge, stake): retrying the same call never double-bets.
    """
    backends = get_backends()
    edge = await backends.agent.get_edge(edge_id)
    if edge.get("is_stale"):
        raise ToolError(f"Edge {edge_id} is stale; refresh edges before betting.")
    body = {
        "game_id": edge.get("game_id"),
        "game_external_id": (edge.get("betting_line") or {}).get("game_id") or edge.get("game_external_id"),
        "edge_id": edge_id,
        "prediction_id": (edge.get("prediction") or {}).get("id"),
        "market_type": edge.get("market_type"),
        "selection": edge.get("selection"),
        "side": edge.get("side"),
        "sportsbook_key": edge.get("sportsbook_key"),
        "predicted_probability": edge.get("predicted_probability"),
        "edge_percentage": edge.get("edge_percentage"),
        "stake": stake,
        "kelly_fraction": edge.get("kelly_fraction"),
        "reasoning": reasoning or f"Placed via MCP on a {edge.get('edge_percentage')}% edge.",
    }
    idempotency_key = str(uuid.uuid5(BET_IDEMPOTENCY_NAMESPACE, f"{edge_id}:{stake}"))
    bet = await backends.emulator.place_bet(body, idempotency_key=idempotency_key)
    return (
        f"Paper bet placed: **{bet.get('selection')}** at {american_odds(bet.get('odds_american'))} "
        f"({bet.get('sportsbook_key')}) for {bet.get('stake')}u.\n\n"
        f"- Bet ID: {bet.get('id')}\n- Result: {bet.get('result')}\n- Placed at: {bet.get('placed_at')}"
    )


@mcp.tool
async def get_bet_history(
    status: Annotated[str | None, Field(description="Filter: open, won, lost, push.")] = None,
    league: Annotated[str | None, Field(description="Filter by league.")] = None,
    market_type: Annotated[str | None, Field(description="SPREAD, TOTAL, or MONEYLINE.")] = None,
    limit: Annotated[int, Field(ge=1, le=200, description="Max bets to return.")] = 25,
) -> str:
    """Paper bet ledger, newest first."""
    bets = await get_backends().emulator.list_bets(status=status, league=league, market_type=market_type, limit=limit)
    return render_bets(bets)
