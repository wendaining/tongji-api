from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from app.core.errors import AppError


@dataclass(frozen=True, slots=True)
class SsoLoginCallback:
    token: str
    uid: str
    ts: str


def parse_ssologin_callback_url(callback_url: str) -> SsoLoginCallback:
    parsed = urlparse(callback_url)
    if parsed.scheme not in {"http", "https"}:
        raise AppError(code="INVALID_LOGIN_CALLBACK", message="callback_url must be an HTTP URL.")
    if parsed.hostname != "1.tongji.edu.cn":
        raise AppError(
            code="INVALID_LOGIN_CALLBACK",
            message="callback_url host must be 1.tongji.edu.cn.",
        )
    if not parsed.path.endswith("/ssologin"):
        raise AppError(
            code="INVALID_LOGIN_CALLBACK",
            message="callback_url path must end with /ssologin.",
        )

    query = parse_qs(parsed.query)
    try:
        token = query["token"][0]
        uid = query["uid"][0]
        ts = query["ts"][0]
    except (KeyError, IndexError) as exc:
        raise AppError(
            code="INVALID_LOGIN_CALLBACK",
            message="callback_url must include token, uid, and ts.",
        ) from exc

    if not token or not uid or not ts:
        raise AppError(
            code="INVALID_LOGIN_CALLBACK",
            message="callback_url token, uid, and ts cannot be empty.",
        )

    return SsoLoginCallback(token=token, uid=uid, ts=ts)

