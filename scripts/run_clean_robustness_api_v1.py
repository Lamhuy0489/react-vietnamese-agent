#!/usr/bin/env python3
"""Run RQ3 clean robustness variants with A0 (rebuild prompt v3) against a vLLM endpoint.

``--split test`` runs the 250 sealed ``robustness_v1`` variants (50 Test canonicals x 5
types) once, after ``final_config_v2``; the freeze check runs first. ``--split dev`` builds
mechanical variants of the first ``--limit`` public Dev tasks for pipeline checks only.
Each variant is the canonical public task with its instruction replaced (task_id and fault
plan stay canonical), checkpointed under ``tasks/<variant_id>/``. Endpoint from
VLLM_BASE_URL / VLLM_API_KEY; ``--dry-run-dummy`` uses the CPU stand-in agent and is never
a result. Private ground truth is never read here.
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

import react_agent.evaluation.final_config_v2 as final_config_v2
from react_agent.agent import AgentRuntime
from react_agent.agent.checkpoint import atomic_json
from react_agent.authoring.robustness_v1 import SEAL, load_sealed
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.evaluation.adversarial_v1 import DryRunAgent
from react_agent.evaluation.clean_robustness_v1 import dev_smoke_variants, variant_tasks
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
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, default=10,
                        help="dev smoke: first N public Dev tasks x 3 mechanical types")
    parser.add_argument("--timeout", type=float, default=150)
    parser.add_argument("--dry-run-dummy", action="store_true",
                        help="CPU stand-in agent; pipeline check only")
    args = parser.parse_args()
    held_out = args.split == "test"
    if held_out:
        final_config_v2.verify(ROOT)  # raises when anything changed after the freeze
    if args.dry_run_dummy and not args.output:
        raise SystemExit("--dry-run-dummy needs an explicit --output outside results/")
    prompt_profile = a0_rebuild.activate("v3")
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
    public = [CleanPublicTask.model_validate_json(line)
              for line in public_path.read_text(encoding="utf-8").splitlines()]
    if any(t.split != args.split for t in public):
        raise ValueError(f"worker input must be the public {args.split} split")
    variants = load_sealed(ROOT) if held_out else dev_smoke_variants(public, args.limit)
    pairs = variant_tasks({t.task_id: t for t in public}, variants)
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
    default = ROOT / "results/rebuild_a" / f"clean_robustness_{args.split}_{args.model_key}"
    output = (args.output or default).resolve()
    files = {args.split: public_path, "faults": faults_path, "agent": agent_path,
             "generation": generation_path,
             "environment_manifest": CLEAN_ROOT / "manifests/environment_manifest.json"}
    if held_out:
        files["robustness_seal"] = ROOT / SEAL
    identity: dict[str, Any] = {
        "benchmark": "clean_robustness_v1", "split": args.split, "config_id": "A0",
        "model_key": args.model_key, "model_id": spec["repo"], "model_revision": spec["revision"],
        "generation": generation_config.model_dump(),
        "file_sha256": {name: sha256(path) for name, path in files.items()},
        "prompt": prompt_profile, "decoding_schema": "per_tool_v2_name_first",
        "variants": [{"variant_id": v["variant_id"], "canonical_task_id": v["canonical_task_id"],
                      "variant_type": v["variant_type"],
                      "instruction_sha256": hashlib.sha256(v["instruction"].encode()).hexdigest()}
                     for v in variants],
    }
    if held_out:
        identity["final_config_sha256"] = final_config_v2.manifest_sha256(ROOT)
    if args.dry_run_dummy:
        identity["dry_run_dummy"] = True
    output.mkdir(parents=True, exist_ok=True)
    identity_path = output / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise SystemExit("Output directory belongs to other inputs; choose a fresh --output")
    atomic_json(identity_path, identity)

    consecutive_infra = 0
    for variant, task in pairs:
        task_root = output / "tasks" / variant["variant_id"]
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
                stream.write(json.dumps({"variant_id": variant["variant_id"], **call}) + "\n")
        if result.status == "model_error" and backend.infra_failures > infra_before:
            shutil.rmtree(task_root)
            consecutive_infra += 1
            print(f"{variant['variant_id']}: infrastructure error, will rerun", flush=True)
            if consecutive_infra >= MAX_CONSECUTIVE_INFRA:
                print("Endpoint looks down; stopping. Rerun the same command to resume.")
                return 2
            continue
        consecutive_infra = 0
        events = [TraceEvent.model_validate_json(line) for line in trace.read_text().splitlines()]
        if not events or events[0].event != "run_start" or events[-1].event != "run_end":
            raise ValueError("variant did not produce a complete trace")
        atomic_json(task_root / "result.json", {"result": result.model_dump(mode="json"),
                                                "trace_sha256": sha256(trace)})
        print(f"{variant['variant_id']}: {result.status}", flush=True)

    done = [json.loads(p.read_text())["result"] for v in variants
            if (p := output / "tasks" / v["variant_id"] / "result.json").exists()]
    summary = {"variants": len(variants), "finished": len(done),
               "statuses": dict(Counter(item["status"] for item in done)),
               "private_ground_truth_loaded": 0,
               "test_variants_loaded": len(variants) if held_out else 0}
    atomic_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if len(done) == len(variants) else 1


if __name__ == "__main__":
    raise SystemExit(main())
