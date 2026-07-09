"""Exam (考试) services — undergraduate exam schedule and metadata.

Ref: Browser scan of /myExam page (2026-07-09).
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient

EXAM_AUTH_ID = 9102  # undergraduate exam auth context


# ---------------------------------------------------------------------------
# Session / Auth helpers
# ---------------------------------------------------------------------------


async def current_auth_id(client: RawOneClient, *, auth_id: int = EXAM_AUTH_ID) -> Any:
    """Set the current auth context for a specific module.

    The exam page calls this before querying exam data.

    Ref: POST /api/sessionservice/session/currentAuthId
    """
    return await client.request(
        "POST",
        "/api/sessionservice/session/currentAuthId",
        data={"authId": str(auth_id)},
    )


# ---------------------------------------------------------------------------
# Metadata / dictionary helpers
# ---------------------------------------------------------------------------


async def get_default_exam_type(client: RawOneClient) -> Any:
    """Get the default exam type / batch for undergraduate.

    Returns the currently active exam batch (e.g. 2024-2025学年第二学期).

    Ref: POST /api/electionservice/underGraduateExamSwitch/getDefaultType
    """
    return await client.request(
        "POST",
        "/api/electionservice/underGraduateExamSwitch/getDefaultType",
        data={},
    )


async def query_dictionary(
    client: RawOneClient,
    *,
    keys: list[str],
    lang: str = "cn",
    type_: str = "allChild",
    auth_id: int | None = None,
) -> Any:
    """Query the system reference dictionary.

    Used to fetch lookup values such as semesters (key ``X_XQ``),
    campus codes, exam types, etc.

    Ref: POST /api/commonservice/dictionary/query
    """
    body: dict[str, Any] = {
        "lang": lang,
        "type": type_,
        "keys": keys,
    }
    if auth_id is not None:
        body["authId"] = str(auth_id)

    return await client.request(
        "POST",
        "/api/commonservice/dictionary/query",
        data=body,
    )


# ---------------------------------------------------------------------------
# Exam schedule (main feature)
# ---------------------------------------------------------------------------


async def get_exam_schedule(
    client: RawOneClient,
    *,
    student_id: str | None = None,
) -> Any:
    """Query the undergraduate exam schedule.

    Returns a flat list of exam arrangements for the current student,
    including placement tests (分级考试) and regular term exams.

    Each exam entry includes subject name, exam time, location, result,
    and associated lookup windows.

    Ref: GET /api/welcomeservice/examinationStudents/exam
        Scanned from /myExam page, 2026-07-09.
    """
    params: dict[str, str] = {}
    if student_id:
        params["studentId"] = student_id

    return await client.request(
        "GET",
        "/api/welcomeservice/examinationStudents/exam",
        params=params if params else None,
    )
