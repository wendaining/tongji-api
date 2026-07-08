"""Teaching progress (教学进度) service.

Ref: Browser Network panel — auditProgressList page.
"""

from __future__ import annotations

import time
from typing import Any

from tongji.core.client import RawOneClient


async def progress_query(
    client: RawOneClient,
    *,
    calendar_id: int | None = None,
    dept_id: str = "1",
    training_level: str = "",
    nature: str = "",
    name: str = "",
    label: str = "",
    short_exchange: str = "",
    long_exchange: str = "",
    week_num: str = "",
    day_of_week: str = "",
    section: str = "",
    keyword: str = "",
    keyword2: str = "",
    page: int = 1,
    page_size: int = 20,
) -> Any:
    """Query teaching progress list.

    Ref: POST /api/arrangementservice/teachingProgress/progressQuery
    """
    condition: dict[str, Any] = {
        "deptId": dept_id,
        "trainingLevel": training_level,
        "nature": nature,
        "name": name,
        "label": label,
        "shortExchange": short_exchange,
        "longExchange": long_exchange,
        "weekNum": week_num,
        "dayOfWeek": day_of_week,
        "section": section,
        "keyWord": keyword,
        "keyWord2": keyword2,
    }
    if calendar_id is not None:
        condition["calendarId"] = calendar_id

    return await client.request(
        "POST",
        "/api/arrangementservice/teachingProgress/progressQuery",
        json_body={"condition": condition, "pageNum_": page, "pageSize_": page_size},
    )


async def get_progress_detail(
    client: RawOneClient, *, id: str, keywords: str = "", page: int = 1, page_size: int = 20
) -> Any:
    """Get teaching progress detail / page content.

    Ref: POST /api/arrangementservice/teachingProgress/getPageContentById
    """
    return await client.request(
        "POST",
        "/api/arrangementservice/teachingProgress/getPageContentById",
        json_body={"condition": {"id": id, "keywords": keywords}, "pageNum_": page, "pageSize_": page_size},
    )


async def get_assist_teacher(client: RawOneClient, *, teaching_class_id: str) -> Any:
    """Get assistant teacher info for a teaching class.

    Ref: GET /api/arrangementservice/teachingProgress/getAssistTeacher
    """
    return await client.request(
        "GET",
        "/api/arrangementservice/teachingProgress/getAssistTeacher",
        params={"teachingClassId": teaching_class_id, "_t": str(int(time.time() * 1000))},
    )
