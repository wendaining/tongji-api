from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.responses import ok
from app.raw_one.client import RawOneClient
from app.raw_one.session_store import SessionStore
from app.tools import routes_admin, routes_calendar, routes_courses, routes_notices, routes_session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.require_api_token()

    session_store = SessionStore(
        settings.session_store_path,
        initial_sessionid=settings.sessionid,
    )
    raw_one_client = RawOneClient(
        base_url=settings.normalized_one_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        session_store=session_store,
    )
    app.state.session_store = session_store
    app.state.raw_one_client = raw_one_client

    try:
        yield
    finally:
        await raw_one_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="one-dot-tongji-api",
        version="0.1.0",
        lifespan=lifespan,
    )
    register_error_handlers(app)

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict:
        return ok({"status": "ok"})

    app.include_router(routes_admin.router)
    app.include_router(routes_session.router)
    app.include_router(routes_calendar.router)
    app.include_router(routes_notices.router)
    app.include_router(routes_courses.router)
    return app


app = create_app()

