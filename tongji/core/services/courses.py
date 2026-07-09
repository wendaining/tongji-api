from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient

COURSE_SEARCH_PATH = "/api/arrangementservice/manualArrange/page"
COURSE_SEARCH_REFERER = "https://1.tongji.edu.cn/taskResultQuery"
COURSE_SEARCH_PAGE_SIZE = 200


def _course_search_payload(
    *,
    calendar_id: int,
    keyword: str,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    return {
        "condition": {
            "trainingLevel": "",
            "campus": "",
            "calendar": calendar_id,
            "college": "",
            "course": keyword,
            "ids": [],
            "isChineseTeaching": None,
        },
        "pageNum_": page,
        "pageSize_": page_size,
    }


async def search_all_courses(
    client: RawOneClient,
    *,
    calendar_id: int,
    keyword: str = "",
) -> Any:
    """Fetch every matching teaching class for a calendar.

    The upstream endpoint requires a JSON request body. A small probe obtains
    ``total_`` first, then every result page is fetched and merged into the
    original raw response envelope.

    Ref: XiaLing233/tongji-course-scheduler crawler/fetchCourseList.py.
    """
    headers = {"Referer": COURSE_SEARCH_REFERER}
    first = await client.request(
        "POST",
        COURSE_SEARCH_PATH,
        params={"profile": ""},
        json=_course_search_payload(
            calendar_id=calendar_id,
            keyword=keyword,
            page=1,
            page_size=20,
        ),
        headers=headers,
    )

    if not isinstance(first, dict):
        return first
    first_data = first.get("data")
    if not isinstance(first_data, dict) or not isinstance(first_data.get("list"), list):
        return first

    try:
        total = max(0, int(first_data.get("total_", len(first_data["list"]))))
    except (TypeError, ValueError):
        return first
    if total == 0:
        return first

    page_count = (total + COURSE_SEARCH_PAGE_SIZE - 1) // COURSE_SEARCH_PAGE_SIZE
    items: list[Any] = []
    for page in range(1, page_count + 1):
        response = await client.request(
            "POST",
            COURSE_SEARCH_PATH,
            params={"profile": ""},
            json=_course_search_payload(
                calendar_id=calendar_id,
                keyword=keyword,
                page=page,
                page_size=COURSE_SEARCH_PAGE_SIZE,
            ),
            headers=headers,
        )
        if not isinstance(response, dict):
            return response
        response_data = response.get("data")
        if not isinstance(response_data, dict) or not isinstance(response_data.get("list"), list):
            return response
        items.extend(response_data["list"])

    merged = dict(first)
    merged["data"] = {**first_data, "list": items}
    return merged


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


async def query_teaching_tasks(
    client: RawOneClient,
    *,
    calendar: int,
    keyword: str = "",
    campus: str = "",
    college: str = "",
    course: str = "",
    training_level: str = "",
    ids: list[int] | None = None,
    is_chinese_teaching: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> Any:
    """Query teaching tasks with full filter conditions (JSON body).

    Supports keyword search, campus filter, and other condition fields.
    Matches the browser Network request format.

    Ref: POST /api/arrangementservice/manualArrange/page?profile
    """
    condition: dict[str, Any] = {
        "trainingLevel": training_level,
        "campus": campus,
        "calendar": calendar,
        "college": college,
        "course": course,
        "ids": ids or [],
        "isChineseTeaching": is_chinese_teaching,
    }
    if keyword:
        condition["keyword"] = keyword

    # Ref: XiaLing233 — form-encoded + Spring MVC dot flattening for condition
    body: dict[str, Any] = {"pageNum_": page, "pageSize_": page_size}
    for k, v in condition.items():
        body[f"condition.{k}"] = v

    return await client.request(
        "POST",
        "/api/arrangementservice/manualArrange/page",
        params={"profile": ""},
        data=body,
    )
