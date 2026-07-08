from __future__ import annotations

from secrets import compare_digest
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import AuthNotConfiguredError, UnauthorizedError

bearer_scheme = HTTPBearer(auto_error=False)


async def require_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if not settings.api_token:
        raise AuthNotConfiguredError()
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError()
    if not compare_digest(credentials.credentials, settings.api_token):
        raise UnauthorizedError()
