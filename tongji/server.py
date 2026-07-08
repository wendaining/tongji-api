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
from tongji.core.dict import translate_calendar, translate_course, translate_credit_stats, translate_dictionary_item, translate_exam_arrange, translate_grade_course, translate_grade_term, translate_notice, translate_plan_course, translate_timetable, translate_tutor_meeting
from tongji.core.errors import register_error_handlers
from tongji.core.logging import configure_logging
from tongji.core.session_store import SessionStore
from tongji.core.services import (
    calendar as calendar_svc,
    courses as courses_svc,
    exams as exams_svc,
    notices as notices_svc,
    session as session_svc,
    students as student_svc,
    tutor_meetings as tutor_svc,
    culture as culture_svc,
    grades as grades_svc,
    timetable as timetable_svc,
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
    # Culture Plan
    # ------------------------------------------------------------------
    @app.get("/plan/credits", tags=["plan"])
    async def plan_credits(
        student_id: str = Query(alias="studentId"),
        translated: bool = Query(default=False),
    ):
        result = await culture_svc.stats_credit(_get_client(), student_id=student_id)
        if translated:
            return translate_credit_stats(result.get("data") or {})
        return result

    @app.get("/plan/courses", tags=["plan"])
    async def plan_courses(
        student_id: str = Query(alias="studentId"),
        translated: bool = Query(default=False),
    ):
        result = await culture_svc.plan_course_tab(_get_client(), student_id=student_id)
        if translated:
            return [translate_plan_course(c) for c in (result.get("data") or [])]
        return result

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Timetable
    # ------------------------------------------------------------------
    @app.get("/timetable", tags=["timetable"])
    async def timetable(
        student_id: str = Query(alias="studentId"),
        calendar_id: int = Query(alias="calendarId"),
        campus: str = Query(default=""),
        translated: bool = Query(default=False),
    ):
        result = await timetable_svc.student_timetable(
            _get_client(),
            student_id=student_id,
            calendar_id=calendar_id,
            campus=campus,
        )
        if translated:
            return [translate_timetable(r) for r in (result.get("data") or [])]
        return result

    @app.get("/grades", tags=["grades"])
    async def my_grades(
        student_id: str = Query(alias="studentId"),
        translated: bool = Query(default=False),
    ):
        result = await grades_svc.get_my_grades(_get_client(), student_id=student_id)
        if translated:
            data = result.get("data") or {}
            terms = []
            for t in (data.get("term") or []):
                terms.append({
                    **translate_grade_term(t),
                    "课程": [translate_grade_course(c) for c in (t.get("creditInfo") or [])],
                })
            return {
                "总绩点": data.get("totalGradePoint"),
                "总学分": data.get("actualCredit"),
                "挂科学分": data.get("failingCredits"),
                "挂科数": data.get("failingCourseCount"),
                "学期": terms,
            }
        return result

    # ------------------------------------------------------------------
    # Exams
    # ------------------------------------------------------------------
    @app.get("/exams/info", tags=["exams"])
    async def exams_info():
        """Return default exam type and semester list."""
        client = _get_client()
        await exams_svc.current_auth_id(client, auth_id=9102)
        exam_type = await exams_svc.get_default_exam_type(client)
        semesters = await exams_svc.query_dictionary(
            client, keys=["X_XQ"], auth_id=9102,
        )
        return {
            "default_exam_type": exam_type.get("data") or exam_type,
            "semesters": semesters.get("data") or semesters,
        }

    @app.get("/exams/dictionary", tags=["exams"])
    async def exams_dictionary(
        keys: str = Query(..., description="Comma-separated dictionary keys, e.g. X_XQ"),
        auth_id: int | None = Query(default=None, alias="authId"),
        translated: bool = Query(default=False),
    ):
        """Query system dictionary for reference data (semesters, exam types, etc.)."""
        key_list = [k.strip() for k in keys.split(",")]
        result = await exams_svc.query_dictionary(
            _get_client(), keys=key_list, auth_id=auth_id,
        )
        if translated:
            data = result.get("data")
            if isinstance(data, dict):
                # Dictionary data is keyed — translate each child list
                out = {}
                for k, v in data.items():
                    if isinstance(v, list):
                        out[k] = [translate_dictionary_item(i) if isinstance(i, dict) else i for i in v]
                    else:
                        out[k] = v
                return out
            return result
        return result

    # ------------------------------------------------------------------
    # Tutor Meetings
    # ------------------------------------------------------------------
    @app.get("/tutor-meetings", tags=["tutor-meetings"])
    async def tutor_meetings(
        search_text: str = Query(default="", alias="searchText"),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        translated: bool = Query(default=False),
    ):
        """Query freshman tutor meetings (新生导师见面会)."""
        client = _get_client()
        await exams_svc.current_auth_id(client, auth_id=13087)
        await session_svc.set_language(client)
        result = await tutor_svc.query_by_page(
            client,
            search_type="2",
            search_text=search_text,
            page=page,
            page_size=page_size,
        )
        if translated:
            data = result.get("data") or {}
            lst = data.get("list") or []
            data["list"] = [translate_tutor_meeting(r) for r in lst]
            return data
        return result

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
