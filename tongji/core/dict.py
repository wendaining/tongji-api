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
# Course
# ---------------------------------------------------------------------------

COURSE_LABEL_FIELDS = [
    ("name", "课程名称"),
    ("teacher", "教师"),
    ("classroom", "教室"),
    ("week", "周次"),
    ("day", "星期"),
    ("period", "节次"),
    ("campus", "校区"),
    ("college", "学院"),
    ("profession", "专业"),
    ("trainingLevel", "培养层次"),
    ("credit", "学分"),
    ("courseCode", "课程代码"),
    ("studentCount", "学生人数"),
]


def translate_course(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a course record."""
    return {label: _pick(raw, code) for code, label in COURSE_LABEL_FIELDS}


# ---------------------------------------------------------------------------
# Timetable
# ---------------------------------------------------------------------------

TIMETABLE_LABEL_FIELDS = [
    ("courseName", "课程名称"),
    ("teacherName", "教师"),
    ("classroomName", "教室"),
    ("weekDay", "星期"),
    ("startSection", "起始节次"),
    ("endSection", "结束节次"),
    ("weeks", "周次"),
    ("campusName", "校区"),
    ("courseCode", "课程代码"),
    ("credit", "学分"),
]


def translate_timetable(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a timetable entry."""
    return {label: _pick(raw, code) for code, label in TIMETABLE_LABEL_FIELDS}


# ---------------------------------------------------------------------------
# Culture plan (培养方案)
# ---------------------------------------------------------------------------

CREDIT_STATS_FIELDS = [
    ("totalCultureCredit", "要求总学分"),
    ("totalGetCredit", "已获学分"),
    ("totalPlanCredit", "培养方案总学分"),
    ("completed", "是否完成"),
]

PLAN_COURSE_FIELDS = [
    ("labName", "模块"),
    ("courseName", "课程名称"),
    ("courseCode", "代码"),
    ("credits", "学分"),
    ("score", "成绩"),
    ("scoreLevel", "等级"),
    ("semester", "学期"),
    ("collegeI18n", "开课学院"),
    ("selCourse", "选修"),
]


def translate_credit_stats(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate credit statistics."""
    return {label: _pick(raw, code) for code, label in CREDIT_STATS_FIELDS}


def translate_plan_course(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a plan course entry."""
    result = {label: _pick(raw, code) for code, label in PLAN_COURSE_FIELDS}
    # selCourse: 0 = 必修, 1 = 选修
    if "selCourse" in raw:
        result["选修"] = "选修" if raw.get("selCourse") == 1 else "必修"
    return result


# ---------------------------------------------------------------------------
# Grades
# ---------------------------------------------------------------------------

GRADE_TERM_FIELDS = [
    ("termName", "学期"),
    ("averagePoint", "学期均绩"),
    ("calName", "学期代码"),
]


def translate_grade_term(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a grade term summary."""
    return {label: _pick(raw, code) for code, label in GRADE_TERM_FIELDS}


def translate_grade_course(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a single course grade entry."""
    return {
        "课程名称": _pick(raw, "courseName"),
        "代码": _pick(raw, "courseCode"),
        "成绩": _pick(raw, "scoreName"),
        "绩点": _pick(raw, "gradePoint"),
        "是否通过": "是" if raw.get("isPass") == 1 else "否",
        "考试类型": _pick(raw, "scoreEaxmTypeI18n"),
        "成绩性质": _pick(raw, "scoreNatureName"),
    }


# ---------------------------------------------------------------------------
# Cross-course mutual apply
# ---------------------------------------------------------------------------

MUTUAL_APPLY_FIELDS = [
    ("id", "ID"),
    ("courseName", "课程名称"),
    ("courseCode", "课程代码"),
    ("newCourseCode", "新课程代码"),
    ("credit", "学分"),
    ("applyTime", "申请时间"),
    ("openCollege", "开课学院"),
    ("statusI18n", "状态"),
    ("isElective", "选修"),
    ("nature", "性质"),
    ("trainingLevel", "培养层次"),
    ("mode", "模式"),
    ("projectId", "项目ID"),
    ("studentId", "学号"),
]


def translate_mutual_apply(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a single cross-course application entry to human-readable Chinese."""
    result = {label: _pick(raw, code) for code, label in MUTUAL_APPLY_FIELDS}
    # isElective: 0 = 必修, 1 = 选修
    if "isElective" in raw:
        result["选修"] = "选修" if raw.get("isElective") == 1 else "必修"
    return result


# ---------------------------------------------------------------------------
# Generic helper
# ---------------------------------------------------------------------------

def pick_i18n(raw: dict[str, Any], *keys: str) -> dict[str, str]:
    """Pick the I18n version of each key from *raw*, falling back to raw code.

    >>> pick_i18n(student, "campus", "faculty", "sex")
    {"campus": "嘉定校区", "faculty": "计算机科学与技术学院", "sex": "男"}
    """
    return {k: _pick(raw, k) for k in keys}
