"""Culture plan / training program service.

Ref: app.js — bclCulturePlan, bclStudentCultureRel, etc.
Browser Network (2026-07): myBclCultureScheme page flow.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from tongji.core.client import RawOneClient

# ── 已有的培养方案概览接口 ──────────────────────────────

async def plan_course_tab(client: RawOneClient, *, student_id: str) -> Any:
    """Fetch a student's plan courses organised by label tabs.

    Ref: GET /api/cultureservice/bclCulturePlan/findPlanCourseTab?studentID=...
    """
    params = urlencode({"studentID": student_id})
    return await client.request(
        "GET",
        f"/api/cultureservice/bclCulturePlan/findPlanCourseTab?{params}",
    )


async def stats_credit(client: RawOneClient, *, student_id: str) -> Any:
    """Fetch credit statistics: total earned vs total required.

    Ref: GET /api/cultureservice/bclCulturePlan/statsCredit?studentID=...
    """
    params = urlencode({"studentID": student_id})
    return await client.request(
        "GET",
        f"/api/cultureservice/bclCulturePlan/statsCredit?{params}",
    )


async def course_label_tree(client: RawOneClient, *, student_id: str) -> Any:
    """Fetch the course label/category tree for a student.

    Ref: GET /api/cultureservice/bclCulturePlan/queryCourseLabelTree?studentID=...
    """
    params = urlencode({"studentID": student_id})
    return await client.request(
        "GET",
        f"/api/cultureservice/bclCulturePlan/queryCourseLabelTree?{params}",
    )


# ── 培养方案详情页接口（myBclCultureScheme 页面） ──────────

async def student_culture_scheme(client: RawOneClient, *, student_id: str) -> Any:
    """Query the student's culture scheme association.

    Returns the scheme id(s) linked to the student, used as input
    to ``culture_scheme_by_id`` and other detail endpoints.

    Ref: GET /api/cultureservice/bclStudentCultureRel/queryStudentCultureScheme?stuid=...
    """
    return await client.request(
        "GET",
        f"/api/cultureservice/bclStudentCultureRel/queryStudentCultureScheme",
        params={"stuid": student_id},
    )


async def culture_scheme_by_id(client: RawOneClient, *, scheme_id: str | int) -> Any:
    """Fetch culture scheme detail by its ID.

    Returns scheme metadata: name, year, term, training level, etc.

    Ref: GET /api/cultureservice/bclCultureScheme/findCultureSchemeById?id=...
    """
    return await client.request(
        "GET",
        "/api/cultureservice/bclCultureScheme/findCultureSchemeById",
        params={"id": str(scheme_id)},
    )


async def culture_scheme_detail_list(
    client: RawOneClient, *, culture_id: str | int,
) -> Any:
    """Fetch the detail / template list for a culture scheme.

    Returns the structured breakdown of all course groups and
    requirements within a scheme.

    Ref: GET /api/cultureservice/bclCultureSchemeDetail/findCultScheDetailOrTemplateList?cultureId=...
    """
    return await client.request(
        "GET",
        "/api/cultureservice/bclCultureSchemeDetail/findCultScheDetailOrTemplateList",
        params={"cultureId": str(culture_id)},
    )


async def culture_scheme_terms(
    client: RawOneClient, *, scheme_id: str | int,
) -> Any:
    """Fetch the school terms associated with a culture scheme.

    Ref: GET /api/cultureservice/bclCultureScheme/getSchemeSchoolTerm?id=...
    """
    return await client.request(
        "GET",
        "/api/cultureservice/bclCultureScheme/getSchemeSchoolTerm",
        params={"id": str(scheme_id)},
    )


async def culture_label_list(
    client: RawOneClient, *, scheme_id: str | int, type_id: str = "2",
) -> Any:
    """Fetch the course label/category list for a scheme.

    ``type_id``: ``"2"`` = culture plan labels (default).

    Ref: GET /api/cultureservice/bclCultureTemplate/coursesLabelList/{schemeId}?type=...
    """
    return await client.request(
        "GET",
        f"/api/cultureservice/bclCultureTemplate/coursesLabelList/{scheme_id}",
        params={"type": type_id},
    )


async def culture_label_relation(
    client: RawOneClient, *, scheme_id: str | int, type_id: str = "2",
) -> Any:
    """Fetch course-to-label relations for a scheme.

    Maps which courses fall under which label/category.

    Ref: GET /api/cultureservice/bclCourseLabelRelation/list/{schemeId}?type=...
    """
    return await client.request(
        "GET",
        f"/api/cultureservice/bclCourseLabelRelation/list/{scheme_id}",
        params={"type": type_id},
    )
