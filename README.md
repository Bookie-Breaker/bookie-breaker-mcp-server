# bookie-breaker-mcp-server

MCP tool server exposing BookieBreaker capabilities as Claude tools. A stateless REST-to-MCP bridge over the
agent, lines-service, statistics-service, simulation-engine, prediction-engine, and bookie-emulator.

## Tools

`get_edges`, `get_edge_detail`, `get_slate`, `get_prediction`, `get_lines`, `place_bet`, `get_bet_history`,
`get_performance`, `ask_analyst`, `run_pipeline`, `get_pipeline_status`, `get_health`, `get_team_stats`,
`get_player_stats`, `get_simulation`

Resources: `bookiebreaker://edges/current`, `bookiebreaker://performance/summary`, `bookiebreaker://games/today`

## Transports

- **stdio** (default) — for Claude Desktop / Claude Code
- **Streamable HTTP** — `MCP_TRANSPORT=http`, serves `/mcp` on port 8007 (used in Docker Compose; `/health`
  serves the container healthcheck). Legacy SSE is deprecated by the MCP spec and not wired.

## Quickstart

### With Docker Compose (recommended)

```bash
task up  # from BookieBreaker/ root; serves streamable HTTP on :8007
```

### Standalone

```bash
cp .env.example .env  # fill in values
task bootstrap
task dev        # streamable HTTP with hot reload
task dev:stdio  # stdio transport
```

### Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "bookiebreaker": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/bookie-breaker-mcp-server",
        "python",
        "-m",
        "mcp_server"
      ],
      "env": {
        "AGENT_URL": "http://localhost:8006",
        "LINES_SERVICE_URL": "http://localhost:8001",
        "STATISTICS_SERVICE_URL": "http://localhost:8002",
        "SIMULATION_ENGINE_URL": "http://localhost:8003",
        "PREDICTION_ENGINE_URL": "http://localhost:8004",
        "BOOKIE_EMULATOR_URL": "http://localhost:8005"
      }
    }
  }
}
```

Or over streamable HTTP against the compose stack: `claude mcp add --transport http bookiebreaker http://localhost:8007/mcp`

## Architecture Decisions

- [Tech Stack Selection (ADR-010)](https://github.com/Bookie-Breaker/bookie-breaker-docs/blob/main/decisions/010-tech-stack-selection.md)
- [Local LLM Strategy (ADR-011)](https://github.com/Bookie-Breaker/bookie-breaker-docs/blob/main/decisions/011-local-llm-strategy.md)

## Environment Variables

See `.env.example` for all variables with descriptions.
