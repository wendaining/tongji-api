from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from pydantic import BaseModel, Field

from tongji.core.client import RawOneClient
from tongji.core.services import (
    calendar,
    classroom,
    courses,
    culture,
    elections,
    exams,
    grades,
    help_center,
    major,
    notices,
    picture,
    session,
    students,
    teaching_progress,
    timetable,
    tutor_meetings,
)
from tongji.modules.base import (
    ModuleDefinition,
    ModuleExecutor,
    create_raw_response_model,
    create_request_model,
)

ServiceCallable = Callable[..., Any]


def _class_name(name: str, suffix: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", name)
    return "".join(part.title() for part in parts if part) + suffix


def _executor(
    service: ServiceCallable,
    *,
    fixed: Mapping[str, Any] | None = None,
) -> ModuleExecutor:
    async def execute(client: RawOneClient, request: BaseModel) -> Any:
        kwargs = request.model_dump()
        kwargs.update(fixed or {})
        return await service(client, **kwargs)

    return execute


def _module(
    name: str,
    route: str,
    summary: str,
    service: ServiceCallable | None = None,
    *,
    method: str = "GET",
    description: str | None = None,
    tags: tuple[str, ...] = (),
    fields: Mapping[str, tuple[Any, Any]] | None = None,
    fixed: Mapping[str, Any] | None = None,
    execute: ModuleExecutor | None = None,
) -> ModuleDefinition:
    if execute is None:
        if service is None:
            raise ValueError(f"Module {name} requires a service or executor")
        execute = _executor(service, fixed=fixed)
    return ModuleDefinition(
        name=name,
        route=route,
        method=method,
        summary=summary,
        description=description or f"Raw 1.tongji.edu.cn API module: {summary}.",
        tags=tags or (route.strip("/").split("/", 1)[0],),
        request_model=create_request_model(_class_name(name, "Request"), fields or {}),
        response_model=create_raw_response_model(_class_name(name, "Response")),
        execute=execute,
    )


async def _student_me(client: RawOneClient, _: BaseModel) -> Any:
    return await students.student_info_list(client, page=1, page_size=1)


async def _exam_schedule(client: RawOneClient, _: BaseModel) -> Any:
    await exams.current_auth_id(client, auth_id=exams.EXAM_AUTH_ID)
    await session.set_language(client)
    return await exams.get_exam_schedule(client)


async def _exam_info(client: RawOneClient, _: BaseModel) -> Any:
    await exams.current_auth_id(client, auth_id=exams.EXAM_AUTH_ID)
    exam_type = await exams.get_default_exam_type(client)
    semesters = await exams.query_dictionary(
        client,
        keys=["X_XQ"],
        auth_id=exams.EXAM_AUTH_ID,
    )
    return {"examType": exam_type, "semesters": semesters}


async def _exam_dictionary(client: RawOneClient, request: BaseModel) -> Any:
    values = request.model_dump(exclude_none=True)
    keys = [key.strip() for key in values.pop("keys").split(",") if key.strip()]
    return await exams.query_dictionary(client, keys=keys, **values)


async def _tutor_meetings(client: RawOneClient, request: BaseModel) -> Any:
    await exams.current_auth_id(client, auth_id=13087)
    await session.set_language(client)
    return await tutor_meetings.query_by_page(
        client,
        search_type="2",
        **request.model_dump(exclude_none=True),
    )


async def _student_picture(client: RawOneClient, request: BaseModel) -> Any:
    value = request.model_dump()["student_ids"]
    return await picture.query_picture(
        client,
        student_ids=[student_id.strip() for student_id in value.split(",") if student_id.strip()],
    )


PAGE_FIELDS = {
    "page": (int, Field(default=1, ge=1)),
    "page_size": (int, Field(default=20, ge=1, le=200, alias="pageSize")),
}

MODULES = (
    _module("students_me", "/students/me", "查询当前学生", execute=_student_me),
    _module(
        "students_list",
        "/students",
        "查询学生列表",
        students.student_info_list,
        fields={
            **PAGE_FIELDS,
            "student_id": (str | None, Field(default=None, alias="studentId")),
            "name": (str | None, None),
            "faculty": (str | None, None),
            "profession": (str | None, None),
            "grade": (str | None, None),
        },
    ),
    _module(
        "notices_list",
        "/notices",
        "查询通知列表",
        notices.list_notices,
        fields={
            **PAGE_FIELDS,
            "keyword": (str | None, None),
        },
    ),
    _module(
        "notices_my",
        "/notices/my",
        "查询与当前用户相关的通知",
        notices.my_notices,
        fields=PAGE_FIELDS,
    ),
    _module(
        "notices_detail",
        "/notices/{notice_id}",
        "查询通知详情",
        notices.notice_detail,
        fields={"notice_id": (str, Field(alias="noticeId"))},
    ),
    _module(
        "notices_unread_count",
        "/notices/unread-count",
        "查询未读通知数量",
        notices.unread_count,
    ),
    _module(
        "courses_list",
        "/courses",
        "查询排课课程",
        courses.query_courses,
        fields={
            "calendar": (int | None, None),
            "campus": (str, ""),
            "college": (str, ""),
            "course": (str, ""),
            "training_level": (str, Field(default="", alias="trainingLevel")),
            **PAGE_FIELDS,
        },
    ),
    _module("calendar_list", "/calendar/list", "查询校历列表", calendar.list_calendars),
    _module(
        "calendar_current_term",
        "/calendar/current-term",
        "查询当前学期",
        calendar.current_term,
    ),
    _module(
        "calendar_current_week",
        "/calendar/current-week",
        "查询当前教学周",
        calendar.current_week,
    ),
    _module(
        "calendar_professional_work",
        "/calendar/professional-work",
        "查询校历教学安排",
        calendar.professional_work,
    ),
    _module(
        "calendar_holidays",
        "/calendar/holidays",
        "查询年度节假日",
        calendar.query_holidays,
        fields={"year": (str, "2026")},
    ),
    _module(
        "calendar_detail",
        "/calendar/{calendar_id}",
        "查询校历详情",
        calendar.calendar_detail,
        fields={"calendar_id": (str, Field(alias="calendarId"))},
    ),
    _module(
        "plan_credits",
        "/plan/credits",
        "查询培养方案学分统计",
        culture.stats_credit,
        fields={"student_id": (str, Field(alias="studentId"))},
    ),
    _module(
        "plan_courses",
        "/plan/courses",
        "查询培养方案课程",
        culture.plan_course_tab,
        fields={"student_id": (str, Field(alias="studentId"))},
    ),
    _module(
        "timetable_student",
        "/timetable",
        "查询学生课表",
        timetable.student_timetable,
        fields={
            "student_id": (str, Field(alias="studentId")),
            "calendar_id": (int, Field(alias="calendarId")),
            "campus": (str, ""),
        },
    ),
    _module(
        "grades_list",
        "/grades",
        "查询学生成绩",
        grades.get_my_grades,
        fields={"student_id": (str, Field(alias="studentId"))},
    ),
    _module(
        "grades_tags",
        "/grades/tags",
        "查询成绩课程标签",
        grades.query_course_tags,
        fields={"student_id": (str, Field(alias="studentId"))},
    ),
    _module("exams_schedule", "/exams", "查询考试安排", execute=_exam_schedule),
    _module("exams_info", "/exams/info", "查询考试元数据", execute=_exam_info),
    _module(
        "exams_dictionary",
        "/exams/dictionary",
        "查询考试数据字典",
        fields={
            "keys": (str, Field(description="Comma-separated dictionary keys")),
            "auth_id": (int | None, Field(default=None, alias="authId")),
        },
        execute=_exam_dictionary,
    ),
    _module(
        "tutor_meetings",
        "/tutor-meetings",
        "查询导师见面会",
        fields={
            "search_text": (str, Field(default="", alias="searchText")),
            **PAGE_FIELDS,
        },
        execute=_tutor_meetings,
    ),
    _module(
        "timetable_major",
        "/timetable/major",
        "查询专业课表",
        timetable.major_timetable,
        fields={
            "code": (str, ...),
            "grade": (str, ...),
            "calendar_id": (int, Field(alias="calendarId")),
            "dir_code": (str, Field(default="", alias="dirCode")),
            "is_major": (bool, Field(default=False, alias="isMajor")),
        },
    ),
    _module(
        "teaching_progress_list",
        "/teaching-progress",
        "查询教学进度",
        teaching_progress.progress_query,
        fields={
            "calendar_id": (int | None, Field(default=None, alias="calendarId")),
            "keyword": (str, ""),
            **PAGE_FIELDS,
        },
    ),
    _module(
        "teaching_progress_detail",
        "/teaching-progress/{progress_id}",
        "查询教学进度详情",
        teaching_progress.get_progress_detail,
        fields={
            "id": (str, Field(alias="progressId")),
            **PAGE_FIELDS,
        },
    ),
    _module(
        "cross_courses_apply",
        "/cross-courses/apply",
        "查询跨学科课程申请",
        elections.mutual_apply_page,
        fields={
            "student_id": (str, Field(alias="studentId")),
            "calendar_id": (int, Field(alias="calendarId")),
            **PAGE_FIELDS,
        },
    ),
    _module("session_ping", "/session/ping", "检查 1 系统会话", session.ping),
    _module(
        "session_user",
        "/session/me",
        "查询 1 系统会话用户",
        session.get_session_user,
    ),
    _module("students_tabs", "/students/tabs", "查询学生可见标签", students.get_visible_tabs),
    _module(
        "students_stations",
        "/students/stations",
        "查询生源地字典",
        students.get_station_info_list,
    ),
    _module(
        "classroom_towers",
        "/classroom/towers",
        "查询教学楼",
        classroom.condition_query_classroom_tower,
    ),
    _module("help_articles", "/help/articles", "查询帮助文章", help_center.list_all_help),
    _module("help_groups", "/help/groups", "查询帮助分组", help_center.find_user_group_list),
    _module(
        "scores_rank",
        "/scores/rank",
        "查询成绩排名",
        major.query_student_score_rank,
        fields={"student_id": (str, Field(alias="studentId"))},
    ),
    _module(
        "culture_strength_class",
        "/culture/strength-class",
        "查询强化班状态",
        culture.my_strength_class_info,
    ),
    _module(
        "attendance_class_dates",
        "/attendance/class-dates",
        "查询有课日期",
        elections.query_have_class_date,
        fields={"year_month": (str, Field(alias="yearMonth"))},
    ),
    _module(
        "attendance_class_content",
        "/attendance/class-content",
        "查询指定日期课程",
        elections.query_attend_class_content,
        fields={"choose_date": (str, Field(alias="chooseDate"))},
    ),
    _module(
        "students_status",
        "/students/status",
        "查询学生申请状态",
        students.get_apply_status_info,
        fields={"student_id": (str, Field(alias="studentId"))},
    ),
    _module(
        "students_activation",
        "/students/activation",
        "查询学生激活状态",
        students.check_activation,
        fields={"student_id": (str, Field(alias="studentId"))},
    ),
    _module("help_my", "/help/my", "查询我的帮助文章", help_center.find_my_help_center),
    _module(
        "students_picture",
        "/students/picture",
        "查询学生照片",
        method="POST",
        fields={"student_ids": (str, Field(alias="studentIds"))},
        execute=_student_picture,
    ),
    _module(
        "elections_rounds",
        "/elections/rounds",
        "查询选课轮次",
        elections.get_rounds,
        fields={"project_id": (int, Field(default=1, alias="projectId"))},
    ),
    _module(
        "elections_apply_list",
        "/elections/apply-list",
        "查询选课申请列表",
        elections.stu_apply_course_list,
        fields={
            **PAGE_FIELDS,
            "calendar_id": (str, Field(default="", alias="calendarId")),
        },
    ),
    _module(
        "classroom_usage_report",
        "/classroom/usage-report",
        "查询教室使用情况",
        classroom.classroom_usage_report_count_query,
        fields={
            "calendar_id": (int, Field(alias="calendarId")),
            "campus": (str, ""),
            "tower_code": (str, Field(default="", alias="towerCode")),
            "week_at": (str, Field(default="1", alias="weekAt")),
            **PAGE_FIELDS,
        },
    ),
    _module(
        "culture_strength_class_info",
        "/culture/strength-class-info",
        "查询强化班信息",
        culture.get_strengthen_class_info,
        fields={"type_id": (int, Field(default=2, alias="type"))},
    ),
)
