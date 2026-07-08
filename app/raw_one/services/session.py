from __future__ import annotations

from typing import Any

from app.raw_one.client import RawOneClient


async def get_session_user(client: RawOneClient) -> Any:
    return await client.request("GET", "/api/sessionservice/session/getSessionUser")


async def ping(client: RawOneClient) -> Any:
    return await client.request("GET", "/api/sessionservice/session/ping")

