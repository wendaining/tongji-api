from __future__ import annotations

import asyncio
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
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import httpx
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from tongji.core.errors import AppError, UpstreamError
from tongji.core.imap import ImapConfig, wait_for_code, fetch_latest_code
from tongji.core.session_store import SessionStore

# ---------------------------------------------------------------------------
# Constants — original values from XiaLing233 / fetch-1-dot-tongji
# ---------------------------------------------------------------------------

IAM_BASE_URL = "https://iam.tongji.edu.cn"
ENTITY_ID = "SYS20230001"

# currentAuth values used by AuthnEngine after login / MFA
SMS_USERNAME_PASSWORD = "urn_oasis_names_tc_SAML_2.0_ac_classes_SMSUsernamePassword"
BAM_USERNAME_PASSWORD = "urn_oasis_names_tc_SAML_2.0_ac_classes_BAMUsernamePassword"

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Ref: XiaLing233 loginout.py — entry_headers
ENTRY_HEADERS = {
    "User-Agent": BROWSER_USER_AGENT,
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.7"
    ),
    "Referer": "https://1.tongji.edu.cn/ssologin",
}

# Ref: XiaLing233 loginout.py — form_headers (Referer is set dynamically)
FORM_HEADERS = {
    "User-Agent": BROWSER_USER_AGENT,
    "Origin": IAM_BASE_URL,
    "Host": "iam.tongji.edu.cn",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

# Ref: XiaLing233 loginout.py — sso_headers
SSO_HEADERS = {
    "User-Agent": BROWSER_USER_AGENT,
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.7"
    ),
}


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Helper functions — aligned with XiaLing233 encrypt.py / loginout.py
# ---------------------------------------------------------------------------


async def _get_rsa_public_key(js_url: str, rsa_client: httpx.AsyncClient) -> str:
    """Ref: XiaLing233 encrypt.py — getRSAPublicKey.

    Iterate lines, skip comments (//), take the FIRST uncommented
    encrypt.setPublicKey call.
    """
    response = await rsa_client.get(js_url, headers={
        "User-Agent": BROWSER_USER_AGENT,
    })
    if response.status_code >= 400:
        raise UpstreamError(
            "无法获取 IAM RSA 公钥脚本。",
            details={"upstream_status": response.status_code},
        )

    for line in response.text.split("\n"):
        if "encrypt.setPublicKey" in line and not line.strip().startswith("//"):
            key_body = line.split("'")[1]
            return f"-----BEGIN PUBLIC KEY-----\n{key_body}\n-----END PUBLIC KEY-----"

    raise UpstreamError("无法从 IAM JS 中解析 RSA 公钥。")


def _get_sp_auth_chain_code(html: str) -> str:
    """Ref: XiaLing233 encrypt.py — getspAuthChainCode.

    Look for a line containing '"#spAuthChainCode1"' and extract the value
    between single quotes.
    """
    for line in html.split("\n"):
        if '"#spAuthChainCode1"' in line:
            return line.split("'")[1]
    return ""


def _extract_rsa_url(html: str) -> str:
    """Ref: XiaLing233 loginout.py — _fetch_entry_page.

    Look for a line containing 'crypt.js' and construct the full URL.
    """
    for line in html.split("\n"):
        if "crypt.js" in line:
            raw = line.split('src="')[1].split('"')[0]
            return f"https://iam.tongji.edu.cn/idp/{raw}"
    return ""


def _extract_authn_lc_key(url: str) -> str:
    """Ref: XiaLing233 loginout.py — _fetch_entry_page.

    authnLcKey is the last query parameter, so split on '=' and take the
    rightmost segment.
    """
    return url.split("=")[-1]


async def _encrypt_password(rsa_url: str, password: str, rsa_client: httpx.AsyncClient) -> str:
    """Ref: XiaLing233 encrypt.py — encryptPassword."""
    public_key_pem = await _get_rsa_public_key(rsa_url, rsa_client)
    rsa_key = RSA.import_key(public_key_pem)
    cipher = PKCS1_v1_5.new(rsa_key)
    encrypted = cipher.encrypt(password.encode())
    return base64.b64encode(encrypted).decode()


