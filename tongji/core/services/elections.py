from __future__ import annotations

import time
from typing import Any

from tongji.core.client import RawOneClient


async def mutual_apply_page(
    client: RawOneClient,
    *,
    calendar_id: int,
    student_id: str,
    project_id: str = "1",
    mode: int = 3,
    course_code: str = "",
    new_course_code: str = "",
    course_name: str = "",
    training_level: str = "",
    open_college: str = "",
    status: str = "",
    is_elective: str = "",
    nature: str = "",
    page: int = 1,
    page_size: int = 20,
) -> Any:
    """Query cross-disciplinary course application list.

    Ref: POST /api/electionservice/elcMutualApply/page
    Uses form-encoded body with dot-notation for nested condition fields,
    matching the Spring MVC convention used by 1.tongji.edu.cn.
    """
    payload: dict[str, Any] = {
        "pageNum_": page,
        "pageSize_": page_size,
        "condition.projectId": project_id,
        "condition.calendarId": str(calendar_id) if calendar_id else "",
        "condition.studentId": student_id,
        "condition.mode": str(mode),
        "condition.courseCode": course_code,
        "condition.newCourseCode": new_course_code,
        "condition.courseName": course_name,
        "condition.trainingLevel": training_level,
        "condition.openCollege": open_college,
        "condition.status": status,
        "condition.isElective": is_elective,
        "condition.nature": nature,
    }
    return await client.request(
        "POST",
        "/api/electionservice/elcMutualApply/page",
        data=payload,
    )


async def mutual_find_dept(
    client: RawOneClient,
    *,
    virtual_dept: int = 0,
    type_: int = 1,
    manage_dept: int = 1,
) -> Any:
    """Find department list for mutual courses.

    Ref: GET /api/electionservice/elcMutualCourses/findDept
    """
    params: dict[str, Any] = {
        "virtualDept": str(virtual_dept),
        "type": str(type_),
        "manageDept": str(manage_dept),
        "_t": str(int(time.time() * 1000)),
    }
    return await client.request(
        "GET",
        "/api/electionservice/elcMutualCourses/findDept",
        params=params,
    )


async def get_is_nest_calendar_id(
    client: RawOneClient,
    *,
    calendar_id: int,
    mode: int = 1,
    project_id: str = "1",
) -> Any:
    """Check whether a calendar is a nested calendar.

    Ref: POST /api/electionservice/electionRound/getIsNestCalendarId
    """
    return await client.request(
        "POST",
        "/api/electionservice/electionRound/getIsNestCalendarId",
        data={
            "calendarId": str(calendar_id),
            "mode": mode,
            "projectId": project_id,
        },
    )


async def get_elec_student_info(client: RawOneClient, *, calendar_id: int) -> Any:
    """Get elective student info for a given calendar.

    Ref: GET /api/electionservice/student/getElecStudentInfo
    """
    import time

    return await client.request(
        "GET",
        "/api/electionservice/student/getElecStudentInfo",
        params={
            "calendarId": str(calendar_id),
            "_t": str(int(time.time() * 1000)),
        },
    )


# ---------------------------------------------------------------------------
# Report / attendance workbench widgets
# ---------------------------------------------------------------------------


async def query_have_class_date(client: RawOneClient, *, year_month: str) -> Any:
    """Query dates that have classes in a given month.

    Used by the workbench calendar widget to highlight class days.

    Ref: GET /api/electionservice/reportManagement/queryHaveClassDate?yearMonth=...
    """
    return await client.request(
        "GET",
        "/api/electionservice/reportManagement/queryHaveClassDate",
        params={"yearMonth": year_month},
    )


async def query_attend_class_content(client: RawOneClient, *, choose_date: str) -> Any:
    """Query class attendance content for a specific date.

    Ref: GET /api/electionservice/reportManagement/queryAttendClassContent?chooseDate=...
    """
    return await client.request(
        "GET",
        "/api/electionservice/reportManagement/queryAttendClassContent",
        params={"chooseDate": choose_date},
    )


# ---------------------------------------------------------------------------
# Election rounds & apply list
# ---------------------------------------------------------------------------


async def get_rounds(client: RawOneClient, *, project_id: int = 1) -> Any:
    """Query the active election rounds for a project.

    Returns the list of election rounds (选课轮次).

    Ref: POST /api/electionservice/student/getRounds?projectId=1
        Scanned via CDP from multiple pages, 2026-07-09.
    """
    return await client.request(
        "POST",
        "/api/electionservice/student/getRounds",
        params={"projectId": str(project_id)},
    )


async def stu_apply_course_list(
    client: RawOneClient,
    *,
    page: int = 1,
    page_size: int = 20,
    calendar_id: str = "",
    code: str = "",
    course_name: str = "",
    college: str = "",
    training_level: str = "",
) -> Any:
    """Query the student's applied course list for selection.

    Returns the paginated list of courses the student has applied for.

    Ref: POST /api/electionservice/electionApply/stuApplyCourseList
        Scanned via CDP from multiple pages, 2026-07-09.
    """
    condition: dict[str, str] = {
        "calendarId": calendar_id,
        "code": code,
        "keyCode": "",
        "keyCode2": "",
        "courseName": course_name,
        "college": college,
        "credits": "",
        "period": "",
        "weekHour": "",
        "weekNum": "",
        "profession": "",
        "studentCode": "",
        "studentName": "",
        "trainingLevel": training_level,
    }
    body: dict[str, Any] = {
        "pageNum_": page,
        "pageSize_": page_size,
    }
    for k, v in condition.items():
        body[f"condition.{k}"] = v

    return await client.request(
        "POST",
        "/api/electionservice/electionApply/stuApplyCourseList",
        data=body,
    )
