# bookie-breaker-mcp-server

## Service Purpose

Python MCP tool server exposing BookieBreaker capabilities as Claude tools. Acts as a thin REST-to-MCP bridge — does not duplicate business logic.

## Language & Conventions

- **Language:** Python 3.12
- **Framework:** FastMCP (MCP SDK), FastAPI
- **Project layout:** `src/mcp_server/` package, `main.py` entry point
- **Naming:** `snake_case.py` files, `snake_case` functions, `PascalCase` classes
- **Package manager:** uv
- **Testing:** pytest in `tests/`

## Key Files

- `src/mcp_server/main.py` — MCP server entry point
- `src/mcp_server/tools/` — MCP tool implementations
- `pyproject.toml` — Dependencies and tool config

## Service-Specific Commands

```bash
task dev          # uvicorn with --reload on port 8007
task lint         # ruff check + format
task test         # pytest --cov
task typecheck    # mypy src/
```

## Dependencies

- **agent** (port 8006) — Primary backend for analysis and pipeline
- **lines-service** (port 8001) — Direct line lookups
- **statistics-service** (port 8002) — Direct stat lookups
- **bookie-emulator** (port 8005) — Bet placement

## Environment Variables

See `.env.example`. Key: `AGENT_URL`, `LINES_SERVICE_URL`, `STATISTICS_SERVICE_URL`, `BOOKIE_EMULATOR_URL`, `PORT=8007`.
