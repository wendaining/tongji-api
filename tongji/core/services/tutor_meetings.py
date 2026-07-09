"""Tutor meeting (新生导师见面会) service.

Ref: Browser Network panel — schoolTutorMeeting page.
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def query_by_page(
    client: RawOneClient,
    *,
    search_type: str = "2",
    search_text: str = "",
    page: int = 1,
    page_size: int = 20,
) -> Any:
    """Query tutor meetings by page.

    ``search_type``: ``"2"`` = meeting name; other values TBD.
    Ref: POST /api/welcomeservice/tutorMeeting/queryByPage
    """
    body: dict[str, Any] = {
        "condition.searchType": search_type,
        "condition.searchText": search_text,
        "pageNum_": page,
        "pageSize_": page_size,
    }
    return await client.request(
        "POST",
        "/api/welcomeservice/tutorMeeting/queryByPage",
        data=body,
    )
