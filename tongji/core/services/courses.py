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
