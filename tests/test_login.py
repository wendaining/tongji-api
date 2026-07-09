from __future__ import annotations

from urllib.parse import parse_qs

import httpx
import pytest
from Crypto.PublicKey import RSA

from tongji.core.errors import AppError
from tongji.core.login import (
    LoginResultStatus,
    ProgrammaticLoginFlow,
    ProgrammaticLoginManager,
    parse_ssologin_callback_url,
)
from tongji.core.session_store import SessionStore


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


def _form(request: httpx.Request) -> dict[str, str]:
    parsed = parse_qs(request.content.decode())
    return {key: value[0] for key, value in parsed.items()}


def _rsa_script() -> str:
    key = RSA.generate(1024)
    public_pem = key.publickey().export_key().decode()
    public_body = public_pem.replace("-----BEGIN PUBLIC KEY-----", "")
    public_body = public_body.replace("-----END PUBLIC KEY-----", "")
    public_body = "".join(public_body.split())
    return f"encrypt.setPublicKey('{public_body}');"


@pytest.mark.asyncio
async def test_programmatic_login_flow_follows_xialing_style_redirect_chain(tmp_path):
    store = SessionStore(tmp_path / "session.json")
    rsa_script = _rsa_script()
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(f"{request.method} {request.url.host}{request.url.path}")
        if request.url.host == "1.tongji.edu.cn" and request.url.path == (
            "/api/ssoservice/system/loginIn"
        ):
            if request.url.query:
                return httpx.Response(
                    302,
                    headers={"Location": "https://1.tongji.edu.cn/ssologin?token=t1&uid=u1&ts=123"},
                    request=request,
                )
            return httpx.Response(
                302,
                headers={
                    "Set-Cookie": "JSESSIONID=one-jsession; Path=/; HttpOnly",
                    "Location": (
                        "https://iam.tongji.edu.cn/idp/authcenter/ActionAuthChain?authnLcKey=lc-key"
                    ),
                },
                request=request,
            )
        if request.url.host == "iam.tongji.edu.cn" and request.url.path == (
            "/idp/authcenter/ActionAuthChain"
        ):
            if request.method == "GET":
                return httpx.Response(
                    200,
                    text="""
                    <input id="authnLcKey" value="lc-key">
                    <script src="crypt.js"></script>
                    <script>$("#spAuthChainCode1").val('chain-code');</script>
                    """,
                    request=request,
                )
            form = _form(request)
            assert form["j_username"] == "student-id"
            assert form["j_password"] != "password"
            assert form["spAuthChainCode"] == "chain-code"
            assert form["authnLcKey"] == "lc-key"
            return httpx.Response(200, json={"loginFailed": "false"}, request=request)
        if request.url.host == "iam.tongji.edu.cn" and request.url.path == "/idp/crypt.js":
            return httpx.Response(200, text=rsa_script, request=request)
        if request.url.host == "iam.tongji.edu.cn" and request.url.path == "/idp/AuthnEngine":
            return httpx.Response(
                302,
                headers={
                    "Location": (
                        "https://iam.tongji.edu.cn/idp/profile/OAUTH2/"
                        "AuthorizationCode/SSO?code=iam-code"
                    )
                },
                request=request,
            )
        if request.url.host == "iam.tongji.edu.cn" and request.url.path == (
            "/idp/profile/OAUTH2/AuthorizationCode/SSO"
        ):
            return httpx.Response(
                302,
                headers={
                    "Location": "https://1.tongji.edu.cn/api/ssoservice/system/loginIn?code=iam-code"
                },
                request=request,
            )
        if request.url.host == "1.tongji.edu.cn" and request.url.path == "/ssologin":
            return httpx.Response(200, text="<html></html>", request=request)
        if request.url.host == "1.tongji.edu.cn" and request.url.path == (
            "/api/sessionservice/session/login"
        ):
            form = _form(request)
            assert form == {"token": "t1", "uid": "u1", "ts": "123"}
            return httpx.Response(
                200,
                headers={"Set-Cookie": "sessionid=one-session; Path=/; HttpOnly"},
                json={"ok": True},
                request=request,
            )
        raise AssertionError(str(request.url))

    async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
    flow = ProgrammaticLoginFlow(
        username="student-id",
        password="password",
        one_base_url="https://1.tongji.edu.cn",
        timeout_seconds=15,
        session_store=store,
        client=async_client,
    )

    result = await flow.start()

    assert result.status == LoginResultStatus.SUCCESS
    assert store.get_sessionid() == "one-session"
    assert store.get_jsessionid() == "one-jsession"
    assert "POST iam.tongji.edu.cn/idp/AuthnEngine" in seen
    assert "POST 1.tongji.edu.cn/api/sessionservice/session/login" in seen
    await async_client.aclose()