def _parse_auth_response(response_text: str) -> dict[str, str]:
    """Ref: XiaLing233 loginout.py — _parse_auth_response.

    Try JSON first; fall back to XML (<JSONObject>...</JSONObject>).
    """
    try:
        payload = json.loads(response_text)
        if isinstance(payload, dict):
            return {str(k): "" if v is None else str(v) for k, v in payload.items()}
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
    """Ref: XiaLing233 loginout.py — _submit_password.

    If loginFailed is non-empty and != 'false', MFA is required.
    """
    login_failed = _login_failed_value(auth_data)
    return login_failed != "" and login_failed != "false"


def _extract_authn_error_tip(auth_data: dict[str, str]) -> str:
    """Ref: XiaLing233 loginout.py — _extract_authn_error_tip."""
    return auth_data.get("authnErrorTip", "").strip()


def _extract_aes_url(html: str) -> str:
    """Ref: XiaLing233 loginout.py — _authn_engine.

    After AuthnEngine redirect lands on 1.tongji.edu.cn, the page contains
    a <script src="/static/js/app.XXXX.js"> tag that holds AES keys used
    for attachment download encryption.
    """
    for part in html.split(">"):
        if "/static/js/app." in part:
            return "https://1.tongji.edu.cn" + part.split("src=")[1].split(">")[0]
    return ""


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
        candidates.extend([
            nested.get("sessionid"),
            nested.get("sessionId"),
            nested.get("xToken"),
            nested.get("token"),
        ])
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


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


# ---------------------------------------------------------------------------
# ProgrammaticLoginFlow — XiaLing233 SSOLoginStateMachine ported to httpx
# ---------------------------------------------------------------------------


