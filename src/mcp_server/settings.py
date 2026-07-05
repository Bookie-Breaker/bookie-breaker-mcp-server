"""Runtime configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    port: int = 8007
    log_level: str = "info"
    mcp_transport: str = "stdio"  # stdio | http (streamable HTTP)

    agent_url: str = "http://localhost:8006"
    lines_service_url: str = "http://localhost:8001"
    statistics_service_url: str = "http://localhost:8002"
    simulation_engine_url: str = "http://localhost:8003"
    prediction_engine_url: str = "http://localhost:8004"
    bookie_emulator_url: str = "http://localhost:8005"

    request_timeout_seconds: float = 10.0
    analysis_timeout_seconds: float = 120.0  # ask_analyst waits on an LLM


@lru_cache
def get_settings() -> Settings:
    return Settings()
