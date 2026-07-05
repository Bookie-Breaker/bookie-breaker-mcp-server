"""Backend failure -> ToolError translation.

ToolError messages are shown to the calling LLM, so they name the failing
service and carry the upstream error message — actionable, never a stack
trace. Everything else stays masked by FastMCP's default handling.
"""

import httpx
from fastmcp.exceptions import ToolError


def tool_error_from_response(service: str, response: httpx.Response) -> ToolError:
    try:
        error = response.json().get("error", {})
        message = str(error.get("message", response.text[:200]))
    except ValueError:
        message = response.text[:200]
    return ToolError(f"{service} returned {response.status_code}: {message}")


def tool_error_from_exception(service: str, base_url: str, exc: httpx.HTTPError) -> ToolError:
    if isinstance(exc, httpx.TimeoutException):
        return ToolError(f"{service} timed out at {base_url}")
    return ToolError(f"{service} unreachable at {base_url}: {type(exc).__name__}")
