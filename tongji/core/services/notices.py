from __future__ import annotations

import time
from typing import Any

from tongji.core.client import RawOneClient


async def list_notices(
    client: RawOneClient,
    *,
    page: int,
    page_size: int,
    keyword: str | None,
) -> Any:
    """Ref: XiaLing233 fetchNewEvents.py — findMyCommonMsgPublish (form-encoded).

    We call findCommonMsgPublishList (global search) instead of
    findMyCommonMsgPublish (user-scoped) since this is a general-purpose
    API, but we keep the same flat form-encoded body style.
    """
    payload: dict[str, Any] = {
        "pageNum_": page,
        "pageSize_": page_size,
    }
    if keyword:
        payload["condition.title"] = keyword
        payload["condition.keyword"] = keyword
    return await client.request(
        "POST",
        "/api/commonservice/commonMsgPublish/findCommonMsgPublishList",
        data=payload,
    )


async def home_page_notices(client: RawOneClient, *, page_size: int) -> Any:
    payload = {"pageNum_": 1, "pageSize_": page_size}
    return await client.request(
        "POST",
        "/api/commonservice/commonMsgPublish/findHomePageCommonMsgPublish",
        data=payload,
    )


async def notice_detail(client: RawOneClient, notice_id: str) -> Any:
    """Ref: XiaLing233 fetchNewEvents.py — findCommonMsgPublishById with t= timestamp."""
    return await client.request(
        "GET",
        "/api/commonservice/commonMsgPublish/findCommonMsgPublishById",
        params={"id": notice_id, "t": str(int(time.time() * 1000))},
    )


async def unread_count(client: RawOneClient) -> Any:
    return await client.request(
        "GET",
        "/api/commonservice/commonMsgPublish/myNotReadCommonMsgCount",
    )


async def my_notices(
    client: RawOneClient,
    *,
    page: int = 1,
    page_size: int = 50,
) -> Any:
    """Query the current user's scoped notice list (workbench widget).

    Uses ``findMyCommonMsgPublish`` instead of the global search variant
    — returns only notices relevant to the logged-in user.

    Ref: POST /api/commonservice/commonMsgPublish/findMyCommonMsgPublish
        Scanned from /workbench page, 2026-07-09.
    """
    return await client.request(
        "POST",
        "/api/commonservice/commonMsgPublish/findMyCommonMsgPublish",
        data={"pageNum_": page, "pageSize_": page_size},
    )
