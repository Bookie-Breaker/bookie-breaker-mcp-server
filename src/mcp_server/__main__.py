"""Transport-selecting runner: MCP_TRANSPORT=stdio (default) or http.

stdio is what Claude Desktop/Code launch; http serves streamable HTTP on
PORT for containerized use. Legacy SSE clients can use transport="sse"
via FastMCP but it is deprecated by the MCP spec and not wired here.
"""

from mcp_server.server import mcp
from mcp_server.settings import get_settings


def main() -> None:
    settings = get_settings()
    if settings.mcp_transport == "http":
        mcp.run(transport="http", host="0.0.0.0", port=settings.port)  # noqa: S104
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
