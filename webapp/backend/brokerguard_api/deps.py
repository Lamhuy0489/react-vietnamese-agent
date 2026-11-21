"""Request dependencies: database, current session, CSRF and permission checks."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status

from brokerguard_api.db import Database
from brokerguard_api.roles import Permission, allowed
from brokerguard_api.security import SessionInfo, csrf_matches, lookup_session
from brokerguard_api.settings import Settings

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_db(request: Request) -> Database:
    db: Database = request.app.state.db
    return db


def current_session(request: Request, db: Database = Depends(get_db),  # noqa: B008
                    settings: Settings = Depends(get_settings)) -> SessionInfo:  # noqa: B008
    info = lookup_session(db, request.cookies.get(settings.session_cookie))
    if info is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa đăng nhập.")
    if request.method not in SAFE_METHODS and not csrf_matches(
            info.csrf_token, request.headers.get(settings.csrf_header),
            request.cookies.get(settings.csrf_cookie)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Thiếu hoặc sai mã CSRF.")
    return info


def require(permission: Permission) -> Callable[[SessionInfo], SessionInfo]:
    def check(info: SessionInfo = Depends(current_session)) -> SessionInfo:  # noqa: B008
        if not allowed(info.user.role, permission):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Vai trò của bạn không có quyền này.")
        return info

    return check
