from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def student_info_list(
    client: RawOneClient,
    *,
    page: int = 1,
    page_size: int = 10,
    student_id: str | None = None,
    name: str | None = None,
    faculty: str | None = None,
    profession: str | None = None,
    grade: str | None = None,
) -> Any:
    """Ref: app.js — POST findStuInfoList (form-encoded)."""
    payload: dict[str, Any] = {
        "pageNum_": page,
        "pageSize_": page_size,
    }
    if student_id:
        payload["studentId"] = student_id
    if name:
        payload["name"] = name
    if faculty:
        payload["faculty"] = faculty
    if profession:
        payload["profession"] = profession
    if grade:
        payload["grade"] = grade
    return await client.request(
        "POST",
        "/api/studentservice/studentInfo/findStuInfoList",
        data=payload,
    )


async def status_profession_list(client: RawOneClient) -> Any:
    """Ref: app.js — POST findStatusProfessionList (form-encoded)."""
    return await client.request(
        "POST",
        "/api/studentservice/studentInfo/findStatusProfessionList",
        data={},
    )
