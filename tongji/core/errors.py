from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException


@dataclass(slots=True)
class AppError(Exception):
    code: str
    message: str
    status_code: int = status.HTTP_400_BAD_REQUEST
    details: dict[str, Any] | None = None
    action_required: str | None = None


class AuthNotConfiguredError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="AUTH_NOT_CONFIGURED",
            message="TJ_API_TOKEN is not configured.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class UnauthorizedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="UNAUTHORIZED",
            message="Missing or invalid bearer token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class NoSessionError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="NO_SESSION",
            message="No 1.tongji.edu.cn sessionid is stored. Please complete login first.",
            status_code=status.HTTP_409_CONFLICT,
        )


class SessionExpiredError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="SESSION_EXPIRED",
            message="1 系统登录态已失效，请重新登录 1 系统后更新 sessionid。",
            status_code=status.HTTP_401_UNAUTHORIZED,
            action_required="login",
        )


class UpstreamError(AppError):
    def __init__(
        self,
        message: str = "1 系统请求失败。",
        *,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="UPSTREAM_ERROR",
            message=message,
            status_code=status_code,
            details=details,
        )


def error_payload(error: AppError) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "error": {
            "code": error.code,
            "message": error.message,
        },
    }
    if error.details:
        payload["error"]["details"] = error.details
    if error.action_required:
        payload["error"]["action_required"] = error.action_required
    return payload


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(error_payload(exc), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        app_error = AppError(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": exc.errors()},
        )
        return JSONResponse(error_payload(app_error), status_code=app_error.status_code)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        app_error = AppError(
            code="HTTP_ERROR",
            message=str(exc.detail),
            status_code=exc.status_code,
        )
        return JSONResponse(error_payload(app_error), status_code=app_error.status_code)
