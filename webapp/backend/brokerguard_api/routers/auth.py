"""Login, logout, current user and invite redemption."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from brokerguard_api.db import Database
from brokerguard_api.deps import current_session, get_db, get_settings
from brokerguard_api.roles import PERMISSIONS, ROLE_LABELS_VI
from brokerguard_api.security import (
    AuthError,
    SessionInfo,
    User,
    authenticate,
    create_session,
    end_session,
    redeem_invite,
)
from brokerguard_api.settings import Settings

router = APIRouter(prefix="/api", tags=["auth"])


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class InviteIn(BaseModel):
    code: str = Field(min_length=4, max_length=128)
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=10, max_length=256)


class MeOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    role_label: str
    permissions: list[str]


def me_out(user: User) -> MeOut:
    return MeOut(id=user.id, username=user.username, display_name=user.display_name,
                 role=user.role.value, role_label=ROLE_LABELS_VI[user.role],
                 permissions=sorted(p.value for p in PERMISSIONS[user.role]))


def _start_session(response: Response, db: Database, settings: Settings, user: User) -> None:
    token, csrf = create_session(db, settings, user)
    max_age = int(settings.session_hours * 3600)
    response.set_cookie(settings.session_cookie, token, max_age=max_age, httponly=True,
                        samesite="strict", secure=settings.secure_cookies, path="/")
    # Readable by the page so it can echo it in the CSRF header (double submit).
    response.set_cookie(settings.csrf_cookie, csrf, max_age=max_age, httponly=False,  # noqa: S604
                        samesite="strict", secure=settings.secure_cookies, path="/")


@router.post("/auth/login", response_model=MeOut)
def login(body: LoginIn, response: Response, db: Database = Depends(get_db),  # noqa: B008
          settings: Settings = Depends(get_settings)) -> MeOut:  # noqa: B008
    try:
        user = authenticate(db, settings, body.username, body.password)
    except AuthError as exc:
        db.audit(None, "auth.login_failed", "{}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from None
    _start_session(response, db, settings, user)
    db.audit(user.id, "auth.login")
    return me_out(user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response,
           info: SessionInfo = Depends(current_session),  # noqa: B008
           db: Database = Depends(get_db),  # noqa: B008
           settings: Settings = Depends(get_settings)) -> None:  # noqa: B008
    end_session(db, request.cookies.get(settings.session_cookie))
    response.delete_cookie(settings.session_cookie, path="/")
    response.delete_cookie(settings.csrf_cookie, path="/")
    db.audit(info.user.id, "auth.logout")


@router.post("/auth/redeem-invite", response_model=MeOut)
def redeem(body: InviteIn, response: Response, db: Database = Depends(get_db),  # noqa: B008
           settings: Settings = Depends(get_settings)) -> MeOut:  # noqa: B008
    try:
        user = redeem_invite(db, body.code, body.username, body.display_name, body.password)
    except AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from None
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tên đăng nhập đã tồn tại.") from None
    _start_session(response, db, settings, user)
    return me_out(user)


@router.get("/me", response_model=MeOut)
def me(info: SessionInfo = Depends(current_session)) -> MeOut:  # noqa: B008
    return me_out(info.user)
