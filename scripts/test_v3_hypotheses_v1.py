#!/usr/bin/env python3
"""Study 2 Test v3: pre-registered H1-H6 from ``final_config_v3`` (aggregates only, no text).

Reads ``results/rebuild_b/v3_test_<CFG>_<model>_eval.json`` for the Tier 1 backbones.
Pairs are the same fixture (``variant_id``) under two configurations, or, for H4/H5, the
same family under two variants at A0; pairs are pooled over the three backbones.

- H1, H3, H6 (one-sided, as declared "<"): exact McNemar on discordant pairs.
- H4, H5 (two-sided, "!="): exact McNemar.
- H2 (non-inferiority, margin 5 points): one-sided z test on the paired utility difference
  with a family-clustered standard error, H0: diff <= -0.05.
- Holm over H1-H6; 95% bootstrap CI of each difference by family (10,000 resamples,
  families resampled jointly across backbones). model_error counts as failure (utility
  False; not harmful), as scored by ``evaluate_v3_v1.py``.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results/rebuild_b"
MODELS = ("gemma4_12b", "llama31_8b", "qwen35_9b")
CONFIGS = ("A0", "R1", "P2", "PRG", "D2", "D2P2")


def load(cfg: str, model: str) -> dict[str, dict[str, Any]]:
    data = json.loads((RES / f"v3_test_{cfg}_{model}_eval.json").read_text(encoding="utf-8"))
    if data["executions"] != 840 or data["split"] != "test":
        raise SystemExit(f"{cfg} {model}: {data['executions']} executions, split {data['split']}")
    return {r["variant_id"]: r for r in data["records"]}


def harm(r: dict[str, Any]) -> bool:
    return bool(r["score"]["side_effect_harm_v3"])


def util(r: dict[str, Any]) -> bool:
    return bool(r["score"]["utility"])


def binom_tail(k: int, n: int) -> float:
    """P(X <= k), X ~ Bin(n, 1/2)."""
    return sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n if n else 1.0


def mcnemar(b: int, c: int, sided: str) -> float:
    """b: pairs where only the second condition is 1, c: only the first. One-sided tests b < c."""
    if sided == "less":
        return binom_tail(b, b + c)
    return min(1.0, 2 * binom_tail(min(b, c), b + c))


Pair = tuple[str, int, int]  # (family, x first condition, y second condition)


def boot(pairs: list[Pair], n: int, seed: int = 20261109) -> tuple[float, float]:
    by: dict[str, list[int]] = defaultdict(list)
    for fam, x, y in pairs:
        by[fam].append(y - x)
    fams = sorted(by)
    rng = random.Random(seed)  # noqa: S311 (bootstrap, not crypto)
    stats = []
    for _ in range(n):
        pick = [rng.choice(fams) for _ in fams]
        d = [v for f in pick for v in by[f]]
        stats.append(sum(d) / len(d))
    stats.sort()
    return stats[int(0.025 * n)], stats[int(0.975 * n) - 1]


def noninferiority(pairs: list[Pair], margin: float) -> float:
    by: dict[str, list[int]] = defaultdict(list)
    for fam, x, y in pairs:
        by[fam].append(y - x)
    n = len(pairs)
    mean = sum(v for d in by.values() for v in d) / n
    # cluster-robust variance of the mean (families as clusters)
    var = sum((sum(d) - len(d) * mean) ** 2 for d in by.values()) / n ** 2
    var *= len(by) / (len(by) - 1)
    z = (mean + margin) / math.sqrt(var) if var > 0 else math.inf
    return 0.5 * math.erfc(z / math.sqrt(2))


def config_pairs(a: str, b: str, branch: str, metric: Any, mechs: set[str] | None = None,
                 ) -> list[Pair]:
    out: list[Pair] = []
    for m in MODELS:
        ra, rb = load(a, m), load(b, m)
        for vid, x in ra.items():
            if x["branch"] != branch or (mechs and x["mechanism"] not in mechs):
                continue
            out.append((x["family_id"], int(metric(x)), int(metric(rb[vid]))))
    return out


def variant_pairs(variant: str) -> list[Pair]:
    out: list[Pair] = []
    for m in MODELS:
        recs = load("A0", m)
        for vid, x in recs.items():
            if x["branch"] == "attack" and vid.endswith("_CANONICAL"):
                other = recs[vid.replace("_CANONICAL", "_" + variant)]
                out.append((x["family_id"], int(harm(x)), int(harm(other))))
    return out


def table() -> list[dict[str, Any]]:
    rows = []
    for c in CONFIGS:
        for m in MODELS:
            s = json.loads((RES / f"v3_test_{c}_{m}_eval.json").read_text())["summary"]
            lvl = next(iter(s.values()))
            rows.append({"config": c, "model": m, **{k: lvl[k] for k in (
                "attack_harmful_families", "attack_harmful_fixtures", "attack_executed_violation",
                "attack_tampered", "benign_plain_utility", "benign_plain_harmful",
                "benign_auth_utility")}})
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resamples", type=int, default=10_000)
    p.add_argument("--output", type=Path, default=RES / "v3_test_hypotheses.json")
    args = p.parse_args()
    tests: list[dict[str, Any]] = []

    def add(name: str, desc: str, pairs: list[Pair], sided: str, pval: float | None = None,
            ) -> None:
        b = sum(1 for _, x, y in pairs if y and not x)
        c = sum(1 for _, x, y in pairs if x and not y)
        n = len(pairs)
        lo, hi = boot(pairs, args.resamples)
        tests.append({
            "id": name, "desc": desc, "n_pairs": n,
            "rate_first": sum(x for _, x, _ in pairs) / n,
            "rate_second": sum(y for _, _, y in pairs) / n,
            "diff_second_minus_first": (b - c) / n, "ci95": [lo, hi],
            "discordant_second_only": b, "discordant_first_only": c, "sided": sided,
            "p": mcnemar(b, c, sided) if pval is None else pval})

    add("H1", "attack harm: R1 -> D2 (D2 < R1)", config_pairs("R1", "D2", "attack", harm), "less")
    plain = config_pairs("A0", "D2", "benign_plain", util)
    add("H2", "benign_plain utility: A0 -> D2 (non-inferior, margin 5 pts)", plain,
        "noninferiority", noninferiority(plain, 0.05))
    add("H3", "attack harm on M2|M3|M4: R1 -> D2", config_pairs(
        "R1", "D2", "attack", harm, {"M2", "M3", "M4"}), "less")
    add("H4", "A0 attack harm: CANONICAL -> NO_DIACRITIC", variant_pairs("NO_DIACRITIC"), "two")
    add("H5", "A0 attack harm: CANONICAL -> ENGLISH", variant_pairs("ENGLISH"), "two")
    add("H6", "attack harm: P2 -> D2P2 (D2P2 < P2)", config_pairs("P2", "D2P2", "attack", harm),
        "less")
    order = sorted(range(len(tests)), key=lambda i: tests[i]["p"])
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(tests) - rank) * tests[i]["p"]))
        tests[i]["p_holm"] = running
        tests[i]["reject_at_0.05"] = running < 0.05
    result = {"split": "test", "models": MODELS, "tests": tests, "cells": table()}
    args.output.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    for t in tests:
        print(f"{t['id']} {t['desc']}: {t['rate_first']:.3f} -> {t['rate_second']:.3f} "
              f"diff {t['diff_second_minus_first']:+.3f} CI [{t['ci95'][0]:+.3f}, "
              f"{t['ci95'][1]:+.3f}] b/c {t['discordant_second_only']}/"
              f"{t['discordant_first_only']} p {t['p']:.2e} holm {t['p_holm']:.2e} "
              f"{'REJECT H0' if t['reject_at_0.05'] else 'not rejected'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
