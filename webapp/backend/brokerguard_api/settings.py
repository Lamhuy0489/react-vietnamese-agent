"""Workspace settings from the environment (``.env.demo`` at the repository root)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parents[3]
WEBAPP_ROOT = REPO_ROOT / "webapp"


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    database: Path = REPO_ROOT / "results/webapp/app.db"
    frontend_dist: Path = WEBAPP_ROOT / "frontend/dist"
    session_cookie: str = "bgw_session"
    csrf_cookie: str = "bgw_csrf"
    csrf_header: str = "X-CSRF-Token"
    session_hours: float = Field(default=12.0, gt=0)
    max_failed_logins: int = Field(default=5, ge=1)
    lockout_minutes: float = Field(default=15.0, gt=0)
    secure_cookies: bool = False  # True behind https (tunnel); local demo runs on http://127.0.0.1

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        e = os.environ if env is None else env
        values: dict[str, object] = {}
        if e.get("WEBAPP_DATABASE"):
            values["database"] = Path(e["WEBAPP_DATABASE"])
        if e.get("WEBAPP_SECURE_COOKIES") == "1":
            values["secure_cookies"] = True
        if e.get("WEBAPP_SESSION_HOURS"):
            values["session_hours"] = float(e["WEBAPP_SESSION_HOURS"])
        return cls.model_validate(values)
