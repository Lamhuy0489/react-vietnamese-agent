#!/usr/bin/env python3
"""Replay Dev v4.1 oracle trajectories through v1 (D2) and BrokerGuard v3 runtimes.

No LLM: ``RecordingReplay`` proposes the oracle's actions in order and the real broker
decides each one. Two paths per fixture:

- benign_auth / benign_plain: the safe trajectory; we want utility (``score_v3``);
- attack: the negative (harmful) trajectory; we want no harm (``side_effect_harm_v3`` or a
  transformed leak), and the safe trajectory, which should keep utility.

This is an upper bound on what the broker can stop (a real model may never propose the
harmful call, or may propose others), so it guides development only; the ASR claims come
from agent runs. Dev v4.1 only (develop on train, choose on val); Test-4 is never read.
Output: counts and family IDs per runtime, split, branch and mechanism.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from types import ModuleType
from typing import Any

from react_agent.authoring.v3 import release as rel
from react_agent.authoring.workbench_qa import RecordingReplay
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.schemas.trace import TraceEvent
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.runtime_d2_v1 import D2Runtime
from react_agent.security_v3 import brokerguard_v3_v1 as v3
from react_agent.tools import doc_search_v2

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/adversarial/release_dev4_1"
CLEAN_ENV = ROOT / rel.CLEAN


def _script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load scripts/{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def runtimes(names: list[str]) -> dict[str, type[D2Runtime]]:
    table: dict[str, type[D2Runtime]] = {"v1": D2Runtime, "v3": v3.BrokerGuardV3Runtime}
    for component in sorted(v3.ALL_COMPONENTS):
        table[f"v3-{component}"] = v3.runtime_class(v3.ALL_COMPONENTS - {component})
    for component in sorted(v3.OPTIONAL_COMPONENTS):
        table[f"v3+{component}"] = v3.runtime_class(v3.ALL_COMPONENTS | {component})
    unknown = set(names) - set(table)
    if unknown:
        raise SystemExit(f"unknown runtime(s) {sorted(unknown)}; choose from {sorted(table)}")
    return {n: table[n] for n in names}


def replay_one(runtime: type[D2Runtime], row: rel.FixtureV3, private: rel.PrivateV3,
               negative: bool, folder: Path, evaluator: ModuleType) -> dict[str, Any]:
    oracle = private.auth_oracle if row.branch == "benign_auth" else private.oracle
    if oracle is None:
        raise ValueError("benign_auth requires an auth oracle")
    backend = RecordingReplay(oracle.negative_actions if negative else oracle.safe_actions,
                              oracle.negative_final if negative else oracle.safe_final)
    environment = folder / "environment"
    registry = doc_search_v2.apply_e2(row.registry(CLEAN_ENV, environment), environment)
    runtime_config = load_runtime_config(ROOT / "configs/agent/A0.yaml")
    generation_config = load_generation_config(ROOT / "configs/runtime/default.yaml")
    runtime(backend, registry, runtime_config=runtime_config,
            generation_config=generation_config).run_instrumented(
        row.task, output=folder / "execution", source_catalog=row.catalog(),
        security_config=configuration("A1"), guard_factory=None, guard_execution=None)
    trace = folder / "execution/trace_legacy.jsonl"
    events = [TraceEvent.model_validate_json(line)
              for line in trace.read_text(encoding="utf-8").splitlines() if line]
    score = rel.score_v3(events, private, row.branch, environment / "database/university.db")
    hits = evaluator.transformed_leaks(events, private, row.branch)
    reasons: Counter[str] = Counter()
    security = folder / "execution/trace_security.jsonl"
    for line in security.read_text(encoding="utf-8").splitlines() if security.exists() else []:
        event = json.loads(line)
        if event.get("event") == "decision":
            data = json.loads(event["data_json"])
            if data.get("effect") != "ALLOW":
                reasons.update(f"{data.get('stage')}:{r}" for r in data.get("reasons", []))
    return {"utility": bool(score["utility"]),
            "harm": bool(score["side_effect_harm_v3"]) or bool(hits),
            "reasons": dict(reasons)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runtimes", nargs="+", default=["v1", "v3"])
    parser.add_argument("--split", choices=("train", "val", "all"), default="train")
    parser.add_argument("--limit", type=int, help="first N fixtures per branch (smoke test)")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/rebuild_c/v3_oracle_replay_v1.json")
    args = parser.parse_args()
    evaluator = _script("evaluate_v3_v2")
    seal = evaluator.sha256(RELEASE / "seal.json")
    privates = evaluator.load_privates("dev4_1", seal)
    val = set(json.loads((RELEASE / "manifest.json").read_text())["dev_val"])
    rows: list[rel.FixtureV3] = []
    for branch in ("benign_auth", "benign_plain", "attack"):
        lines = (RELEASE / f"dev_{branch}.jsonl").read_text(encoding="utf-8").splitlines()
        picked = [rel.FixtureV3.model_validate_json(line) for line in lines if line]
        picked = [r for r in picked if args.split == "all"
                  or (r.family_id in val) == (args.split == "val")]
        rows += picked[:args.limit] if args.limit else picked
    report: dict[str, Any] = {"release": "dev4_1", "seal_sha256": seal, "split": args.split,
                              "scope": "oracle replay, Dev only, no LLM", "runtimes": {}}
    with tempfile.TemporaryDirectory(prefix="v3replay_") as tmp:
        for name, runtime in runtimes(args.runtimes).items():
            tally: dict[str, Counter[str]] = defaultdict(Counter)
            fails: dict[str, set[str]] = defaultdict(set)
            reasons: Counter[str] = Counter()
            for i, row in enumerate(rows):
                private = privates[row.family_id]
                mech = private.mechanism
                paths = (False, True) if row.branch == "attack" else (False,)
                for negative in paths:
                    folder = Path(tmp) / f"{name}_{i}_{int(negative)}"
                    out = replay_one(runtime, row, private, negative, folder, evaluator)
                    shutil.rmtree(folder, ignore_errors=True)
                    reasons.update(out["reasons"])
                    if negative:
                        tally["attack_negative"]["n"] += 1
                        tally["attack_negative"]["harm"] += out["harm"]
                        tally[f"attack_negative:{mech}"]["n"] += 1
                        tally[f"attack_negative:{mech}"]["harm"] += out["harm"]
                        if out["harm"]:
                            fails[f"harm:{mech}"].add(row.family_id)
                    else:
                        key = f"{row.branch}_safe"
                        tally[key]["n"] += 1
                        tally[key]["utility"] += out["utility"]
                        tally[key]["harm"] += out["harm"]
                        if not out["utility"]:
                            fails[f"utility_lost:{row.branch}"].add(row.family_id)
            report["runtimes"][name] = {
                "tally": {k: dict(v) for k, v in sorted(tally.items())},
                "fail_families": {k: sorted(v) for k, v in sorted(fails.items())},
                "non_allow_reasons": dict(reasons.most_common())}
            summary = {k: v for k, v in sorted(tally.items()) if ":" not in k}
            print(name, json.dumps({k: dict(v) for k, v in summary.items()}), flush=True)
            print("   ", {k.split(":")[1]: f"{v['harm']}/{v['n']}" for k, v in sorted(tally.items())
                          if k.startswith("attack_negative:")}, flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
