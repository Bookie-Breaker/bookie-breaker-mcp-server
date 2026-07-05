"""ASGI entry point: streamable HTTP transport at /mcp plus /health.

Used by uvicorn (task dev, Docker). For stdio (Claude Desktop/Code) run
``python -m mcp_server`` instead.
"""

from mcp_server.server import mcp

app = mcp.http_app()
