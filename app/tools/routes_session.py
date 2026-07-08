from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.responses import ok
from app.core.security import require_bearer_token
from app.raw_one.client import RawOneClient
from app.raw_one.services import session as session_service
from app.tools.dependencies import get_raw_one_client

RawOneClientDep = Annotated[RawOneClient, Depends(get_raw_one_client)]

router = APIRouter(
    prefix="/tools/tongji",
    tags=["tongji-session"],
    dependencies=[Depends(require_bearer_token)],
)


@router.get("/me")
async def me(client: RawOneClientDep) -> dict:
    return ok(await session_service.get_session_user(client))


@router.get("/session/ping")
async def ping(client: RawOneClientDep) -> dict:
    return ok(await session_service.ping(client))
