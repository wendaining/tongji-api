from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.responses import ok
from app.core.security import require_bearer_token
from app.raw_one.client import RawOneClient
from app.raw_one.services import courses as courses_service
from app.tools.dependencies import get_raw_one_client

RawOneClientDep = Annotated[RawOneClient, Depends(get_raw_one_client)]

router = APIRouter(
    prefix="/tools/tongji",
    tags=["tongji-courses"],
    dependencies=[Depends(require_bearer_token)],
)


@router.get("/courses")
async def courses(
    client: RawOneClientDep,
    calendar: int | None = Query(default=None),
    campus: str = Query(default=""),
    college: str = Query(default=""),
    course: str = Query(default=""),
    training_level: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=500),
) -> dict:
    return ok(
        await courses_service.query_courses(
            client,
            calendar=calendar,
            campus=campus,
            college=college,
            course=course,
            training_level=training_level,
            page=page,
            page_size=page_size,
        )
    )
