"""Compatibility patch for google-genai cleanup bugs.

The installed google-genai version may schedule BaseApiClient.aclose() from
__del__ even when no async httpx client was created. In that case the upstream
implementation raises AttributeError on `_async_httpx_client`.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from google.genai import _api_client


def apply_google_genai_cleanup_patch() -> None:
    if getattr(_api_client.BaseApiClient, "_mediflow_cleanup_patch", False):
        return

    original_aclose: Callable[..., Awaitable[None]] = _api_client.BaseApiClient.aclose

    async def safe_aclose(self) -> None:
        if (
            not self._http_options.httpx_async_client
            and not hasattr(self, "_async_httpx_client")
        ):
            if getattr(self, "_aiohttp_session", None) and not self._http_options.aiohttp_client:
                await self._aiohttp_session.close()
            return

        await original_aclose(self)

    _api_client.BaseApiClient.aclose = safe_aclose
    _api_client.BaseApiClient._mediflow_cleanup_patch = True


apply_google_genai_cleanup_patch()
