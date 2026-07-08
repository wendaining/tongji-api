"""Translation layer for 1.tongji.edu.cn raw responses.

The upstream API returns I18n fields alongside numeric codes (e.g.
``campus: 3`` and ``campusI18n: "嘉定校区"``).  This module picks the
human-readable version wherever available and falls back to the raw code.

Adding a new service translation is just a matter of listing the
code → label field pairs.
"""

from __future__ import annotations

from typing import Any


def _pick(raw: dict[str, Any], code_key: str, i18n_key: str | None = None) -> Any:
    """Return the best human-readable value for *code_key*.

    Prefers ``<key>I18n`` when present; otherwise returns the raw code.
    """
    i18n = i18n_key or f"{code_key}I18n"
    return raw.get(i18n) or raw.get(code_key)


# ---------------------------------------------------------------------------
# Student info
# ---------------------------------------------------------------------------

STUDENT_LABEL_FIELDS = [
    ("studentId", "学号"),
    ("name", "姓名"),
    ("sex", "性别"),
    ("grade", "年级"),
    ("faculty", "学院"),
    ("profession", "专业"),
    ("trainingLevel", "培养层次"),
    ("campus", "校区"),
    ("formLearning", "学习形式"),
    ("registrationStatus", "学籍状态"),
    ("enrolDate", "入学日期"),
    ("enrolMethods", "入学方式"),
    ("leaveSchool", "在读状态"),
    ("phoneNumber", "电话"),
    ("trainingCategory", "学生类别"),
    ("isOverseas", "是否留学生"),
    ("specialPlan", "专项计划"),
    ("specialCategory", "特殊类别"),
    ("statusProfession", "学籍专业"),
    ("statusFaculty", "学籍学院"),
    ("enrolSeason", "入学季节"),
    ("cultureProfession", "培养专业"),
]


def translate_student(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a single student record to human-readable Chinese."""
    return {label: _pick(raw, code) for code, label in STUDENT_LABEL_FIELDS}


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

CALENDAR_LABEL_FIELDS = [
    ("id", "ID"),
    ("year", "学年"),
    ("term", "学期"),
    ("beginDay", "开始日期"),
    ("endDay", "结束日期"),
    ("weekNum", "总周数"),
    ("teachingWeekStart", "教学周起始"),
    ("teachingWeekEnd", "教学周结束"),
    ("examWeekStart", "考试周起始"),
    ("examWeekEnd", "考试周结束"),
]


def translate_calendar(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a calendar record."""
    return {label: _pick(raw, code) for code, label in CALENDAR_LABEL_FIELDS}


# ---------------------------------------------------------------------------
# Notice
# ---------------------------------------------------------------------------

NOTICE_LABEL_FIELDS = [
    ("id", "ID"),
    ("title", "标题"),
    ("createUser", "发布人"),
    ("createTime", "创建时间"),
    ("publishTime", "发布时间"),
    ("startTime", "生效时间"),
    ("endTime", "截止时间"),
    ("faceUserName", "面向对象"),
    ("topStatus", "置顶"),
    ("content", "内容"),
    ("commonAttachmentList", "附件"),
]


def translate_notice(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a notice record."""
    return {label: _pick(raw, code) for code, label in NOTICE_LABEL_FIELDS}


# ---------------------------------------------------------------------------
# Generic helper
# ---------------------------------------------------------------------------

def pick_i18n(raw: dict[str, Any], *keys: str) -> dict[str, str]:
    """Pick the I18n version of each key from *raw*, falling back to raw code.

    >>> pick_i18n(student, "campus", "faculty", "sex")
    {"campus": "嘉定校区", "faculty": "计算机科学与技术学院", "sex": "男"}
    """
    return {k: _pick(raw, k) for k in keys}
