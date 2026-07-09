from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def list_calendars(client: RawOneClient) -> Any:
    return await client.request("GET", "/api/baseresservice/schoolCalendar/list")


async def current_term(client: RawOneClient) -> Any:
    return await client.request("GET", "/api/baseresservice/schoolCalendar/currentTermCalendar")


async def current_week(client: RawOneClient) -> Any:
    return await client.request("GET", "/api/baseresservice/schoolCalendar/currentWeek")


async def calendar_detail(client: RawOneClient, calendar_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/baseresservice/schoolCalendar/detail",
        params={"id": calendar_id},
    )


async def professional_work(client: RawOneClient) -> Any:
    """Query the professional work / academic calendar schedule.

    Returns a list of date-range entries with business names (e.g. "上课",
    "考试", "实践教学").  Used by the workbench calendar widget.

    Ref: GET /api/baseresservice/schoolCalendar/professionalWork
    """
    return await client.request(
        "GET",
        "/api/baseresservice/schoolCalendar/professionalWork",
    )


async def query_holidays(client: RawOneClient, *, year: str) -> Any:
    """Query holiday schedule for a given year.

    Ref: GET /api/baseresservice/holiday/queryHolidayByYear?year=...
    """
    return await client.request(
        "GET",
        "/api/baseresservice/holiday/queryHolidayByYear",
        params={"year": year},
    )


async def query_operation_guide(client: RawOneClient) -> Any:
    """Query the user operation guide content.

    Returns guide articles displayed on the workbench help widget.

    Ref: GET /api/baseresservice/operationGuide/queryUserOperationGuide
    """
    return await client.request(
        "GET",
        "/api/baseresservice/operationGuide/queryUserOperationGuide",
    )

