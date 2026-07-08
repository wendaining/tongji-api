from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.responses import ok
from app.core.security import require_bearer_token
from app.raw_one.client import RawOneClient
from app.raw_one.services import calendar as calendar_service
from app.tools.dependencies import get_raw_one_client

RawOneClientDep = Annotated[RawOneClient, Depends(get_raw_one_client)]

router = APIRouter(
    prefix="/tools/tongji/calendar",
    tags=["tongji-calendar"],
    dependencies=[Depends(require_bearer_token)],
)


@router.get("/list")
async def list_calendars(client: RawOneClientDep) -> dict:
    return ok(await calendar_service.list_calendars(client))


@router.get("/current-term")
async def current_term(client: RawOneClientDep) -> dict:
    return ok(await calendar_service.current_term(client))


@router.get("/current-week")
async def current_week(client: RawOneClientDep) -> dict:
    return ok(await calendar_service.current_week(client))


@router.get("/{calendar_id}")
async def calendar_detail(calendar_id: str, client: RawOneClientDep) -> dict:
    return ok(await calendar_service.calendar_detail(client, calendar_id))
