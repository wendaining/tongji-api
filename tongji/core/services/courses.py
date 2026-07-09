from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def query_courses(
    client: RawOneClient,
    *,
    calendar: int | None,
    campus: str,
    college: str,
    course: str,
    training_level: str,
    page: int,
    page_size: int,
) -> Any:
    """Ref: XiaLing233 uses form-encoded POST bodies — align here too.

    Nested condition fields are flattened with dot notation as Spring MVC
    expects for form-encoded nested objects.
    """
    payload: dict[str, Any] = {
        "condition.trainingLevel": training_level,
        "condition.campus": campus,
        "condition.calendar": calendar or "",
        "condition.college": college,
        "condition.course": course,
        "condition.ids": "",
        "condition.isChineseTeaching": "",
        "pageNum_": page,
        "pageSize_": page_size,
    }
    return await client.request(
        "POST",
        "/api/arrangementservice/manualArrange/page",
        params={"profile": ""},
        data=payload,
    )


async def query_teaching_tasks(
    client: RawOneClient,
    *,
    calendar: int,
    keyword: str = "",
    campus: str = "",
    college: str = "",
    course: str = "",
    training_level: str = "",
    ids: list[int] | None = None,
    is_chinese_teaching: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> Any:
    """Query teaching tasks with full filter conditions (JSON body).

    Supports keyword search, campus filter, and other condition fields.
    Matches the browser Network request format.

    Ref: POST /api/arrangementservice/manualArrange/page?profile
    """
    condition: dict[str, Any] = {
        "trainingLevel": training_level,
        "campus": campus,
        "calendar": calendar,
        "college": college,
        "course": course,
        "ids": ids or [],
        "isChineseTeaching": is_chinese_teaching,
    }
    if keyword:
        condition["keyword"] = keyword

    # Ref: XiaLing233 — form-encoded + Spring MVC dot flattening for condition
    body: dict[str, Any] = {"pageNum_": page, "pageSize_": page_size}
    for k, v in condition.items():
        body[f"condition.{k}"] = v

    return await client.request(
        "POST",
        "/api/arrangementservice/manualArrange/page",
        params={"profile": ""},
        data=body,
    )
