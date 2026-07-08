from __future__ import annotations

from typing import Any


def ok(data: Any = None) -> dict[str, Any]:
    return {"ok": True, "data": data if data is not None else {}}

