from __future__ import annotations

import json

import httpx
import pytest

from tongji.core.client import RawOneClient
from tongji.core.services.courses import search_all_courses
from tongji.core.session_store import SessionStore


@pytest.mark.asyncio
async def test_search_all_courses_fetches_and_merges_every_page(tmp_path):
    store = SessionStore(tmp_path / "session.json")
    store.save("stored-session", source="manual", jsessionid="stored-jsession")
    requests: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/arrangementservice/manualArrange/page"
        assert request.url.query == b"profile="
        assert request.headers["Referer"] == "https://1.tongji.edu.cn/taskResultQuery"
        assert request.headers["X-Token"] == "stored-session"
        body = json.loads(request.content)
        requests.append(body)

        if body["pageSize_"] == 20:
            return httpx.Response(
                200,
                json={"code": 200, "data": {"list": [{"id": "probe"}], "total_": 201}},
            )
        start = (body["pageNum_"] - 1) * body["pageSize_"]
        end = min(start + body["pageSize_"], 201)
        return httpx.Response(
            200,
            json={
                "code": 200,
                "data": {
                    "list": [{"id": f"course-{index}"} for index in range(start, end)],
                    "total_": 201,
                },
            },
        )

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

    result = await search_all_courses(client, calendar_id=122, keyword="操作系统")

    assert [request["pageNum_"] for request in requests] == [1, 1, 2]
    assert [request["pageSize_"] for request in requests] == [20, 200, 200]
    assert all(request["condition"]["calendar"] == 122 for request in requests)
    assert all(request["condition"]["course"] == "操作系统" for request in requests)
    assert result["data"]["total_"] == 201
    assert len(result["data"]["list"]) == 201
    assert result["data"]["list"][0] == {"id": "course-0"}
    assert result["data"]["list"][-1] == {"id": "course-200"}
    await async_client.aclose()


@pytest.mark.asyncio
async def test_search_all_courses_preserves_non_paginated_upstream_response(tmp_path):
    store = SessionStore(tmp_path / "session.json")
    store.save("stored-session", source="manual", jsessionid="stored-jsession")
    upstream = {"code": 300, "message": "无数据"}
    async_client = httpx.AsyncClient(
        base_url="https://1.tongji.edu.cn",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=upstream)),
    )
    client = RawOneClient(
        base_url="https://1.tongji.edu.cn",
        timeout_seconds=15,
        session_store=store,
        client=async_client,
    )

    assert await search_all_courses(client, calendar_id=122) == upstream
    await async_client.aclose()
