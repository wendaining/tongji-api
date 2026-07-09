from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "jsessionid",
    "j_password",
    "sms_checkcode",
    "grant_code",
    "imap_grantcode",
    "iam_password",
    "password",
    "sessionid",
    "token",
    "x-token",
}

SENSITIVE_PATTERNS = [
    re.compile(r"(sessionid=)[^;\s]+", re.IGNORECASE),
    re.compile(r"(JSESSIONID=)[^;\s]+", re.IGNORECASE),
    re.compile(r"(j_password=)[^&\s]+", re.IGNORECASE),
    re.compile(r"(sms_checkcode=)[^&\s]+", re.IGNORECASE),
    re.compile(r"(X-Token:\s*)[^\s]+", re.IGNORECASE),
    re.compile(r"(Authorization:\s*Bearer\s+)[^\s]+", re.IGNORECASE),
    re.compile(r"([?&]token=)[^&\s]+", re.IGNORECASE),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(r"\1<redacted>", redacted)
    return redacted


def redact_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in mapping.items():
        if key.lower() in SENSITIVE_KEYS:
            result[key] = "<redacted>"
        elif isinstance(value, str):
            result[key] = redact_text(value)
        elif isinstance(value, Mapping):
            result[key] = redact_mapping(value)
        else:
            result[key] = value
    return result


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        if record.args:
            record.args = tuple(
                redact_text(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        return True


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    root_logger = logging.getLogger()
    if not any(isinstance(existing, RedactingFilter) for existing in root_logger.filters):
        root_logger.addFilter(RedactingFilter())
