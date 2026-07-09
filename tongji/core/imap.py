"""IMAP email verification code reader — aligned with XiaLing233 imap.py.

Ref: https://github.com/XiaLing233/fetch-1-dot-tongji/blob/master/crawler/auth/imap.py

QQ mail defaults: imap.qq.com:993, grant code (not password) required.
Verification emails are expected in INBOX with subject "增强认证验证码通知".
"""

from __future__ import annotations

import email as email_module
import imaplib
import re
import time
from dataclasses import dataclass

# Ref: XiaLing233 imap.py — subject search keyword and code regex
SEARCH_SUBJECT = "增强认证验证码通知"
CODE_PATTERN = re.compile(r"验证码[：:]?\s*(\d{6})")


@dataclass
class ImapConfig:
    email: str
    grant_code: str
    server: str = "imap.qq.com"
    port: int = 993


def _connect(config: ImapConfig) -> imaplib.IMAP4_SSL:
    mailbox = imaplib.IMAP4_SSL(config.server, config.port)
    mailbox.login(config.email, config.grant_code)
    return mailbox


def fetch_latest_code(config: ImapConfig) -> str | None:
    """Read the most recent verification code from INBOX.

    Searches for emails whose subject contains the IAM verification subject
    (both unseen and seen), picks the latest one, and extracts the 6-digit
    code.  Returns None if no matching email is found.
    """
    mailbox = _connect(config)
    try:
        mailbox.select("INBOX")

        # Search UNSEEN first, then ALL as fallback
        code = _search_and_extract(mailbox, f'(UNSEEN SUBJECT "{SEARCH_SUBJECT}")')
        if code:
            return code
        code = _search_and_extract(mailbox, f'(SUBJECT "{SEARCH_SUBJECT}")')
        return code
    finally:
        mailbox.logout()


def wait_for_code(
    config: ImapConfig,
    *,
    timeout_seconds: int = 45,
    poll_interval_seconds: int = 5,
) -> str | None:
    """Poll IMAP until a verification code arrives or timeout.

    Ref: XiaLing233 loginout.py _submit_enhance_code — after sending the
    verification code request, polls IMAP to read the code automatically.
    """
    deadline = time.monotonic() + timeout_seconds
    last_seen_id: str | None = None

    mailbox = _connect(config)
    try:
        mailbox.select("INBOX")

        # Snapshot: remember the latest matching email id so we can detect
        # a NEW email arriving after the code request.
        criteria = f'(SUBJECT "{SEARCH_SUBJECT}")'
        result, data = mailbox.search(None, criteria)
        if data and data[0]:
            last_seen_id = data[0].split()[-1].decode()

        while time.monotonic() < deadline:
            time.sleep(poll_interval_seconds)

            result, data = mailbox.search(None, criteria)
            if not data or not data[0]:
                continue

            latest_id = data[0].split()[-1].decode()
            if last_seen_id and latest_id == last_seen_id:
                continue  # no new email yet

            # New email arrived — extract code
            code = _extract_code_from_email(mailbox, latest_id)
            if code:
                return code
            last_seen_id = latest_id

        return None
    finally:
        mailbox.logout()


def _search_and_extract(mailbox: imaplib.IMAP4_SSL, criteria: str) -> str | None:
    result, data = mailbox.search(None, criteria)
    if not data or not data[0]:
        return None
    latest_id = data[0].split()[-1].decode()
    return _extract_code_from_email(mailbox, latest_id)


def _extract_code_from_email(mailbox: imaplib.IMAP4_SSL, email_id: str) -> str | None:
    result, msg_data = mailbox.fetch(email_id, "(RFC822)")
    if not msg_data or not isinstance(msg_data[0], tuple):
        return None
    raw_email = msg_data[0][1]
    if not isinstance(raw_email, bytes):
        return None
    msg = email_module.message_from_bytes(raw_email)
    content = _get_email_content(msg)
    match = CODE_PATTERN.search(content)
    return match.group(1) if match else None


def _get_email_content(msg: email_module.message.Message) -> str:
    """Ref: XiaLing233 imap.py — _get_email_content."""
    content = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in {"text/plain", "text/html"}:
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    content = payload.decode("utf-8", errors="ignore")
                    break
    else:
        payload = msg.get_payload(decode=True)
        if isinstance(payload, bytes):
            content = payload.decode("utf-8", errors="ignore")

    # If HTML, strip tags to plain text
    if "<html" in content:
        from html.parser import HTMLParser

        class _Stripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text: list[str] = []

            def handle_data(self, data: str) -> None:
                self.text.append(data)

        stripper = _Stripper()
        stripper.feed(content)
        content = "".join(stripper.text)

    return content
