"""Student timetable service.

Ref: app.js — GET /api/arrangementservice/timetable/course/{studentId}
    ?calendarId={id}&campus={code}
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def student_timetable(
    client: RawOneClient,
    *,
    student_id: str,
    calendar_id: int,
    campus: str = "",
) -> Any:
    """Fetch a student's course timetable for a given calendar and campus."""
    return await client.request(
        "GET",
        f"/api/arrangementservice/timetable/course/{student_id}",
        params={
            "calendarId": str(calendar_id),
            "campus": campus,
        },
    )


async def major_timetable(
    client: RawOneClient,
    *,
    code: str,
    grade: str,
    calendar_id: int,
    dir_code: str = "",
    is_major: bool = False,
) -> Any:
    """Fetch major (专业) timetable by major code, grade and calendar.

    Ref: GET /api/arrangementservice/timetable/major
    """
    import time

    return await client.request(
        "GET",
        "/api/arrangementservice/timetable/major",
        params={
            "code": code,
            "grade": grade,
            "calendarId": str(calendar_id),
            "dirCode": dir_code,
            "isMajor": str(is_major).lower(),
            "_t": str(int(time.time() * 1000)),
        },
    )
