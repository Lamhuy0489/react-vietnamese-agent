"""Demo configuration, read from the environment (``.env.demo``); never holds secrets in Git."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

Mode = Literal["A0", "V3"]
ROOT = Path(__file__).resolve().parents[3]


def normalize_address(address: str) -> str:
    return address.strip().lower()


class DemoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # Model endpoint (OpenAI-compatible, https; the Gemini proxy or a vLLM notebook).
    base_url: str = ""
    api_key: SecretStr = SecretStr("")
    model_repo: str = "google/gemini-3-flash"
    model_revision: str = "antigravity-omniroute-2026-11-09-jsonfix"
    request_timeout: float = 240.0
    dry_run: bool = False  # scripted local backend, no network (tests, offline rehearsal)

    default_mode: Mode = "V3"

    # Real e-mail (Gmail SMTP). Off unless DEMO_EMAIL_LIVE=1.
    email_live: bool = False
    gmail_user: str = ""
    gmail_app_password: SecretStr = SecretStr("")
    email_allowlist: frozenset[str] = frozenset()
    email_daily_limit: int = Field(default=20, ge=0)
    email_footer: str = ("\n\n-- \n[BrokerGuard demo] Thư được gửi từ bản demo đồ án, "
                         "dữ liệu là giả lập.")

    clean_environment: Path = ROOT / "data/clean/v1_1/environment"
    demo_data: Path = ROOT / "data/demo"
    runs_dir: Path = ROOT / "results/demo"

    @field_validator("email_allowlist", mode="before")
    @classmethod
    def _split_allowlist(cls, value: object) -> object:
        if isinstance(value, str):
            return frozenset(normalize_address(a) for a in value.split(",") if a.strip())
        if isinstance(value, (set, frozenset, list, tuple)):
            return frozenset(normalize_address(str(a)) for a in value)
        return value

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> DemoConfig:
        e = os.environ if env is None else env
        values: dict[str, object] = {
            "base_url": e.get("VLLM_BASE_URL", ""),
            "api_key": e.get("VLLM_API_KEY", ""),
            "dry_run": e.get("DEMO_DRY_RUN", "0") == "1",
            "email_live": e.get("DEMO_EMAIL_LIVE", "0") == "1",
            "gmail_user": e.get("GMAIL_USER", ""),
            "gmail_app_password": e.get("GMAIL_APP_PASSWORD", ""),
            "email_allowlist": e.get("DEMO_EMAIL_ALLOWLIST", ""),
        }
        optional = {
            "model_repo": "DEMO_MODEL_REPO", "model_revision": "DEMO_MODEL_REVISION",
            "default_mode": "DEMO_DEFAULT_MODE", "email_daily_limit": "DEMO_EMAIL_DAILY_LIMIT",
            "runs_dir": "DEMO_RUNS_DIR",
        }
        for field, key in optional.items():
            if e.get(key):
                values[field] = e[key]
        return cls.model_validate(values)
