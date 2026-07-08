"""Evaluation / questionnaire service.

Ref: Browser Network panel — schoolTutorMeeting page questionnaire force check.
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def force_questionnaire(client: RawOneClient, *, calendar_id: int) -> Any:
    """Force-check whether a questionnaire needs to be completed.

    The tutor meeting page calls this to see if the student must fill out
    a survey before proceeding.

    Ref: POST /api/evaluationservice/questionnaireStudent/force
    """
    return await client.request(
        "POST",
        "/api/evaluationservice/questionnaireStudent/force",
        json_body={"calendarId": calendar_id},
    )
