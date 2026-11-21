import sqlite3

from fastapi.testclient import TestClient

from brokerguard_api.db import Database
from brokerguard_api.roles import Permission, Role, allowed
from brokerguard_api.security import create_invite
from tests.conftest import PASSWORD, login, make_user


def test_login_sets_hardened_cookies_and_me(client: TestClient, db: Database) -> None:
    make_user(db, "huy", Role.ADMIN)
    r = client.post("/api/auth/login", json={"username": "HUY", "password": PASSWORD})
    assert r.status_code == 200 and r.json()["role_label"] == "Quản trị"
    cookies = [h for k, h in r.headers.items() if k.lower() == "set-cookie"]
    session = next(c for c in cookies if c.startswith("bgw_session="))
    assert "HttpOnly" in session and "SameSite=strict" in session
    assert client.get("/api/me").json()["username"] == "huy"
    assert r.headers["X-Frame-Options"] == "DENY" and r.headers["Cache-Control"] == "no-store"


def test_password_is_stored_as_argon2id(db: Database) -> None:
    make_user(db, "minh", Role.VIEWER)
    with db.connect() as c:
        stored = c.execute("SELECT password_hash FROM users").fetchone()[0]
    assert stored.startswith("$argon2id$") and PASSWORD not in stored


def test_wrong_password_and_unknown_user_look_the_same(client: TestClient, db: Database) -> None:
    make_user(db, "huy", Role.ADMIN)
    a = client.post("/api/auth/login", json={"username": "huy", "password": "sai-mat-khau-1"})
    b = client.post("/api/auth/login", json={"username": "ai-do", "password": "sai-mat-khau-1"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_lockout_after_repeated_failures(client: TestClient, db: Database) -> None:
    make_user(db, "huy", Role.ADMIN)
    for _ in range(3):
        client.post("/api/auth/login", json={"username": "huy", "password": "sai-mat-khau-1"})
    r = client.post("/api/auth/login", json={"username": "huy", "password": PASSWORD})
    assert r.status_code == 401 and "tạm khóa" in r.json()["detail"]


def test_unauthenticated_and_csrf(client: TestClient, db: Database) -> None:
    assert client.get("/api/me").status_code == 401
    make_user(db, "huy", Role.ADMIN)
    headers = login(client, "huy")
    assert client.post("/api/auth/logout").status_code == 403  # no CSRF header
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": "x"}).status_code == 403
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/me").status_code == 401


def test_session_token_is_not_stored_in_clear(client: TestClient, db: Database) -> None:
    make_user(db, "huy", Role.ADMIN)
    login(client, "huy")
    token = client.cookies["bgw_session"]
    with db.connect() as c:
        stored = [r[0] for r in c.execute("SELECT token_hash FROM sessions")]
    assert stored and token not in stored


def test_invite_redeem_once(client: TestClient, db: Database) -> None:
    code = create_invite(db, Role.PRESENTER, None)
    body = {"code": code, "username": "thay.giao", "display_name": "Thầy", "password": PASSWORD}
    r = client.post("/api/auth/redeem-invite", json=body)
    assert r.status_code == 200 and r.json()["role"] == "presenter"
    again = client.post("/api/auth/redeem-invite", json={**body, "username": "khac"})
    assert again.status_code == 400
    bad = client.post("/api/auth/redeem-invite", json={**body, "code": "khong-ton-tai"})
    assert bad.status_code == 400


def test_duplicate_username_rejected(db: Database) -> None:
    make_user(db, "huy", Role.ADMIN)
    try:
        make_user(db, "Huy", Role.VIEWER)
    except sqlite3.IntegrityError:
        return
    raise AssertionError("usernames must be unique ignoring case")


def test_permission_table() -> None:
    assert allowed(Role.PRESENTER, Permission.SEND_REAL_EMAIL)
    assert not allowed(Role.EDITOR, Permission.SEND_REAL_EMAIL)
    assert not allowed(Role.VIEWER, Permission.SEND_REAL_EMAIL)
    assert not allowed(Role.VIEWER, Permission.SWITCH_MODE)
    assert allowed(Role.EDITOR, Permission.EDIT_SOURCES)
    assert all(allowed(Role.ADMIN, p) for p in Permission)


def test_migrations_are_idempotent(db: Database) -> None:
    assert db.migrate() == db.migrate()
