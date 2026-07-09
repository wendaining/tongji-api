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


async def query_course_tags(client: RawOneClient, *, student_id: str) -> Any:
    """Query the course category / tag tree used for filtering on the grades page.

    Returns a flat list of tag nodes with ``id``, ``parentID``, ``nameCN``,
    ``shortName``, ``trainingLevel`` etc. — constructing a tree is the
    caller's responsibility.

    Ref: GET /api/scoremanagementservice/studentScoreBk/queryCourseTag?studentId=...
        Scanned from /oldStysteMyGrades page, 2026-07-09.
    """
    return await client.request(
        "GET",
        "/api/scoremanagementservice/studentScoreBk/queryCourseTag",
        params={"studentId": student_id},
    )
