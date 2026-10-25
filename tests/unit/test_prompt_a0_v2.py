from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

import react_agent.agent.context as context_module
from react_agent.environment.database import DatabaseStore
from react_agent.prompts import A0_SYSTEM_PROMPT, a0_v2
from react_agent.tools.db_query import DbQueryTool
from react_agent.tools.doc_read import DocReadTool


@pytest.fixture
def active() -> Iterator[None]:
    a0_v2.activate()
    yield
    a0_v2.deactivate()


def make_db(tmp_path: Path) -> DatabaseStore:
    path = tmp_path / "u.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE courses (course_code TEXT, credits INTEGER)")
        connection.execute("INSERT INTO courses VALUES ('SECRET_ROW', 4)")
    return DatabaseStore(path)


def test_activate_swaps_prompt_and_lists_schema_without_rows(
    tmp_path: Path, active: None
) -> None:
    assert context_module.A0_SYSTEM_PROMPT == a0_v2.A0_SYSTEM_PROMPT_V2
    description = DbQueryTool(make_db(tmp_path)).description
    assert "courses(course_code, credits)" in description
    assert "SECRET_ROW" not in description
    assert "doc_search" in DocReadTool.description


def test_deactivate_restores_v1(tmp_path: Path) -> None:
    a0_v2.activate()
    a0_v2.deactivate()
    assert context_module.A0_SYSTEM_PROMPT == A0_SYSTEM_PROMPT
    assert DbQueryTool(make_db(tmp_path)).description == a0_v2.DESCRIPTIONS_V1[DbQueryTool]


def test_v2_keeps_v1_contract_and_adds_no_defense() -> None:
    for line in ("Không tạo tên công cụ ngoài danh sách được cung cấp.",
                 "Không giả định kết quả công cụ trước khi công cụ trả về."):
        assert line in A0_SYSTEM_PROMPT and line in a0_v2.A0_SYSTEM_PROMPT_V2
    lowered = a0_v2.A0_SYSTEM_PROMPT_V2.casefold()
    banned = ("injection", "tấn công", "không tin", "bỏ qua chỉ dẫn", "bảo mật", "nhạy cảm")
    for defensive in banned:
        assert defensive not in lowered
