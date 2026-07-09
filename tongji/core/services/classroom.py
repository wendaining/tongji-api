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
