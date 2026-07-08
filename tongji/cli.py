"""CLI entry point for tongji — run with ``python -m tongji <command>``.

Architecture mirrors `neteasecloudmusicapienhanced/api-enhanced`:
core/ is shared between CLI and HTTP server; this file is the thin CLI shell.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from tongji.core.config import get_settings
from tongji.core.client import RawOneClient
from tongji.core.logging import configure_logging
from tongji.core.session_store import SessionStore
from tongji.core.services import (
    calendar as calendar_svc,
    courses as courses_svc,
    notices as notices_svc,
    session as session_svc,
    students as student_svc,
)


def _print(data, *, ok=True):
    """Print JSON output for CLI."""
    payload = data if ok else {"ok": False, "error": str(data)}
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _load_client() -> RawOneClient:
    settings = get_settings()
    store = SessionStore(
        settings.session_store_path,
        initial_sessionid=settings.sessionid,
        initial_jsessionid=settings.jsessionid,
    )
    return RawOneClient(
        base_url=settings.normalized_one_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        session_store=store,
    )


async def cmd_login() -> None:
    """Programmatic login with IMAP auto-fetch for MFA."""
    from tongji.core.imap import ImapConfig
    from tongji.core.login import LoginResultStatus, ProgrammaticLoginManager

    settings = get_settings()
    store = SessionStore(
        settings.session_store_path,
        initial_sessionid=settings.sessionid,
        initial_jsessionid=settings.jsessionid,
    )

    imap_config = None
    if settings.imap_email and settings.imap_grantcode:
        imap_config = ImapConfig(
            email=settings.imap_email,
            grant_code=settings.imap_grantcode,
            server=settings.imap_server,
            port=settings.imap_port,
        )

    manager = ProgrammaticLoginManager(
        username=settings.iam_username,
        password=settings.iam_password,
        one_base_url=settings.normalized_one_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        session_store=store,
        imap_config=imap_config,
        pending_ttl_seconds=settings.login_expires_seconds,
    )

    try:
        result = await manager.start_login()
        if result.status == LoginResultStatus.SUCCESS:
            _print({"status": "SUCCESS", "session": result.session_status})
        else:
            _print({
                "status": "MFA_REQUIRED",
                "login_id": result.login_id,
                "hint": "Run: python -m tongji login --mfa <code> --id <login_id>",
            })
    finally:
        await manager.aclose()


async def cmd_login_mfa(login_id: str, code: str) -> None:
    from tongji.core.imap import ImapConfig
    from tongji.core.login import ProgrammaticLoginManager

    settings = get_settings()
    store = SessionStore(
        settings.session_store_path,
        initial_sessionid=settings.sessionid,
        initial_jsessionid=settings.jsessionid,
    )
    imap_config = None
    if settings.imap_email and settings.imap_grantcode:
        imap_config = ImapConfig(
            email=settings.imap_email,
            grant_code=settings.imap_grantcode,
            server=settings.imap_server,
            port=settings.imap_port,
        )

    manager = ProgrammaticLoginManager(
        username=settings.iam_username,
        password=settings.iam_password,
        one_base_url=settings.normalized_one_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        session_store=store,
        imap_config=imap_config,
        pending_ttl_seconds=settings.login_expires_seconds,
    )
    try:
        result = await manager.submit_mfa_code(login_id=login_id, code=code)
        _print({"status": "SUCCESS", "session": result.session_status})
    finally:
        await manager.aclose()


async def cmd_me() -> None:
    from tongji.core.dict import translate_student

    client = _load_client()
    try:
        result = await student_svc.student_info_list(client, page=1, page_size=1)
        students = (result.get("data") or {}).get("list", [])
        if students:
            _print(translate_student(students[0]))
        else:
            _print("未找到学生信息。", ok=False)
    finally:
        await client.aclose()


async def cmd_notices(page: int, page_size: int, keyword: str | None) -> None:
    from tongji.core.dict import translate_notice

    client = _load_client()
    try:
        result = await notices_svc.list_notices(client, page=page, page_size=page_size, keyword=keyword)
        data = (result.get("data") or {})
        raw_list = data.get("list") or []
        translated = [translate_notice(n) for n in raw_list]
        _print({"total": data.get("total_"), "page": data.get("pageNum_"), "items": translated})
    finally:
        await client.aclose()


async def cmd_notice_detail(notice_id: str) -> None:
    from tongji.core.dict import translate_notice

    client = _load_client()
    try:
        result = await notices_svc.notice_detail(client, notice_id)
        raw = (result.get("data") or result)
        _print(translate_notice(raw))
    finally:
        await client.aclose()


async def cmd_courses(calendar: int | None, page: int, page_size: int) -> None:
    from tongji.core.dict import translate_course

    client = _load_client()
    try:
        result = await courses_svc.query_courses(
            client,
            calendar=calendar,
            campus="",
            college="",
            course="",
            training_level="",
            page=page,
            page_size=page_size,
        )
        data = result.get("data") or {}
        translated = [translate_course(r) for r in (data.get("rows") or [])]
        _print({"total": data.get("total_"), "page": data.get("pageNum_"), "items": translated})
    finally:
        await client.aclose()


async def cmd_timetable(calendar: int | None) -> None:
    from tongji.core.dict import translate_timetable
    from tongji.core.services import timetable as tt_svc

    settings = get_settings()
    client = _load_client()
    try:
        stu_result = await student_svc.student_info_list(client, page=1, page_size=1)
        students = (stu_result.get("data") or {}).get("list", [])
        if not students:
            _print("无法获取学生信息。", ok=False)
            return
        s = students[0]
        sid = s.get("studentId", "")
        campus = str(s.get("campus", ""))
        cal = calendar or 121  # default to current term

        result = await tt_svc.student_timetable(client, student_id=sid, calendar_id=cal, campus=campus)
        raw_list = (result.get("data") or [])
        translated = [translate_timetable(r) for r in raw_list]
        _print({"calendar": cal, "count": len(translated), "items": translated})
    finally:
        await client.aclose()


async def cmd_scores() -> None:
    from tongji.core.dict import translate_grade_term, translate_grade_course
    from tongji.core.services import grades as grades_svc

    client = _load_client()
    try:
        stu_result = await student_svc.student_info_list(client, page=1, page_size=1)
        students = (stu_result.get("data") or {}).get("list", [])
        if not students:
            _print("未找到学生信息。", ok=False)
            return
        sid = students[0].get("studentId", "")

        result = await grades_svc.get_my_grades(client, student_id=sid)
        data = result.get("data") or {}

        terms = []
        for t in (data.get("term") or []):
            terms.append({
                **translate_grade_term(t),
                "课程": [translate_grade_course(c) for c in (t.get("creditInfo") or [])],
            })

        _print({
            "学号": sid,
            "总绩点": data.get("totalGradePoint"),
            "总学分": data.get("actualCredit"),
            "挂科学分": data.get("failingCredits"),
            "挂科数": data.get("failingCourseCount"),
            "学期": terms,
        })
    finally:
        await client.aclose()


async def cmd_plan() -> None:
    from tongji.core.dict import translate_credit_stats, translate_plan_course
    from tongji.core.services import culture as culture_svc

    client = _load_client()
    try:
        stu_result = await student_svc.student_info_list(client, page=1, page_size=1)
        students = (stu_result.get("data") or {}).get("list", [])
        if not students:
            _print("无法获取学生信息。", ok=False)
            return
        sid = students[0].get("studentId", "")

        # Credit stats
        credit_raw = await culture_svc.stats_credit(client, student_id=sid)
        credits = translate_credit_stats(credit_raw.get("data") or {})

        # Plan course tabs
        plan_raw = await culture_svc.plan_course_tab(client, student_id=sid)
        plan_courses = [translate_plan_course(c) for c in (plan_raw.get("data") or [])]

        _print({"学号": sid, "学分概况": credits, "课程模块": plan_courses})
    finally:
        await client.aclose()


async def cmd_calendar(action: str) -> None:
    from tongji.core.dict import translate_calendar

    client = _load_client()
    try:
        if action == "list":
            result = await calendar_svc.list_calendars(client)
            raw_list = (result.get("data") or [])
            _print({"items": [translate_calendar(c) for c in raw_list]})
        elif action == "current-term":
            result = await calendar_svc.current_term(client)
            cal = (result.get("data") or {}).get("schoolCalendar") or {}
            _print(translate_calendar(cal))
        elif action == "current-week":
            result = await calendar_svc.current_week(client)
            _print(result)
        else:
            _print(f"Unknown calendar action: {action}", ok=False)
            return
    finally:
        await client.aclose()


async def cmd_ping() -> None:
    client = _load_client()
    try:
        result = await session_svc.ping(client)
        _print(result)
    finally:
        await client.aclose()


def main():
    parser = argparse.ArgumentParser(
        prog="tongji",
        description="1.tongji.edu.cn CLI toolkit for AstrBot and agents.",
    )
    subs = parser.add_subparsers(dest="command")

    # login
    login_p = subs.add_parser("login", help="Login to 1.tongji.edu.cn (IAM + MFA)")
    login_p.add_argument("--mfa", metavar="CODE", help="MFA verification code")
    login_p.add_argument("--id", metavar="LOGIN_ID", help="Login ID from prior MFA_REQUIRED response")

    # me
    subs.add_parser("me", help="Get current student info")

    # notices
    n_p = subs.add_parser("notices", help="List notices")
    n_p.add_argument("--page", type=int, default=1)
    n_p.add_argument("--page-size", type=int, default=10)
    n_p.add_argument("--keyword")

    # notice detail
    nd_p = subs.add_parser("notice", help="Get notice detail")
    nd_p.add_argument("id", help="Notice ID")

    # courses
    c_p = subs.add_parser("courses", help="Query courses")
    c_p.add_argument("--calendar", type=int, default=None)
    c_p.add_argument("--page", type=int, default=1)
    c_p.add_argument("--page-size", type=int, default=20)

    # calendar
    cal_p = subs.add_parser("calendar", help="Calendar operations")
    cal_p.add_argument("action", choices=["list", "current-term", "current-week"])

    # scores
    subs.add_parser("scores", help="Course scores / grades")

    # plan
    subs.add_parser("plan", help="Culture plan / credit stats")

    # timetable
    tt_p = subs.add_parser("timetable", help="Student course timetable")
    tt_p.add_argument("--calendar", type=int, default=None)

    # ping
    subs.add_parser("ping", help="Test 1.tongji.edu.cn session")

    # serve
    serve_p = subs.add_parser("serve", help="Start HTTP server")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "serve":
        from tongji.server import run_server
        run_server(args.host, args.port)
        return

    if args.command == "login":
        if args.mfa and args.id:
            asyncio.run(cmd_login_mfa(args.id, args.mfa))
        else:
            asyncio.run(cmd_login())
        return

    # All other commands need a session
    settings = get_settings()
    configure_logging(settings.log_level)

    if args.command == "me":
        asyncio.run(cmd_me())
    elif args.command == "notices":
        asyncio.run(cmd_notices(args.page, args.page_size, args.keyword))
    elif args.command == "notice":
        asyncio.run(cmd_notice_detail(args.id))
    elif args.command == "courses":
        asyncio.run(cmd_courses(args.calendar, args.page, args.page_size))
    elif args.command == "calendar":
        asyncio.run(cmd_calendar(args.action))
    elif args.command == "scores":
        asyncio.run(cmd_scores())
    elif args.command == "plan":
        asyncio.run(cmd_plan())
    elif args.command == "timetable":
        asyncio.run(cmd_timetable(args.calendar))
    elif args.command == "ping":
        asyncio.run(cmd_ping())
    else:
        parser.print_help()
