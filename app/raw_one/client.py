from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from app.core.errors import NoSessionError, SessionExpiredError, UpstreamError
from app.raw_one.session_store import SessionStore

SESSION_EXPIRED_MESSAGE = "sessionid is not exist."


class RawOneClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        session_store: SessionStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session_store = session_store
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
        require_session: bool = True,
    ) -> Any:
        response = await self._send(
            method,
            path,
            params=params,
            json_body=json_body,
            require_session=require_session,
        )
        return self._parse_response(response)

    async def _send(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None,
        json_body: Any | None,
        require_session: bool,
    ) -> httpx.Response:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "one-dot-tongji-api/0.1",
        }
        sessionid = self.session_store.get_sessionid()
        cookie_header = self.session_store.get_cookie_header()
        if require_session:
            if not sessionid or not cookie_header:
                raise NoSessionError()
            headers["X-Token"] = sessionid
            headers["Cookie"] = cookie_header

        try:
            return await self._client.request(
                method,
                path,
                params=params,
                json=json_body,
                headers=headers,
            )
        except httpx.TimeoutException as exc:
            raise UpstreamError("请求 1 系统超时。") from exc
        except httpx.TransportError as exc:
            raise UpstreamError("无法连接 1 系统。") from exc

    def _parse_response(self, response: httpx.Response) -> Any:
        data = self._decode_body(response)
        if self._is_session_expired(response, data):
            raise SessionExpiredError()
        if response.status_code >= 400:
            raise UpstreamError(
                "1 系统返回错误响应。",
                details={"upstream_status": response.status_code, "body": self._body_summary(data)},
            )
        return data

    @staticmethod
    def _decode_body(response: httpx.Response) -> Any:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type.lower():
            try:
                return response.json()
            except ValueError:
                return response.text[:500]
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return response.text[:500]

    @staticmethod
    def _body_summary(data: Any) -> Any:
        if isinstance(data, str):
            return data[:200]
        return data

    @staticmethod
    def _is_session_expired(response: httpx.Response, data: Any) -> bool:
        if response.status_code in {401, 403}:
            return True
        if isinstance(data, dict) and data.get("message") == SESSION_EXPIRED_MESSAGE:
            return True
        if isinstance(data, str) and SESSION_EXPIRED_MESSAGE in data:
            return True
        return False
