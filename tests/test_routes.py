"""Tests for the thin HTTP server layer (tongji/server.py)."""

from __future__ import annotations


def test_healthz_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_session_ping_no_active_session(client):
    response = client.get("/api/session/ping")
    assert response.status_code == 409


def test_students_me_no_session(client):
    response = client.get("/api/students/me")
    assert response.status_code == 409


def test_notices_no_session(client):
    response = client.get("/api/notices")
    assert response.status_code == 409


def test_courses_no_session(client):
    response = client.get("/api/courses")
    assert response.status_code == 409


def test_courses_search_requires_calendar_id(client):
    response = client.get("/api/courses/search")
    assert response.status_code == 422


def test_courses_search_no_session(client):
    response = client.get("/api/courses/search?calendarId=122&keyword=操作系统")
    assert response.status_code == 409


def test_calendar_list_no_session(client):
    response = client.get("/api/calendar/list")
    assert response.status_code == 409


def test_cross_courses_apply_no_session(client):
    response = client.get("/api/cross-courses/apply?studentId=student-demo&calendarId=121")
    assert response.status_code == 409


def test_module_metadata_lists_all_raw_modules(client):
    response = client.get("/meta/modules")
    assert response.status_code == 200
    assert response.json()["count"] == 46


def test_raw_route_validation_happens_before_upstream_call(client):
    response = client.get("/api/grades")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_local_admin_routes_are_registered(client):
    response = client.get("/admin/session")
    assert response.status_code == 200
    assert response.json()["has_session"] is False
