#!/usr/bin/env python3
"""Build the deterministic Phase 1 SQLite fixture from checked-in JSON seed data."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_DIR = ROOT / "data" / "smoke" / "database"
SEED_PATH = DATABASE_DIR / "seed.json"
DATABASE_PATH = DATABASE_DIR / "university.db"

SCHEMA = (
    "CREATE TABLE courses (course_code TEXT PRIMARY KEY, course_name TEXT, "
    "credits INTEGER, department TEXT)",
    "CREATE TABLE course_sections (section_id TEXT PRIMARY KEY, course_code TEXT, "
    "semester TEXT, room TEXT, capacity INTEGER)",
    "CREATE TABLE scholarships (student_id TEXT PRIMARY KEY, student_name TEXT, "
    "department TEXT, scholarship_type TEXT)",
    "CREATE TABLE events (event_id TEXT PRIMARY KEY, event_name TEXT, "
    "event_date TEXT, attendee_count INTEGER)",
    "CREATE TABLE academic_calendar (semester TEXT PRIMARY KEY, "
    "registration_start TEXT, semester_end TEXT)",
)

INSERTS = {
    "courses": "INSERT INTO courses VALUES (?, ?, ?, ?)",
    "course_sections": "INSERT INTO course_sections VALUES (?, ?, ?, ?, ?)",
    "scholarships": "INSERT INTO scholarships VALUES (?, ?, ?, ?)",
    "events": "INSERT INTO events VALUES (?, ?, ?, ?)",
    "academic_calendar": "INSERT INTO academic_calendar VALUES (?, ?, ?)",
}


def main() -> int:
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    temporary_path = DATABASE_DIR / ".university.tmp.db"
    temporary_path.unlink(missing_ok=True)
    with sqlite3.connect(temporary_path) as connection:
        for statement in SCHEMA:
            connection.execute(statement)
        for table, statement in INSERTS.items():
            connection.executemany(statement, seed[table])
        connection.commit()
    temporary_path.replace(DATABASE_PATH)
    print(f"Built {DATABASE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
