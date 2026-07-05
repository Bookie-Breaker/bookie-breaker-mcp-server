"""get_prediction tool."""

from typing import Annotated, Any

from pydantic import Field

from mcp_server.formatting import percent, table
from mcp_server.server import get_backends, mcp


def render_predictions(payload: dict[str, Any] | list[dict[str, Any]]) -> str:
    items: list[dict[str, Any]] = payload.get("predictions", []) if isinstance(payload, dict) else payload
    if not items:
        return "No predictions found for this game."
    rows = [
        [
            str(item.get("market_type", "")),
            str(item.get("selection", "")),
            percent(item.get("predicted_probability")),
            f"{percent(item.get('confidence_lower'))} – {percent(item.get('confidence_upper'))}",
            str(item.get("model_version_id", ""))[:8],
        ]
        for item in items
    ]
    return "## Latest Predictions\n\n" + table(["Market", "Selection", "Probability", "90% CI", "Model"], rows)


@mcp.tool
async def get_prediction(
    game_id: Annotated[str, Field(description="statistics-service game UUID (from get_slate).")],
    market_type: Annotated[str | None, Field(description="SPREAD, TOTAL, or MONEYLINE.")] = None,
) -> str:
    """Latest calibrated prediction probabilities for a game, with confidence intervals."""
    payload = await get_backends().prediction.latest_for_game(game_id, market_type=market_type)
    return render_predictions(payload)
