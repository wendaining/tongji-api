from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.raw_one.login import LoginResultStatus, LoginStartResult


def test_healthz_does_not_require_auth(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "data": {"status": "ok"}}


def test_admin_routes_require_bearer_token(client):
    response = client.get("/admin/session/status")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_session_update_does_not_echo_sessionid(client, auth_headers):
    response = client.put(
        "/admin/session",
        headers=auth_headers,
        json={"sessionid": "manual-session", "jsessionid": "manual-jsession"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["has_session"] is True
    assert body["data"]["has_jsession"] is True
    assert "sessionid" not in body["data"]
    assert "jsessionid" not in body["data"]


def test_login_start_success_returns_session_status(client, auth_headers):
    class FakeLoginManager:
        async def start_login(self) -> LoginStartResult:
            return LoginStartResult(
                status=LoginResultStatus.SUCCESS,
                session_status={"has_session": True, "has_jsession": True},
            )

    client.app.state.login_manager = FakeLoginManager()
    response = client.post("/admin/login/start", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "SUCCESS"
    assert data["session"] == {"has_session": True, "has_jsession": True}


def test_login_start_mfa_returns_login_id(client, auth_headers):
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    class FakeLoginManager:
        async def start_login(self) -> LoginStartResult:
            return LoginStartResult(
                status=LoginResultStatus.MFA_REQUIRED,
                login_id="login-1",
                expires_at=expires_at,
                mfa_channel="email",
                masked_email="a***@example.com",
            )

    client.app.state.login_manager = FakeLoginManager()
    response = client.post("/admin/login/start", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "MFA_REQUIRED"
    assert data["login_id"] == "login-1"
    assert data["mfa"]["channel"] == "email"
    assert data["mfa"]["masked_email"] == "a***@example.com"


def test_login_mfa_submits_code(client, auth_headers):
    class FakeLoginManager:
        async def submit_mfa_code(self, *, login_id: str, code: str) -> LoginStartResult:
            assert login_id == "login-1"
            assert code == "123456"
            return LoginStartResult(
                status=LoginResultStatus.SUCCESS,
                session_status={"has_session": True, "has_jsession": True},
            )

    client.app.state.login_manager = FakeLoginManager()
    response = client.post(
        "/admin/login/mfa",
        headers=auth_headers,
        json={"login_id": "login-1", "code": "123456"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "SUCCESS"


def test_login_status_uses_pending_manager(client, auth_headers):
    class FakeLoginManager:
        async def pending_status(self, login_id: str) -> dict:
            assert login_id == "login-1"
            return {"exists": True}

    client.app.state.login_manager = FakeLoginManager()
    response = client.get("/admin/login/login-1/status", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"] == {"exists": True}
