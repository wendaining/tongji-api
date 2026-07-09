from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

from tongji.core.errors import UpstreamError
from tongji.sdk import TongjiClient
from tongji.tools.models import (
    CalendarSummary,
    CourseSummary,
    ExamSummary,
    NoticeSummary,
    StudentSummary,
    ToolSuccess,
)


def _data(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def _items(payload: Any) -> list[dict[str, Any]]:
    value = _data(payload)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("list", "rows", "records", "items"):
            items = value.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


def _display(raw: dict[str, Any], key: str) -> Any:
    return raw.get(f"{key}I18n") or raw.get(key)


def _student(raw: dict[str, Any]) -> StudentSummary:
    return StudentSummary(
        student_id=str(raw.get("studentId") or "") or None,
        name=raw.get("name"),
        grade=str(raw.get("grade") or "") or None,
        faculty=_display(raw, "faculty"),
        profession=_display(raw, "profession"),
        campus_code=raw.get("campus"),
        campus_name=_display(raw, "campus"),
        training_level_code=raw.get("trainingLevel"),
        training_level_name=_display(raw, "trainingLevel"),
    )


def _parse_date_ms(value: Any) -> str | None:
    """Convert a millisecond Unix timestamp to a YYYY-MM-DD string."""
    if not value:
        return None
    try:
        ts = int(value)
        if ts > 1_000_000_000_000:  # milliseconds → seconds
            ts //= 1000
        dt = datetime.fromtimestamp(ts, tz=UTC)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return str(value)


def _calendar(raw: dict[str, Any]) -> CalendarSummary:
    year_val = raw.get("year") or raw.get("academicYear")
    academic_year: str | None
    if isinstance(year_val, int):
        academic_year = f"{year_val}-{year_val + 1}"
    else:
        academic_year = str(year_val or "").strip() or None

    term_code = raw.get("term")
    term_name: str | None = raw.get("termI18n")
    if not term_name and term_code is not None:
        term_name = f"第{term_code}学期"
    elif not term_name:
        term_name = None
    else:
        term_name = str(term_name)

    return CalendarSummary(
        calendar_id=raw.get("id") or raw.get("calendarId"),
        academic_year=academic_year,
        term_code=term_code,
        term_name=term_name,
        begin_date=_parse_date_ms(raw.get("beginDay")) or raw.get("startDate"),
        end_date=_parse_date_ms(raw.get("endDay")) or raw.get("endDate"),
        total_weeks=raw.get("weekNum"),
    )


def _notice(raw: dict[str, Any], *, include_content: bool = False) -> NoticeSummary:
    return NoticeSummary(
        notice_id=raw.get("id"),
        title=raw.get("title"),
        publisher=raw.get("createUser"),
        publish_time=raw.get("publishTime"),
        start_time=raw.get("startTime"),
        end_time=raw.get("endTime"),
        audience=raw.get("faceUserName"),
        content=raw.get("content") if include_content else None,
        attachments=raw.get("commonAttachmentList") or [],
    )


def _course(raw: dict[str, Any]) -> CourseSummary:
    return CourseSummary(
        course_code=raw.get("courseCode") or raw.get("code"),
        course_name=raw.get("courseName") or raw.get("name"),
        teacher_name=raw.get("teacherName") or raw.get("teacher"),
        classroom_name=raw.get("classroomName") or raw.get("classroom"),
        weekday=raw.get("weekDay") or raw.get("day"),
        start_section=raw.get("startSection"),
        end_section=raw.get("endSection") or raw.get("period"),
        weeks=raw.get("weeks") or raw.get("week"),
        campus_name=raw.get("campusName") or _display(raw, "campus"),
        credit=raw.get("credit"),
    )


def _exam(raw: dict[str, Any]) -> ExamSummary:
    return ExamSummary(
        exam_id=raw.get("id"),
        subject=raw.get("subject"),
        exam_time=raw.get("examTime"),
        location=raw.get("examAddress"),
        result=raw.get("examResults"),
        calendar_name=raw.get("calendarName"),
        notice=raw.get("notice"),
    )


def _current_term_record(payload: Any) -> dict[str, Any]:
    value = _data(payload)
    if isinstance(value, dict):
        nested = value.get("schoolCalendar")
        if isinstance(nested, dict):
            return nested
        return value
    return {}


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _calculated_week(term: dict[str, Any], today: date) -> int | None:
    start = _parse_date(
        term.get("teachingWeekStart") or term.get("beginDay") or term.get("startDate")
    )
    if start is None:
        return None
    first_monday = start - timedelta(days=start.weekday())
    week = ((today - first_monday).days // 7) + 1
    total = term.get("weekNum")
    if week < 1:
        return 0
    if isinstance(total, int) and week > total:
        return total + 1
    return week


def _extract_week(payload: Any) -> int | None:
    value = _data(payload)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    if isinstance(value, dict):
        for key in ("currentWeek", "week", "weekNum"):
            candidate = value.get(key)
            if isinstance(candidate, int):
                return candidate
            if isinstance(candidate, str) and candidate.isdigit():
                return int(candidate)
    return None


def _active_in_week(value: Any, week: int | None) -> bool:
    if week is None or value in (None, "", []):
        return True
    if isinstance(value, list):
        return week in {int(item) for item in value if str(item).isdigit()}
    numbers: set[int] = set()
    for start, end in re.findall(r"(\d+)(?:\s*[-~至]\s*(\d+))?", str(value)):
        first = int(start)
        last = int(end) if end else first
        numbers.update(range(first, last + 1))
    return not numbers or week in numbers


class AgentTools:
    def __init__(self, sdk: TongjiClient) -> None:
        self.sdk = sdk

    async def me(self) -> ToolSuccess:
        items = _items(await self.sdk.call("students_me"))
        return ToolSuccess(data=_student(items[0]).model_dump() if items else None)

    async def current_term(self) -> ToolSuccess:
        raw = _current_term_record(await self.sdk.call("calendar_current_term"))
        return ToolSuccess(data=_calendar(raw).model_dump())

    async def current_week(self, *, today: date | None = None) -> ToolSuccess:
        today = today or date.today()
        try:
            week = _extract_week(await self.sdk.call("calendar_current_week"))
            if week is not None:
                return ToolSuccess(data={"week": week}, meta={"source": "upstream"})
        except UpstreamError:
            pass
        term = _current_term_record(await self.sdk.call("calendar_current_term"))
        week = _calculated_week(term, today)
        if week is None:
            raise UpstreamError("无法从 1 系统校历计算当前教学周。")
        return ToolSuccess(
            data={"week": week},
            meta={"source": "calculated", "date": today.isoformat()},
        )

    async def calendars(self) -> ToolSuccess:
        raw_items = _items(await self.sdk.call("calendar_list"))
        items = [_calendar(item).model_dump() for item in raw_items]
        return ToolSuccess(data=items, meta={"count": len(items)})

    async def notices(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
    ) -> ToolSuccess:
        raw = await self.sdk.call(
            "notices_my",
            {"page": page, "page_size": page_size},
        )
        items = [_notice(item).model_dump() for item in _items(raw)]
        if keyword:
            normalized = keyword.casefold()
            items = [item for item in items if normalized in (item.get("title") or "").casefold()]
        data = _data(raw)
        total = data.get("total_") if isinstance(data, dict) else len(items)
        return ToolSuccess(
            data=items,
            meta={"page": page, "page_size": page_size, "total": total},
        )

    async def notice_detail(self, notice_id: str) -> ToolSuccess:
        raw = _data(await self.sdk.call("notices_detail", {"notice_id": notice_id}))
        value = raw if isinstance(raw, dict) else {}
        return ToolSuccess(data=_notice(value, include_content=True).model_dump())

    async def unread_count(self) -> ToolSuccess:
        raw = _data(await self.sdk.call("notices_unread_count"))
        count = raw.get("count") if isinstance(raw, dict) else raw
        return ToolSuccess(data={"count": count})

    async def _identity_and_term(self) -> tuple[StudentSummary, CalendarSummary]:
        student_items = _items(await self.sdk.call("students_me"))
        if not student_items:
            raise UpstreamError("无法获取当前学生信息。")
        term_raw = _current_term_record(await self.sdk.call("calendar_current_term"))
        return _student(student_items[0]), _calendar(term_raw)

    async def courses(self, *, page: int = 1, page_size: int = 100) -> ToolSuccess:
        _, term = await self._identity_and_term()
        raw = await self.sdk.call(
            "courses_list",
            {
                "calendar": term.calendar_id,
                "page": page,
                "page_size": page_size,
            },
        )
        items = [_course(item).model_dump() for item in _items(raw)]
        return ToolSuccess(
            data=items,
            meta={
                "calendar_id": term.calendar_id,
                "page": page,
                "page_size": page_size,
            },
        )

    async def schedule(self, *, today_only: bool) -> ToolSuccess:
        student, term = await self._identity_and_term()
        if not student.student_id or term.calendar_id is None:
            raise UpstreamError("当前学生或学期信息不完整。")
        raw = await self.sdk.call(
            "timetable_student",
            {
                "student_id": student.student_id,
                "calendar_id": term.calendar_id,
                "campus": student.campus_code or "",
            },
        )
        week_response = await self.current_week()
        week = week_response.data.get("week")
        entries = [_course(item).model_dump() for item in _items(raw)]
        entries = [entry for entry in entries if _active_in_week(entry.get("weeks"), week)]
        if today_only:
            weekday = date.today().isoweekday()
            entries = [entry for entry in entries if str(entry.get("weekday")) == str(weekday)]
        return ToolSuccess(
            data=entries,
            meta={
                "calendar_id": term.calendar_id,
                "week": week,
                "weekday": date.today().isoweekday() if today_only else None,
                "week_source": week_response.meta.get("source"),
            },
        )

    async def grades(self) -> ToolSuccess:
        student, _ = await self._identity_and_term()
        raw = _data(await self.sdk.call("grades_list", {"student_id": student.student_id}))
        return ToolSuccess(data=raw)

    async def score_rank(self) -> ToolSuccess:
        student, _ = await self._identity_and_term()
        raw = _data(await self.sdk.call("scores_rank", {"student_id": student.student_id}))
        return ToolSuccess(
            data=raw,
            meta={"available": raw is not None},
        )

    async def exams(self) -> ToolSuccess:
        items = [_exam(item).model_dump() for item in _items(await self.sdk.call("exams_schedule"))]
        return ToolSuccess(data=items, meta={"count": len(items)})
