from __future__ import annotations

from typing import Any

from app.raw_one.client import RawOneClient


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

