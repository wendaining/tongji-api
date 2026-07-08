from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class SessionRecord(BaseModel):
    sessionid: str
    source: str = "manual"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_validated_at: datetime | None = None

    model_config = ConfigDict(extra="ignore")


class SessionStatus(BaseModel):
    has_session: bool
    source: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_validated_at: datetime | None = None


class SessionStore:
    def __init__(self, path: Path, *, initial_sessionid: str | None = None) -> None:
        self.path = path
        self._lock = RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if initial_sessionid and not self.read():
            self.save(initial_sessionid, source="environment")

    def read(self) -> SessionRecord | None:
        with self._lock:
            if not self.path.exists():
                return None
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return SessionRecord.model_validate(raw)

    def save(self, sessionid: str, *, source: str) -> SessionRecord:
        normalized = sessionid.strip()
        if not normalized:
            raise ValueError("sessionid cannot be empty")

        with self._lock:
            existing = self.read()
            now = utc_now()
            record = SessionRecord(
                sessionid=normalized,
                source=source,
                created_at=existing.created_at if existing else now,
                updated_at=now,
                last_validated_at=existing.last_validated_at if existing else None,
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
            tmp_path.replace(self.path)
            return record

    def clear(self) -> None:
        with self._lock:
            if self.path.exists():
                self.path.unlink()

    def get_sessionid(self) -> str | None:
        record = self.read()
        return record.sessionid if record else None

    def mark_validated(self) -> SessionRecord | None:
        with self._lock:
            existing = self.read()
            if not existing:
                return None
            existing.last_validated_at = utc_now()
            existing.updated_at = utc_now()
            tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp_path.write_text(existing.model_dump_json(indent=2), encoding="utf-8")
            tmp_path.replace(self.path)
            return existing

    def status(self) -> SessionStatus:
        record = self.read()
        if not record:
            return SessionStatus(has_session=False)
        return SessionStatus(
            has_session=True,
            source=record.source,
            created_at=record.created_at,
            updated_at=record.updated_at,
            last_validated_at=record.last_validated_at,
        )

    def public_status(self) -> dict[str, Any]:
        return self.status().model_dump(mode="json")

