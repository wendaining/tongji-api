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
