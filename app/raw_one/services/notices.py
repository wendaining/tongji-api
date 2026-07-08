from __future__ import annotations

from typing import Any

from app.raw_one.client import RawOneClient


async def list_notices(
    client: RawOneClient,
    *,
    page: int,
    page_size: int,
    keyword: str | None,
) -> Any:
    payload: dict[str, Any] = {
        "condition": {},
        "pageNum_": page,
        "pageSize_": page_size,
    }
    if keyword:
        payload["condition"]["title"] = keyword
        payload["condition"]["keyword"] = keyword
    return await client.request(
        "POST",
        "/api/commonservice/commonMsgPublish/findCommonMsgPublishList",
        json_body=payload,
    )


async def home_page_notices(client: RawOneClient, *, page_size: int) -> Any:
    payload = {"pageNum_": 1, "pageSize_": page_size}
    return await client.request(
        "POST",
        "/api/commonservice/commonMsgPublish/findHomePageCommonMsgPublish",
        json_body=payload,
    )


async def notice_detail(client: RawOneClient, notice_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/commonservice/commonMsgPublish/findCommonMsgPublishById",
        params={"id": notice_id},
    )


async def unread_count(client: RawOneClient) -> Any:
    return await client.request(
        "GET",
        "/api/commonservice/commonMsgPublish/myNotReadCommonMsgCount",
    )

