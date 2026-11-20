#!/usr/bin/env python3
"""Paper revision (reviewer B1/C9): family-level statistics and a deny-all-sinks reference.

Reads only aggregate evaluator outputs ``results/rebuild_b/v3_<split>_<CFG>_<model>_eval.json``
and, for deny-all, the tool *names* in NoDef (A0) traces; no fixture text is read or printed.

For each comparison (first -> second configuration, pooled over the three backbones):
- fixture level: rates, discordant pairs, exact McNemar (as in the pre-registered scripts);
- family level: unit = family (any fixture of the family on any backbone), exact McNemar;
  unit = (backbone, family), exact McNemar (the "/144" counts in the paper);
- cluster sign-flip permutation test on per-family summed differences (families pooled over
  backbones), and the design effect DEFF = cluster-robust var / naive var of the mean difference;
- 95% family bootstrap CI (10,000 resamples), as before.
Deny-all-sinks: benign success = A0 utility and no sink call executed; attack harm = A0 harm
with no sink call executed (answer-channel leaks, which blocking sinks does not stop).
This is an estimate (the model might act differently after a denial). Not pre-registered.
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
RES = ROOT / "results" / "rebuild_b"
MODELS = ("gemma4_12b", "llama31_8b", "qwen35_9b")
SINKS = {"send_email_mock", "post_webhook_mock"}
SPLITS = {"test": ("v3_test", 840), "test3": ("v3_test3", 560)}
SEED = 20261113


def load(split: str, cfg: str, model: str) -> dict[str, dict[str, Any]]:
    prefix, n = SPLITS[split]
    data = json.loads((RES / f"{prefix}_{cfg}_{model}_eval.json").read_text(encoding="utf-8"))
    if data["executions"] != n:
        raise SystemExit(f"{split} {cfg} {model}: {data['executions']} executions")
    return {r["variant_id"]: r for r in data["records"]}


def harm(r: dict[str, Any]) -> int:
    return int(bool(r["score"]["side_effect_harm_v3"]))


def util(r: dict[str, Any]) -> int:
    return int(bool(r["score"]["utility"]))


def binom_le(k: int, n: int) -> float:
    return sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n if n else 1.0


def mcnemar_less(b: int, c: int) -> float:
    """One-sided: second condition lower (b = second-only, c = first-only)."""
    return binom_le(b, b + c)


def mcnemar_two(b: int, c: int) -> float:
    return min(1.0, 2 * binom_le(min(b, c), b + c))


Row = tuple[str, str, int, int]  # (model, family, x first, y second)


def rows(split: str, a: str, b: str, branches: set[str], metric: Any,
         mechs: set[str] | None = None) -> list[Row]:
    out: list[Row] = []
    for m in MODELS:
        ra, rb = load(split, a, m), load(split, b, m)
        for vid, x in ra.items():
            if x["branch"] in branches and (not mechs or x["mechanism"] in mechs):
                out.append((m, x["family_id"], metric(x), metric(rb[vid])))
    return out


def analyse(rs: list[Row], resamples: int, direction: str) -> dict[str, Any]:
    n = len(rs)
    b = sum(1 for *_, x, y in rs if y and not x)
    c = sum(1 for *_, x, y in rs if x and not y)
    by: dict[str, list[int]] = defaultdict(list)
    for _, f, x, y in rs:
        by[f].append(y - x)
    fams = sorted(by)
    mean = (b - c) / n
    # design effect of the mean paired difference, families as clusters
    naive = sum((d - mean) ** 2 for f in fams for d in by[f]) / (n - 1) / n
    robust = sum((sum(by[f]) - len(by[f]) * mean) ** 2 for f in fams) / n ** 2
    robust *= len(fams) / (len(fams) - 1)
    deff = robust / naive if naive > 0 else float("nan")
    rng = random.Random(SEED)  # noqa: S311 (resampling, not crypto)
    sums = [sum(by[f]) for f in fams]
    obs = sum(sums)
    hits = 0
    for _ in range(resamples):
        t = sum(s if rng.random() < 0.5 else -s for s in sums)
        hits += (t <= obs) if direction == "less" else (abs(t) >= abs(obs))
    perm_p = (hits + 1) / (resamples + 1)
    boots = []
    for _ in range(resamples):
        pick = [rng.choice(fams) for _ in fams]
        d = [v for f in pick for v in by[f]]
        boots.append(sum(d) / len(d))
    boots.sort()
    ci = (boots[int(0.025 * resamples)], boots[int(0.975 * resamples) - 1])

    def unit_test(key: Any) -> dict[str, Any]:
        first: dict[Any, int] = defaultdict(int)
        second: dict[Any, int] = defaultdict(int)
        for m, f, x, y in rs:
            k = key(m, f)
            first[k] |= x
            second[k] |= y
        bb = sum(1 for k in first if second[k] and not first[k])
        cc = sum(1 for k in first if first[k] and not second[k])
        p = mcnemar_less(bb, cc) if direction == "less" else mcnemar_two(bb, cc)
        return {"units": len(first), "first": sum(first.values()), "second": sum(second.values()),
                "b_second_only": bb, "c_first_only": cc, "p": p}

    fx_p = mcnemar_less(b, c) if direction == "less" else mcnemar_two(b, c)
    return {
        "n_fixtures": n, "n_families": len(fams),
        "rate_first": sum(x for *_, x, _ in rs) / n, "rate_second": sum(y for *_, y in rs) / n,
        "diff": mean, "ci95_family_bootstrap": ci,
        "fixture_mcnemar": {"b_second_only": b, "c_first_only": c, "p": fx_p},
        "family_any": unit_test(lambda m, f: f),
        "backbone_family_any": unit_test(lambda m, f: (m, f)),
        "cluster_permutation_p": perm_p, "design_effect": deff,
        "direction": direction,
    }


def deny_all(split: str) -> dict[str, Any]:
    prefix, _ = SPLITS[split]
    out: dict[str, Any] = {}
    tot = {"benign_plain": [0, 0, 0], "benign_auth": [0, 0, 0]}  # n, a0 util, deny-all util
    atk = [0, 0, 0]  # n, a0 harmful, harmful without any executed sink call
    for m in MODELS:
        recs = load(split, "A0", m)
        runs = RES / f"{prefix}_A0_{m}" / "runs" / "A0"
        for vid, r in recs.items():
            br = r["branch"]
            sink = False
            trace = runs / vid / "execution" / "trace_legacy.jsonl"
            if not trace.exists():
                raise SystemExit(f"missing trace {trace}")
            with trace.open(encoding="utf-8") as fh:
                proposed: dict[str, str] = {}
                for line in fh:
                    e = json.loads(line)
                    if e["event"] == "tool_call_proposed":
                        proposed[str(e["data"].get("call_id"))] = str(e["data"].get("name"))
                    elif e["event"] == "tool_call_executed":
                        if proposed.get(str(e.get("call_id"))) in SINKS:
                            sink = True
            if br == "attack":
                atk[0] += 1
                atk[1] += harm(r)
                atk[2] += int(harm(r) and not sink)
                continue
            t = tot[br]
            t[0] += 1
            t[1] += util(r)
            t[2] += int(util(r) and not sink)
    for br, (n, a0, da) in tot.items():
        out[br] = {"n": n, "a0_utility": a0, "deny_all_utility": da}
    n = sum(v[0] for v in tot.values())
    out["benign_total"] = {"n": n, "a0_utility": sum(v[1] for v in tot.values()),
                           "deny_all_utility": sum(v[2] for v in tot.values())}
    out["attack"] = {"n": atk[0], "a0_harmful": atk[1], "deny_all_harmful": atk[2]}
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resamples", type=int, default=10_000)
    p.add_argument("--output", type=Path, default=RES / "paper_cluster_stats_v1.json")
    args = p.parse_args()
    benign = {"benign_plain", "benign_auth"}
    comps = [
        ("test", "H1 harm R1 -> D2", "R1", "D2", {"attack"}, harm, None, "less"),
        ("test", "H3 harm R1 -> D2 (M2,M3,M4)", "R1", "D2", {"attack"}, harm,
         {"M2", "M3", "M4"}, "less"),
        ("test", "H6 harm P2 -> D2P2", "P2", "D2P2", {"attack"}, harm, None, "less"),
        ("test", "harm A0 -> D2P2", "A0", "D2P2", {"attack"}, harm, None, "less"),
        ("test", "benign utility A0 -> D2P2", "A0", "D2P2", benign, util, None, "two"),
        ("test3", "harm A0 -> D2P2", "A0", "D2P2", {"attack"}, harm, None, "less"),
        ("test3", "benign utility A0 -> D2P2", "A0", "D2P2", benign, util, None, "two"),
        ("test3", "benign_plain utility A0 -> D2P2", "A0", "D2P2", {"benign_plain"}, util,
         None, "two"),
        ("test3", "benign_auth utility A0 -> D2P2", "A0", "D2P2", {"benign_auth"}, util,
         None, "two"),
    ]
    result: dict[str, Any] = {"seed": SEED, "resamples": args.resamples, "comparisons": [],
                              "deny_all": {}}
    for split, name, a, b, brs, metric, mechs, direction in comps:
        res = analyse(rows(split, a, b, brs, metric, mechs), args.resamples, direction)
        res.update({"split": split, "name": name})
        result["comparisons"].append(res)
        fa, bf, fx = res["family_any"], res["backbone_family_any"], res["fixture_mcnemar"]
        lo, hi = res["ci95_family_bootstrap"]
        print(f"[{split}] {name}: {res['rate_first']:.3f}->{res['rate_second']:.3f} "
              f"diff {res['diff']:+.3f} CI[{lo:+.3f},{hi:+.3f}] | "
              f"fixture b/c {fx['b_second_only']}/{fx['c_first_only']} p {fx['p']:.1e} | "
              f"fam {fa['first']}->{fa['second']}/"
              f"{fa['units']} b/c {fa['b_second_only']}/{fa['c_first_only']} p {fa['p']:.1e} | "
              f"bb-fam {bf['first']}->{bf['second']}/{bf['units']} p {bf['p']:.1e} | "
              f"perm p {res['cluster_permutation_p']:.1e} DEFF {res['design_effect']:.2f}")
    for split in SPLITS:
        result["deny_all"][split] = deny_all(split)
        print(f"[{split}] deny-all:", result["deny_all"][split])
    args.output.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
