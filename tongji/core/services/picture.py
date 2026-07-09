"""Picture / image query service (transformer).

Ref: Browser CDP scan of /StudentBaseInfo page, 2026-07-09.
"""

from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def query_picture(client: RawOneClient, *, student_ids: list[str]) -> Any:
    """Query student pictures / avatars by student ID list.

    Returns the picture URL or binary data for the requested students.

    Ref: POST /api/transformer/picture/queryPicture
        postData: {"list": ["student-demo"]}
    """
    return await client.request(
        "POST",
        "/api/transformer/picture/queryPicture",
        data={"list": student_ids},
    )
