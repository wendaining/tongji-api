"""Small CLI over the same registry used by the HTTP server."""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from tongji.core.client import RawOneClient
from tongji.core.config import get_settings
from tongji.core.errors import AppError
from tongji.core.imap import ImapConfig
from tongji.core.logging import configure_logging
from tongji.core.login import LoginResultStatus, ProgrammaticLoginManager
from tongji.core.session_store import SessionStore
from tongji.sdk import TongjiClient


def _print(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _session_store() -> SessionStore:
    settings = get_settings()
    return SessionStore(
        settings.session_store_path,
        initial_sessionid=settings.sessionid,
        initial_jsessionid=settings.jsessionid,
    )


def _raw_client() -> RawOneClient:
    settings = get_settings()
    return RawOneClient(
        base_url=settings.normalized_one_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        session_store=_session_store(),
    )


def _imap_config() -> ImapConfig | None:
    settings = get_settings()
    if not settings.imap_email or not settings.imap_grantcode:
        return None
    return ImapConfig(
        email=settings.imap_email,
        grant_code=settings.imap_grantcode,
        server=settings.imap_server,
        port=settings.imap_port,
    )


async def _login() -> None:
    settings = get_settings()
    manager = ProgrammaticLoginManager(
        username=settings.iam_username,
        password=settings.iam_password,
        one_base_url=settings.normalized_one_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        session_store=_session_store(),
        imap_config=_imap_config(),
        pending_ttl_seconds=settings.login_expires_seconds,
    )
    try:
        result = await manager.start_login()
        if result.status == LoginResultStatus.MFA_REQUIRED:
            code = input("IAM 邮箱验证码: ").strip()
            result = await manager.submit_mfa_code(
                login_id=result.login_id or "",
                code=code,
            )
        _print({"status": result.status.value, "session": result.session_status})
    finally:
        await manager.aclose()


async def _call(module_name: str, data: str) -> None:
    params = json.loads(data)
    if not isinstance(params, dict):
        raise ValueError("--data must be a JSON object")
    client = _raw_client()
    try:
        sdk = TongjiClient(client)
        _print(await sdk.call(module_name, params))
    finally:
        await client.aclose()


async def _ping() -> None:
    client = _raw_client()
    try:
        sdk = TongjiClient(client)
        _print(await sdk.call("session_ping"))
    finally:
        await client.aclose()


async def _logout() -> None:
    settings = get_settings()
    manager = ProgrammaticLoginManager(
        username=settings.iam_username,
        password=settings.iam_password,
        one_base_url=settings.normalized_one_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        session_store=_session_store(),
    )
    try:
        await manager.logout()
        _print({"ok": True, "session": _session_store().public_status()})
    finally:
        await manager.aclose()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tongji")
    subcommands = parser.add_subparsers(dest="command", required=True)

    serve = subcommands.add_parser("serve", help="Start the HTTP API server")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)

    subcommands.add_parser("login", help="Login through Tongji IAM")
    subcommands.add_parser("logout", help="Log out and clear the stored session")
    subcommands.add_parser("ping", help="Check the stored 1.tongji.edu.cn session")
    subcommands.add_parser("modules", help="List available raw API modules")

    call = subcommands.add_parser("call", help="Call a raw API module")
    call.add_argument("module")
    call.add_argument("--data", default="{}", help="JSON object with module parameters")
    return parser


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    args = _parser().parse_args()
    try:
        if args.command == "serve":
            from tongji.server import run_server

            run_server(host=args.host, port=args.port)
        elif args.command == "login":
            asyncio.run(_login())
        elif args.command == "ping":
            asyncio.run(_ping())
        elif args.command == "logout":
            asyncio.run(_logout())
        elif args.command == "modules":
            from tongji.modules import get_registry

            _print(get_registry().metadata())
        elif args.command == "call":
            asyncio.run(_call(args.module, args.data))
    except (AppError, ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, AppError):
            _print(
                {
                    "ok": False,
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                        "action_required": exc.action_required,
                    },
                }
            )
        else:
            _print({"ok": False, "error": str(exc)})
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
