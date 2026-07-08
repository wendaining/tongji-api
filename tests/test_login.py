from __future__ import annotations

import pytest

from app.core.errors import AppError
from app.raw_one.login import parse_ssologin_callback_url


def test_parse_ssologin_callback_url():
    callback = parse_ssologin_callback_url(
        "https://1.tongji.edu.cn/ssologin?token=abc&uid=u1&ts=123"
    )

    assert callback.token == "abc"
    assert callback.uid == "u1"
    assert callback.ts == "123"


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/ssologin?token=abc&uid=u1&ts=123",
        "https://1.tongji.edu.cn/not-ssologin?token=abc&uid=u1&ts=123",
        "https://1.tongji.edu.cn/ssologin?token=abc&uid=u1",
    ],
)
def test_parse_ssologin_callback_url_rejects_invalid_urls(url):
    with pytest.raises(AppError):
        parse_ssologin_callback_url(url)

