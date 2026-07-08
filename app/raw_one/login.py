from __future__ import annotations

import base64
import json
import re
import secrets
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from http.cookiejar import Cookie
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from app.core.errors import AppError, UpstreamError
from app.raw_one.session_store import SessionStore

IAM_BASE_URL = "https://iam.tongji.edu.cn"
ENTITY_ID = "SYS20230001"
SMS_USERNAME_PASSWORD = "urn_oasis_names_tc_SAML_2.0_ac_classes_SMSUsernamePassword"
BAM_USERNAME_PASSWORD = "urn_oasis_names_tc_SAML_2.0_ac_classes_BAMUsernamePassword"

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

ENTRY_HEADERS = {
    "User-Agent": BROWSER_USER_AGENT,
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "Referer": "https://1.tongji.edu.cn/ssologin",
}

FORM_HEADERS = {
    "User-Agent": BROWSER_USER_AGENT,
    "Origin": IAM_BASE_URL,
    "Host": "iam.tongji.edu.cn",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

SSO_HEADERS = {
    "User-Agent": BROWSER_USER_AGENT,
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
}


class LoginResultStatus(StrEnum):
    SUCCESS = "SUCCESS"
    MFA_REQUIRED = "MFA_REQUIRED"


@dataclass(frozen=True, slots=True)
class SsoLoginCallback:
    token: str
    uid: str
    ts: str


@dataclass(frozen=True, slots=True)
class LoginStartResult:
    status: LoginResultStatus
    login_id: str | None = None
    expires_at: datetime | None = None
    mfa_channel: str | None = None
    masked_email: str | None = None
    masked_mobile: str | None = None
    session_status: dict[str, Any] | None = None


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


class ProgrammaticLoginFlow:
    def __init__(
        self,
        *,
        username: str,
        password: str,
        one_base_url: str,
        timeout_seconds: float,
        session_store: SessionStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.username = username
        self.password = password
        self.one_base_url = one_base_url.rstrip("/")
        self.session_store = session_store
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
        )
        self._owns_client = client is None
        self.chain_url = ""
        self.authn_lc_key = ""
        self.sp_auth_chain_code = ""
        self.rsa_url = ""
        self.auth_payload: dict[str, str] = {}
        self.is_mfa = False
        self.last_auth_data: dict[str, str] = {}

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def start(self) -> LoginStartResult:
        await self._fetch_entry_page()
        auth_data = await self._submit_password()
        login_failed = _login_failed_value(auth_data)

        if _is_mfa_required(auth_data):
            self.is_mfa = True
            await self._request_email_code()
            return LoginStartResult(
                status=LoginResultStatus.MFA_REQUIRED,
                mfa_channel="email",
                masked_email=auth_data.get("email") or None,
                masked_mobile=auth_data.get("mobile") or None,
            )

        if login_failed not in {"", "false"}:
            raise AppError(
                code="IAM_LOGIN_FAILED",
                message=_extract_authn_error_tip(auth_data) or "同济 IAM 登录失败。",
                status_code=401,
            )

        await self._finish_login()
        return LoginStartResult(
            status=LoginResultStatus.SUCCESS,
            session_status=self.session_store.public_status(),
        )

    async def submit_mfa_code(self, code: str) -> LoginStartResult:
        normalized_code = code.strip()
        if not normalized_code:
            raise AppError(code="INVALID_MFA_CODE", message="MFA code cannot be empty.")

        self.auth_payload = {
            "j_username": self.username,
            "type": "email",
            "sms_checkcode": normalized_code,
            "popViewException": "Pop2",
            "j_checkcode": "请输入验证码",
            "op": "login",
            "spAuthChainCode": self.sp_auth_chain_code,
        }
        response = await self.client.post(
            self.chain_url,
            data=self.auth_payload,
            headers=self._form_headers(),
            follow_redirects=False,
        )
        auth_data = _parse_auth_response(response.text)
        self.last_auth_data = auth_data

        login_failed = _login_failed_value(auth_data)
        if login_failed not in {"", "false"}:
            raise AppError(
                code="IAM_MFA_FAILED",
                message=_extract_authn_error_tip(auth_data) or "同济 IAM 验证码未通过。",
                status_code=401,
            )

        await self._finish_login()
        return LoginStartResult(
            status=LoginResultStatus.SUCCESS,
            session_status=self.session_store.public_status(),
        )

    async def _fetch_entry_page(self) -> None:
        entry_url = f"{self.one_base_url}/api/ssoservice/system/loginIn"
        response, _ = await self._get_follow_redirects(entry_url, headers=ENTRY_HEADERS)
        if response.status_code >= 400:
            raise UpstreamError(
                "无法进入同济 IAM 登录页面。",
                details={"upstream_status": response.status_code},
            )

        self.chain_url = str(response.url)
        self.authn_lc_key = _extract_authn_lc_key(self.chain_url, response.text)
        self.rsa_url = _extract_rsa_url(response.text)
        self.sp_auth_chain_code = _extract_sp_auth_chain_code(response.text)

        if not self.chain_url or not self.authn_lc_key:
            raise UpstreamError("无法解析 IAM 登录页面 authnLcKey。")
        if not self.rsa_url:
            raise UpstreamError("无法解析 IAM 登录页面 RSA 脚本地址。")
        if not self.sp_auth_chain_code:
            raise UpstreamError("无法解析 IAM 登录页面 spAuthChainCode。")

    async def _submit_password(self) -> dict[str, str]:
        encrypted_password = await self._encrypt_password()
        payload = {
            "j_username": self.username,
            "j_password": encrypted_password,
            "j_checkcode": "请输入验证码",
            "op": "login",
            "spAuthChainCode": self.sp_auth_chain_code,
            "authnLcKey": self.authn_lc_key,
        }
        response = await self.client.post(
            self.chain_url,
            data=payload,
            headers=self._form_headers(),
            follow_redirects=False,
        )
        auth_data = _parse_auth_response(response.text)
        self.last_auth_data = auth_data
        return auth_data

    async def _request_email_code(self) -> None:
        response = await self.client.post(
            f"{IAM_BASE_URL}/idp/sendCheckCode.do",
            data={"j_username": self.username, "type": "email"},
            headers=self._form_headers(),
            follow_redirects=False,
        )
        if response.status_code >= 400:
            raise UpstreamError(
                "同济 IAM 邮箱验证码发送失败。",
                details={"upstream_status": response.status_code},
            )

    async def _finish_login(self) -> None:
        location_url = await self._post_authn_engine()
        response, redirect_urls = await self._get_follow_redirects(
            location_url,
            headers=SSO_HEADERS,
        )
        if response.status_code >= 400:
            raise UpstreamError(
                "同济 IAM SSO 跳转失败。",
                details={"upstream_status": response.status_code},
            )

        ssologin_url = _find_ssologin_url(response, redirect_urls)
        callback = parse_ssologin_callback_url(ssologin_url)
        sessionid = await self._session_login(callback)
        jsessionid = self._cookie_value("JSESSIONID", domain_contains="1.tongji.edu.cn")
        self.session_store.save(
            sessionid,
            source="programmatic_login",
            jsessionid=jsessionid,
        )

    async def _post_authn_engine(self) -> str:
        for current_auth in self._current_auth_candidates():
            auth_url = (
                f"{IAM_BASE_URL}/idp/AuthnEngine?"
                f"currentAuth={current_auth}&authnLcKey={self.authn_lc_key}&entityId={ENTITY_ID}"
            )
            response = await self.client.post(
                auth_url,
                data=self.auth_payload,
                headers=self._form_headers(),
                follow_redirects=False,
            )
            location_url = response.headers.get("Location")
            if location_url:
                return location_url

        raise UpstreamError("同济 IAM AuthnEngine 未返回 SSO 跳转地址。")

    async def _session_login(self, callback: SsoLoginCallback) -> str:
        response = await self.client.post(
            f"{self.one_base_url}/api/sessionservice/session/login",
            data={
                "token": callback.token,
                "uid": callback.uid,
                "ts": callback.ts,
            },
            headers={
                "User-Agent": BROWSER_USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Origin": self.one_base_url,
                "Referer": f"{self.one_base_url}/ssologin",
            },
            follow_redirects=False,
        )
        if response.status_code >= 400:
            raise UpstreamError(
                "1 系统 session/login 请求失败。",
                details={"upstream_status": response.status_code},
            )

        sessionid = self._cookie_value("sessionid", domain_contains="1.tongji.edu.cn")
        if sessionid:
            return sessionid

        try:
            data = response.json()
        except ValueError:
            data = {}
        sessionid = _extract_sessionid_from_json(data)
        if not sessionid:
            raise UpstreamError(
                "1 系统 session/login 未返回 sessionid。",
                details={"upstream_status": response.status_code},
            )
        return sessionid

    async def _encrypt_password(self) -> str:
        response = await self.client.get(self.rsa_url, headers=SSO_HEADERS, follow_redirects=True)
        if response.status_code >= 400:
            raise UpstreamError(
                "无法获取 IAM RSA 公钥脚本。",
                details={"upstream_status": response.status_code},
            )

        public_key = _extract_rsa_public_key(response.text)
        rsa_key = RSA.import_key(public_key)
        cipher = PKCS1_v1_5.new(rsa_key)
        encrypted = cipher.encrypt(self.password.encode())
        return base64.b64encode(encrypted).decode()

    async def _get_follow_redirects(
        self,
        url: str,
        *,
        headers: dict[str, str],
        max_redirects: int = 12,
    ) -> tuple[httpx.Response, list[str]]:
        redirect_urls: list[str] = []
        response = await self.client.get(url, headers=headers, follow_redirects=False)
        redirect_urls.append(str(response.url))

        for _ in range(max_redirects):
            if response.status_code not in {301, 302, 303, 307, 308}:
                return response, redirect_urls

            location = response.headers.get("Location")
            if not location:
                return response, redirect_urls

            next_url = urljoin(str(response.url), location)
            response = await self.client.get(next_url, headers=headers, follow_redirects=False)
            redirect_urls.append(str(response.url))

        raise UpstreamError("同济 IAM 重定向次数过多。")

    def _form_headers(self) -> dict[str, str]:
        return {**FORM_HEADERS, "Referer": self.chain_url}

    def _current_auth_candidates(self) -> list[str]:
        # The observed reference implementation and the written analysis disagree
        # on the SMS/BAM mapping, so try the observed working order first and keep
        # the alternate as a fallback before giving up.
        if self.is_mfa:
            return [SMS_USERNAME_PASSWORD, BAM_USERNAME_PASSWORD]
        return [BAM_USERNAME_PASSWORD, SMS_USERNAME_PASSWORD]

    def _cookie_value(self, name: str, *, domain_contains: str | None = None) -> str | None:
        for cookie in self.client.cookies.jar:
            if not isinstance(cookie, Cookie):
                continue
            if cookie.name != name:
                continue
            if domain_contains and domain_contains not in cookie.domain:
                continue
            if cookie.value:
                return cookie.value
        value = self.client.cookies.get(name, default=None)
        return value or None


class ProgrammaticLoginManager:
    def __init__(
        self,
        *,
        username: str | None,
        password: str | None,
        one_base_url: str,
        timeout_seconds: float,
        session_store: SessionStore,
        pending_ttl_seconds: int = 600,
    ) -> None:
        self.username = username
        self.password = password
        self.one_base_url = one_base_url
        self.timeout_seconds = timeout_seconds
        self.session_store = session_store
        self.pending_ttl_seconds = pending_ttl_seconds
        self._pending: dict[str, tuple[ProgrammaticLoginFlow, datetime]] = {}

    async def start_login(self) -> LoginStartResult:
        await self._cleanup_expired()
        self._require_credentials()
        flow = ProgrammaticLoginFlow(
            username=self.username or "",
            password=self.password or "",
            one_base_url=self.one_base_url,
            timeout_seconds=self.timeout_seconds,
            session_store=self.session_store,
        )
        try:
            result = await flow.start()
        except Exception:
            await flow.aclose()
            raise

        if result.status == LoginResultStatus.MFA_REQUIRED:
            login_id = secrets.token_urlsafe(24)
            expires_at = datetime.now(UTC) + timedelta(seconds=self.pending_ttl_seconds)
            self._pending[login_id] = (flow, expires_at)
            return LoginStartResult(
                status=result.status,
                login_id=login_id,
                expires_at=expires_at,
                mfa_channel=result.mfa_channel,
                masked_email=result.masked_email,
                masked_mobile=result.masked_mobile,
            )

        await flow.aclose()
        return result

    async def submit_mfa_code(self, *, login_id: str, code: str) -> LoginStartResult:
        await self._cleanup_expired()
        flow_tuple = self._pending.pop(login_id, None)
        if flow_tuple is None:
            raise AppError(
                code="LOGIN_CHALLENGE_NOT_FOUND",
                message="登录挑战不存在或已过期，请重新发起登录。",
                status_code=404,
            )

        flow, _ = flow_tuple
        try:
            return await flow.submit_mfa_code(code)
        finally:
            await flow.aclose()

    async def aclose(self) -> None:
        pending = list(self._pending.values())
        self._pending.clear()
        for flow, _ in pending:
            await flow.aclose()

    async def pending_status(self, login_id: str) -> dict[str, Any]:
        await self._cleanup_expired()
        flow_tuple = self._pending.get(login_id)
        if flow_tuple is None:
            return {"exists": False}
        _, expires_at = flow_tuple
        return {"exists": True, "expires_at": expires_at.isoformat()}

    def _require_credentials(self) -> None:
        if not self.username or not self.password:
            raise AppError(
                code="IAM_CREDENTIALS_NOT_CONFIGURED",
                message="TJ_IAM_USERNAME and TJ_IAM_PASSWORD are required for programmatic login.",
                status_code=500,
            )

    async def _cleanup_expired(self) -> None:
        now = datetime.now(UTC)
        expired_ids = [
            login_id for login_id, (_, expires_at) in self._pending.items() if expires_at <= now
        ]
        for login_id in expired_ids:
            flow, _ = self._pending.pop(login_id)
            await flow.aclose()


def _extract_authn_lc_key(url: str, html: str) -> str:
    parsed = urlparse(url)
    query_value = parse_qs(parsed.query).get("authnLcKey", [""])[0]
    if query_value:
        return query_value

    patterns = [
        r'id=["\']authnLcKey["\'][^>]*value=["\']([^"\']+)["\']',
        r'name=["\']authnLcKey["\'][^>]*value=["\']([^"\']+)["\']',
        r'authnLcKey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
    ]
    return _first_regex_group(patterns, html)


def _extract_rsa_url(html: str) -> str:
    patterns = [
        r'src=["\']([^"\']*crypt\.js[^"\']*)["\']',
        r'src=["\']([^"\']*secondAuth\.js[^"\']*)["\']',
    ]
    raw_url = _first_regex_group(patterns, html)
    return urljoin(f"{IAM_BASE_URL}/idp/", raw_url) if raw_url else ""


def _extract_sp_auth_chain_code(html: str) -> str:
    patterns = [
        r'\$\(["\']#spAuthChainCode1["\']\)\.val\(["\']([^"\']+)["\']\)',
        r'id=["\']spAuthChainCode1["\'][^>]*value=["\']([^"\']+)["\']',
        r'name=["\']spAuthChainCode["\'][^>]*value=["\']([^"\']+)["\']',
    ]
    return _first_regex_group(patterns, html)


def _extract_rsa_public_key(js_text: str) -> str:
    patterns = [
        r'encrypt\.setPublicKey\(["\']([^"\']+)["\']\)',
        r'setPublicKey\(["\']([^"\']+)["\']\)',
    ]
    key_body = _first_regex_group(patterns, js_text)
    if not key_body:
        raise UpstreamError("无法从 IAM JS 中解析 RSA 公钥。")
    return f"-----BEGIN PUBLIC KEY-----\n{key_body}\n-----END PUBLIC KEY-----"


def _first_regex_group(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _parse_auth_response(response_text: str) -> dict[str, str]:
    try:
        payload = json.loads(response_text)
        if isinstance(payload, dict):
            return {str(key): "" if value is None else str(value) for key, value in payload.items()}
    except json.JSONDecodeError:
        pass

    try:
        xml_root = ET.fromstring(response_text)
    except ET.ParseError as exc:
        raise UpstreamError("无法解析 IAM 登录响应。") from exc

    auth_data: dict[str, str] = {}
    for child in xml_root:
        auth_data[child.tag] = "" if child.text is None else child.text.strip()
    return auth_data


def _login_failed_value(auth_data: dict[str, str]) -> str:
    return auth_data.get("loginFailed", "").strip().lower()


def _is_mfa_required(auth_data: dict[str, str]) -> bool:
    login_failed = _login_failed_value(auth_data)
    if login_failed in {"", "false"}:
        return False
    return bool(
        auth_data.get("popViewException")
        or auth_data.get("email")
        or auth_data.get("mobile")
        or login_failed == "popviewexception"
    )


def _extract_authn_error_tip(auth_data: dict[str, str]) -> str:
    return auth_data.get("authnErrorTip", "").strip()


def _find_ssologin_url(response: httpx.Response, redirect_urls: list[str] | None = None) -> str:
    candidates = [*(redirect_urls or []), str(response.url)]
    for candidate in candidates:
        parsed = urlparse(candidate)
        if parsed.hostname == "1.tongji.edu.cn" and parsed.path.endswith("/ssologin"):
            return candidate
    raise UpstreamError("SSO 跳转未到达 1 系统 ssologin URL。")


def _extract_sessionid_from_json(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    candidates: list[Any] = [
        data.get("sessionid"),
        data.get("sessionId"),
        data.get("xToken"),
        data.get("token"),
    ]
    nested = data.get("data")
    if isinstance(nested, dict):
        candidates.extend(
            [
                nested.get("sessionid"),
                nested.get("sessionId"),
                nested.get("xToken"),
                nested.get("token"),
            ]
        )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None
