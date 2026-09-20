import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "knowledge", ROOT / "scripts/validate_knowledge.py"
    )
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def test_repository_memory_navigation() -> None:
    assert module().validate(ROOT) == []


def test_memory_rejects_missing_sections_and_unsafe_links(tmp_path: Path) -> None:
    memory = tmp_path / "knowledge"
    memory.mkdir()
    (memory / "handoff.md").write_text("[missing](absent.md)\n[escape](../../outside.md)\n")
    failures = module().validate(tmp_path)
    assert "handoff_date" in failures
    assert "handoff_section:Đang làm" in failures
    assert "broken_link:handoff.md:absent.md" in failures
    assert "outside_repository:handoff.md:../../outside.md" in failures


def test_memory_does_not_follow_remote_or_private_links(tmp_path: Path) -> None:
    memory = tmp_path / "knowledge"
    memory.mkdir()
    (memory / "README.md").write_text(
        "[web](https://example.invalid/not-fetched)\n"
        "[gt](../data/clean/private/gt.json)\n"
        "[test](../data/clean/splits/test.jsonl)\n"
        "[credential](../credential%20kaggle/kaggle.json)\n"
    )
    failures = module().validate(tmp_path)
    assert len([f for f in failures if f.startswith("restricted_memory_link:")]) == 3
    assert not any("example.invalid" in f for f in failures)


def test_root_dashboard_links_are_checked(tmp_path: Path) -> None:
    (tmp_path / "START_HERE.md").write_text(
        "[missing](knowledge/absent.md)\n"
        "[escape](../outside.md)\n"
        "[secret](credential%20kaggle/kaggle.json)\n"
        "[web](https://example.invalid/not-fetched)\n"
    )
    failures = module().validate(tmp_path)
    assert "broken_link:START_HERE.md:knowledge/absent.md" in failures
    assert "outside_repository:START_HERE.md:../outside.md" in failures
    assert "restricted_memory_link:START_HERE.md:credential%20kaggle/kaggle.json" in failures
    assert not any("example.invalid" in f for f in failures)


def test_dashboard_uses_root_relative_navigation(tmp_path: Path) -> None:
    memory = tmp_path / "knowledge"
    memory.mkdir()
    (memory / "README.md").write_text("[home](../START_HERE.md)\n")
    (tmp_path / "START_HERE.md").write_text("[index](knowledge/README.md)\n")
    failures = module().validate(tmp_path)
    assert not any("link:" in failure for failure in failures)


def test_memory_checker_does_not_scan_vault_settings(tmp_path: Path) -> None:
    vault = tmp_path / ".obsidian"
    vault.mkdir()
    (vault / "README.md").write_text("[not-project-memory](absent.md)\n")
    assert not any("absent.md" in failure for failure in module().validate(tmp_path))
