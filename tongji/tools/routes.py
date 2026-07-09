from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request

from tongji.tools.models import (
    CalendarSummary,
    CountSummary,
    CourseSummary,
    ExamSummary,
    NoticeSummary,
    StudentSummary,
    ToolSuccess,
    WeekSummary,
)
from tongji.tools.service import AgentTools

router = APIRouter(prefix="/tools/tongji", tags=["agent-tools"])


def _tools(request: Request) -> AgentTools:
    return request.app.state.agent_tools


@router.get(
    "/me",
    response_model=ToolSuccess[StudentSummary | None],
    summary="查询当前学生",
)
async def me(request: Request) -> ToolSuccess:
    return await _tools(request).me()


@router.get(
    "/session/status",
    response_model=ToolSuccess[dict[str, Any]],
    summary="查询本地会话状态",
)
async def session_status(request: Request) -> ToolSuccess:
    return ToolSuccess(data=request.app.state.session_store.public_status())


@router.get(
    "/calendar/current-term",
    response_model=ToolSuccess[CalendarSummary],
    summary="查询当前学期",
)
async def current_term(request: Request) -> ToolSuccess:
    return await _tools(request).current_term()


@router.get(
    "/calendar/current-week",
    response_model=ToolSuccess[WeekSummary],
    summary="查询当前教学周",
)
async def current_week(request: Request) -> ToolSuccess:
    return await _tools(request).current_week()


@router.get(
    "/calendar",
    response_model=ToolSuccess[list[CalendarSummary]],
    summary="查询校历",
)
async def calendars(request: Request) -> ToolSuccess:
    return await _tools(request).calendars()


@router.get(
    "/notices",
    response_model=ToolSuccess[list[NoticeSummary]],
    summary="查询最近通知",
)
async def notices(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
) -> ToolSuccess:
    return await _tools(request).notices(page=page, page_size=page_size, keyword=keyword)


@router.get(
    "/notices/unread-count",
    response_model=ToolSuccess[CountSummary],
    summary="查询未读通知数量",
)
async def unread_count(request: Request) -> ToolSuccess:
    return await _tools(request).unread_count()


@router.get(
    "/notices/{notice_id}",
    response_model=ToolSuccess[NoticeSummary],
    summary="查询通知详情",
)
async def notice_detail(request: Request, notice_id: str) -> ToolSuccess:
    return await _tools(request).notice_detail(notice_id)


@router.get(
    "/courses",
    response_model=ToolSuccess[list[CourseSummary]],
    summary="查询当前学期课程",
)
async def courses(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
) -> ToolSuccess:
    return await _tools(request).courses(page=page, page_size=page_size)


@router.get(
    "/schedule/today",
    response_model=ToolSuccess[list[CourseSummary]],
    summary="查询今日课表",
)
async def schedule_today(request: Request) -> ToolSuccess:
    return await _tools(request).schedule(today_only=True)


@router.get(
    "/schedule/week",
    response_model=ToolSuccess[list[CourseSummary]],
    summary="查询本周课表",
)
async def schedule_week(request: Request) -> ToolSuccess:
    return await _tools(request).schedule(today_only=False)


@router.get(
    "/grades",
    response_model=ToolSuccess[Any],
    summary="查询当前学生成绩",
)
async def tool_grades(request: Request) -> ToolSuccess:
    return await _tools(request).grades()


@router.get(
    "/exams",
    response_model=ToolSuccess[list[ExamSummary]],
    summary="查询当前学生考试安排",
)
async def tool_exams(request: Request) -> ToolSuccess:
    return await _tools(request).exams()