@pytest.mark.asyncio
async def test_programmatic_login_manager_supports_manual_email_mfa(tmp_path):
    store = SessionStore(tmp_path / "session.json")
    rsa_script = _rsa_script()
    sent_email_code = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal sent_email_code
        if request.url.host == "1.tongji.edu.cn" and request.url.path == (
            "/api/ssoservice/system/loginIn"
        ):
            if request.url.query:
                return httpx.Response(
                    302,
                    headers={"Location": "https://1.tongji.edu.cn/ssologin?token=t1&uid=u1&ts=123"},
                    request=request,
                )
            return httpx.Response(
                302,
                headers={
                    "Set-Cookie": "JSESSIONID=one-jsession; Path=/; HttpOnly",
                    "Location": (
                        "https://iam.tongji.edu.cn/idp/authcenter/ActionAuthChain?authnLcKey=lc-key"
                    ),
                },
                request=request,
            )
        if request.url.host == "iam.tongji.edu.cn" and request.url.path == (
            "/idp/authcenter/ActionAuthChain"
        ):
            if request.method == "GET":
                return httpx.Response(
                    200,
                    text="""
                    <input id="authnLcKey" value="lc-key">
                    <script src="crypt.js"></script>
                    <script>$("#spAuthChainCode1").val('chain-code');</script>
                    """,
                    request=request,
                )
            form = _form(request)
            if "sms_checkcode" not in form:
                return httpx.Response(
                    200,
                    json={
                        "loginFailed": "popViewException",
                        "popViewException": "Pop2",
                        "email": "a***@example.com",
                    },
                    request=request,
                )
            assert sent_email_code is True
            assert form["sms_checkcode"] == "123456"
            return httpx.Response(200, json={"loginFailed": "false"}, request=request)
        if request.url.host == "iam.tongji.edu.cn" and request.url.path == "/idp/crypt.js":
            return httpx.Response(200, text=rsa_script, request=request)
        if request.url.host == "iam.tongji.edu.cn" and request.url.path == (
            "/idp/sendCheckCode.do"
        ):
            sent_email_code = True
            form = _form(request)
            assert form == {"j_username": "student-id", "type": "email"}
            return httpx.Response(200, text="ok", request=request)
        if request.url.host == "iam.tongji.edu.cn" and request.url.path == "/idp/AuthnEngine":
            return httpx.Response(
                302,
                headers={
                    "Location": (
                        "https://iam.tongji.edu.cn/idp/profile/OAUTH2/"
                        "AuthorizationCode/SSO?code=iam-code"
                    )
                },
                request=request,
            )
        if request.url.host == "iam.tongji.edu.cn" and request.url.path == (
            "/idp/profile/OAUTH2/AuthorizationCode/SSO"
        ):
            return httpx.Response(
                302,
                headers={
                    "Location": "https://1.tongji.edu.cn/api/ssoservice/system/loginIn?code=iam-code"
                },
                request=request,
            )
        if request.url.host == "1.tongji.edu.cn" and request.url.path == "/ssologin":
            return httpx.Response(200, text="<html></html>", request=request)
        if request.url.host == "1.tongji.edu.cn" and request.url.path == (
            "/api/sessionservice/session/login"
        ):
            return httpx.Response(
                200,
                headers={"Set-Cookie": "sessionid=one-session; Path=/; HttpOnly"},
                json={"ok": True},
                request=request,
            )
        raise AssertionError(str(request.url))

    async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)

    class TestFlow(ProgrammaticLoginFlow):
        def __init__(self, **kwargs):
            super().__init__(**kwargs, client=async_client)

    manager = ProgrammaticLoginManager(
        username="student-id",
        password="password",
        one_base_url="https://1.tongji.edu.cn",
        timeout_seconds=15,
        session_store=store,
    )

    original_flow_class = ProgrammaticLoginFlow
    try:
        import tongji.core.login as login_module

        login_module.ProgrammaticLoginFlow = TestFlow
        start_result = await manager.start_login()
        assert start_result.status == LoginResultStatus.MFA_REQUIRED
        assert start_result.login_id
        assert start_result.masked_email == "a***@example.com"

        final_result = await manager.submit_mfa_code(
            login_id=start_result.login_id,
            code="123456",
        )
        assert final_result.status == LoginResultStatus.SUCCESS
        assert store.get_sessionid() == "one-session"
    finally:
        import tongji.core.login as login_module

        login_module.ProgrammaticLoginFlow = original_flow_class
        await async_client.aclose()
