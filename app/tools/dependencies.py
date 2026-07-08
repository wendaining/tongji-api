from __future__ import annotations

from fastapi import Request

from app.raw_one.client import RawOneClient
from app.raw_one.login import ProgrammaticLoginManager
from app.raw_one.session_store import SessionStore


def get_session_store(request: Request) -> SessionStore:
    return request.app.state.session_store


def get_raw_one_client(request: Request) -> RawOneClient:
    return request.app.state.raw_one_client


def get_login_manager(request: Request) -> ProgrammaticLoginManager:
    return request.app.state.login_manager
