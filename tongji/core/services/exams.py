"""Exam (考试) services — read-only queries for exam schedule.

Ref: Browser Network panel — StuExamEnquiries page initialization flow.
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def current_auth_id(client: RawOneClient, *, auth_id: int = 9102) -> Any:
    """Set the current auth context for a specific module.

    The exam page calls this with authId=9102 (undergraduate exam context)
    before querying exam data.

    Ref: POST /api/sessionservice/session/currentAuthId
    """
    return await client.request(
        "POST",
        "/api/sessionservice/session/currentAuthId",
        json_body={"authId": auth_id},
    )


async def get_default_exam_type(client: RawOneClient) -> Any:
    """Get the default exam type / batch for undergraduate.

    Returns the currently active exam batch (e.g. 2024-2025学年第二学期),
    which is then used as a filter in subsequent exam queries.

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
        json_body=body,
    )
