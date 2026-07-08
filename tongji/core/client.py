from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from tongji.core.errors import NoSessionError, SessionExpiredError, UpstreamError
from tongji.core.session_store import SessionStore

SESSION_EXPIRED_MESSAGE = "sessionid is not exist."

# Ref: XiaLing233 fetchNewEvents.py — browser-like headers everywhere
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

REQUEST_HEADERS = {
    "User-Agent": BROWSER_USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
}


class RawOneClient:
    """Unified HTTP client for 1.tongji.edu.cn.

    All API calls go through this client so that session cookies and
    common headers are applied consistently.  Headers and cookie handling
    are aligned with XiaLing233 / fetch-1-dot-tongji.
    """

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
        data: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
        require_session: bool = True,
    ) -> Any:
        """Send a request to 1.tongji.edu.cn.

        Prefer ``data`` (form-encoded, xialing-style) over ``json_body``
        (JSON) when the reference implementation uses form data.
        """
        response = await self._send(
            method,
            path,
            params=params,
            data=data,
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
        data: Mapping[str, Any] | None,
        json_body: Any | None,
        require_session: bool,
    ) -> httpx.Response:
        headers = dict(REQUEST_HEADERS)
        sessionid = self.session_store.get_sessionid()
        cookie_header = self.session_store.get_cookie_header()

        if require_session:
            if not sessionid or not cookie_header:
                raise NoSessionError()
            headers["X-Token"] = sessionid
            headers["Cookie"] = cookie_header

        # Ref: XiaLing233 uses urlencode() for form posts — set the matching
        # Content-Type only when sending form data.
        if data is not None and json_body is None:
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        try:
            return await self._client.request(
                method,
                path,
                params=params,
                data=data,
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
