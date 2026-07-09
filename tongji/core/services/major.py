"""Major / score-rank services.

Ref: Browser scan of /studentScoreRank page, 2026-07-09.
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def query_student_score_rank(client: RawOneClient, *, student_id: str) -> Any:
    """Query the student's academic score ranking within their major.

    Returns rank info including ``score``, ``majorScoreRank``,
    ``majorScorePercent``, and ``majorStudentCount``.

    Ref: GET /api/majorservice/scoreRank/queryStudentScoreRank?studentId=...
    """
    return await client.request(
        "GET",
        "/api/majorservice/scoreRank/queryStudentScoreRank",
        params={"studentId": student_id},
    )
