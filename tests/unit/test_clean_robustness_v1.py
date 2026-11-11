from __future__ import annotations

import json
from pathlib import Path

import pytest

from react_agent.authoring.robustness_v1 import load_sealed
from react_agent.evaluation import final_config_v2
from react_agent.evaluation.clean_robustness_v1 import dev_smoke_variants, summarize, variant_tasks
from react_agent.schemas.clean_task import CleanPublicTask

ROOT = Path(__file__).resolve().parents[2]


def _public(split: str) -> list[CleanPublicTask]:
    path = ROOT / f"data/clean/v1_1/splits/{split}.jsonl"
    return [CleanPublicTask.model_validate_json(line) for line in path.read_text().splitlines()]


def test_variant_keeps_canonical_task_and_replaces_only_instruction() -> None:
    public = _public("test")
    pairs = variant_tasks({t.task_id: t for t in public}, load_sealed(ROOT))
    assert len(pairs) == 250
    by_id = {t.task_id: t for t in public}
    for variant, task in pairs:
        canonical = by_id[variant["canonical_task_id"]]
        assert task.task_id == canonical.task_id and task.instruction == variant["instruction"]
        assert task.model_dump(exclude={"instruction"}) == canonical.model_dump(
            exclude={"instruction"})


def test_dev_smoke_builds_three_mechanical_variants_per_dev_task() -> None:
    rows = dev_smoke_variants(_public("dev"), 5)
    assert len(rows) == 15 and {r["split"] for r in rows} == {"dev"}
    assert all(r["instruction"] for r in rows)


def test_variant_split_must_match_canonical() -> None:
    dev = _public("dev")
    row = dev_smoke_variants(dev, 1)[0] | {"split": "test"}
    with pytest.raises(ValueError, match="split"):
        variant_tasks({t.task_id: t for t in dev}, [row])


def test_summarize_counts_paired_flips() -> None:
    rows = [{"variant_type": "paraphrase", "canonical_task_id": "a", "success": False,
             "status": "completed"},
            {"variant_type": "paraphrase", "canonical_task_id": "b", "success": True,
             "status": "completed"},
            {"variant_type": "code_mix", "canonical_task_id": "a", "success": True,
             "status": "model_error"}]
    out = summarize(rows, {"a": True, "b": False})
    assert out["paraphrase"] == {"variants": 2, "successes": 1, "model_error": 0,
                                 "canonical_successes": 1, "lost": 1, "gained": 1}
    assert out["code_mix"]["model_error"] == 1 and out["code_mix"]["lost"] == 0


def test_freeze_v2_detects_changes(tmp_path: Path) -> None:
    for name in (*final_config_v2.FROZEN_FILES, "src/react_agent/x.py", "configs/a.yaml"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(name)
    with pytest.raises(final_config_v2.FrozenConfigError, match="missing"):
        final_config_v2.verify(tmp_path)
    manifest = final_config_v2.build(tmp_path, {"k": 1})
    (tmp_path / final_config_v2.MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / final_config_v2.MANIFEST).write_text(json.dumps(manifest))
    assert final_config_v2.verify(tmp_path)["decisions"] == {"k": 1}
    (tmp_path / "src/react_agent/new.py").write_text("x")
    with pytest.raises(final_config_v2.FrozenConfigError, match="new.py"):
        final_config_v2.verify(tmp_path)
