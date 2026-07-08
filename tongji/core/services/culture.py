"""Culture plan / training program service.

Ref: app.js — bclCulturePlan, bclStudentCultureRel, etc.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from tongji.core.client import RawOneClient


async def plan_course_tab(client: RawOneClient, *, student_id: str) -> Any:
    """Fetch a student's plan courses organised by label tabs."""
    params = urlencode({"studentID": student_id})
    return await client.request(
        "GET",
        f"/api/cultureservice/bclCulturePlan/findPlanCourseTab?{params}",
    )


async def stats_credit(client: RawOneClient, *, student_id: str) -> Any:
    """Fetch credit statistics: total earned vs total required."""
    params = urlencode({"studentID": student_id})
    return await client.request(
        "GET",
        f"/api/cultureservice/bclCulturePlan/statsCredit?{params}",
    )


async def course_label_tree(client: RawOneClient, *, student_id: str) -> Any:
    """Fetch the course label/category tree for a student."""
    params = urlencode({"studentID": student_id})
    return await client.request(
        "GET",
        f"/api/cultureservice/bclCulturePlan/queryCourseLabelTree?{params}",
    )


async def student_culture_rel(client: RawOneClient, *, student_id: str) -> Any:
    """Fetch the student's culture program relation info."""
    return await client.request(
        "GET",
        f"/api/cultureservice//bclStudentCultureRel/findStudentCultureRelByStudentId?stuid={student_id}",
    )
