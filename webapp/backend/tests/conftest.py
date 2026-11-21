from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from brokerguard_api.db import Database
from brokerguard_api.main import create_app
from brokerguard_api.roles import Role
from brokerguard_api.security import create_user
from brokerguard_api.settings import Settings

PASSWORD = "mat-khau-thu-nghiem-01"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(database=tmp_path / "app.db", frontend_dist=tmp_path / "no_dist",
                    max_failed_logins=3)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings), base_url="http://127.0.0.1") as c:
        yield c


@pytest.fixture
def db(client: TestClient) -> Database:
    database: Database = client.app.state.db  # type: ignore[attr-defined]
    return database


def make_user(db: Database, username: str, role: Role) -> None:
    create_user(db, username, username.title(), PASSWORD, role)


def login(client: TestClient, username: str, password: str = PASSWORD) -> dict[str, str]:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"X-CSRF-Token": client.cookies["bgw_csrf"]}
