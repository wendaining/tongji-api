"""Student grades service.

Ref: oldStysteMyGrades page — GET /api/scoremanagementservice/scoreGrades/getMyGrades
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def get_my_grades(client: RawOneClient, *, student_id: str) -> Any:
    """Fetch complete grade report including all terms, courses, GPA.

    Returns: {totalGradePoint, actualCredit, failingCredits, failingCourseCount, term: [...]}
    """
    return await client.request(
        "GET",
        "/api/scoremanagementservice/scoreGrades/getMyGrades",
        params={"studentId": student_id},
    )
