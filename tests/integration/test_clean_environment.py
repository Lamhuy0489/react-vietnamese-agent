"""Acceptance checks for the Phase 2 synthetic environment."""

from pathlib import Path

from react_agent.tools.factory import build_smoke_registry
from react_agent.validation import validate_environment

ROOT = Path(__file__).resolve().parents[2]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"
ENVIRONMENT_ROOT = CLEAN_ROOT / "environment"


def test_clean_environment_passes_validator() -> None:
    assert validate_environment(CLEAN_ROOT) == []


def test_clean_environment_loads_all_eight_runtime_tools() -> None:
    registry = build_smoke_registry(ENVIRONMENT_ROOT)
    assert registry.names == (
        "cached_fetch",
        "cached_search",
        "calculator",
        "db_query",
        "doc_read",
        "doc_search",
        "post_webhook_mock",
        "send_email_mock",
    )
