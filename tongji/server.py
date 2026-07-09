"""FastAPI adapter over the shared raw module registry and Agent tools."""

from __future__ import annotations

from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

import uvicorn
from fastapi import FastAPI

from tongji.admin_routes import router as admin_router
from tongji.core.client import RawOneClient
from tongji.core.config import Settings, get_settings
from tongji.core.errors import register_error_handlers
from tongji.core.imap import ImapConfig
from tongji.core.logging import configure_logging
from tongji.core.login import ProgrammaticLoginManager
from tongji.core.session_store import SessionStore
from tongji.modules.registry import get_registry
from tongji.routes import build_raw_router
from tongji.sdk import TongjiClient
from tongji.tools.routes import router as tools_router
from tongji.tools.service import AgentTools


def _version() -> str:
    try:
        return version("one-dot-tongji-api")
    except PackageNotFoundError:
        return "0.0.0"


def _imap_config(settings: Settings) -> ImapConfig | None:
    if not settings.imap_email or not settings.imap_grantcode:
        return None
    return ImapConfig(
        email=settings.imap_email,
        grant_code=settings.imap_grantcode,
        server=settings.imap_server,
        port=settings.imap_port,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    registry = get_registry()
    store = SessionStore(
        settings.session_store_path,
        initial_sessionid=settings.sessionid,
        initial_jsessionid=settings.jsessionid,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        raw_client = RawOneClient(
            base_url=settings.normalized_one_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            session_store=store,
        )
        login_manager = ProgrammaticLoginManager(
            username=settings.iam_username,
            password=settings.iam_password,
            one_base_url=settings.normalized_one_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            session_store=store,
            imap_config=_imap_config(settings),
            pending_ttl_seconds=settings.login_expires_seconds,
        )
        sdk = TongjiClient(raw_client, registry=registry)
        app.state.raw_client = raw_client
        app.state.login_manager = login_manager
        app.state.session_store = store
        app.state.sdk = sdk
        app.state.agent_tools = AgentTools(sdk)
        try:
            yield
        finally:
            await login_manager.aclose()
            await raw_client.aclose()

    app = FastAPI(
        title="tongji-api",
        version=_version(),
        description=("Raw 1.tongji.edu.cn modules and normalized tools for AstrBot and agents."),
        lifespan=lifespan,
    )
    register_error_handlers(app)

    @app.get("/healthz", tags=["health"], summary="服务存活检查")
    async def healthz() -> dict[str, object]:
        return {"ok": True, "status": "ok", "version": _version()}

    @app.get("/meta/modules", tags=["metadata"], summary="列出 raw API modules")
    async def module_metadata() -> dict[str, object]:
        return {"count": len(registry), "modules": registry.metadata()}

    @app.get("/meta/tools", tags=["metadata"], summary="列出 Agent 工具")
    async def tool_metadata() -> dict[str, object]:
        tools = [route for route in app.openapi()["paths"] if route.startswith("/tools/tongji/")]
        return {"count": len(tools), "tools": tools}

    app.include_router(build_raw_router(registry))
    app.include_router(tools_router)
    if settings.is_loopback_host:
        app.include_router(admin_router)
    return app


def run_server(host: str | None = None, port: int | None = None) -> None:
    settings = get_settings()
    uvicorn.run(
        create_app(settings),
        host=host or settings.host,
        port=port or settings.port,
    )
