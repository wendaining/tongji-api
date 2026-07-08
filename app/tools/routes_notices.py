from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.responses import ok
from app.core.security import require_bearer_token
from app.raw_one.client import RawOneClient
from app.raw_one.services import notices as notices_service
from app.tools.dependencies import get_raw_one_client

RawOneClientDep = Annotated[RawOneClient, Depends(get_raw_one_client)]

router = APIRouter(
    prefix="/tools/tongji/notices",
    tags=["tongji-notices"],
    dependencies=[Depends(require_bearer_token)],
)


@router.get("")
async def list_notices(
    client: RawOneClientDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    keyword: str | None = Query(default=None),
) -> dict:
    return ok(
        await notices_service.list_notices(
            client,
            page=page,
            page_size=page_size,
            keyword=keyword,
        )
    )


@router.get("/unread-count")
async def unread_count(client: RawOneClientDep) -> dict:
    return ok(await notices_service.unread_count(client))


@router.get("/{notice_id}")
async def notice_detail(notice_id: str, client: RawOneClientDep) -> dict:
    return ok(await notices_service.notice_detail(client, notice_id))
