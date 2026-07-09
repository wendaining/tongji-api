from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class ToolModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


ToolData = TypeVar("ToolData")


class ToolSuccess(ToolModel, Generic[ToolData]):
    ok: Literal[True] = True
    data: ToolData
    meta: dict[str, Any] = Field(default_factory=dict)


class StudentSummary(ToolModel):
    student_id: str | None = None
    name: str | None = None
    grade: str | None = None
    faculty: str | None = None
    profession: str | None = None
    campus_code: str | int | None = None
    campus_name: str | None = None
    training_level_code: str | int | None = None
    training_level_name: str | None = None


class CalendarSummary(ToolModel):
    calendar_id: int | str | None = None
    academic_year: str | None = None
    term_code: str | int | None = None
    term_name: str | None = None
    begin_date: str | None = None
    end_date: str | None = None
    total_weeks: int | None = None


class NoticeSummary(ToolModel):
    notice_id: str | int | None = None
    title: str | None = None
    publisher: str | None = None
    publish_time: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    audience: str | None = None
    content: str | None = None
    attachments: list[Any] = Field(default_factory=list)


class CourseSummary(ToolModel):
    course_code: str | None = None
    course_name: str | None = None
    teacher_name: str | None = None
    classroom_name: str | None = None
    weekday: int | str | None = None
    start_section: int | str | None = None
    end_section: int | str | None = None
    weeks: Any = None
    campus_name: str | None = None
    credit: float | str | None = None


class ExamSummary(ToolModel):
    exam_id: str | int | None = None
    subject: str | None = None
    exam_time: str | None = None
    location: str | None = None
    result: str | None = None
    calendar_name: str | None = None
    notice: str | None = None


class WeekSummary(ToolModel):
    week: int


class CountSummary(ToolModel):
    count: int | str | None = None
