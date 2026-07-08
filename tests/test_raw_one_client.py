from __future__ import annotations

import httpx
import pytest

from app.core.errors import SessionExpiredError
from app.raw_one.client import RawOneClient
from app.raw_one.session_store import SessionStore


@pytest.mark.asyncio
async def test_raw_one_client_injects_session_headers(tmp_path):
    store = SessionStore(tmp_path / "session.json")
    store.save("stored-session", source="manual")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Token"] == "stored-session"
        assert request.headers["Cookie"] == "sessionid=stored-session"
        return httpx.Response(200, json={"ok": True})

    async_client = httpx.AsyncClient(
        base_url="https://1.tongji.edu.cn",
        transport=httpx.MockTransport(handler),
    )
    client = RawOneClient(
        base_url="https://1.tongji.edu.cn",
        timeout_seconds=15,
        session_store=store,
        client=async_client,
    )

    assert await client.request("GET", "/api/test") == {"ok": True}
    await async_client.aclose()


@pytest.mark.asyncio
async def test_raw_one_client_maps_session_expired_message(tmp_path):
    store = SessionStore(tmp_path / "session.json")
    store.save("bad-session", source="manual")

    async_client = httpx.AsyncClient(
        base_url="https://1.tongji.edu.cn",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(401, json={"message": "sessionid is not exist."})
        ),
    )
    client = RawOneClient(
        base_url="https://1.tongji.edu.cn",
        timeout_seconds=15,
        session_store=store,
        client=async_client,
    )

    with pytest.raises(SessionExpiredError):
        await client.request("GET", "/api/test")
    await async_client.aclose()


@pytest.mark.asyncio
async def test_login_with_sso_persists_sessionid_from_json(tmp_path):
    store = SessionStore(tmp_path / "session.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/sessionservice/session/login"
        assert request.method == "POST"
        assert request.content
        assert "X-Token" not in request.headers
        return httpx.Response(200, json={"data": {"sessionid": "new-session"}})

    async_client = httpx.AsyncClient(
        base_url="https://1.tongji.edu.cn",
        transport=httpx.MockTransport(handler),
    )
    client = RawOneClient(
        base_url="https://1.tongji.edu.cn",
        timeout_seconds=15,
        session_store=store,
        client=async_client,
    )

    sessionid = await client.login_with_sso(token="token", uid="uid", ts="ts")

    assert sessionid == "new-session"
    assert store.get_sessionid() == "new-session"
    await async_client.aclose()

