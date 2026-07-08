"""Thin HTTP wrapper around tongji/core — mirrors neteasecloudmusicapi Enhanced pattern.

Start with ``python -m tongji serve`` or ``python tongji/server.py``.
No Bearer token — the 1.tongji.edu.cn session is the only authentication.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Query

from tongji.core.config import get_settings
from tongji.core.client import RawOneClient
from tongji.core.dict import translate_calendar, translate_course, translate_notice
from tongji.core.errors import register_error_handlers
from tongji.core.logging import configure_logging
from tongji.core.session_store import SessionStore
from tongji.core.services import (
    calendar as calendar_svc,
    courses as courses_svc,
    notices as notices_svc,
    session as session_svc,
    students as student_svc,
)

_client: RawOneClient | None = None


def _get_client() -> RawOneClient:
    if _client is None:
        raise RuntimeError("Server not initialized — check lifespan.")
    return _client


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    store = SessionStore(
        settings.session_store_path,
        initial_sessionid=settings.sessionid,
        initial_jsessionid=settings.jsessionid,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _client
        _client = RawOneClient(
            base_url=settings.normalized_one_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            session_store=store,
        )
        try:
            yield
        finally:
            await _client.aclose()

    app = FastAPI(title="tongji-api", version="0.2.0", lifespan=lifespan)
    register_error_handlers(app)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    @app.get("/healthz", tags=["health"])
    async def healthz():
        return {"ok": True, "status": "ok"}

    # ------------------------------------------------------------------
    # Student
    # ------------------------------------------------------------------
    @app.get("/students/me", tags=["students"])
    async def student_me():
        return await student_svc.student_info_list(_get_client(), page=1, page_size=1)

    @app.get("/students", tags=["students"])
    async def student_list(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=10, ge=1, le=100),
        student_id: str | None = Query(default=None, alias="studentId"),
        name: str | None = Query(default=None),
        faculty: str | None = Query(default=None),
        profession: str | None = Query(default=None),
        grade: str | None = Query(default=None),
    ):
        return await student_svc.student_info_list(
            _get_client(),
            page=page, page_size=page_size,
            student_id=student_id, name=name,
            faculty=faculty, profession=profession, grade=grade,
        )

    # ------------------------------------------------------------------
    # Notices
    # ------------------------------------------------------------------
    @app.get("/notices", tags=["notices"])
    async def notice_list(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=10, ge=1, le=100),
        keyword: str | None = Query(default=None),
        translated: bool = Query(default=False),
    ):
        result = await notices_svc.list_notices(
            _get_client(), page=page, page_size=page_size, keyword=keyword,
        )
        if translated:
            data = result.get("data") or {}
            data["list"] = [translate_notice(n) for n in (data.get("list") or [])]
        return result

    @app.get("/notices/{notice_id}", tags=["notices"])
    async def notice_detail(
        notice_id: str,
        translated: bool = Query(default=False),
    ):
        result = await notices_svc.notice_detail(_get_client(), notice_id)
        if translated:
            return translate_notice(result.get("data") or result)
        return result

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------
    @app.get("/courses", tags=["courses"])
    async def course_list(
        calendar: int | None = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=200),
        translated: bool = Query(default=False),
    ):
        result = await courses_svc.query_courses(
            _get_client(),
            calendar=calendar, campus="", college="", course="",
            training_level="", page=page, page_size=page_size,
        )
        if translated:
            data = result.get("data") or {}
            data["rows"] = [translate_course(r) for r in (data.get("rows") or [])]
        return result

    # ------------------------------------------------------------------
    # Calendar
    # ------------------------------------------------------------------
    @app.get("/calendar/list", tags=["calendar"])
    async def calendar_list(translated: bool = Query(default=False)):
        result = await calendar_svc.list_calendars(_get_client())
        if translated:
            return [translate_calendar(c) for c in (result.get("data") or [])]
        return result

    @app.get("/calendar/current-term", tags=["calendar"])
    async def calendar_current_term(translated: bool = Query(default=False)):
        result = await calendar_svc.current_term(_get_client())
        if translated:
            cal = (result.get("data") or {}).get("schoolCalendar") or {}
            return translate_calendar(cal)
        return result

    @app.get("/calendar/current-week", tags=["calendar"])
    async def calendar_current_week():
        return await calendar_svc.current_week(_get_client())

    @app.get("/calendar/{calendar_id}", tags=["calendar"])
    async def calendar_detail(calendar_id: str, translated: bool = Query(default=False)):
        result = await calendar_svc.calendar_detail(_get_client(), calendar_id)
        if translated:
            cal = result.get("data") or {}
            return translate_calendar(cal)
        return result

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------
    @app.get("/session/ping", tags=["session"])
    async def session_ping():
        return await session_svc.ping(_get_client())

    @app.get("/session/me", tags=["session"])
    async def session_user():
        return await session_svc.get_session_user(_get_client())

    return app


def run_server(host: str = "127.0.0.1", port: int = 8000):
    app = create_app()
    uvicorn.run(app, host=host, port=port)
