from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from tongji.core.login import LoginResultStatus

router = APIRouter(prefix="/admin", tags=["local-admin"])


class MfaRequest(BaseModel):
    login_id: str = Field(min_length=1)
    code: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


def _result_payload(result: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": result.status.value}
    if result.status == LoginResultStatus.SUCCESS:
        payload["session"] = result.session_status
    else:
        payload.update(
            {
                "login_id": result.login_id,
                "expires_at": result.expires_at,
                "mfa_channel": result.mfa_channel,
                "masked_email": result.masked_email,
                "masked_mobile": result.masked_mobile,
            }
        )
    return payload


@router.post("/login/start", summary="启动同济 IAM 登录")
async def login_start(request: Request) -> dict[str, Any]:
    result = await request.app.state.login_manager.start_login()
    return _result_payload(result)


@router.post("/login/mfa", summary="提交 IAM MFA 验证码")
async def login_mfa(request: Request, body: MfaRequest) -> dict[str, Any]:
    result = await request.app.state.login_manager.submit_mfa_code(
        login_id=body.login_id,
        code=body.code,
    )
    return _result_payload(result)


@router.get("/login/{login_id}", summary="查询登录挑战状态")
async def login_status(request: Request, login_id: str) -> dict[str, Any]:
    return await request.app.state.login_manager.pending_status(login_id)


@router.get("/session", summary="查询本地会话状态")
async def session_status(request: Request) -> dict[str, Any]:
    return request.app.state.session_store.public_status()


@router.delete("/session", summary="删除本地会话")
async def session_clear(request: Request) -> dict[str, Any]:
    await request.app.state.login_manager.logout()
    return request.app.state.session_store.public_status()
