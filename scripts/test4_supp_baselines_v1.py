"""Supplementary baselines R1, D2, P1, MEL, G1 on Test-4 (decision log 2026-11-19 00:25).

Counts only, same metrics as ``test4_analysis_v1.py``; the comparison with v3 (pooled McNemar) is
exploratory, added after the Test-4 results were known, outside H1-H4. Writes
``results/rebuild_c/test4_supp_baselines_v1.json``.
"""

from __future__ import annotations

import json
from typing import Any

import test4_analysis_v1 as t4a

SUPP = ["R1", "D2", "P1", "MEL", "G1"]


def row(cfg: str) -> dict[str, Any]:
    union: set[str] = set()
    per: dict[str, Any] = {}
    plain = [0, 0]
    auth = [0, 0]
    for m in t4a.MODELS:
        s, recs = t4a.summary(cfg, m), t4a.t4(cfg, m)
        union |= t4a.harmed(recs, "harm_transformed")
        per[m] = {
            "harmful_families": s["attack_harmful_families_transformed"],
            "sink_violations": s["attack_sink_violations"],
            "utility_plain": s["benign_plain_utility"],
            "utility_auth": s["benign_auth_utility"],
            "false_block": s["false_block_any_denial"],
            "statuses": s["statuses"],
            "cost_all": t4a.cost(recs),
        }
        for acc, key in ((plain, "utility_plain"), (auth, "utility_auth")):
            k, n = t4a.ratio(per[m][key])
            acc[0] += k
            acc[1] += n
    return {
        "families_harmed_pooled": len(union),
        "utility_plain_pooled": f"{plain[0]}/{plain[1]}",
        "utility_auth_pooled": f"{auth[0]}/{auth[1]}",
        "vs_v3_exploratory": t4a.family_test(cfg, "V3P2", "harm_transformed")[
            "pooled_any_backbone"
        ],
        "per_backbone": per,
    }


def main() -> None:
    rows = {cfg: row(cfg) for cfg in SUPP}
    out: dict[str, Any] = {"note": "supplementary, outside H1-H4 (decision log 2026-11-19 00:25)"}
    out.update(rows)
    path = t4a.RC / "test4_supp_baselines_v1.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    for cfg, r in rows.items():
        v = r["vs_v3_exploratory"]
        per = {
            m: (b["harmful_families"], b["sink_violations"], b["utility_plain"], b["false_block"])
            for m, b in r["per_backbone"].items()
        }
        print(cfg, r["families_harmed_pooled"], r["utility_plain_pooled"], r["utility_auth_pooled"])
        print("  vs v3", v["reference"], v["v3"], v.get("p_one_sided"), per)


if __name__ == "__main__":
    main()
