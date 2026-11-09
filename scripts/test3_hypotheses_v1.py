#!/usr/bin/env python3
"""Study 2 Test-3: pre-registered T1-T3 from ``final_config_v4`` (aggregates only, no text).

Reads ``results/rebuild_b/v3_test3_<CFG>_<model>_eval.json`` (CFG in A0, D2P2, D3DEST) for
the Tier 1 backbones; pairs are the same fixture under two configurations, pooled over the
three backbones. Helpers (exact McNemar, family bootstrap, clustered z) are those of
``test_v3_hypotheses_v1.py``.

- T1 D3 > D2P2, benign utility (benign_plain + benign_auth): one-sided exact McNemar.
- T2 D3 attack harm not higher than D2P2 by more than 2 points: one-sided z test with a
  family-clustered SE, H0: harm(D3) - harm(D2P2) >= 0.02.
- T3 D3 < A0, attack harm: one-sided exact McNemar.
- Holm over T1-T3; 95% bootstrap CI by family (10,000 resamples, seed 20261110);
  model_error counts as failure (utility False, not harmful).
Secondary rows (not in Holm): T1 by benign branch, per-backbone cells.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "h3", Path(__file__).with_name("test_v3_hypotheses_v1.py"))
if _spec is None or _spec.loader is None:
    raise SystemExit("test_v3_hypotheses_v1.py not found")
h3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h3)

RES = Path("/Users/huylam/Downloads/Do an tot nghiep/results/rebuild_b")
MODELS = h3.MODELS
SEED = 20261110
Pair = tuple[str, int, int]


def load(cfg: str, model: str) -> dict[str, dict[str, Any]]:
    data = json.loads((RES / f"v3_test3_{cfg}_{model}_eval.json").read_text(encoding="utf-8"))
    if data["executions"] != 560 or data["split"] != "test3":
        raise SystemExit(f"{cfg} {model}: {data['executions']} executions, split {data['split']}")
    return {r["variant_id"]: r for r in data["records"]}


def pairs(a: str, b: str, branches: set[str], metric: Any, models: tuple[str, ...] = MODELS,
          ) -> list[Pair]:
    out: list[Pair] = []
    for m in models:
        ra, rb = load(a, m), load(b, m)
        for vid, x in ra.items():
            if x["branch"] in branches:
                out.append((m + ":" + x["family_id"], int(metric(x)), int(metric(rb[vid]))))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resamples", type=int, default=10_000)
    p.add_argument("--output", type=Path, default=RES / "v3_test3_hypotheses.json")
    args = p.parse_args()

    def row(name: str, desc: str, ps: list[Pair], sided: str, pval: float) -> dict[str, Any]:
        b = sum(1 for _, x, y in ps if y and not x)
        c = sum(1 for _, x, y in ps if x and not y)
        n = len(ps)
        # families resampled jointly across backbones: strip the model prefix for clustering
        fam = [(f.split(":", 1)[1], x, y) for f, x, y in ps]
        lo, hi = h3.boot(fam, args.resamples, seed=SEED)
        return {"id": name, "desc": desc, "n_pairs": n,
                "rate_first": sum(x for _, x, _ in ps) / n,
                "rate_second": sum(y for _, _, y in ps) / n,
                "diff_second_minus_first": (b - c) / n, "ci95": [lo, hi],
                "discordant_second_only": b, "discordant_first_only": c, "sided": sided, "p": pval}

    benign = {"benign_plain", "benign_auth"}
    t1 = pairs("D2P2", "D3DEST", benign, h3.util)
    b1 = sum(1 for _, x, y in t1 if y and not x)
    c1 = sum(1 for _, x, y in t1 if x and not y)
    t2 = pairs("D2P2", "D3DEST", {"attack"}, h3.harm)
    # swapped order: H0 harm(D3) - harm(D2P2) >= margin
    t2_fam = [(f.split(":", 1)[1], y, x) for f, x, y in t2]
    t3 = pairs("A0", "D3DEST", {"attack"}, h3.harm)
    b3 = sum(1 for _, x, y in t3 if y and not x)
    c3 = sum(1 for _, x, y in t3 if x and not y)
    tests = [
        row("T1", "benign utility D2P2 -> D3DEST (D3 > D2P2)", t1, "greater",
            h3.mcnemar(c1, b1, "less")),
        row("T2", "attack harm D2P2 -> D3DEST (D3 not worse by > 2 pts)", t2, "noninferiority",
            h3.noninferiority(t2_fam, 0.02)),
        row("T3", "attack harm A0 -> D3DEST (D3 < A0)", t3, "less", h3.mcnemar(b3, c3, "less")),
    ]
    order = sorted(range(3), key=lambda i: tests[i]["p"])
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (3 - rank) * tests[i]["p"]))
        tests[i]["p_holm"] = running
        tests[i]["reject_at_0.05"] = running < 0.05
    secondary = []
    for br in ("benign_plain", "benign_auth"):
        ps = pairs("D2P2", "D3DEST", {br}, h3.util)
        b = sum(1 for _, x, y in ps if y and not x)
        c = sum(1 for _, x, y in ps if x and not y)
        secondary.append(row("T1_" + br, f"{br} utility D2P2 -> D3DEST", ps, "greater",
                             h3.mcnemar(c, b, "less")))
    ps = pairs("A0", "D2P2", {"attack"}, h3.harm)
    b = sum(1 for _, x, y in ps if y and not x)
    c = sum(1 for _, x, y in ps if x and not y)
    secondary.append(row("S_D2P2_A0", "attack harm A0 -> D2P2 (replication)", ps, "less",
                         h3.mcnemar(b, c, "less")))
    cells = []
    for cfg in ("A0", "D2P2", "D3DEST"):
        for m in MODELS:
            raw = json.loads((RES / f"v3_test3_{cfg}_{m}_eval.json").read_text())
            s = next(iter(raw["summary"].values()))
            cells.append({"config": cfg, "model": m, **{k: s[k] for k in (
                "attack_harmful_families", "attack_harmful_fixtures", "attack_executed_violation",
                "attack_tampered", "benign_plain_utility", "benign_plain_harmful",
                "benign_auth_utility", "statuses")}})
    result = {"split": "test3", "config": "final_config_v4", "models": MODELS, "tests": tests,
              "secondary": secondary, "cells": cells}
    args.output.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    for t in tests + secondary:
        lo, hi = t["ci95"]
        verdict = "REJECT H0" if t.get("reject_at_0.05") else "not rejected"
        holm = f" holm {t['p_holm']:.2e} {verdict}" if "p_holm" in t else ""
        print(f"{t['id']} {t['desc']}: {t['rate_first']:.3f} -> {t['rate_second']:.3f} "
              f"diff {t['diff_second_minus_first']:+.3f} CI [{lo:+.3f}, {hi:+.3f}] "
              f"b/c {t['discordant_second_only']}/{t['discordant_first_only']} "
              f"p {t['p']:.2e}{holm}")
    for cell in cells:
        print(cell["config"], cell["model"],
              {k: v for k, v in cell.items() if k not in ("config", "model")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
