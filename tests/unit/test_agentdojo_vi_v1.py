"""AgentDojo-VI data and check-equivalence helpers (no agentdojo import needed)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/agentdojo_vi"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("agentdojo_vi_v1",
                                                  ROOT / "scripts/agentdojo_vi_v1.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mapping_longest_first_and_case_insensitive() -> None:
    vi = _load()
    pairs = vi.equivalents("slack")
    assert vi.map_text("Mình thấy nó trong Phòng họp", pairs) == "Mình thấy nó trong meeting room"
    assert vi.map_text("vẽ tranh và bơi lội", pairs) == "painting và swimming"
    assert vi.map_answer("Tổng chi tiêu là 1.050 bảng", vi.equivalents("banking")) == (
        "Tổng chi tiêu là 1050 bảng")
    assert vi.map_answer("tỷ lệ 7.2% và 98.70", []) == "tỷ lệ 7.2% và 98.70"


def test_task_files_cover_suites() -> None:
    banking = yaml.safe_load((DATA / "banking/user_tasks.yaml").read_text(encoding="utf-8"))
    slack = yaml.safe_load((DATA / "slack/user_tasks.yaml").read_text(encoding="utf-8"))
    assert sorted(banking) == sorted(f"user_task_{i}" for i in range(16))
    assert sorted(slack) == sorted(f"user_task_{i}" for i in range(21))
    goals = yaml.safe_load((DATA / "injection_tasks.yaml").read_text(encoding="utf-8"))
    assert len(goals["banking"]) == 9 and len(goals["slack"]) == 5


def test_literals_kept_in_prompts() -> None:
    banking = yaml.safe_load((DATA / "banking/user_tasks.yaml").read_text(encoding="utf-8"))
    for task, literal in [("user_task_0", "bill-december-2023.txt"),
                          ("user_task_3", "GB29NWBK60161331926819"),
                          ("user_task_14", "1j1l-2k3j"), ("user_task_15", "1234 Elm Street"),
                          ("user_task_15", "CA133012400231215421872")]:
        assert literal in banking[task]
