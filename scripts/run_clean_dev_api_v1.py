#!/usr/bin/env python3
"""Run the 150 public clean v1.1 Dev tasks with A0 (rebuild prompt) against a vLLM endpoint.

Endpoint URL and key come from VLLM_BASE_URL / VLLM_API_KEY. Output follows the
``run_checkpointed`` layout (``tasks/<id>/result.json`` + ``trace.jsonl``) so
``evaluate_clean_rebuild_v1.py --full-dev`` can score it. A task that ends with an
infrastructure error is not checkpointed and reruns on the next invocation;
model errors are kept. Private ground truth is never read.

``--split test`` runs the 100 held-out Test tasks once, after the R3 freeze (the
frozen-file check runs first); ``--dry-run-dummy`` uses a CPU stand-in agent to
check the pipeline (R3) and is never a result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

import react_agent.evaluation.final_config_v1 as final_config_v1
from react_agent.agent import AgentRuntime
from react_agent.agent.checkpoint import atomic_json
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.evaluation.adversarial_v1 import DryRunAgent
from react_agent.llm.openai_compat_v1 import OpenAICompatBackend, OrderedHTTPSJSON
from react_agent.prompts import a0_rebuild
from react_agent.schemas.clean_task import CleanPublicTask, FaultSpec
from react_agent.schemas.trace import TraceEvent
from react_agent.tools.factory import build_clean_registry

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"
MAX_CONSECUTIVE_INFRA = 3


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, help="run only the first N Dev tasks")
    parser.add_argument("--timeout", type=float, default=150)
    parser.add_argument("--prompt", choices=["v2", "v3"], default="v3")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--dry-run-dummy", action="store_true",
                        help="CPU stand-in agent; pipeline check only")
    args = parser.parse_args()
    held_out = args.split == "test"
    if held_out:
        final_config_v1.verify(ROOT)  # raises when anything changed after R3
        if args.prompt != "v3" or (args.limit and not args.dry_run_dummy):
            raise SystemExit("Test runs use the frozen configuration only")
    if args.dry_run_dummy and not args.output:
        raise SystemExit("--dry-run-dummy needs an explicit --output outside results/")
    prompt_profile = a0_rebuild.activate(args.prompt)
    spec = yaml.safe_load((ROOT / "configs/models/backbones_v2.yaml").read_text())[args.model_key]
    if not spec["revision"]:
        raise SystemExit("Pin the revision in configs/models/backbones_v2.yaml first")
    base_url, api_key = os.environ.get("VLLM_BASE_URL"), os.environ.get("VLLM_API_KEY")
    if args.dry_run_dummy:
        base_url = api_key = "dry-run"
    if not base_url or not api_key:
        raise SystemExit("Set VLLM_BASE_URL (https://.../v1) and VLLM_API_KEY")

    public_path = CLEAN_ROOT / f"splits/{args.split}.jsonl"
    faults_path = ROOT / f"configs/clean/{args.split}_fault_plans_v1.json"
    tasks = [CleanPublicTask.model_validate_json(line)
             for line in public_path.read_text(encoding="utf-8").splitlines()]
    if len(tasks) != (100 if held_out else 150) or any(t.split != args.split for t in tasks):
        raise ValueError(f"worker input must be the exact public {args.split} split")
    tasks = tasks[: args.limit] if args.limit else tasks
    faults = json.loads(faults_path.read_text())["fault_plans"]
    agent_path = ROOT / "configs/agent/A0.yaml"
    generation_path = ROOT / "configs/runtime/default.yaml"
    runtime_config = load_runtime_config(agent_path)
    generation_config = load_generation_config(generation_path)

    backend: Any
    if args.dry_run_dummy:
        backend = DryRunAgent(spec["repo"], spec["revision"])
    else:
        backend = OpenAICompatBackend(
            OrderedHTTPSJSON(base_url, api_key, timeout=args.timeout),
            repo=spec["repo"], revision=spec["revision"],
            chat_template_kwargs=spec.get("chat_template_kwargs"),
            tool_definitions=build_clean_registry(CLEAN_ROOT / "environment").definitions())
    backend.probe()
    default = ROOT / "results/rebuild_a" / f"clean_{args.split}_{args.model_key}"
    output = (args.output or default).resolve()
    identity: dict[str, Any] = {
        "benchmark": "clean_v1.1", "split": args.split, "config_id": "A0",
        "model_key": args.model_key, "model_id": spec["repo"], "model_revision": spec["revision"],
        "generation": generation_config.model_dump(),
        "file_sha256": {name: sha256(path) for name, path in {
            args.split: public_path, "faults": faults_path, "agent": agent_path,
            "generation": generation_path,
            "environment_manifest": CLEAN_ROOT / "manifests/environment_manifest.json",
        }.items()},
        "prompt": prompt_profile,
        "decoding_schema": "per_tool_v2_name_first",
        "task_ids": [task.task_id for task in tasks],
    }
    if held_out:
        identity["final_config_sha256"] = final_config_v1.manifest_sha256(ROOT)
    if args.dry_run_dummy:
        identity["dry_run_dummy"] = True
    output.mkdir(parents=True, exist_ok=True)
    identity_path = output / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise SystemExit("Output directory belongs to other inputs; choose a fresh --output")
    atomic_json(identity_path, identity)

    consecutive_infra = 0
    for task in tasks:
        task_root = output / "tasks" / task.task_id
        if (task_root / "result.json").exists():
            continue
        shutil.rmtree(task_root, ignore_errors=True)  # leftover of an infrastructure failure
        task_root.mkdir(parents=True)
        first_call, infra_before = len(backend.calls), backend.infra_failures
        registry = build_clean_registry(
            CLEAN_ROOT / "environment",
            fault_plan=[FaultSpec.model_validate(item) for item in faults.get(task.task_id, [])],
        )
        runtime = AgentRuntime(backend, registry, runtime_config=runtime_config,
                               generation_config=generation_config)
        trace = task_root / "trace.jsonl"
        result = runtime.run(task, trace_path=trace)
        with (output / "calls.jsonl").open("a", encoding="utf-8") as stream:
            for call in backend.calls[first_call:]:
                stream.write(json.dumps({"task_id": task.task_id, **call}) + "\n")
        if result.status == "model_error" and backend.infra_failures > infra_before:
            shutil.rmtree(task_root)
            consecutive_infra += 1
            print(f"{task.task_id}: infrastructure error, will rerun", flush=True)
            if consecutive_infra >= MAX_CONSECUTIVE_INFRA:
                print("Endpoint looks down; stopping. Rerun the same command to resume.")
                return 2
            continue
        consecutive_infra = 0
        events = [TraceEvent.model_validate_json(line) for line in trace.read_text().splitlines()]
        if not events or events[0].event != "run_start" or events[-1].event != "run_end":
            raise ValueError("task did not produce a complete trace")
        atomic_json(task_root / "result.json", {"result": result.model_dump(mode="json"),
                                                "trace_sha256": sha256(trace)})
        print(f"{task.task_id}: {result.status}", flush=True)

    done = [json.loads((output / "tasks" / task.task_id / "result.json").read_text())["result"]
            for task in tasks if (output / "tasks" / task.task_id / "result.json").exists()]
    summary = {"tasks": len(tasks), "finished": len(done),
               "statuses": dict(Counter(item["status"] for item in done)),
               "private_ground_truth_loaded": 0, "test_tasks_loaded": len(tasks) if held_out else 0}
    atomic_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if len(done) == len(tasks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
