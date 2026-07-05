"""Markdown rendering helpers — tools return markdown, never JSON dumps."""

from typing import Any


def american_odds(value: Any) -> str:
    try:
        odds = int(value)
    except (TypeError, ValueError):
        return "—"
    return f"+{odds}" if odds > 0 else str(odds)


def percent(value: Any, digits: int = 1) -> str:
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def points(value: Any, digits: int = 1) -> str:
    """A raw percentage-point value (edge_percentage is already in points)."""
    try:
        return f"{float(value):.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def units(value: Any) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{amount:+.2f}u"


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def kv_section(title: str, pairs: list[tuple[str, str]]) -> str:
    body = "\n".join(f"- **{key}:** {value}" for key, value in pairs)
    return f"## {title}\n\n{body}"
