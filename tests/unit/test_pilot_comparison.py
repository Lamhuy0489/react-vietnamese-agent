"""Negative controls for comparisons with missing or incompatible model runs."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


def comparison_module() -> ModuleType:
    script = Path(__file__).resolve().parents[2] / "scripts/compare_clean_v11_pilots.py"
    spec = importlib.util.spec_from_file_location("pilot_comparison", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pair(root: Path, name: str, *, generation: int = 512) -> tuple[Path, Path]:
    ids = [f"task_{i}" for i in range(21)]
    evaluation = {
        "source_identity": {
            "model_id": "qwen-lm/qwen2.5" if name == "qwen" else "metaresearch/llama-3.2",
            "model_revision": "transformers/3b-instruct/1",
            "task_ids": ids,
            "file_sha256": {"dev": "frozen"},
            "generation": {"max_new_tokens": generation},
            "git_commit": "fixture",
        },
        "evaluator": "frozen",
        "test_tasks_read": 0,
        "evaluated_tasks": 21,
        "results": [{"task_id": task_id} for task_id in ids],
        "successes": 5,
        "failures": {"answer_facts": 16},
    }
    path = root / f"{name}.json"
    path.write_text(json.dumps(evaluation))
    audit = root / f"{name}-audit.json"
    audit.write_text(
        json.dumps(
            {
                "valid": True,
                "evaluation_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "schema_validity_rate": 0.8,
                "statuses": {"completed": 21},
            }
        )
    )
    return path, audit


def test_missing_models_are_not_zero_scores(tmp_path: Path) -> None:
    module = comparison_module()
    result = module.comparison([pair(tmp_path, "qwen")])
    assert result["complete"] is False
    assert result["conditions"]["llama"]["status"] == "not_run"
    assert "successes" not in result["conditions"]["gemma"]


def test_comparison_rejects_generation_change_and_tampered_result(tmp_path: Path) -> None:
    module = comparison_module()
    qwen = pair(tmp_path, "qwen")
    llama = pair(tmp_path, "llama", generation=1024)
    with pytest.raises(ValueError, match="incompatible"):
        module.comparison([qwen, llama])
    qwen[0].write_text(qwen[0].read_text() + " ")
    with pytest.raises(ValueError, match="audit"):
        module.comparison([qwen])
