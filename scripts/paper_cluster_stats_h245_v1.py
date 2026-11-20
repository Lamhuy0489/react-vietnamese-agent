#!/usr/bin/env python3
"""Paper revision (review 2, item 4.6): family-level tests for H2, H4 and H5 on Test-I.

Completes ``paper_cluster_stats_v1.py`` (H1, H3, H6 at family level) so all six pre-registered
hypotheses use the same unit before Holm. Reads only evaluator outputs; no fixture text.
- H2 (non-inferiority, margin 5 points): benign_plain utility A0 -> D2. Cluster sign-flip
  permutation test of H0: mean difference <= -5 points (differences shifted by +0.05), one-sided;
  95% family bootstrap CI as before.
- H4, H5 (two-sided): A0 attack harm, CANONICAL vs NO_DIACRITIC / ENGLISH, paired by
  (backbone, family); exact McNemar on family "any harmful" units and cluster permutation.
"""

from __future__ import annotations

import importlib.util
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("pcs", _HERE / "paper_cluster_stats_v1.py")
if _spec is None or _spec.loader is None:
    raise SystemExit("cannot load paper_cluster_stats_v1.py")
pcs: Any = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pcs)

MARGIN = 0.05
RESAMPLES = 10_000


def variant_rows(variant: str) -> list[tuple[str, str, int, int]]:
    out = []
    for m in pcs.MODELS:
        recs = pcs.load("test", "A0", m)
        for vid, r in recs.items():
            if r["branch"] == "attack" and vid.endswith("_CANONICAL"):
                other = recs[vid[: -len("CANONICAL")] + variant]
                out.append((m, r["family_id"], pcs.harm(r), pcs.harm(other)))
    return out


def noninferiority(rs: list[tuple[str, str, int, int]]) -> dict[str, Any]:
    by: dict[str, list[float]] = defaultdict(list)
    for _, f, x, y in rs:
        by[f].append(y - x + MARGIN)
    sums = [sum(v) for v in by.values()]
    obs = sum(sums)
    rng = random.Random(pcs.SEED)  # noqa: S311 (resampling, not crypto)
    hits = sum(sum(s if rng.random() < 0.5 else -s for s in sums) >= obs for _ in range(RESAMPLES))
    p = (hits + 1) / (RESAMPLES + 1)
    return {"margin": MARGIN, "shifted_mean": obs / len(rs), "perm_p_one_sided": p}


def main() -> int:
    out: dict[str, Any] = {}
    plain = pcs.rows("test", "A0", "D2", {"benign_plain"}, pcs.util)
    h2 = pcs.analyse(plain, RESAMPLES, "two")
    h2["noninferiority"] = noninferiority(plain)
    out["H2"] = h2
    for name, variant in (("H4", "NO_DIACRITIC"), ("H5", "ENGLISH")):
        out[name] = pcs.analyse(variant_rows(variant), RESAMPLES, "two")
    for k, v in out.items():
        fa, lo_hi = v["family_any"], v["ci95_family_bootstrap"]
        extra = v.get("noninferiority", {})
        print(f"{k}: {v['rate_first']:.3f}->{v['rate_second']:.3f} diff {v['diff']:+.3f} "
              f"CI[{lo_hi[0]:+.3f},{lo_hi[1]:+.3f}] "
              f"fam {fa['first']}->{fa['second']}/{fa['units']} "
              f"b/c {fa['b_second_only']}/{fa['c_first_only']} p {fa['p']:.3f} "
              f"perm {v['cluster_permutation_p']:.3f} DEFF {v['design_effect']:.2f} {extra}")
    (pcs.RES / "paper_cluster_stats_h245_v1.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
