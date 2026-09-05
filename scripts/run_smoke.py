#!/usr/bin/env python3
"""Run all Phase 1 smoke tasks with a CPU-only dummy or replay backend."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from react_agent.agent import AgentRuntime
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.llm import DummyBackend, ReplayBackend
from react_agent.schemas.task import SmokeTask
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "smoke"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("dummy", "replay"), default="replay")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def load_tasks() -> list[SmokeTask]:
    return [
        SmokeTask.model_validate_json(line)
        for line in (DATA_ROOT / "tasks.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def data_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(DATA_ROOT.rglob("*")):
        if path.is_file() and path.name != "university.db":
            digest.update(path.relative_to(DATA_ROOT).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def git_commit() -> str:
    git = shutil.which("git")
    if git is None:
        return "unavailable"
    result = subprocess.run(  # noqa: S603 - fixed executable and arguments
        [git, "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def task_succeeded(task: SmokeTask, status: str, sequence: list[str], answer: str) -> bool:
    valid_sequence = sequence in task.expected.acceptable_tool_sequences
    facts_present = all(
        fact.casefold() in answer.casefold() for fact in task.expected.required_answer_facts
    )
    return status == "completed" and valid_sequence and facts_present


def main() -> int:
    args = parse_args()
    tasks = load_tasks()
    replays: dict[str, list[str]] = json.loads(
        (DATA_ROOT / "replay_responses.json").read_text(encoding="utf-8")
    )
    if not (DATA_ROOT / "database" / "university.db").is_file():
        raise SystemExit("Run scripts/build_smoke_environment.py first.")

    suite_id = datetime.now(UTC).strftime("phase1_%Y%m%dT%H%M%SZ")
    output_dir = (args.output or ROOT / "results" / "phase1" / suite_id).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    combined_trace = output_dir / "traces.jsonl"
    combined_trace.write_text("", encoding="utf-8")
    runtime_config = load_runtime_config(ROOT / "configs" / "agent" / "A0.yaml")
    generation_config = load_generation_config(ROOT / "configs" / "runtime" / "default.yaml")
    results: list[dict[str, Any]] = []
    total_model_outputs = 0
    total_parse_errors = 0

    with tempfile.TemporaryDirectory(prefix="react-smoke-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        for task in tasks:
            backend = (
                DummyBackend() if args.backend == "dummy" else ReplayBackend(replays[task.task_id])
            )
            runtime = AgentRuntime(
                backend,
                build_smoke_registry(DATA_ROOT),
                runtime_config=runtime_config,
                generation_config=generation_config,
            )
            task_trace = temporary_root / f"{task.task_id}.jsonl"
            result = runtime.run(task, trace_path=task_trace)
            trace_lines = task_trace.read_text(encoding="utf-8").splitlines()
            with combined_trace.open("a", encoding="utf-8") as stream:
                for line in trace_lines:
                    stream.write(line + "\n")
                    event = json.loads(line)
                    total_model_outputs += event["event"] == "model_output"
                    total_parse_errors += event["event"] == "parse_error"
            answer = result.final_answer or ""
            success = task_succeeded(task, result.status, result.tool_sequence, answer)
            results.append({**result.model_dump(), "success": success})

    failures = [result for result in results if not result["success"]]
    covered = sorted({tool for result in results for tool in result["tool_sequence"]})
    summary = {
        "total_tasks": len(tasks),
        "completed_runs": sum(result["status"] == "completed" for result in results),
        "crashed_runs": sum(result["status"] == "model_error" for result in results),
        "task_successes": sum(bool(result["success"]) for result in results),
        "schema_validity_rate": (
            (total_model_outputs - total_parse_errors) / total_model_outputs
            if total_model_outputs
            else None
        ),
        "tools_covered": covered,
        "backend": args.backend,
    }
    metadata = {
        "suite_id": suite_id,
        "git_commit": git_commit(),
        "config_id": runtime_config.config_id,
        "model_id": args.backend,
        "model_revision": "phase1_v1",
        "temperature": generation_config.temperature,
        "seed": generation_config.seed,
        "task_set": "smoke_v1",
        "data_hash": data_hash(),
        "started_at": datetime.now(UTC).isoformat(),
        "runtime_version": "0.1.0",
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "failures.json").write_text(
        json.dumps(failures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Artifacts: {output_dir}")
    if args.backend == "dummy":
        return 0 if summary["completed_runs"] == len(tasks) and not summary["crashed_runs"] else 1
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
