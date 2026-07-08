from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tongji.core.config import reset_settings_cache
from tongji.server import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TJ_IAM_USERNAME", "student-id")
    monkeypatch.setenv("TJ_IAM_PASSWORD", "password")
    monkeypatch.setenv("TJ_SESSION_STORE_PATH", str(tmp_path / "session.json"))
    monkeypatch.delenv("TJ_SESSIONID", raising=False)
    monkeypatch.delenv("TJ_JSESSIONID", raising=False)
    monkeypatch.delenv("TJ_IMAP_EMAIL", raising=False)
    monkeypatch.delenv("TJ_IMAP_GRANTCODE", raising=False)
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_settings_cache()
