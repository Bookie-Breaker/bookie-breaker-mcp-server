"""Envelope-unwrapping HTTP layer shared by all backend clients.

The MCP server is a stateless REST bridge: every method returns the raw
``data`` payload (dict or list) from the standard BookieBreaker envelope
and maps failures to ToolError so the calling LLM sees an actionable
message instead of a stack trace.
"""

from typing import Any

import httpx

from mcp_server.errors import tool_error_from_exception, tool_error_from_response


class BackendClient:
    service_name = "backend"
    health_path = "/healthz"

    def __init__(self, base_url: str, client: httpx.AsyncClient) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    @property
    def base_url(self) -> str:
        return self._base_url

    async def get_data(self, path: str, params: dict[str, Any] | None = None, timeout: float | None = None) -> Any:
        try:
            response = await self._client.get(
                f"{self._base_url}{path}",
                params={k: v for k, v in (params or {}).items() if v is not None},
                timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
            )
        except httpx.HTTPError as exc:
            raise tool_error_from_exception(self.service_name, self._base_url, exc) from exc
        return self._unwrap(response)

    async def post_data(
        self,
        path: str,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        try:
            response = await self._client.post(
                f"{self._base_url}{path}",
                json=json,
                headers=headers,
                timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
            )
        except httpx.HTTPError as exc:
            raise tool_error_from_exception(self.service_name, self._base_url, exc) from exc
        return self._unwrap(response)

    def _unwrap(self, response: httpx.Response) -> Any:
        if response.status_code >= 400:
            raise tool_error_from_response(self.service_name, response)
        payload: dict[str, Any] = response.json()
        return payload.get("data", payload)

    async def is_healthy(self) -> bool:
        try:
            response = await self._client.get(f"{self._base_url}{self.health_path}", timeout=2.0)
        except httpx.HTTPError:
            return False
        return response.status_code == 200
