#!/usr/bin/env python3
"""Run VN-AgentInject v3 fixtures through the agent (Study 2, WP3 pilot onward).

Same pipeline as ``run_adversarial_e2_api_v1.py`` (frozen Phase 5 closure runtime or D2,
rebuild prompt v3, per-tool decoding schema, environment E2 ``doc_search``, checkpoint and
resume, infrastructure reruns). Differences:

- fixtures come from a v3 release (``pilot_v3`` or ``release_v3``) and build their own
  registry and host catalog (``FixtureV3.registry``/``catalog``);
- models resolve from ``backbones_v3.yaml``; Meta-SecAlign uses the ``input`` role backend;
- only public fixture files are read; private oracles stay with ``evaluate_v3_v1.py``.

The Test split runs only when ``configs/final/final_config_v3.json`` matches every pinned
file and lists the (model, configuration) pair (plan WP9); its hash enters the identity.
Test-3 (``--split test3``, ``release_test3``) does the same under ``final_config_v4.json``.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import time
from collections import Counter
from pathlib import Path
from typing import Any, cast

import yaml

from react_agent.agent.checkpoint import atomic_json
from react_agent.authoring.v3 import release as rel
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.evaluation import final_config_v3, final_config_v4
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
from react_agent.security_v3 import d3 as d3mod
from react_agent.security_v3 import sanitizer as san
from react_agent.security_v3.d2_no_rule import D2NoRuleRuntime
from react_agent.security_v3.melon import MelonBackend
from react_agent.security_v3.progent_lite import apply_progent_lite
from react_agent.security_v3.prompt_baselines import PromptBaselineBackend
from react_agent.security_v3.promptguard import THRESHOLD as PG_THRESHOLD
from react_agent.security_v3.promptguard import (
    PromptGuardFilterBackend,
    local_classifier,
    local_identity,
)
from react_agent.tools import doc_search_v2
from react_agent.tools.factory import build_clean_registry

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ENV = ROOT / rel.CLEAN
MAX_CONSECUTIVE_INFRA = 8  # quick-tunnel drops come in bursts (Dev round 3)
PROMPT_BASELINES: dict[str, dict[str, Any]] = {
    "p1": {"spotlight_mode": "datamark"}, "p2": {"sandwich": True},
    "p1p2": {"spotlight_mode": "datamark", "sandwich": True},
    "d2p1": {"spotlight_mode": "datamark"}, "d2p2": {"sandwich": True},
    "d2nrp2": {"sandwich": True}, "d2p2san": {"sandwich": True},
    "d3p2v1": {"sandwich": True}, "d3dest": {"sandwich": True}}
# D3 (Dev): narrowed A1 layer + reminder v2 + denial feedback v2, and its ablations.
D3 = {"d3", "d3p2v1", "d3fbv1", "d3dest"}
D3_REMINDER_V2 = {"d3", "d3fbv1"}
D3_FEEDBACK_V1 = {"d3fbv1", "d3dest"}
# Dev round 3: sanitizer (SAN) alone on A0, with D2, and with D2+P2.
SANITIZED = {"san", "d2san", "d2p2san"}
DEFENSES = {"d2", "g1", "mel", "prg", *PROMPT_BASELINES, *SANITIZED, *D3}
NO_GUARD_LEVELS = [level for level in LEVELS if not configuration(cast(Level, level)).llm_guard]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_spec(config: Path, key: str) -> dict[str, Any]:
    spec: dict[str, Any] = yaml.safe_load(config.read_text(encoding="utf-8"))[key]
    if spec.get("from") == "backbones_v2":
        spec = model_spec(config.with_name("backbones_v2.yaml"), key)
    return spec


def config_name(levels: list[str], defense: str | None) -> str | None:
    """Configuration name used by the chains and the frozen Test matrix (A0, R1, P2, D2P2...)."""
    if defense:
        return defense.upper()
    names: dict[tuple[str, ...], str] = {("A0",): "A0", ("A1",): "R1"}
    return names.get(tuple(levels))


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
    parser.add_argument("--split", choices=["pilot", "dev", "test", "test3"], default="pilot")
    parser.add_argument("--branches", nargs="+", default=list(rel.BRANCH_CODE),
                        choices=list(rel.BRANCH_CODE))
    parser.add_argument("--levels", nargs="+", default=["A0"], choices=NO_GUARD_LEVELS)
    parser.add_argument("--defense", choices=sorted(DEFENSES),
                        help="d2 (D2 runtime, --levels A1); p1/p2/p1p2 prompt baselines on A0; "
                             "d2p1 = D2 + spotlighting; d2p2 = D2 + sandwich (Dev round 1); "
                             "d2nrp2 = D2 without the A1 rule layer + sandwich (Dev round 2); "
                             "san/d2san/d2p2san = task-aware sanitizer alone (A0), with D2, "
                             "with D2+P2 (Dev round 3); d3 = D2 with the destination-scoped A1 "
                             "layer, reminder v2 and denial feedback v2; ablations d3p2v1 "
                             "(P2 reminder), d3fbv1 (feedback v1), d3dest (both v1)")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--shard", default="0/1",
                        help="I/N: run fixtures I, I+N, ... (same output and identity; "
                             "one process per shard)")
    parser.add_argument("--fixtures", type=Path,
                        help="WP8: run these attack fixtures (jsonl) instead of the release "
                             "split; the file hash enters the identity")
    parser.add_argument("--timeout", type=float, default=150)
    parser.add_argument("--dry-run-dummy", action="store_true",
                        help="CPU stand-in endpoint; pipeline check only")
    args = parser.parse_args(argv)
    final_sha: str | None = None
    if args.split in ("test", "test3"):
        frozen: Any = final_config_v3 if args.split == "test" else final_config_v4
        label = "Test v3" if args.split == "test" else "Test-3"
        try:
            manifest = frozen.verify(ROOT)
        except frozen.FrozenConfigError as exc:
            raise SystemExit(f"{label} refused: {exc}") from exc
        test_config = config_name(args.levels, args.defense)
        if test_config is None or not frozen.allowed(manifest, args.model_key, test_config):
            raise SystemExit(f"{label} refused: {args.model_key} {test_config} not in the matrix")
        if args.fixtures or sorted(args.branches) != sorted(rel.BRANCH_CODE):
            raise SystemExit(f"{label} runs the sealed release, all branches, no --fixtures")
        final_sha = frozen.manifest_sha256(ROOT)
    if args.dry_run_dummy and not args.output:
        raise SystemExit("--dry-run-dummy needs an explicit --output outside results/")
    d2 = args.defense in ("d2", "d2p1", "d2p2", "d2nrp2", "d2san", "d2p2san", *D3)
    if d2 and args.levels != ["A1"]:
        raise SystemExit("--defense d2/d2p1/d2p2 runs as --levels A1")
    if args.defense in ("p1", "p2", "p1p2", "g1", "mel", "prg", "san") and (
            args.levels != ["A0"]):
        raise SystemExit("prompt baselines run on --levels A0 (no other defense)")
    release = ROOT / rel.release_folder(args.split)
    prompt_profile = a0_rebuild.activate("v3")
    a6_profile = a6_provenance_v3.activate()
    spec = model_spec(ROOT / args.models_config, args.model_key)
    base_url, api_key = os.environ.get("VLLM_BASE_URL"), os.environ.get("VLLM_API_KEY")
    if args.dry_run_dummy:
        base_url = api_key = "dry-run"
    if not base_url or not api_key:
        raise SystemExit("Set VLLM_BASE_URL (https://.../v1) and VLLM_API_KEY")
    if args.fixtures:
        rows = [rel.FixtureV3.model_validate_json(line) for line in
                args.fixtures.read_text(encoding="utf-8").splitlines() if line]
        if {row.split for row in rows} != {args.split}:
            raise SystemExit("--fixtures rows must belong to --split")
    else:
        rows = load_rows(release, args.split, args.branches)
    shard, shards = (int(x) for x in args.shard.split("/"))
    if not 0 <= shard < shards:
        raise SystemExit("--shard I/N needs 0 <= I < N")
    all_rows, rows = rows, rows[shard::shards]

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
    prompt_baseline = PROMPT_BASELINES.get(args.defense or "")
    if prompt_baseline:
        backend = PromptBaselineBackend(backend, **prompt_baseline)
    if args.defense in D3_REMINDER_V2:
        backend = d3mod.ReminderV2Backend(backend)
    if args.defense == "mel":
        backend = MelonBackend(backend)
    if args.defense in SANITIZED:  # outermost: P2's reminder is added after cleaning
        if args.dry_run_dummy:
            sanitizer_backend: Any = san.DryRunSanitizer()
        else:
            sanitizer_backend = OpenAICompatBackend(
                OrderedHTTPSJSON(base_url, api_key, timeout=args.timeout),
                repo=spec["repo"], revision=spec["revision"],
                chat_template_kwargs=spec.get("chat_template_kwargs"),
                response_schema=san.SCHEMA)
        backend = san.SanitizerBackend(backend, sanitizer_backend, generation_config)
    guard_identity: dict[str, Any] | None = None
    if args.defense == "g1":  # Prompt Guard 2 filter; local CPU service
        url = os.environ.get("PROMPTGUARD_URL", "http://127.0.0.1:8765")
        if args.dry_run_dummy:
            guard_identity = {"dry_run": True}
            backend = PromptGuardFilterBackend(backend, lambda text: 0.0)
        else:
            guard_identity = local_identity(url)
            backend = PromptGuardFilterBackend(backend, local_classifier(url))
    try:
        backend.probe()
    except InfrastructureError as exc:
        print(f"Endpoint unreachable at start ({exc}); rerun the same command to resume.")
        return 2

    tag = args.defense or "_".join(args.levels)
    output = (args.output or ROOT / "results/rebuild_b" /
              f"v3_{args.split}_{tag}_{args.model_key}").resolve()
    files = ({"fixtures": args.fixtures} if args.fixtures else
             {f"{args.split}_{b}": release / f"{args.split}_{b}.jsonl" for b in args.branches})
    identity: dict[str, Any] = {
        "benchmark": "vn_agentinject_v3", "split": args.split,
        "runtime": D2_RUNTIME_VERSION if d2 else RUNTIME_VERSION,
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
        "variant_ids": [row.variant_id for row in all_rows],
        **({"final_config_v3_sha256": final_sha} if final_sha and args.split == "test" else {}),
        **({"final_config_v4_sha256": final_sha} if final_sha and args.split == "test3" else {}),
    }
    if args.defense:
        files_d = [ROOT / "src/react_agent/security_v3/prompt_baselines.py"] if (
            prompt_baseline) else []
        if args.defense == "prg":
            files_d.append(ROOT / "src/react_agent/security_v3/progent_lite.py")
        if args.defense == "mel":
            files_d.append(ROOT / "src/react_agent/security_v3/melon.py")
        if guard_identity is not None:
            files_d.append(ROOT / "src/react_agent/security_v3/promptguard.py")
        if d2:
            files_d += [ROOT / "src/react_agent/security_v1/control_data_policy_v1.py",
                        ROOT / "src/react_agent/security_v1/runtime_d2_v1.py"]
        if args.defense == "d2nrp2":
            files_d.append(ROOT / "src/react_agent/security_v3/d2_no_rule.py")
        if args.defense in SANITIZED:
            files_d.append(ROOT / "src/react_agent/security_v3/sanitizer.py")
        if args.defense in D3:
            files_d.append(ROOT / "src/react_agent/security_v3/d3.py")
        identity["defense"] = {"name": args.defense, "prompt_baseline": prompt_baseline,
                               "prompt_guard": guard_identity and {
                                   **guard_identity, "threshold": PG_THRESHOLD},
                               "file_sha256": {f.name: sha256(f) for f in files_d}}
        if args.defense in SANITIZED:  # key absent for earlier defenses (identity unchanged)
            identity["defense"]["sanitizer"] = san.identity()
        if args.defense in D3:
            identity["defense"]["d3"] = {
                "profile": d3mod.PROFILE,
                "reminder": "v2" if args.defense in D3_REMINDER_V2 else "p2_v1",
                "denial_feedback": "v1" if args.defense in D3_FEEDBACK_V1 else "v2"}
    if args.dry_run_dummy:
        identity["dry_run_dummy"] = True
    runtime_class = (D2NoRuleRuntime if args.defense == "d2nrp2"
                     else d3mod.D3FeedbackV1Runtime if args.defense in D3_FEEDBACK_V1
                     else d3mod.D3Runtime if args.defense in D3
                     else D2Runtime if d2 else Phase5ClosureRuntime)
    output.mkdir(parents=True, exist_ok=True)
    # one runner per output folder and shard (held until exit)
    lock = (output / (".lock" if shards == 1 else f".lock{shard}")).open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(f"{output} is in use by another runner") from None
    identity_path = output / "identity.json"
    with (output / ".identity.lock").open("w") as identity_lock:  # shards start together
        fcntl.flock(identity_lock, fcntl.LOCK_EX)
        if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
            raise SystemExit("Output directory belongs to other inputs; choose a fresh --output")
        if not identity_path.exists():
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
            if isinstance(backend, san.SanitizerBackend):
                backend.begin(folder)
            environment = folder / "environment"
            registry = doc_search_v2.apply_e2(row.registry(CLEAN_ENV, environment), environment)
            if args.defense == "prg":  # policy from the public instruction only
                registry = apply_progent_lite(registry, row.task.instruction)
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
                time.sleep(10)
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
    if isinstance(backend, MelonBackend):
        summary["melon"] = {"masked_calls": backend.masked_calls,
                            "detections": backend.detections}
    if isinstance(backend, san.SanitizerBackend):
        summary["sanitizer"] = backend.stats  # this process only (resumes add up per log)
    atomic_json(output / ("summary.json" if shards == 1 else f"summary.shard{shard}.json"),
                summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["finished"] == summary["scheduled"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
