# bookie-breaker-mcp-server

## Service Purpose

Python MCP tool server exposing BookieBreaker capabilities as Claude tools. A stateless REST-to-MCP bridge —
15 tools + 3 resources delegating to the agent, lines-service, statistics-service, simulation-engine,
prediction-engine, and bookie-emulator. No database, no business logic.

## Language & Conventions

- **Language:** Python 3.12
- **Framework:** FastMCP (standalone `fastmcp` package) over httpx
- **Transports:** stdio (Claude Desktop/Code, default) and streamable HTTP (`MCP_TRANSPORT=http`, Docker)
- **Project layout:** `src/mcp_server/` package
- **Naming:** `snake_case.py` files, `snake_case` functions, `PascalCase` classes
- **Package manager:** uv
- **Testing:** pytest in `tests/` (`unit/` in-memory FastMCP client + respx; `integration/` real stdio/HTTP transports against a stub backend)

## Key Files

- `src/mcp_server/server.py` — FastMCP instance, backend lifecycle, /health route; importing registers everything
- `src/mcp_server/tools/` — MCP tool implementations (one module per capability group)
- `src/mcp_server/resources.py` — bookiebreaker:// resources
- `src/mcp_server/backends/` — Envelope-unwrapping httpx clients per backend service
- `src/mcp_server/formatting.py` — Markdown rendering helpers (tools return markdown, never JSON dumps)
- `src/mcp_server/errors.py` — Backend failure -> ToolError mapping
- `src/mcp_server/main.py` — ASGI app (streamable HTTP); `__main__.py` — transport-selecting runner

## Service-Specific Commands

```bash
task dev          # streamable HTTP with hot reload on port 8007
task dev:stdio    # stdio transport (Claude Desktop/Code)
task lint         # ruff check + format
task test         # pytest --cov
task typecheck    # mypy src/
```

## Dependencies

- **agent** (8006) — edges, slate, analysis (ask_analyst), pipeline
- **lines-service** (8001) — current lines and movement
- **statistics-service** (8002) — team/player stats
- **simulation-engine** (8003) — latest simulation per game
- **prediction-engine** (8004) — latest predictions per game
- **bookie-emulator** (8005) — paper bets and performance

## Environment Variables

See `.env.example`. Key: `MCP_TRANSPORT` (stdio | http), all six `*_URL` vars, `PORT=8007`,
`ANALYSIS_TIMEOUT_SECONDS` (ask_analyst waits on LLM generation).
