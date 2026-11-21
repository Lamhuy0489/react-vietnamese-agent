"""Passwords (argon2id), opaque session tokens, CSRF tokens, login lockout, invites."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from brokerguard_api.db import Database, now
from brokerguard_api.roles import Role
from brokerguard_api.settings import Settings

_HASHER = PasswordHasher()  # argon2id with the library's current recommended parameters
MIN_PASSWORD = 10
# Verified against when the username does not exist, so timing does not reveal accounts.
_DUMMY_HASH = _HASHER.hash(secrets.token_urlsafe(16))


class AuthError(Exception):
    """Login failed; the message is safe to show (no hint whether the user exists)."""


@dataclass(frozen=True)
class User:
    id: int
    username: str
    display_name: str
    role: Role
    active: bool


@dataclass(frozen=True)
class SessionInfo:
    user: User
    csrf_token: str


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD:
        raise ValueError(f"password must have at least {MIN_PASSWORD} characters")
    return _HASHER.hash(password)


def _verify(password_hash: str, password: str) -> bool:
    try:
        return _HASHER.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _user(r: sqlite3.Row) -> User:
    return User(id=r["id"], username=r["username"], display_name=r["display_name"],
                role=Role(r["role"]), active=bool(r["active"]))


def create_user(db: Database, username: str, display_name: str, password: str, role: Role) -> User:
    username = username.strip()
    if not username or len(username) > 64:
        raise ValueError("invalid username")
    with db.connect() as c:
        cur = c.execute(
            "INSERT INTO users (username, display_name, password_hash, role, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, display_name.strip() or username, hash_password(password), role.value,
             now()))
        row = c.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _user(row)


def set_password(db: Database, user_id: int, password: str) -> None:
    with db.connect() as c:
        c.execute("UPDATE users SET password_hash = ?, failed_logins = 0, locked_until = NULL "
                  "WHERE id = ?", (hash_password(password), user_id))
        c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))


def authenticate(db: Database, settings: Settings, username: str, password: str) -> User:
    with db.connect() as c:
        row = c.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    if row is None:
        _verify(_DUMMY_HASH, password)
        raise AuthError("Sai tài khoản hoặc mật khẩu.")
    if row["locked_until"] and row["locked_until"] > now():
        raise AuthError("Tài khoản tạm khóa do đăng nhập sai nhiều lần. Thử lại sau.")
    if not _verify(row["password_hash"], password):
        failed, locked = row["failed_logins"] + 1, None
        if failed >= settings.max_failed_logins:
            locked = (datetime.now(UTC) + timedelta(minutes=settings.lockout_minutes)
                      ).isoformat(timespec="seconds")
            failed = 0
        with db.connect() as c:  # committed before the error is raised
            c.execute("UPDATE users SET failed_logins = ?, locked_until = ? WHERE id = ?",
                      (failed, locked, row["id"]))
        raise AuthError("Sai tài khoản hoặc mật khẩu.")
    if not row["active"]:
        raise AuthError("Tài khoản đã bị vô hiệu hóa.")
    with db.connect() as c:
        c.execute("UPDATE users SET failed_logins = 0, locked_until = NULL WHERE id = ?",
                  (row["id"],))
        if _HASHER.check_needs_rehash(row["password_hash"]):
            c.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                      (_HASHER.hash(password), row["id"]))
    return _user(row)


def create_session(db: Database, settings: Settings, user: User) -> tuple[str, str]:
    """Return (session token, csrf token); only the session token's hash is stored."""
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    expires = (datetime.now(UTC) + timedelta(hours=settings.session_hours)).isoformat(
        timespec="seconds")
    with db.connect() as c:
        c.execute("DELETE FROM sessions WHERE expires_at <= ?", (now(),))
        c.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
                  (_digest(token), user.id, csrf, now(), expires))
    return token, csrf


def lookup_session(db: Database, token: str | None) -> SessionInfo | None:
    if not token:
        return None
    with db.connect() as c:
        row = c.execute(
            "SELECT u.*, s.csrf_token FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > ?", (_digest(token), now())).fetchone()
    if row is None or not row["active"]:
        return None
    return SessionInfo(user=_user(row), csrf_token=row["csrf_token"])


def end_session(db: Database, token: str | None) -> None:
    if token:
        with db.connect() as c:
            c.execute("DELETE FROM sessions WHERE token_hash = ?", (_digest(token),))


def csrf_matches(expected: str, header: str | None, cookie: str | None) -> bool:
    return bool(header) and bool(cookie) and hmac.compare_digest(expected, header or "") and (
        hmac.compare_digest(expected, cookie or ""))


def create_invite(db: Database, role: Role, created_by: int | None, *, hours: float = 72) -> str:
    code = secrets.token_urlsafe(12)
    expires = (datetime.now(UTC) + timedelta(hours=hours)).isoformat(timespec="seconds")
    with db.connect() as c:
        c.execute("INSERT INTO invites (code_hash, role, created_by, expires_at) VALUES (?,?,?,?)",
                  (_digest(code), role.value, created_by, expires))
    db.audit(created_by, "invite.create", json.dumps({"role": role.value}))
    return code


def redeem_invite(db: Database, code: str, username: str, display_name: str,
                  password: str) -> User:
    with db.connect() as c:
        row = c.execute("SELECT * FROM invites WHERE code_hash = ? AND used_by IS NULL "
                        "AND expires_at > ?", (_digest(code.strip()), now())).fetchone()
    if row is None:
        raise AuthError("Mã mời không hợp lệ hoặc đã hết hạn.")
    user = create_user(db, username, display_name, password, Role(row["role"]))
    with db.connect() as c:
        updated = c.execute("UPDATE invites SET used_by = ?, used_at = ? WHERE code_hash = ? "
                            "AND used_by IS NULL", (user.id, now(), row["code_hash"])).rowcount
        if updated != 1:  # raced with another redemption: undo the account
            c.execute("DELETE FROM users WHERE id = ?", (user.id,))
            raise AuthError("Mã mời không hợp lệ hoặc đã hết hạn.")
    db.audit(user.id, "invite.redeem", json.dumps({"role": user.role.value}))
    return user
