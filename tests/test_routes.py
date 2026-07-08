"""Tests for the thin HTTP server layer (tongji/server.py)."""

from __future__ import annotations


def test_healthz_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_session_ping_no_active_session(client):
    # No session file → raw_one client raises NoSessionError (409)
    response = client.get("/session/ping")
    assert response.status_code == 409


def test_students_me_no_session(client):
    response = client.get("/students/me")
    assert response.status_code == 409


def test_notices_no_session(client):
    response = client.get("/notices")
    assert response.status_code == 409


def test_courses_no_session(client):
    response = client.get("/courses")
    assert response.status_code == 409


def test_calendar_list_no_session(client):
    response = client.get("/calendar/list")
    assert response.status_code == 409
