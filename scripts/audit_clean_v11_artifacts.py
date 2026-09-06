#!/usr/bin/env python3
"""Audit the selected v1.1 pilot artifacts and export a compact frozen receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from react_agent.llm.pilot_profiles import PROFILES
from react_agent.schemas.trace import TraceEvent

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--expected",
        type=Path,
        default=ROOT / "experiments/manifests/phase2_clean_v11_kaggle_v1.json",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("preserve existing audit receipt")
    run = args.artifacts / "phase2_clean_dev_pilot"
    expected = json.loads(args.expected.read_text())
    profile_key = expected.get("model_profile", "qwen")
    profile = PROFILES[profile_key]
    identity = json.loads((run / "identity.json").read_text())
    bundle_info = json.loads((args.artifacts / "kaggle_bundle_info.json").read_text())
    summary = json.loads((run / "summary.json").read_text())
    evaluation = json.loads(args.evaluation.read_text())
    selection = json.loads((ROOT / "data/clean/v1_1/dev_pilot/task_ids.json").read_text())[
        "task_ids"
    ]
    failures: list[str] = []
    if (
        identity["git_commit"] != expected["source_commit"]
        or bundle_info["git_commit"] != expected["source_commit"]
    ):
        failures.append("source commit mismatch")
    if (
        bundle_info["archive_sha256"] != expected["archive_sha256"]
        or bundle_info["dataset_version"] != 1
    ):
        failures.append("worker bundle mismatch")
    if identity["task_ids"] != selection or evaluation["source_identity"] != identity:
        failures.append("task/evaluation identity mismatch")
    if (
        identity["backend"] != "hf"
        or identity["model_id"] != profile.model_id
        or identity["model_revision"] != profile.revision
        or bundle_info["model_source"] != profile.source
        or identity.get("chat_adapter", "native") != profile.chat_adapter
    ):
        failures.append("model identity mismatch")
    paths = {
        "agent": ROOT / "configs/agent/A0.yaml",
        "generation": ROOT / "configs/runtime/default.yaml",
        "dev": ROOT / "data/clean/v1_1/splits/dev.jsonl",
        "selection": ROOT / "data/clean/v1_1/dev_pilot/task_ids.json",
        "faults": ROOT / "data/clean/v1_1/dev_pilot/fault_plans.json",
        "environment_manifest": ROOT / "data/clean/v1_1/manifests/environment_manifest.json",
    }
    if identity["file_sha256"] != {name: sha(path) for name, path in paths.items()}:
        failures.append("run input hash mismatch")
    directories = {path.name for path in (run / "tasks").iterdir() if path.is_dir()}
    if directories != set(selection):
        failures.append("missing/extra task checkpoints")
    events: list[TraceEvent] = []
    statuses: Counter[str] = Counter()
    run_ids: set[str] = set()
    task_seconds: list[float] = []
    for task_id in selection:
        task_root = run / "tasks" / task_id
        checkpoint = json.loads((task_root / "result.json").read_text())
        trace_path = task_root / "trace.jsonl"
        if checkpoint["trace_sha256"] != sha(trace_path):
            failures.append(f"trace hash mismatch: {task_id}")
        trace = [
            TraceEvent.model_validate_json(line) for line in trace_path.read_text().splitlines()
        ]
        if not trace or trace[0].event != "run_start" or trace[-1].event != "run_end":
            failures.append(f"terminal boundary: {task_id}")
            continue
        run_ids.add(trace[0].run_id)
        task_seconds.append((trace[-1].timestamp - trace[0].timestamp).total_seconds())
        statuses[trace[-1].data["status"]] += 1
        calls: dict[str, list[str]] = defaultdict(list)
        for event in trace:
            if event.task_id != task_id or event.run_id != checkpoint["result"]["run_id"]:
                failures.append(f"trace identity mismatch: {task_id}")
            if event.call_id:
                calls[event.call_id].append(event.event)
        if any(
            names != ["tool_call_proposed", "tool_call_executed", "tool_result"]
            for names in calls.values()
        ):
            failures.append(f"tool event ordering: {task_id}")
        events.extend(trace)
    if len(run_ids) != 21 or dict(statuses) != summary["statuses"] or summary["model_errors"] != 0:
        failures.append("run counts/summary mismatch")
    files = [path for path in args.artifacts.rglob("*") if path.is_file()]
    secrets = [
        str(json.loads(path.read_text()).get("key", "")).encode()
        for path in (ROOT / "credential kaggle").glob("*.json")
    ]
    secret_matches = sum(
        bool(secret) and secret in path.read_bytes() for secret in secrets for path in files
    )
    if secret_matches:
        failures.append("credential secret found in artifacts")
    outputs = sum(event.event == "model_output" for event in events)
    parse_errors = sum(event.event == "parse_error" for event in events)
    report = {
        "valid": not failures,
        "failures": failures,
        "kernel_version": 1,
        "source_commit": expected["source_commit"],
        "model_profile": profile_key,
        "model_source": profile.source,
        "chat_adapter": profile.chat_adapter,
        "dataset_hash": expected["dataset_hash"],
        "tasks": len(selection),
        "terminal_runs": len(run_ids),
        "statuses": dict(statuses),
        "trace_events": len(events),
        "schema_validity_rate": (outputs - parse_errors) / outputs,
        "model_outputs": outputs,
        "parse_errors": parse_errors,
        "task_seconds_total": sum(task_seconds),
        "task_seconds_mean": sum(task_seconds) / len(task_seconds),
        "dev_diagnostic_successes": evaluation["successes"],
        "evaluation_scope": evaluation["scope"],
        "credential_secret_matches": secret_matches,
        "secret_values_checked": len(secrets),
        "raw_artifact_sha256": {
            path.relative_to(args.artifacts).as_posix(): sha(path) for path in sorted(files)
        },
        "evaluation_sha256": sha(args.evaluation),
        "evaluation_path": str(args.evaluation),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "raw_artifact_sha256"}, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
