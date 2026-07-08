from __future__ import annotations


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
        json={"sessionid": "manual-session"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["has_session"] is True
    assert "sessionid" not in body["data"]


def test_login_start_returns_one_entry_url(client, auth_headers):
    response = client.post("/admin/login/start", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["login_url"] == "https://1.tongji.edu.cn/api/ssoservice/system/loginIn"
    assert data["login_url_type"] == "one_entry_redirects_to_iam"


def test_complete_login_uses_callback_url(client, auth_headers):
    class FakeRawOneClient:
        async def login_with_sso(self, *, token: str, uid: str, ts: str) -> str:
            assert (token, uid, ts) == ("abc", "u1", "123")
            client.app.state.session_store.save("completed-session", source="browser_handoff")
            return "completed-session"

    client.app.state.raw_one_client = FakeRawOneClient()
    response = client.post(
        "/admin/login/complete",
        headers=auth_headers,
        json={
            "callback_url": "https://1.tongji.edu.cn/ssologin?token=abc&uid=u1&ts=123",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["has_session"] is True

