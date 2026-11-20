#!/usr/bin/env python3
"""Run Dev v4.1 or the sealed Test-4 through the agent (BrokerGuard v3, v1 and baselines).

Copy of ``run_v3_api_v3.py`` (kept unchanged: it made the Dev v4.1 V3P2 and ablation runs)
with one addition: ``--release test4`` runs the sealed Test-4 release (560 fixtures) or, with
``--fixtures`` pointing at the pinned 24 adaptive attacks, the adaptive part. Test-4 runs only
when ``configs/final/final_config_v5.json`` verifies against every pinned file and the
(model, configuration) pair is in its matrix; all branches, no other fixture file, no
``--max-new-tokens``. The manifest hash enters the identity. The Dev path is unchanged.

Notes inherited from ``run_v3_api_v3.py``, itself a copy of ``run_v3_api_v2.py`` (decision log
2026-11-16 18:30) with one addition: ``--defense v3p2`` = BrokerGuard v3 runtime
(``security_v3/brokerguard_v3_v1.py``: C1 intent policy, C2 value labels, C3 parameter
pinning) on ``--levels A1`` with the P2 sandwich reminder, and the ablations ``v3p2-c1``,
``v3p2-c2``, ``v3p2-c3`` (one component removed). Every other defense behaves exactly as in
``run_v3_api_v2.py`` and the identity keeps ``runner: run_v3_api_v2`` (same pipeline, so
``evaluate_v3_v2.py`` scores it); ``runner_file`` and the hash of this file are added, and the
v3 defenses record the hashes of the four v3 modules. Inherited notes from v2:

- releases: ``--release dev4`` (``release_dev4``) or ``dev4_1`` (``release_dev4_1``, the
  errata release). Every fixture file is checked against the release ``seal.json`` before
  the run, and the seal hash enters the identity;
- held-out splits other than the gated Test-4 path are refused;
- per execution, ``metrics.json`` (``react_agent.evaluation.run_metrics_v1``): prompt and
  completion tokens and seconds of every LLM call by role (agent, sanitizer, ...), extra
  LLM calls made by a defense, agent turns, tool calls proposed / passed the gate /
  executed / denied (by tool, sinks apart), gate decisions by component, stage and effect,
  non-allow reasons, confirmation-required count, final-answer redaction and a time split
  (LLM, tool, pre-execution gate, other runtime). ``summary.json`` aggregates them per
  level and branch (mean, median, p90, p95, max, sum).

Only public fixture files are read; private oracles stay with ``evaluate_v3_v2.py``.
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
from react_agent.evaluation import final_config_v5
from react_agent.evaluation import run_metrics_v1 as metrics_mod
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
from react_agent.security_v3 import brokerguard_v3_v1 as v3mod
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
    "d3p2v1": {"sandwich": True}, "d3dest": {"sandwich": True},
    "v3p2": {"sandwich": True}, "v3p2-c1": {"sandwich": True},
    "v3p2-c2": {"sandwich": True}, "v3p2-c3": {"sandwich": True}}
# BrokerGuard v3 (Dev v4.1): full runtime and one-component ablations, all with P2.
V3 = {"v3p2": frozenset(v3mod.ALL_COMPONENTS),
      **{f"v3p2-{c.lower()}": frozenset(v3mod.ALL_COMPONENTS - {c})
         for c in sorted(v3mod.ALL_COMPONENTS)}}
V3_FILES = ("intent_policy_v1.py", "value_labels_v1.py", "param_pinning_v1.py",
            "brokerguard_v3_v1.py")
# D3 (Dev): narrowed A1 layer + reminder v2 + denial feedback v2, and its ablations.
D3 = {"d3", "d3p2v1", "d3fbv1", "d3dest"}
D3_REMINDER_V2 = {"d3", "d3fbv1"}
D3_FEEDBACK_V1 = {"d3fbv1", "d3dest"}
# Dev round 3: sanitizer (SAN) alone on A0, with D2, and with D2+P2.
SANITIZED = {"san", "d2san", "d2p2san"}
DEFENSES = {"d2", "g1", "mel", "prg", *PROMPT_BASELINES, *SANITIZED, *D3, *V3}
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


RELEASES = {"dev4": "data/adversarial/release_dev4", "dev4_1": "data/adversarial/release_dev4_1",
            "test4": "data/adversarial/release_test4"}
TEST_RELEASES = {"test4"}


def test4_gate(args: argparse.Namespace) -> str:
    """Refuse a Test-4 run unless final_config_v5 verifies and allows it; the manifest hash."""
    try:
        manifest = final_config_v5.verify(ROOT)
    except final_config_v5.FrozenConfigError as exc:
        raise SystemExit(f"Test-4 refused: {exc}") from exc
    test_config = config_name(args.levels, args.defense)
    if test_config is None or not final_config_v5.allowed(manifest, args.model_key, test_config):
        raise SystemExit(f"Test-4 refused: {args.model_key} {test_config} not in the matrix")
    if sorted(args.branches) != sorted(rel.BRANCH_CODE):
        raise SystemExit("Test-4 refused: runs all branches")
    if args.fixtures and args.fixtures.resolve() != (ROOT / final_config_v5.ADAPTIVE).resolve():
        raise SystemExit(f"Test-4 refused: --fixtures may only be {final_config_v5.ADAPTIVE}")
    if args.max_new_tokens is not None:
        raise SystemExit("Test-4 refused: --max-new-tokens is a Dev-only diagnostic")
    return final_config_v5.manifest_sha256(ROOT)


def check_seal(folder: Path, names: list[str]) -> str:
    """Refuse to run on files that differ from the release seal; return the seal hash."""
    seal_path = folder / "seal.json"
    sealed = json.loads(seal_path.read_text(encoding="utf-8"))["files_sha256"]
    for name in names:
        if sealed.get(name) != sha256(folder / name):
            raise SystemExit(f"{folder / name} does not match {seal_path}; refusing to run")
    return sha256(seal_path)


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
    parser.add_argument("--release", choices=sorted(RELEASES), default="dev4_1")
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
                             "(P2 reminder), d3fbv1 (feedback v1), d3dest (both v1); "
                             "v3p2 = BrokerGuard v3 + sandwich (--levels A1), ablations "
                             "v3p2-c1/-c2/-c3")
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
    parser.add_argument("--max-new-tokens", type=int,
                        help="Dev diagnostic only (decision log 2026-11-10 01:50): override the "
                             "pinned output budget; enters the identity via 'generation'")
    args = parser.parse_args(argv)
    final_sha = test4_gate(args) if args.release in TEST_RELEASES else None
    if args.dry_run_dummy and not args.output:
        raise SystemExit("--dry-run-dummy needs an explicit --output outside results/")
    d2 = args.defense in ("d2", "d2p1", "d2p2", "d2nrp2", "d2san", "d2p2san", *D3, *V3)
    if d2 and args.levels != ["A1"]:
        raise SystemExit("--defense d2/d2p1/d2p2 runs as --levels A1")
    if args.defense in ("p1", "p2", "p1p2", "g1", "mel", "prg", "san") and (
            args.levels != ["A0"]):
        raise SystemExit("prompt baselines run on --levels A0 (no other defense)")
    release = ROOT / RELEASES[args.release]
    # Dev v4 rows keep split = dev (build_dev_pool_v4.py); Test-4 rows have split = test4
    split = "test4" if args.release == "test4" else "dev"
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
        if {row.split for row in rows} != {split}:
            raise SystemExit(f"--fixtures rows must be {split} rows")
        seal_sha = sha256(release / "seal.json")
    else:
        seal_sha = check_seal(release, [f"{split}_{b}.jsonl" for b in args.branches])
        rows = load_rows(release, split, args.branches)
    shard, shards = (int(x) for x in args.shard.split("/"))
    if not 0 <= shard < shards:
        raise SystemExit("--shard I/N needs 0 <= I < N")
    all_rows, rows = rows, rows[shard::shards]

    agent_path = ROOT / "configs/agent/A0.yaml"
    generation_path = ROOT / "configs/runtime/default.yaml"
    runtime_config = load_runtime_config(agent_path)
    generation_config = load_generation_config(generation_path)
    if args.max_new_tokens is not None:
        generation_config = generation_config.model_copy(
            update={"max_new_tokens": args.max_new_tokens})
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
    part = "_adaptive" if args.release in TEST_RELEASES and args.fixtures else ""
    output = (args.output or ROOT / "results/rebuild_c" /
              f"{args.release}{part}_{tag}_{args.model_key}").resolve()
    files = ({"fixtures": args.fixtures} if args.fixtures else
             {f"{split}_{b}": release / f"{split}_{b}.jsonl" for b in args.branches})
    identity: dict[str, Any] = {
        "benchmark": "vn_agentinject_v3", "split": split, "release": args.release,
        "release_seal_sha256": seal_sha, "runner": "run_v3_api_v2",
        "runner_file": "run_v3_api_v4", "runner_sha256": sha256(Path(__file__).resolve()),
        "metrics": metrics_mod.METRICS_VERSION,
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
            "release_v3_module": ROOT / "src/react_agent/authoring/v3/release.py",
            "run_metrics": ROOT / "src/react_agent/evaluation/run_metrics_v1.py"}.items()},
        "prompt": prompt_profile, "decoding_schema": "per_tool_v2_name_first",
        "a6_policy": a6_profile, "levels": args.levels,
        "variant_ids": [row.variant_id for row in all_rows],
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
        if args.defense in V3:
            files_d += [ROOT / "src/react_agent/security_v3" / name for name in V3_FILES]
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
        if args.defense in V3:
            identity["defense"]["v3"] = {"profile": v3mod.PROFILE,
                                         "components": sorted(V3[args.defense])}
    if final_sha:
        identity["final_config_v5_sha256"] = final_sha
    if args.dry_run_dummy:
        identity["dry_run_dummy"] = True
    runtime_class = (v3mod.runtime_class(V3[args.defense]) if args.defense in V3
                     else D2NoRuleRuntime if args.defense == "d2nrp2"
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
    window = metrics_mod.CallWindow(backend)
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
            window.open()
            started = time.perf_counter()
            runtime = runtime_class(
                backend, registry,
                runtime_config=runtime_config, generation_config=generation_config)
            run = runtime.run_instrumented(
                row.task, output=folder / "execution", source_catalog=row.catalog(),
                security_config=config, guard_factory=None, guard_execution=None)
            wall = time.perf_counter() - started
            calls = window.close()
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
            atomic_json(folder / "metrics.json",
                        metrics_mod.execution_metrics(folder / "execution", calls, wall))
            atomic_json(folder / "result.json", {
                "level": level, "variant_id": row.variant_id, "branch": row.branch,
                "family_id": row.family_id, "variant_type": row.variant_type,
                "status": run.result.status,
                "trace_sha256": sha256(folder / "execution/trace_legacy.jsonl")})
            print(f"{level} {row.variant_id}: {run.result.status}", flush=True)

    done = [json.loads(path.read_text()) for level in args.levels for row in rows
            if (path := output / "runs" / level / row.variant_id / "result.json").exists()]
    metrics: dict[str, list[dict[str, Any]]] = {f"{d['level']}:{d['branch']}": [] for d in done}
    for d in done:
        path = output / "runs" / d["level"] / d["variant_id"] / "metrics.json"
        if path.exists():
            metrics[f"{d['level']}:{d['branch']}"].append(json.loads(path.read_text()))
    summary = {"scheduled": len(rows) * len(args.levels), "finished": len(done),
               "cost": {k: metrics_mod.aggregate(v) for k, v in sorted(metrics.items())},
               # latency is comparable only between runs made under the same concurrency
               "concurrency": {"shards": shards,
                               "parallel_configs": os.environ.get("DEV4_PARALLEL_CONFIGS")},
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
