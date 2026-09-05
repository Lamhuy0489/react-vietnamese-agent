#!/usr/bin/env python3
"""Public-only worker with per-task checkpoints; no private GT imports or reads."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from react_agent.agent import AgentRuntime
from react_agent.agent.checkpoint import atomic_json, run_checkpointed
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.llm import DummyBackend
from react_agent.llm.base import LLMBackend
from react_agent.schemas.clean_task import CleanPublicTask, FaultSpec
from react_agent.schemas.task import RuntimeTask
from react_agent.tools.factory import build_clean_registry

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["dummy", "hf"], default="dummy")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    public_path = CLEAN_ROOT / "splits/dev.jsonl"
    selection_path = CLEAN_ROOT / "dev_pilot/task_ids.json"
    fault_path = CLEAN_ROOT / "dev_pilot/fault_plans.json"
    public = [
        CleanPublicTask.model_validate_json(line) for line in public_path.read_text().splitlines()
    ]
    ids = json.loads(selection_path.read_text())["task_ids"]
    by_id = {task.task_id: task for task in public}
    if len(public) != 150 or len(by_id) != 150 or any(task.split != "dev" for task in public):
        raise ValueError("worker input must be the exact public Dev split")
    if len(ids) != 21 or len(set(ids)) != 21 or not set(ids) <= by_id.keys():
        raise ValueError("invalid 21-task Dev selection")
    tasks = [by_id[task_id] for task_id in ids]
    if set(Counter(task.category for task in tasks).values()) != {3}:
        raise ValueError("selection requires three tasks in each of seven categories")
    faults = json.loads(fault_path.read_text())
    agent_path = ROOT / "configs/agent/A0.yaml"
    generation_path = ROOT / "configs/runtime/default.yaml"
    runtime_config = load_runtime_config(agent_path)
    generation_config = load_generation_config(generation_path)
    backend: LLMBackend
    if args.backend == "hf":
        if args.model_path is None:
            raise ValueError("--model-path required for hf")
        from run_hf_smoke import load_backend

        backend = load_backend(args.model_path, "qwen-lm/qwen2.5", "transformers/3b-instruct/1")
    else:
        backend = DummyBackend()
    identity: dict[str, Any] = {
        "benchmark": "clean_v1.1",
        "evaluator_version": "clean_v1_1_typed_v1",
        "git_commit": os.environ.get("FROZEN_GIT_COMMIT", "local_unfrozen"),
        "backend": args.backend,
        "model_id": backend.model_id,
        "model_revision": backend.model_revision,
        "generation": generation_config.model_dump(),
        "file_sha256": {
            name: sha256(path)
            for name, path in {
                "dev": public_path,
                "selection": selection_path,
                "faults": fault_path,
                "environment_manifest": CLEAN_ROOT / "manifests/environment_manifest.json",
                "agent": agent_path,
                "generation": generation_path,
            }.items()
        },
    }

    def runtime_factory(task: RuntimeTask) -> AgentRuntime:
        return AgentRuntime(
            backend,
            build_clean_registry(
                CLEAN_ROOT / "environment",
                fault_plan=[
                    FaultSpec.model_validate(spec) for spec in faults.get(task.task_id, [])
                ],
            ),
            runtime_config=runtime_config,
            generation_config=generation_config,
        )

    started = datetime.now(UTC).isoformat()
    results = run_checkpointed(
        list(tasks), runtime_factory, args.output, identity, resume=args.resume
    )
    summary = {
        "tasks": len(results),
        "terminal_runs": len(results),
        "statuses": dict(Counter(result.status for result in results)),
        "model_errors": sum(result.status == "model_error" for result in results),
        "test_tasks_loaded": 0,
        "private_ground_truth_loaded": 0,
        "invocation_started_at": started,
        "invocation_finished_at": datetime.now(UTC).isoformat(),
    }
    atomic_json(args.output / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return int(summary["model_errors"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
