"""Classroom / campus resource services.

Ref: Browser scan of /classroomUsageReport page, 2026-07-09.
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def condition_query_classroom_tower(client: RawOneClient) -> Any:
    """Query the classroom tower (教学楼) dictionary list.

    Returns a paginated dict with ``list`` of tower entries, each including
    ``id``, ``code``, ``name``, ``campus``, ``departmentCode`` etc.

    Ref: POST /api/baseresservice/classroomTowerInfo/conditionQueryByDict
    """
    return await client.request(
        "POST",
        "/api/baseresservice/classroomTowerInfo/conditionQueryByDict",
        data={},
    )


async def classroom_usage_report_count_query(
    client: RawOneClient,
    *,
    calendar_id: int,
    campus: str = "",
    tower_code: str = "",
    week_at: str = "1",
    page: int = 1,
    page_size: int = 20,
) -> Any:
    """Query the classroom usage report / occupancy statistics.

    Returns paginated classroom usage data for the given calendar and filters.

    Ref: POST /api/baseresservice/classroomOccupation/classroomUsageReportCountQuery
        postData: {pageNum_,pageSize_,calendarId,campus,towerCode,weekAt,
                   weekDayList:[],timeStart,timeEnd,conditionValue}
        Scanned from /classroomUsageReport page via CDP, 2026-07-09.
    """
    return await client.request(
        "POST",
        "/api/baseresservice/classroomOccupation/classroomUsageReportCountQuery",
        data={
            "pageNum_": page,
            "pageSize_": page_size,
            "calendarId": calendar_id,
            "campus": campus,
            "towerCode": tower_code,
            "weekAt": week_at,
            "weekDayList": [],
            "timeStart": "",
            "timeEnd": "",
            "conditionValue": "",
        },
    )
