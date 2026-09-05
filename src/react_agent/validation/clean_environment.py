#!/usr/bin/env python3
"""Validate the frozen-shape synthetic environment used by clean benchmark v1."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from react_agent.environment import CacheStore, DocumentStore

ROOT = Path(__file__).resolve().parents[3]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"
EXPECTED_TABLE_COUNTS = {
    "departments": 10,
    "courses": 60,
    "rooms": 30,
    "course_sections": 80,
    "students": 100,
    "registrations": 200,
    "scholarships": 40,
    "staff_directory": 40,
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_environment(clean_root: Path = CLEAN_ROOT) -> list[str]:
    """Return deterministic validation failures; an empty list means acceptance."""

    failures: list[str] = []
    environment_root = clean_root / "environment"
    manifest_root = clean_root / "manifests"
    document_path = environment_root / "documents" / "documents.json"
    page_path = environment_root / "cached_pages" / "pages.json"
    seed_path = environment_root / "database" / "seed.json"
    database_path = environment_root / "database" / "university.db"
    catalog_path = manifest_root / "source_catalog.json"
    manifest_path = manifest_root / "environment_manifest.json"
    required = (
        document_path,
        page_path,
        seed_path,
        database_path,
        catalog_path,
        manifest_path,
    )
    for path in required:
        if not path.is_file():
            failures.append(f"missing file: {path.relative_to(clean_root)}")
    if failures:
        return failures

    # Reuse runtime parsers so benchmark fixtures cannot drift from tool inputs.
    try:
        DocumentStore.from_json(document_path)
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        failures.append(f"invalid document store: {error}")
    try:
        CacheStore.from_json(page_path)
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        failures.append(f"invalid cached-page store: {error}")

    documents = _read_json(document_path)
    pages = _read_json(page_path)
    seed = _read_json(seed_path)
    catalog = _read_json(catalog_path)
    manifest = _read_json(manifest_path)
    if len(documents) != 50:
        failures.append(f"expected 50 documents, found {len(documents)}")
    if len(pages) != 25:
        failures.append(f"expected 25 cached pages, found {len(pages)}")
    if len(catalog) != 75:
        failures.append(f"expected 75 source catalog entries, found {len(catalog)}")

    document_ids = [item["doc_id"] for item in documents]
    page_ids = [item["page_id"] for item in pages]
    if len(document_ids) != len(set(document_ids)):
        failures.append("duplicate document IDs")
    if len(page_ids) != len(set(page_ids)):
        failures.append("duplicate cached-page IDs")
    if any(
        not page["source_url"].startswith("https://synthetic-university.invalid/") for page in pages
    ):
        failures.append("cached page URL escaped the reserved .invalid domain")

    catalog_ids = [item["source_id"] for item in catalog]
    if set(catalog_ids) != set(document_ids + page_ids):
        failures.append("source catalog IDs do not exactly match environment source IDs")
    if len(catalog_ids) != len(set(catalog_ids)):
        failures.append("duplicate source catalog IDs")
    fact_ids = [
        f"{item['source_id']}:{fact['fact_id']}" for item in catalog for fact in item["facts"]
    ]
    if len(fact_ids) != len(set(fact_ids)):
        failures.append("duplicate source-scoped fact IDs")
    domains = Counter(item["domain"] for item in catalog)
    if len(domains) < 10:
        failures.append(f"expected at least 10 domains, found {len(domains)}")

    if set(seed) != set(EXPECTED_TABLE_COUNTS):
        failures.append("seed table names differ from the eight-table contract")
    for table, expected_count in EXPECTED_TABLE_COUNTS.items():
        if len(seed.get(table, [])) != expected_count:
            failures.append(
                f"seed table {table}: expected {expected_count}, found {len(seed.get(table, []))}"
            )

    uri = f"file:{database_path}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            table_names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
                )
            }
            if table_names != set(EXPECTED_TABLE_COUNTS):
                failures.append("SQLite table names differ from the eight-table contract")
            for table, expected_count in EXPECTED_TABLE_COUNTS.items():
                # Table is selected from the frozen constant above, never from external input.
                count = connection.execute(
                    f"SELECT COUNT(*) FROM {table}"  # noqa: S608 - frozen table constant
                ).fetchone()[0]
                if count != expected_count:
                    failures.append(
                        f"SQLite table {table}: expected {expected_count}, found {count}"
                    )
            foreign_key_checks = (
                (
                    "courses.department_id",
                    "SELECT COUNT(*) FROM courses c LEFT JOIN departments d "
                    "ON c.department_id=d.department_id WHERE d.department_id IS NULL",
                ),
                (
                    "course_sections.course_code/room_id",
                    "SELECT COUNT(*) FROM course_sections s LEFT JOIN courses c "
                    "ON s.course_code=c.course_code LEFT JOIN rooms r ON s.room_id=r.room_id "
                    "WHERE c.course_code IS NULL OR r.room_id IS NULL",
                ),
                (
                    "registrations.student_id/section_id",
                    "SELECT COUNT(*) FROM registrations g LEFT JOIN students s "
                    "ON g.student_id=s.student_id LEFT JOIN course_sections x "
                    "ON g.section_id=x.section_id "
                    "WHERE s.student_id IS NULL OR x.section_id IS NULL",
                ),
                (
                    "scholarships.student_id",
                    "SELECT COUNT(*) FROM scholarships h LEFT JOIN students s "
                    "ON h.student_id=s.student_id WHERE s.student_id IS NULL",
                ),
            )
            for relation, query in foreign_key_checks:
                if connection.execute(query).fetchone()[0] != 0:
                    failures.append(f"broken synthetic foreign-key relation: {relation}")
    except sqlite3.Error as error:
        failures.append(f"invalid SQLite database: {error}")

    if manifest.get("environment_version") != "clean_env_v1":
        failures.append("incorrect environment version")
    if manifest.get("seed") != 2026 or manifest.get("synthetic") is not True:
        failures.append("manifest must declare seed 2026 and synthetic=true")
    if manifest.get("internet_required") is not False:
        failures.append("clean environment must be offline")
    if manifest.get("database_tables") != EXPECTED_TABLE_COUNTS:
        failures.append("manifest table counts differ from the contract")
    manifest_files = manifest.get("files", {})
    for path in (document_path, page_path, seed_path, database_path, catalog_path):
        relative = str(path.relative_to(clean_root))
        if manifest_files.get(relative) != _sha256(path):
            failures.append(f"checksum mismatch: {relative}")

    return failures
