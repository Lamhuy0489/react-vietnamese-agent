#!/usr/bin/env python3
"""Offline check of the C1 intent policy P(u) on Dev v4.1 (no LLM, no Test data).

For every Dev v4.1 fixture the extractor sees only ``task.instruction`` (u). The Dev
oracles are used here as labels, never by the policy:

- benign_auth / benign_plain: every required sink action must be ALLOWED (utility);
- attack: every negative sink action must not be ALLOWED (block), while the task's own
  required sink actions should stay ALLOWED.

The same counts are computed for v1 rule 2 (destination occurs as a substring of u),
so C1 is compared with v1 on the same footing. Output: counts and family IDs only.

Protocol (decision log 2026-11-15 16:30): develop on Dev-train, choose the config on
Dev-val (42 families). Test-4 is never read here.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from react_agent.security_v1.control_data_policy_v1 import destination_allowed
from react_agent.security_v3.intent_policy_v1 import (
    SINKS,
    Decision,
    IntentConfig,
    extract,
)

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/adversarial/release_dev4_1"
BRANCHES = ("benign_auth", "benign_plain", "attack")


def _load() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], set[str]]:
    rows: list[dict[str, Any]] = []
    for branch in BRANCHES:
        with (RELEASE / f"dev_{branch}.jsonl").open(encoding="utf-8") as fh:
            rows += [json.loads(line) for line in fh if line.strip()]
    oracles = {o["family_id"]: o for o in json.loads(
        (RELEASE / "private/oracles.json").read_text(encoding="utf-8"))}
    manifest = json.loads((RELEASE / "manifest.json").read_text(encoding="utf-8"))
    return rows, oracles, set(manifest["dev_val"])


def _sinks(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [a for a in actions if a.get("name") in SINKS]


def _labels(row: dict[str, Any], oracle: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    """(must-allow sink actions, must-block sink actions) for one fixture."""
    if row["branch"] == "benign_auth":
        auth = oracle.get("auth_oracle") or {}
        return _sinks(auth.get("required_sink_actions", [])), []
    base = oracle["oracle"]
    must_allow = _sinks(base.get("required_sink_actions", []))
    if row["branch"] == "attack":
        return must_allow, _sinks(base.get("negative_actions", []))
    return must_allow, []


def _v1_allows(action: dict[str, Any], user: str) -> bool:
    key = SINKS[action["name"]][0]
    return destination_allowed(str(action["arguments"].get(key, "")), user)


def evaluate(rows: list[dict[str, Any]], oracles: dict[str, dict[str, Any]], val: set[str],
             config: IntentConfig) -> dict[str, Any]:
    out: dict[str, Any] = {}
    tallies: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    fails: dict[tuple[str, str], set[str]] = defaultdict(set)
    reasons: Counter[str] = Counter()
    by_variant: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in rows:
        split = "val" if row["family_id"] in val else "train"
        oracle = oracles[row["family_id"]]
        user = row["task"]["instruction"]
        policy = extract(user, config)
        must_allow, must_block = _labels(row, oracle)
        key = (split, row["branch"])
        t = tallies[key]
        t["fixtures"] += 1
        if must_allow:
            verdicts = [policy.decide(a["name"], a["arguments"]) for a in must_allow]
            ok = all(v.decision is Decision.ALLOW for v in verdicts)
            t["need_allow"] += 1
            t["c1_allow_ok"] += ok
            t["c1_confirm"] += any(v.decision is Decision.CONFIRM for v in verdicts)
            t["v1_allow_ok"] += all(_v1_allows(a, user) for a in must_allow)
            if not ok:
                fails[(split, row["branch"] + ":allow")].add(row["family_id"])
                reasons.update(f"{row['branch']}:allow:{v.reason}" for v in verdicts
                               if v.decision is not Decision.ALLOW)
                by_variant[key][row["variant_type"]] += 1
        if must_block:
            verdicts = [policy.decide(a["name"], a["arguments"]) for a in must_block]
            blocked = all(v.decision is not Decision.ALLOW for v in verdicts)
            mech = oracle["mechanism"]
            t["need_block"] += 1
            t["c1_block_ok"] += blocked
            t[f"c1_block_ok:{mech}"] += blocked
            t[f"need_block:{mech}"] += 1
            v1_blocked = not any(_v1_allows(a, user) for a in must_block)
            t["v1_block_ok"] += v1_blocked
            t[f"v1_block_ok:{mech}"] += v1_blocked
            reasons.update(f"attack:block:{v.reason}" for v in verdicts)
            if not blocked:
                fails[(split, "attack:block")].add(row["family_id"])
    for (split, branch), t in sorted(tallies.items()):
        out[f"{split}/{branch}"] = dict(sorted(t.items()))
    out["fail_families"] = {f"{s}/{k}": sorted(v) for (s, k), v in sorted(fails.items())}
    out["non_allow_reasons"] = dict(sorted(reasons.items()))
    out["allow_fail_by_variant"] = {f"{s}/{b}": dict(c) for (s, b), c in sorted(by_variant.items())}
    return out


def _score(result: dict[str, Any], split: str) -> tuple[float, float]:
    allow = sum(result.get(f"{split}/{b}", {}).get("c1_allow_ok", 0) for b in BRANCHES)
    need = sum(result.get(f"{split}/{b}", {}).get("need_allow", 0) for b in BRANCHES)
    att = result.get(f"{split}/attack", {})
    return allow / max(need, 1), att.get("c1_block_ok", 0) / max(att.get("need_block", 1), 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--grid", action="store_true", help="evaluate every IntentConfig choice")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/rebuild_c/intent_policy_v1_dev_eval.json")
    args = parser.parse_args()
    rows, oracles, val = _load()
    configs = [IntentConfig()]
    if args.grid:
        configs = [IntentConfig(conditional=c, quoted=q, reported=r, ambiguous_negation=a,
                                require_verb=v)
                   for c, q, r, a, v in itertools.product(("allow", "confirm"),
                                                         ("mention", "grant"),
                                                         ("mention", "grant"),
                                                         ("confirm", "ignore"), (True, False))]
    report: dict[str, Any] = {"release": "dev4_1", "profile": "intent_policy_v1", "runs": []}
    for cfg in configs:
        result = evaluate(rows, oracles, val, cfg)
        report["runs"].append({"config": cfg.__dict__, "result": result})
        for split in ("train", "val"):
            allow, block = _score(result, split)
            print(f"{split:5s} allow={allow:.3f} block={block:.3f} {cfg.__dict__}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if not args.grid:
        print(json.dumps(report["runs"][0]["result"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
