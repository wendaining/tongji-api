from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.responses import ok
from app.core.security import require_bearer_token
from app.raw_one.client import RawOneClient
from app.raw_one.services import students as student_service
from app.tools.dependencies import get_raw_one_client

RawOneClientDep = Annotated[RawOneClient, Depends(get_raw_one_client)]

router = APIRouter(
    prefix="/tools/tongji/students",
    tags=["tongji-students"],
    dependencies=[Depends(require_bearer_token)],
)


@router.get("/me")
async def my_info(client: RawOneClientDep) -> dict:
    """Get the current user's student information."""
    return ok(await student_service.student_info_list(client, page=1, page_size=1))


@router.get("")
async def list_students(
    client: RawOneClientDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    student_id: str | None = Query(default=None, alias="studentId"),
    name: str | None = Query(default=None),
    faculty: str | None = Query(default=None),
    profession: str | None = Query(default=None),
    grade: str | None = Query(default=None),
) -> dict:
    """Search student information (scoped to the current user's visibility)."""
    return ok(
        await student_service.student_info_list(
            client,
            page=page,
            page_size=page_size,
            student_id=student_id,
            name=name,
            faculty=faculty,
            profession=profession,
            grade=grade,
        )
    )


@router.get("/status-professions")
async def status_professions(client: RawOneClientDep) -> dict:
    """List all known student status → profession mappings (dictionary)."""
    return ok(await student_service.status_profession_list(client))
