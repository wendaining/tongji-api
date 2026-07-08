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
