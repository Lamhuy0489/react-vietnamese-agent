#!/usr/bin/env python3
"""Re-baseline the adversarial Dev fixtures in environment E2 (decision log 2026-10-28).

Same pipeline as the pinned ``run_adversarial_dev_api_v1.py`` (frozen Phase 5 closure
runtime, rebuild prompt v3, per-tool decoding schema, A6 v3 policy, checkpoint and
resume, infrastructure reruns, guard keepalive), with one change: every fixture registry
is wrapped by ``apply_e2``, so ``doc_search`` also reports exact identifier matches.
Every configuration runs in the same environment. Dev only: Test-2 runs go through a
runner gated by ``final_config_v2``.

For speed, run each level as its own process against its own endpoint, e.g.
``--levels A0`` and ``--levels A1`` on two agent notebooks and ``--levels A6`` on a
third with the guard. Each process writes to its own output directory.
Score with ``evaluate_adversarial_dev_v1.py`` and ``evaluate_side_effect_harm_v1.py``.
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

from react_agent.adversarial_release import load_split
from react_agent.agent.checkpoint import atomic_json
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.evaluation.adversarial_v1 import (
    LEVELS,
    DryRunAgent,
    DryRunGuardFactory,
    GuardFactory,
    GuardKeepalive,
    guard_infrastructure_failure,
    prepare_registry,
    run_catalog,
)
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
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.tools import doc_search_v2
from react_agent.tools.factory import build_clean_registry

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/adversarial/release_v2"
CLEAN_ENV = ROOT / "data/clean/v1_1/environment"
MAX_CONSECUTIVE_INFRA = 3


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-key", default="qwen3_8b")
    parser.add_argument("--guard-key", default="llama32_3b_prompted")
    parser.add_argument("--levels", nargs="+", default=["A0", "A1", "A6"], choices=LEVELS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, help="pilot: first N families, one pair each")
    parser.add_argument("--timeout", type=float, default=150)
    parser.add_argument("--dry-run-dummy", action="store_true",
                        help="CPU stand-ins for both endpoints; pipeline check only")
    args = parser.parse_args()
    if args.dry_run_dummy and not args.output:
        raise SystemExit("--dry-run-dummy needs an explicit --output outside results/")
    prompt_profile = a0_rebuild.activate("v3")
    a6_profile = a6_provenance_v3.activate()
    models = yaml.safe_load((ROOT / "configs/models/backbones_v2.yaml").read_text())
    spec, guard_spec = models[args.model_key], models["guard_candidates"][args.guard_key]
    base_url, api_key = os.environ.get("VLLM_BASE_URL"), os.environ.get("VLLM_API_KEY")
    if args.dry_run_dummy:
        base_url = api_key = "dry-run"
    if not base_url or not api_key:
        raise SystemExit("Set VLLM_BASE_URL (https://.../v1) and VLLM_API_KEY")
    needs_guard = any(configuration(cast(Level, level)).llm_guard for level in args.levels)
    guard_url, guard_key = os.environ.get("GUARD_BASE_URL"), os.environ.get("GUARD_API_KEY")
    if needs_guard and not args.dry_run_dummy and (not guard_url or not guard_key):
        raise SystemExit("A2+ needs GUARD_BASE_URL and GUARD_API_KEY")

    rows = load_split(RELEASE, "dev")
    if args.limit:
        families = sorted({r.family_id for r in rows})[: args.limit]
        rows = [r for f in families for b in ("attack", "benign")
                for r in [next(x for x in rows if x.family_id == f and x.branch == b)]]
    agent_path = ROOT / "configs/agent/A0.yaml"
    generation_path = ROOT / "configs/runtime/default.yaml"
    runtime_config = load_runtime_config(agent_path)
    generation_config = load_generation_config(generation_path)
    backend: Any
    guard_factory: Any = None
    if args.dry_run_dummy:
        backend = DryRunAgent(spec["repo"], spec["revision"])
        if needs_guard:
            guard_factory = DryRunGuardFactory(guard_spec["repo"], guard_spec["revision"])
    else:
        # E2 keeps doc_search's name, description and schema: the definitions are the same.
        backend = OpenAICompatBackend(
            OrderedHTTPSJSON(base_url, api_key, timeout=args.timeout),
            repo=spec["repo"], revision=spec["revision"],
            chat_template_kwargs=spec.get("chat_template_kwargs"),
            tool_definitions=build_clean_registry(CLEAN_ENV).definitions())
        if needs_guard:
            guard_factory = GuardFactory(cast(str, guard_url), cast(str, guard_key),
                                         guard_spec["repo"], guard_spec["revision"],
                                         args.timeout)
    try:
        backend.probe()
        if guard_factory:
            guard_factory().probe()
    except InfrastructureError as exc:
        print(f"Endpoint unreachable at start ({exc}); rerun the same command to resume.")
        return 2
    keepalive = GuardKeepalive(guard_factory.ping) if guard_factory else None

    name = f"adv_dev_e2_{args.model_key}_{'_'.join(args.levels)}"
    output = (args.output or ROOT / "results/rebuild_a" / name).resolve()
    identity: dict[str, Any] = {
        "benchmark": "adversarial_release_v2", "split": "dev", "runtime": RUNTIME_VERSION,
        "environment": doc_search_v2.ENVIRONMENT_VERSION,
        "model_key": args.model_key, "model_id": spec["repo"], "model_revision": spec["revision"],
        "guard": {"repo": guard_spec["repo"], "revision": guard_spec["revision"]},
        "generation": generation_config.model_dump(),
        "file_sha256": {name: sha256(path) for name, path in {
            "seal": RELEASE / "seal.json", "dev_attack": RELEASE / "dev_attack.jsonl",
            "dev_benign": RELEASE / "dev_benign.jsonl", "agent": agent_path,
            "generation": generation_path,
            "doc_search_v2": ROOT / "src/react_agent/tools/doc_search_v2.py"}.items()},
        "prompt": prompt_profile, "decoding_schema": "per_tool_v2_name_first",
        "overlay_input_model_fix": True, "a6_policy": a6_profile,
        "levels": args.levels, "variant_ids": [row.variant_id for row in rows],
    }
    if args.dry_run_dummy:
        identity["dry_run_dummy"] = True
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
            guard = guard_factory if config.llm_guard else None
            if keepalive and not guard:
                keepalive.tick()
            environment = folder / "environment"
            registry = doc_search_v2.apply_e2(
                prepare_registry(row, CLEAN_ENV, environment), environment)
            runtime = Phase5ClosureRuntime(
                backend, registry,
                runtime_config=runtime_config, generation_config=generation_config)
            run = runtime.run_instrumented(
                row.task, output=folder / "execution", source_catalog=run_catalog(row),
                security_config=config, guard_factory=guard,
                guard_execution=WarmGuardConfig(guard.repo, guard.revision, args.timeout)
                if guard else None)
            infra = (run.result.status == "model_error"
                     and backend.infra_failures > infra_before) or (
                guard is not None and guard_infrastructure_failure(folder / "execution"))
            if infra:
                shutil.rmtree(folder)
                consecutive_infra += 1
                print(f"{level} {row.variant_id}: infrastructure error, will rerun", flush=True)
                if consecutive_infra >= MAX_CONSECUTIVE_INFRA:
                    print("Endpoint looks down; stopping. Rerun the same command to resume.")
                    return 2
                continue
            consecutive_infra = 0
            if keepalive and guard:
                keepalive.touch()
            atomic_json(folder / "result.json", {
                "level": level, "variant_id": row.variant_id, "branch": row.branch,
                "family_id": row.family_id, "status": run.result.status,
                "trace_sha256": sha256(folder / "execution/trace_legacy.jsonl")})
            print(f"{level} {row.variant_id}: {run.result.status}", flush=True)

    done = [json.loads(path.read_text()) for level in args.levels for row in rows
            if (path := output / "runs" / level / row.variant_id / "result.json").exists()]
    summary = {"scheduled": len(rows) * len(args.levels), "finished": len(done),
               "statuses": dict(Counter(f"{d['level']}:{d['status']}" for d in done)),
               "private_ground_truth_loaded": 0, "test_payloads_loaded": 0}
    atomic_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["finished"] == summary["scheduled"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
