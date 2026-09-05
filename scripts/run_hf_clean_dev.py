#!/usr/bin/env python3
"""Run a frozen public-Dev-only Phase 2 pilot with a local Hugging Face model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from run_hf_smoke import file_sha256, load_backend

from react_agent.agent import AgentRuntime
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.schemas.clean_task import CleanPublicTask, FaultSpec
from react_agent.tools.factory import build_clean_registry

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--model-id", default="qwen-lm/qwen2.5")
    parser.add_argument("--model-revision", default="transformers/3b-instruct/1")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _git_commit() -> str:
    frozen = os.environ.get("FROZEN_GIT_COMMIT")
    if frozen:
        return frozen
    git = shutil.which("git")
    if git is None:
        return "unavailable"
    result = subprocess.run(  # noqa: S603 - fixed executable and arguments
        [git, "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _public_dev_hash() -> str:
    return hashlib.sha256((CLEAN_ROOT / "splits" / "dev.jsonl").read_bytes()).hexdigest()


def load_selected_dev_tasks() -> list[CleanPublicTask]:
    all_tasks = {
        task.task_id: task
        for task in (
            CleanPublicTask.model_validate_json(line)
            for line in (CLEAN_ROOT / "splits" / "dev.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line
        )
    }
    selection = json.loads((CLEAN_ROOT / "dev_pilot" / "task_ids.json").read_text(encoding="utf-8"))
    selected = [all_tasks[task_id] for task_id in selection["task_ids"]]
    if len(selected) != 21 or Counter(task.category for task in selected) != Counter(
        {
            "single_source": 3,
            "parameter_extraction": 3,
            "multi_step": 3,
            "db_document": 3,
            "ambiguous": 3,
            "error_recovery": 3,
            "no_tool": 3,
        }
    ):
        raise RuntimeError("Dev pilot selection must contain exactly three tasks per category")
    return selected


def load_fault_plans() -> dict[str, list[FaultSpec]]:
    raw = json.loads((CLEAN_ROOT / "dev_pilot" / "fault_plans.json").read_text(encoding="utf-8"))
    return {
        task_id: [FaultSpec.model_validate(item) for item in fault_plan]
        for task_id, fault_plan in raw.items()
    }


def main() -> int:
    args = parse_args()
    tasks = load_selected_dev_tasks()
    fault_plans = load_fault_plans()
    backend = load_backend(args.model_path, args.model_id, args.model_revision)
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    combined_trace = output_dir / "traces.jsonl"
    combined_trace.write_text("", encoding="utf-8")
    runtime_config_path = ROOT / "configs" / "agent" / "A0.yaml"
    generation_config_path = ROOT / "configs" / "runtime" / "default.yaml"
    runtime_config = load_runtime_config(runtime_config_path)
    generation_config = load_generation_config(generation_config_path)
    results: list[dict[str, Any]] = []
    event_counts: Counter[str] = Counter()

    with tempfile.TemporaryDirectory(prefix="react-clean-dev-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        for task in tasks:
            runtime = AgentRuntime(
                backend,
                build_clean_registry(
                    CLEAN_ROOT / "environment", fault_plan=fault_plans.get(task.task_id, [])
                ),
                runtime_config=runtime_config,
                generation_config=generation_config,
            )
            task_trace = temporary_root / f"{task.task_id}.jsonl"
            result = runtime.run(task, trace_path=task_trace)
            with combined_trace.open("a", encoding="utf-8") as stream:
                for line in task_trace.read_text(encoding="utf-8").splitlines():
                    stream.write(line + "\n")
                    event_counts[json.loads(line)["event"]] += 1
            results.append(result.model_dump(mode="json"))
            print(
                f"{task.task_id}: status={result.status} tools={result.tool_sequence}", flush=True
            )

    terminal_statuses = {"completed", "parse_failure", "max_steps", "model_error"}
    summary = {
        "total_tasks": len(tasks),
        "terminal_runs": sum(item["status"] in terminal_statuses for item in results),
        "completed_runs": sum(item["status"] == "completed" for item in results),
        "model_crashes": sum(item["status"] == "model_error" for item in results),
        "parse_failures": sum(item["status"] == "parse_failure" for item in results),
        "max_steps": sum(item["status"] == "max_steps" for item in results),
        "schema_validity_rate": (
            (event_counts["model_output"] - event_counts["parse_error"])
            / event_counts["model_output"]
            if event_counts["model_output"]
            else None
        ),
        "tools_covered": sorted({tool for item in results for tool in item["tool_sequence"]}),
        "test_tasks_loaded": 0,
        "private_ground_truth_loaded": 0,
    }
    metadata = {
        "suite_id": datetime.now(UTC).strftime("phase2_dev_hf_%Y%m%dT%H%M%SZ"),
        "git_commit": _git_commit(),
        "config_id": runtime_config.config_id,
        "config_hashes": {
            "agent": file_sha256(runtime_config_path),
            "generation": file_sha256(generation_config_path),
        },
        "model_id": backend.model_id,
        "model_revision": backend.model_revision,
        "model_path": str(args.model_path),
        "temperature": generation_config.temperature,
        "max_new_tokens": generation_config.max_new_tokens,
        "seed": generation_config.seed,
        "task_set": "clean_v1.0_dev_pilot_21",
        "selected_task_ids": [task.task_id for task in tasks],
        "public_dev_sha256": _public_dev_hash(),
        "started_at": datetime.now(UTC).isoformat(),
        "runtime_version": "0.1.0",
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return int(summary["terminal_runs"] != len(tasks) or summary["model_crashes"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
