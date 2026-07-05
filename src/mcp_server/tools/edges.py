"""get_edges and get_edge_detail tools."""

from typing import Annotated, Any

from pydantic import Field

from mcp_server.formatting import american_odds, kv_section, percent, points, table
from mcp_server.server import get_backends, mcp


def render_edges(edges: list[dict[str, Any]]) -> str:
    if not edges:
        return "No active edges right now."
    rows = [
        [
            str(edge.get("id", "")),
            f"{edge.get('away_team') or '?'} @ {edge.get('home_team') or '?'}",
            str(edge.get("market_type", "")),
            str(edge.get("selection", "")),
            american_odds(edge.get("odds_american")),
            str(edge.get("sportsbook_key", "")),
            points(edge.get("edge_percentage")),
            percent(edge.get("predicted_probability")),
            "yes" if edge.get("has_paper_bet") else "no",
        ]
        for edge in edges
    ]
    header = f"## Active Edges ({len(edges)})\n\n"
    return header + table(
        ["Edge ID", "Game", "Market", "Selection", "Odds", "Book", "Edge", "Model Prob", "Bet Placed"], rows
    )


@mcp.tool
async def get_edges(
    league: Annotated[str | None, Field(description="Filter by league, e.g. NBA. Omit for all leagues.")] = None,
    market_type: Annotated[str | None, Field(description="SPREAD, TOTAL, or MONEYLINE.")] = None,
    min_edge: Annotated[float | None, Field(description="Minimum edge in percentage points, e.g. 3.0.")] = None,
    date: Annotated[str | None, Field(description="Game date (YYYY-MM-DD).")] = None,
    include_stale: Annotated[bool, Field(description="Include stale/expired edges.")] = False,
    limit: Annotated[int, Field(ge=1, le=100, description="Max edges to return.")] = 25,
) -> str:
    """List currently detected positive-EV betting edges, best first."""
    edges = await get_backends().agent.list_edges(
        league=league,
        market_type=market_type,
        min_edge=min_edge,
        date=date,
        include_stale=include_stale,
        limit=limit,
    )
    return render_edges(edges)


@mcp.tool
async def get_edge_detail(
    edge_id: Annotated[str, Field(description="The edge UUID from get_edges.")],
) -> str:
    """Full detail for one edge: game, prediction, market line, paper bet, and any stored analysis."""
    edge = await get_backends().agent.get_edge(edge_id)
    game = edge.get("game") or {}
    home = (game.get("home_team") or {}).get("abbreviation", "?")
    away = (game.get("away_team") or {}).get("abbreviation", "?")
    sections = [
        kv_section(
            f"Edge: {edge.get('selection')} ({away} @ {home})",
            [
                ("Market", str(edge.get("market_type"))),
                ("Odds", f"{american_odds(edge.get('odds_american'))} at {edge.get('sportsbook_key')}"),
                ("Edge", points(edge.get("edge_percentage"))),
                ("Model probability", percent(edge.get("predicted_probability"))),
                ("Implied probability", percent(edge.get("implied_probability"))),
                ("Expected value", percent(edge.get("expected_value"))),
                ("Kelly fraction", percent(edge.get("kelly_fraction"), 2)),
                ("Recommended stake", f"{edge.get('recommended_stake')}u"),
                ("Confidence", percent(edge.get("confidence"))),
                ("Stale", "yes" if edge.get("is_stale") else "no"),
                ("Detected", str(edge.get("detected_at"))),
            ],
        )
    ]
    prediction = edge.get("prediction")
    if prediction:
        sections.append(
            kv_section(
                "Prediction",
                [
                    ("Prediction ID", str(prediction.get("id"))),
                    ("Model version", str(prediction.get("model_version_id"))),
                    ("Adjustment magnitude", str(prediction.get("adjustment_magnitude"))),
                ],
            )
        )
    paper_bet = edge.get("paper_bet")
    if paper_bet:
        sections.append(
            kv_section(
                "Paper Bet",
                [
                    ("Bet ID", str(paper_bet.get("id"))),
                    ("Stake", f"{paper_bet.get('stake')}u"),
                    ("Result", str(paper_bet.get("result"))),
                ],
            )
        )
    analysis = edge.get("analysis")
    if analysis:
        sections.append(
            kv_section(
                "Stored Analysis",
                [("Analysis ID", str(analysis.get("id"))), ("Title", str(analysis.get("title")))],
            )
        )
    return "\n\n".join(sections)