class ProgrammaticLoginFlow:
    """State-machine login for 1.tongji.edu.cn.

    Ported from XiaLing233 / fetch-1-dot-tongji / crawler/auth/loginout.py,
    adapted for httpx async.  Every extraction helper, header set, and form
    field is kept as close to the original as possible.
    """

    def __init__(
        self,
        *,
        username: str,
        password: str,
        one_base_url: str,
        timeout_seconds: float,
        session_store: SessionStore,
        imap_config: ImapConfig | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.username = username
        self.password = password
        self.one_base_url = one_base_url.rstrip("/")
        self.session_store = session_store
        self.imap_config = imap_config
        # httpx cookie jar persists across the whole flow just like
        # requests.Session does in the reference implementation.
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
        )
        self._owns_client = client is None

        # State — mirrors LoginContext in loginout.py
        self.chain_url = ""
        self.authn_lc_key = ""
        self.sp_auth_chain_code = ""
        self.rsa_url = ""
        self.is_mfa = False
        self.auth_payload: dict[str, str] = {}

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    # ------------------------------------------------------------------
    # Public entry points (called by ProgrammaticLoginManager)
    # ------------------------------------------------------------------

    async def start(self) -> LoginStartResult:
        await self._fetch_entry_page()
        auth_data = await self._submit_password()

        if _is_mfa_required(auth_data):
            self.is_mfa = True
            await self._request_email_code()

            # Ref: XiaLing233 loginout.py — _submit_enhance_code polls IMAP
            # after a 15-second wait.  We try auto-fetch first; fall back to
            # manual input if IMAP is not configured or the code hasn't arrived.
            if self.imap_config:
                code = await self._wait_for_mfa_code()
                if code:
                    return await self._finish_mfa_login(code)

            return LoginStartResult(
                status=LoginResultStatus.MFA_REQUIRED,
                mfa_channel="email",
                masked_email=auth_data.get("email") or None,
                masked_mobile=auth_data.get("mobile") or None,
            )

        login_failed = _login_failed_value(auth_data)
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
        """Ref: XiaLing233 loginout.py — _submit_enhance_code."""
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
            # authnLcKey is NOT needed here — it's already in chain_url's query string.
        }

        data = urlencode(self.auth_payload)

        response = await self.client.post(
            self.chain_url,
            content=data,
            headers=self._form_headers(),
            follow_redirects=False,
        )
        auth_data = _parse_auth_response(response.text)

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

    # ------------------------------------------------------------------
    # Step: FETCH_ENTRY — ref _fetch_entry_page
    # ------------------------------------------------------------------

    async def _fetch_entry_page(self) -> None:
        """Ref: XiaLing233 loginout.py — _fetch_entry_page.

        Follow redirects from the SSO entry point to the IAM login page,
        then extract authnLcKey, RSA script URL, and spAuthChainCode.
        """
        entry_url = f"{self.one_base_url}/api/ssoservice/system/loginIn"

        # Allow auto-redirect all the way to ActionAuthChain (like requests does)
        response = await self.client.get(entry_url, headers=ENTRY_HEADERS, follow_redirects=True)
        if response.status_code >= 400:
            raise UpstreamError(
                "无法进入同济 IAM 登录页面。",
                details={"upstream_status": response.status_code},
            )

        self.chain_url = str(response.url)
        # authnLcKey is always the last query param
        self.authn_lc_key = _extract_authn_lc_key(self.chain_url)
        self.rsa_url = _extract_rsa_url(response.text)
        self.sp_auth_chain_code = _get_sp_auth_chain_code(response.text)

        if not self.chain_url or not self.authn_lc_key:
            raise UpstreamError("无法解析 IAM 登录页面 authnLcKey。")
        if not self.rsa_url:
            raise UpstreamError("无法解析 IAM 登录页面 RSA 脚本地址。")
        if not self.sp_auth_chain_code:
            raise UpstreamError("无法解析 IAM 登录页面 spAuthChainCode。")

    # ------------------------------------------------------------------
    # Step: SUBMIT_PASSWORD — ref _submit_password
    # ------------------------------------------------------------------

    async def _submit_password(self) -> dict[str, str]:
        """Ref: XiaLing233 loginout.py — _submit_password.

        RSA-encrypt the password and POST to ActionAuthChain.
        Uses urlencode() to match the reference exactly.
        """
        encrypted_password = await _encrypt_password(self.rsa_url, self.password, self.client)

        self.auth_payload = {
            "j_username": self.username,
            "j_password": encrypted_password,
            "j_checkcode": "请输入验证码",
            "op": "login",
            "spAuthChainCode": self.sp_auth_chain_code,
            "authnLcKey": self.authn_lc_key,
        }
        data = urlencode(self.auth_payload)

        response = await self.client.post(
            self.chain_url,
            content=data,
            headers=self._form_headers(),
            follow_redirects=False,
        )
        return _parse_auth_response(response.text)

    # ------------------------------------------------------------------
    # Step: REQUEST_ENHANCE_CODE — ref _request_enhance_code
    # ------------------------------------------------------------------

    async def _request_email_code(self) -> None:
        """Ref: XiaLing233 loginout.py — _request_enhance_code."""
        data = urlencode({"j_username": self.username, "type": "email"})

        response = await self.client.post(
            f"{IAM_BASE_URL}/idp/sendCheckCode.do",
            content=data,
            headers=self._form_headers(),
            follow_redirects=False,
        )
        if response.status_code >= 400:
            raise UpstreamError(
                "同济 IAM 邮箱验证码发送失败。",
                details={"upstream_status": response.status_code},
            )

    async def _wait_for_mfa_code(self) -> str | None:
        """Poll IMAP for the MFA verification code (runs in thread pool)."""
        if not self.imap_config:
            return None
        return await asyncio.to_thread(
            wait_for_code,
            self.imap_config,
            timeout_seconds=20,
            poll_interval_seconds=5,
        )

    async def _finish_mfa_login(self, code: str) -> LoginStartResult:
        """Auto-submit the MFA code and complete the login."""
        self.auth_payload = {
            "j_username": self.username,
            "type": "email",
            "sms_checkcode": code,
            "popViewException": "Pop2",
            "j_checkcode": "请输入验证码",
            "op": "login",
            "spAuthChainCode": self.sp_auth_chain_code,
        }

        data = urlencode(self.auth_payload)
        response = await self.client.post(
            self.chain_url,
            content=data,
            headers=self._form_headers(),
            follow_redirects=False,
        )
        auth_data = _parse_auth_response(response.text)
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

    # ------------------------------------------------------------------
    # Step: AUTHN_ENGINE + SESSION_LOGIN — ref _authn_engine + _session_login
    # ------------------------------------------------------------------

    async def _finish_login(self) -> None:
        """Ref: XiaLing233 loginout.py — _authn_engine + _session_login."""
        location_url = await self._post_authn_engine()

        # After AuthnEngine, switch to SSO headers and follow redirects
        # to land on 1.tongji.edu.cn (just like the reference does with
        # session.headers.clear() + sso_headers + allow_redirects=True).
        response = await self.client.get(
            location_url,
            headers=SSO_HEADERS,
            follow_redirects=True,
        )
        if response.status_code >= 400:
            raise UpstreamError(
                "同济 IAM SSO 跳转失败。",
                details={"upstream_status": response.status_code},
            )

        ssologin_url = str(response.url)
        # Also extract AES URL (used later for attachment downloads)
        aes_url = _extract_aes_url(response.text)
        if aes_url:
            self.session_store.set_metadata("aes_url", aes_url)

        callback = parse_ssologin_callback_url(ssologin_url)
        sessionid = await self._session_login(callback)
        jsessionid = self._cookie_value("JSESSIONID", domain_contains="1.tongji.edu.cn")
        self.session_store.save(
            sessionid,
            source="programmatic_login",
            jsessionid=jsessionid,
        )

    async def _post_authn_engine(self) -> str:
        """Ref: XiaLing233 loginout.py — _authn_engine (first half).

        POST to AuthnEngine with the appropriate currentAuth value.
        Returns the Location header for the next redirect.
        """
        if self.is_mfa:
            current_auth = SMS_USERNAME_PASSWORD
        else:
            current_auth = BAM_USERNAME_PASSWORD

        auth_url = (
            f"{IAM_BASE_URL}/idp/AuthnEngine?"
            f"currentAuth={current_auth}&authnLcKey={self.authn_lc_key}&entityId={ENTITY_ID}"
        )

        data = urlencode(self.auth_payload)
        response = await self.client.post(
            auth_url,
            content=data,
            headers=self._form_headers(),
            follow_redirects=False,
        )
        location_url = response.headers.get("Location")
        if not location_url:
            raise UpstreamError("同济 IAM AuthnEngine 未返回 SSO 跳转地址。")
        return location_url

    async def _session_login(self, callback: SsoLoginCallback) -> str:
        """Ref: XiaLing233 loginout.py — _session_login."""
        data = urlencode({
            "token": callback.token,
            "uid": callback.uid,
            "ts": callback.ts,
        })

        response = await self.client.post(
            f"{self.one_base_url}/api/sessionservice/session/login",
            content=data,
            headers={
                "User-Agent": BROWSER_USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Origin": self.one_base_url,
                "Referer": f"{self.one_base_url}/ssologin",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            follow_redirects=False,
        )
        if response.status_code >= 400:
            raise UpstreamError(
                "1 系统 session/login 请求失败。",
                details={"upstream_status": response.status_code},
            )

        # Try cookie jar first (like requests.Session would)
        sessionid = self._cookie_value("sessionid", domain_contains="1.tongji.edu.cn")
        if sessionid:
            return sessionid

        # Fall back to JSON body
        try:
            data_json = response.json()
        except ValueError:
            data_json = {}
        sessionid = _extract_sessionid_from_json(data_json)
        if not sessionid:
            raise UpstreamError(
                "1 系统 session/login 未返回 sessionid。",
                details={"upstream_status": response.status_code},
            )
        return sessionid

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _form_headers(self) -> dict[str, str]:
        """Ref: loginout.py sets Referer to chain_url dynamically."""
        return {**FORM_HEADERS, "Referer": self.chain_url}

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
        return self.client.cookies.get(name, default=None) or None


# ---------------------------------------------------------------------------
# ProgrammaticLoginManager — FastAPI lifecycle wrapper
# ---------------------------------------------------------------------------


class ProgrammaticLoginManager:
    """Manages pending login flows with TTL.

    Holds in-memory state for login_id → flow mapping so that the admin
    routes can start a login, return a login_id, and later accept an MFA
    code against that id.
    """

    def __init__(
        self,
        *,
        username: str | None,
        password: str | None,
        one_base_url: str,
        timeout_seconds: float,
        session_store: SessionStore,
        imap_config: ImapConfig | None = None,
        pending_ttl_seconds: int = 600,
    ) -> None:
        self.username = username
        self.password = password
        self.one_base_url = one_base_url
        self.timeout_seconds = timeout_seconds
        self.session_store = session_store
        self.imap_config = imap_config
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
            imap_config=self.imap_config,
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
