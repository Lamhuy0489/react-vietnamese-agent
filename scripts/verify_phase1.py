#!/usr/bin/env python3
"""Verify frozen A0 purity, Phase 1 files, and mock capability boundaries."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from react_agent.config import load_yaml
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "smoke"
EXPECTED_TOOLS = {
    "doc_search",
    "doc_read",
    "db_query",
    "cached_search",
    "cached_fetch",
    "calculator",
    "send_email_mock",
    "post_webhook_mock",
}
REQUIRED_FILES = (
    "configs/agent/A0.yaml",
    "configs/models/smoke_model.yaml",
    "configs/runtime/default.yaml",
    "data/smoke/tasks.jsonl",
    "data/smoke/documents/documents.json",
    "data/smoke/cached_pages/pages.json",
    "data/smoke/database/seed.json",
    "data/smoke/database/university.db",
    "docs/phase1_design.md",
    "docs/tool_contracts.md",
    "docs/trace_schema.md",
    "docs/phase1_report.md",
)


def main() -> int:
    failures = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    config = load_yaml(ROOT / "configs" / "agent" / "A0.yaml")
    security = config.get("security")
    if not isinstance(security, dict) or any(value is not False for value in security.values()):
        failures.append("A0 security flags must all be false")

    if (DATA_ROOT / "database" / "university.db").is_file():
        uri = f"file:{DATA_ROOT / 'database' / 'university.db'}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            course_count = connection.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        if course_count != 4:
            failures.append("SQLite smoke fixture has unexpected course count")

    registry = build_smoke_registry(DATA_ROOT)
    if set(registry.names) != EXPECTED_TOOLS:
        failures.append("registry must contain exactly the eight approved tools")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: A0 purity, required artifacts, SQLite fixture, and 8-tool registry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
