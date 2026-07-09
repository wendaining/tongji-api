from __future__ import annotations

from tongji.core.session_store import SessionStore


def test_session_store_save_read_status_and_clear(tmp_path):
    store = SessionStore(tmp_path / "session.json")

    assert store.status().has_session is False

    saved = store.save("secret-session", source="manual", jsessionid="secret-jsession")
    assert saved.sessionid == "secret-session"
    assert saved.jsessionid == "secret-jsession"

    loaded = store.read()
    assert loaded is not None
    assert loaded.sessionid == "secret-session"
    assert store.get_sessionid() == "secret-session"
    assert store.get_jsessionid() == "secret-jsession"
    assert store.get_cookie_header() == "JSESSIONID=secret-jsession; sessionid=secret-session"

    status = store.public_status()
    assert status["has_session"] is True
    assert status["has_jsession"] is True
    assert status["is_valid"] is True
    assert "sessionid" not in status
    assert status["source"] == "manual"

    store.clear()
    assert store.read() is None
    assert store.public_status() == {
        "has_session": False,
        "has_jsession": False,
        "source": None,
        "created_at": None,
        "updated_at": None,
        "last_validated_at": None,
        "invalidated_at": None,
        "is_valid": False,
    }


def test_session_store_can_mark_session_invalid(tmp_path):
    store = SessionStore(tmp_path / "session.json")
    store.save("session-value", source="test", jsessionid="jsession-value")

    record = store.mark_invalid()

    assert record is not None
    assert record.invalidated_at is not None
    assert store.public_status()["is_valid"] is False

    store.save("new-session", source="login", jsessionid="new-jsession")
    assert store.public_status()["is_valid"] is True


def test_session_store_imports_initial_sessionid_when_empty(tmp_path):
    store = SessionStore(tmp_path / "session.json", initial_sessionid="env-session")

    assert store.get_sessionid() == "env-session"
    assert store.status().source == "environment"


def test_session_store_does_not_override_existing_with_initial_sessionid(tmp_path):
    path = tmp_path / "session.json"
    store = SessionStore(path)
    store.save("manual-session", source="manual")

    new_store = SessionStore(path, initial_sessionid="env-session")

    assert new_store.get_sessionid() == "manual-session"
    assert new_store.status().source == "manual"
