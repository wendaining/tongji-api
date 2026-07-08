from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.responses import ok
from app.core.security import require_bearer_token
from app.raw_one.login import LoginResultStatus, ProgrammaticLoginManager
from app.raw_one.session_store import SessionStore
from app.tools.dependencies import get_login_manager, get_session_store

LoginManagerDep = Annotated[ProgrammaticLoginManager, Depends(get_login_manager)]
SessionStoreDep = Annotated[SessionStore, Depends(get_session_store)]

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_bearer_token)],
)


class MfaCodeRequest(BaseModel):
    login_id: str = Field(min_length=1)
    code: str = Field(min_length=1)


class SessionUpdateRequest(BaseModel):
    sessionid: str = Field(min_length=1)
    jsessionid: str | None = None


def _login_result_payload(result) -> dict:
    if result.status == LoginResultStatus.SUCCESS:
        return {
            "status": result.status,
            "session": result.session_status,
        }
    return {
        "status": result.status,
        "login_id": result.login_id,
        "expires_at": result.expires_at.isoformat() if result.expires_at else None,
        "mfa": {
            "channel": result.mfa_channel,
            "masked_email": result.masked_email,
            "masked_mobile": result.masked_mobile,
            "next_step": "POST /admin/login/mfa with login_id and code",
        },
    }


@router.post("/login/start")
async def start_login(login_manager: LoginManagerDep) -> dict:
    result = await login_manager.start_login()
    return ok(_login_result_payload(result))


@router.post("/login/mfa")
async def submit_login_mfa(
    body: MfaCodeRequest,
    login_manager: LoginManagerDep,
) -> dict:
    result = await login_manager.submit_mfa_code(login_id=body.login_id, code=body.code)
    return ok(_login_result_payload(result))


@router.get("/login/{login_id}/status")
async def login_status(login_id: str, login_manager: LoginManagerDep) -> dict:
    return ok(await login_manager.pending_status(login_id))


@router.get("/session/status")
async def session_status(store: SessionStoreDep) -> dict:
    return ok(store.public_status())


@router.put("/session")
async def update_session(
    body: SessionUpdateRequest,
    store: SessionStoreDep,
) -> dict:
    store.save(body.sessionid, source="manual", jsessionid=body.jsessionid)
    return ok(store.public_status())


@router.delete("/session")
async def delete_session(store: SessionStoreDep) -> dict:
    store.clear()
    return ok(store.public_status())
