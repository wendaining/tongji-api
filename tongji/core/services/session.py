from __future__ import annotations

from typing import Any

from tongji.core.client import RawOneClient


async def get_session_user(client: RawOneClient) -> Any:
    return await client.request("GET", "/api/sessionservice/session/getSessionUser")


async def ping(client: RawOneClient) -> Any:
    return await client.request("GET", "/api/sessionservice/session/ping")


async def set_language(client: RawOneClient, *, language: str = "cn") -> Any:
    """Set the session UI language.

    Ref: PUT /api/sessionservice/session/setLanguage
    """
    return await client.request(
        "PUT",
        "/api/sessionservice/session/setLanguage",
        data={"language": language},
    )
