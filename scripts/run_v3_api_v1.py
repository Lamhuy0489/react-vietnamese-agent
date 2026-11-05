#!/usr/bin/env python3
"""Run VN-AgentInject v3 fixtures through the agent (Study 2, WP3 pilot onward).

Same pipeline as ``run_adversarial_e2_api_v1.py`` (frozen Phase 5 closure runtime or D2,
rebuild prompt v3, per-tool decoding schema, environment E2 ``doc_search``, checkpoint and
resume, infrastructure reruns). Differences:

- fixtures come from a v3 release (``pilot_v3`` or ``release_v3``) and build their own
  registry and host catalog (``FixtureV3.registry``/``catalog``);
- models resolve from ``backbones_v3.yaml``; Meta-SecAlign uses the ``input`` role backend;
- only public fixture files are read; private oracles stay with ``evaluate_v3_v1.py``.

The Test split is refused until ``final_config_v3`` exists (plan WP9).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, cast

import yaml

from react_agent.agent.checkpoint import atomic_json
from react_agent.authoring.v3 import release as rel
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.evaluation.adversarial_v1 import LEVELS, DryRunAgent
from react_agent.llm.openai_compat_v1 import (
    InfrastructureError,
    OpenAICompatBackend,
    OrderedHTTPSJSON,
)
from react_agent.prompts import a0_rebuild
from react_agent.security_v1 import a6_provenance_v3
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.phase5_closure_runtime_v1 import (
    RUNTIME_VERSION,
    Phase5ClosureRuntime,
)
from react_agent.security_v1.runtime_d2_v1 import RUNTIME_VERSION as D2_RUNTIME_VERSION
from react_agent.security_v1.runtime_d2_v1 import D2Runtime
from react_agent.tools import doc_search_v2
from react_agent.tools.factory import build_clean_registry

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ENV = ROOT / rel.CLEAN
MAX_CONSECUTIVE_INFRA = 3
NO_GUARD_LEVELS = [level for level in LEVELS if not configuration(cast(Level, level)).llm_guard]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_spec(config: Path, key: str) -> dict[str, Any]:
    spec: dict[str, Any] = yaml.safe_load(config.read_text(encoding="utf-8"))[key]
    if spec.get("from") == "backbones_v2":
        spec = model_spec(config.with_name("backbones_v2.yaml"), key)
    return spec


def load_rows(folder: Path, split: str, branches: list[str]) -> list[rel.FixtureV3]:
    rows: list[rel.FixtureV3] = []
    for branch in branches:
        path = folder / f"{split}_{branch}.jsonl"
        if path.exists():
            rows += [rel.FixtureV3.model_validate_json(line)
                     for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise SystemExit(f"no fixtures for {split} in {folder}")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-key", default="qwen3_8b")
    parser.add_argument("--models-config", default="configs/models/backbones_v3.yaml")
    parser.add_argument("--split", choices=["pilot", "dev"], default="pilot")
    parser.add_argument("--branches", nargs="+", default=list(rel.BRANCH_CODE),
                        choices=list(rel.BRANCH_CODE))
    parser.add_argument("--levels", nargs="+", default=["A0"], choices=NO_GUARD_LEVELS)
    parser.add_argument("--defense", choices=["d2"], help="D2 runtime on --levels A1")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=150)
    parser.add_argument("--dry-run-dummy", action="store_true",
                        help="CPU stand-in endpoint; pipeline check only")
    args = parser.parse_args(argv)
    if args.dry_run_dummy and not args.output:
        raise SystemExit("--dry-run-dummy needs an explicit --output outside results/")
    if args.defense and args.levels != ["A1"]:
        raise SystemExit("--defense d2 runs as --levels A1")
    release = ROOT / (rel.PILOT_RELEASE if args.split == "pilot" else rel.RELEASE)
    prompt_profile = a0_rebuild.activate("v3")
    a6_profile = a6_provenance_v3.activate()
    spec = model_spec(ROOT / args.models_config, args.model_key)
    base_url, api_key = os.environ.get("VLLM_BASE_URL"), os.environ.get("VLLM_API_KEY")
    if args.dry_run_dummy:
        base_url = api_key = "dry-run"
    if not base_url or not api_key:
        raise SystemExit("Set VLLM_BASE_URL (https://.../v1) and VLLM_API_KEY")
    rows = load_rows(release, args.split, args.branches)

    agent_path = ROOT / "configs/agent/A0.yaml"
    generation_path = ROOT / "configs/runtime/default.yaml"
    runtime_config = load_runtime_config(agent_path)
    generation_config = load_generation_config(generation_path)
    backend: Any
    if args.dry_run_dummy:
        backend = DryRunAgent(spec["repo"], spec["revision"])
    else:
        backend_cls: type[OpenAICompatBackend] = OpenAICompatBackend
        if spec.get("untrusted_role") == "input":  # Meta-SecAlign interface (WP2)
            from react_agent.llm.secalign_role_v1 import SecAlignInputRoleBackend
            backend_cls = SecAlignInputRoleBackend
        backend = backend_cls(
            OrderedHTTPSJSON(base_url, api_key, timeout=args.timeout),
            repo=spec["repo"], revision=spec["revision"],
            chat_template_kwargs=spec.get("chat_template_kwargs"),
            tool_definitions=build_clean_registry(CLEAN_ENV).definitions())
    try:
        backend.probe()
    except InfrastructureError as exc:
        print(f"Endpoint unreachable at start ({exc}); rerun the same command to resume.")
        return 2

    tag = "d2" if args.defense else "_".join(args.levels)
    output = (args.output or ROOT / "results/rebuild_b" /
              f"v3_{args.split}_{tag}_{args.model_key}").resolve()
    files = {f"{args.split}_{b}": release / f"{args.split}_{b}.jsonl" for b in args.branches}
    identity: dict[str, Any] = {
        "benchmark": "vn_agentinject_v3", "split": args.split,
        "runtime": D2_RUNTIME_VERSION if args.defense else RUNTIME_VERSION,
        "environment": doc_search_v2.ENVIRONMENT_VERSION,
        "model_key": args.model_key, "model_id": spec["repo"], "model_revision": spec["revision"],
        "untrusted_role": spec.get("untrusted_role", "user"),
        "generation": generation_config.model_dump(),
        "file_sha256": {name: sha256(path) for name, path in {
            **{k: v for k, v in files.items() if v.exists()},
            "spec": ROOT / "data/adversarial/v3_authoring/spec.json",
            "agent": agent_path, "generation": generation_path,
            "doc_search_v2": ROOT / "src/react_agent/tools/doc_search_v2.py",
            "release_v3_module": ROOT / "src/react_agent/authoring/v3/release.py"}.items()},
        "prompt": prompt_profile, "decoding_schema": "per_tool_v2_name_first",
        "a6_policy": a6_profile, "levels": args.levels,
        "variant_ids": [row.variant_id for row in rows],
    }
    if args.defense:
        identity["defense"] = {"name": "D2", "file_sha256": {
            path.name: sha256(path) for path in (
                ROOT / "src/react_agent/security_v1/control_data_policy_v1.py",
                ROOT / "src/react_agent/security_v1/runtime_d2_v1.py")}}
    if args.dry_run_dummy:
        identity["dry_run_dummy"] = True
    runtime_class = D2Runtime if args.defense else Phase5ClosureRuntime
    output.mkdir(parents=True, exist_ok=True)
    identity_path = output / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise SystemExit("Output directory belongs to other inputs; choose a fresh --output")
    atomic_json(identity_path, identity)

    consecutive_infra = 0
    for level in cast(list[Level], args.levels):
        config = configuration(level)
        for row in rows:
            folder = output / "runs" / level / row.variant_id
            if (folder / "result.json").exists():
                continue
            shutil.rmtree(folder, ignore_errors=True)  # leftover of an infrastructure failure
            folder.mkdir(parents=True)
            infra_before = backend.infra_failures
            environment = folder / "environment"
            registry = doc_search_v2.apply_e2(row.registry(CLEAN_ENV, environment), environment)
            runtime = runtime_class(
                backend, registry,
                runtime_config=runtime_config, generation_config=generation_config)
            run = runtime.run_instrumented(
                row.task, output=folder / "execution", source_catalog=row.catalog(),
                security_config=config, guard_factory=None, guard_execution=None)
            if run.result.status == "model_error" and backend.infra_failures > infra_before:
                shutil.rmtree(folder)
                consecutive_infra += 1
                print(f"{level} {row.variant_id}: infrastructure error, will rerun", flush=True)
                if consecutive_infra >= MAX_CONSECUTIVE_INFRA:
                    print("Endpoint looks down; stopping. Rerun the same command to resume.")
                    return 2
                continue
            consecutive_infra = 0
            atomic_json(folder / "result.json", {
                "level": level, "variant_id": row.variant_id, "branch": row.branch,
                "family_id": row.family_id, "variant_type": row.variant_type,
                "status": run.result.status,
                "trace_sha256": sha256(folder / "execution/trace_legacy.jsonl")})
            print(f"{level} {row.variant_id}: {run.result.status}", flush=True)

    done = [json.loads(path.read_text()) for level in args.levels for row in rows
            if (path := output / "runs" / level / row.variant_id / "result.json").exists()]
    summary = {"scheduled": len(rows) * len(args.levels), "finished": len(done),
               "statuses": dict(Counter(f"{d['level']}:{d['status']}" for d in done)),
               "private_ground_truth_loaded": 0}
    atomic_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["finished"] == summary["scheduled"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
