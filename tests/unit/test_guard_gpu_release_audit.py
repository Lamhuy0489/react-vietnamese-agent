"""Synthetic Dummy checkpoint audit, not model-quality scoring."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


@pytest.fixture
def audit() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts/audit_phase5_guard_gpu_release.py"
    spec = importlib.util.spec_from_file_location("guard_release_qa", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def sample(audit: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict]:
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    clean = "data/clean/v1_1/"
    files = {
        "agent": "configs/agent/A0.yaml",
        "generation": "configs/runtime/default.yaml",
        "dev": clean + "splits/dev.jsonl",
        "selection": clean + "dev_pilot/task_ids.json",
        "faults": clean + "dev_pilot/fault_plans.json",
        "environment_manifest": clean + "manifests/environment_manifest.json",
    }
    ids = [f"synthetic_{i}" for i in range(21)]
    for path in files.values():
        write(tmp_path / path, {})
    write(tmp_path / files["generation"], {"temperature": 0.0, "max_new_tokens": 512, "seed": 42})
    write(tmp_path / files["selection"], {"task_ids": ids})
    hashes = {path: audit.digest(tmp_path / path) for path in files.values()}
    bundle = {"source_commit": "a" * 40, "source_sha256": hashes}
    raw = tmp_path / "raw"
    write(
        raw / "dummy/identity.json",
        {
            "backend": "dummy",
            "benchmark": "clean_v1.1",
            "chat_adapter": "native",
            "evaluator_version": "clean_v1_1_typed_v1",
            "git_commit": "a" * 40,
            "model_id": "dummy",
            "model_revision": "phase1_v1",
            "model_profile": "qwen",
            "measurement_protocol": None,
            "generation": {"temperature": 0.0, "max_new_tokens": 512, "seed": 42},
            "task_ids": ids,
            "file_sha256": {name: hashes[path] for name, path in files.items()},
        },
    )
    results = []
    for task_id in ids:
        task = raw / "dummy/tasks" / task_id
        task.mkdir(parents=True)
        run_id = "run_" + task_id
        events = [
            {
                "run_id": run_id,
                "task_id": task_id,
                "step": 0,
                "event": event,
                "timestamp": "2026-09-08T00:00:00Z",
                "data": {},
            }
            for event in ("run_start", "model_output", "final_answer", "run_end")
        ]
        (task / "trace.jsonl").write_text("\n".join(json.dumps(e) for e in events))
        result = {
            "run_id": run_id,
            "task_id": task_id,
            "status": "completed",
            "steps": 1,
            "final_answer": "synthetic",
            "parse_errors": 0,
            "tool_sequence": [],
        }
        write(
            task / "result.json",
            {"result": result, "trace_sha256": audit.digest(task / "trace.jsonl")},
        )
        results.append(result)
    write(raw / "dummy/results.json", results)
    write(
        raw / "dummy/summary.json",
        {
            "tasks": 21,
            "terminal_runs": 21,
            "statuses": {"completed": 21},
            "model_errors": 0,
            "test_tasks_loaded": 0,
            "private_ground_truth_loaded": 0,
        },
    )
    return raw, bundle


def test_dummy_integrity(audit: ModuleType, sample: tuple[Path, dict]) -> None:
    assert audit.audit_dummy(*sample)["events"] == 84


@pytest.mark.parametrize("change", ["identity", "hash", "order", "aggregate", "missing"])
def test_corruption_rejected(audit: ModuleType, sample: tuple[Path, dict], change: str) -> None:
    raw, _ = sample
    task = raw / "dummy/tasks/synthetic_0"
    if change == "identity":
        path = raw / "dummy/identity.json"
        value = json.loads(path.read_text())
        value["backend"] = "hf"
        write(path, value)
    elif change in {"hash", "order"}:
        trace = task / "trace.jsonl"
        trace.write_text("\n".join(reversed(trace.read_text().splitlines())))
        if change == "order":
            value = json.loads((task / "result.json").read_text())
            value["trace_sha256"] = audit.digest(trace)
            write(task / "result.json", value)
    elif change == "aggregate":
        write(raw / "dummy/results.json", [])
    else:
        task.rename(raw / "saved")
    with pytest.raises(ValueError):
        audit.audit_dummy(*sample)
