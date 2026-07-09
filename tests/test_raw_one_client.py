from __future__ import annotations

import json

import httpx
import pytest

from tongji.core.client import RawOneClient
from tongji.core.errors import SessionExpiredError
from tongji.core.session_store import SessionStore


@pytest.mark.asyncio
async def test_raw_one_client_injects_session_headers(tmp_path):
    store = SessionStore(tmp_path / "session.json")
    store.save("stored-session", source="manual", jsessionid="stored-jsession")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Token"] == "stored-session"
        assert request.headers["Cookie"] == "JSESSIONID=stored-jsession; sessionid=stored-session"
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
async def test_raw_one_client_sends_json_and_extra_headers(tmp_path):
    store = SessionStore(tmp_path / "session.json")
    store.save("stored-session", source="manual", jsessionid="stored-jsession")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Referer"] == "https://1.tongji.edu.cn/taskResultQuery"
        assert request.headers["Content-Type"] == "application/json"
        assert json.loads(request.content) == {"pageNum_": 1}
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

    assert await client.request(
        "POST",
        "/api/test",
        json={"pageNum_": 1},
        headers={"Referer": "https://1.tongji.edu.cn/taskResultQuery"},
    ) == {"ok": True}
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
