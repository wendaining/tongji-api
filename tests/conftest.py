from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import reset_settings_cache
from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TJ_API_TOKEN", "test-token")
    monkeypatch.setenv("TJ_SESSION_STORE_PATH", str(tmp_path / "session.json"))
    monkeypatch.delenv("TJ_SESSIONID", raising=False)
    reset_settings_cache()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_settings_cache()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}

