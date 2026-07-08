from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator

from app.core.config import Settings, get_settings
from app.core.responses import ok
from app.core.security import require_bearer_token
from app.raw_one.client import RawOneClient
from app.raw_one.login import parse_ssologin_callback_url
from app.raw_one.session_store import SessionStore
from app.tools.dependencies import get_raw_one_client, get_session_store

SettingsDep = Annotated[Settings, Depends(get_settings)]
RawOneClientDep = Annotated[RawOneClient, Depends(get_raw_one_client)]
SessionStoreDep = Annotated[SessionStore, Depends(get_session_store)]

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_bearer_token)],
)


class LoginCompleteRequest(BaseModel):
    callback_url: str | None = None
    token: str | None = None
    uid: str | None = None
    ts: str | None = None

    @model_validator(mode="after")
    def validate_callback_or_triplet(self) -> LoginCompleteRequest:
        has_callback = bool(self.callback_url)
        has_triplet = bool(self.token and self.uid and self.ts)
        if has_callback == has_triplet:
            raise ValueError("Provide either callback_url or token/uid/ts.")
        return self


class SessionUpdateRequest(BaseModel):
    sessionid: str = Field(min_length=1)


@router.post("/login/start")
async def start_login(settings: SettingsDep) -> dict:
    login_url = f"{settings.normalized_one_base_url}/api/ssoservice/system/loginIn"
    return ok(
        {
            "login_url": login_url,
            "login_url_type": "one_entry_redirects_to_iam",
            "completion": {
                "method": "POST",
                "url": "/admin/login/complete",
                "body": {"callback_url": "https://1.tongji.edu.cn/ssologin?token=...&uid=...&ts=..."},
            },
        }
    )


@router.post("/login/complete")
async def complete_login(
    body: LoginCompleteRequest,
    client: RawOneClientDep,
    store: SessionStoreDep,
) -> dict:
    if body.callback_url:
        callback = parse_ssologin_callback_url(body.callback_url)
        token, uid, ts = callback.token, callback.uid, callback.ts
    else:
        token, uid, ts = body.token or "", body.uid or "", body.ts or ""
    await client.login_with_sso(token=token, uid=uid, ts=ts)
    return ok(store.public_status())


@router.get("/session/status")
async def session_status(store: SessionStoreDep) -> dict:
    return ok(store.public_status())


@router.put("/session")
async def update_session(
    body: SessionUpdateRequest,
    store: SessionStoreDep,
) -> dict:
    store.save(body.sessionid, source="manual")
    return ok(store.public_status())


@router.delete("/session")
async def delete_session(store: SessionStoreDep) -> dict:
    store.clear()
    return ok(store.public_status())
