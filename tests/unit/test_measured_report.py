"""Reject unpaired or tampered performance metrics rather than reporting spurious speed."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def report_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "measured_report", ROOT / "scripts/report_measured_pilot.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(root: Path) -> tuple[Path, Path, Path]:
    ids = json.loads((ROOT / "data/clean/v1_1/dev_pilot/task_ids.json").read_text())["task_ids"]
    run = root / "phase2_clean_dev_pilot"
    run.mkdir()
    identity = {
        "measurement_protocol": "dev21_performance_v1",
        "task_ids": ids,
        "model_profile": "fixture",
    }
    (run / "identity.json").write_text(json.dumps(identity))
    (run / "model_setup.json").write_text("{}")
    measurements = []
    scores = []
    for i, task in enumerate(ids):
        directory = run / "tasks" / task
        directory.mkdir(parents=True)
        trace = [
            {
                "event": name,
                "timestamp": f"2026-09-06T00:00:{second:02d}+00:00",
                "task_id": task,
                "run_id": f"run_{i}",
                "step": 0,
                "data": {},
            }
            for name, second in (("run_start", 0), ("model_output", 1), ("run_end", 2))
        ]
        path = directory / "trace.jsonl"
        path.write_text("".join(json.dumps(e) + "\n" for e in trace))
        (directory / "result.json").write_text(
            json.dumps(
                {
                    "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        )
        measurements.append(
            {
                "task_id": task,
                "call_index": 1,
                "input_tokens": 20,
                "output_tokens": 10,
                "generate_seconds": 1.0,
                "call_seconds": 1.5,
                "peak_allocated_bytes": [100, 200],
            }
        )
        scores.append({"task_id": task, "success": True, "status": "completed", "failures": []})
    (run / "inference_metrics.jsonl").write_text(
        "".join(json.dumps(m) + "\n" for m in measurements)
    )
    evaluation = root / "evaluation.json"
    evaluation.write_text(
        json.dumps(
            {"source_identity": identity, "test_tasks_read": 0, "results": scores, "failures": {}}
        )
    )
    audit = root / "audit.json"
    audit.write_text(
        json.dumps(
            {
                "valid": True,
                "evaluation_sha256": hashlib.sha256(evaluation.read_bytes()).hexdigest(),
                "raw_artifact_sha256": {
                    path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in run.rglob("*")
                    if path.is_file()
                },
            }
        )
    )
    return run, evaluation, audit


def test_report_uses_ratio_of_totals_and_all_tasks(tmp_path: Path) -> None:
    report = report_module().condition(*fixture(tmp_path))
    assert report["successes"] == 21
    assert report["output_tokens"] == 210
    assert report["output_tokens_per_generate_second_including_prefill"] == 10
    assert report["latency_all_tasks_seconds"]["mean"] == 2
    assert report["success_ci95_cluster_bootstrap"] == (1, 1)


def test_report_rejects_post_audit_metric_changes(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    metrics = args[0] / "inference_metrics.jsonl"
    metrics.write_text(metrics.read_text().replace('"output_tokens": 10', '"output_tokens": 500'))
    with pytest.raises(ValueError, match="differs from audit"):
        report_module().condition(*args)
