from __future__ import annotations

from typing import Any

from app.raw_one.client import RawOneClient


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
    payload = {
        "condition": {
            "trainingLevel": training_level,
            "campus": campus,
            "calendar": calendar,
            "college": college,
            "course": course,
            "ids": [],
            "isChineseTeaching": None,
        },
        "pageNum_": page,
        "pageSize_": page_size,
    }
    return await client.request(
        "POST",
        "/api/arrangementservice/manualArrange/page",
        params={"profile": ""},
        json_body=payload,
    )

