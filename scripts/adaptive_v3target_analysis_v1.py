"""Adaptive round against v3 on Dev-val (decision log 2026-11-18 20:55): counts only.

42 owner/Minh fixtures (one per Dev-val family, sha b348dcf8...) under A0, v1 (D2P2) and
v3 (V3P2) x 3 backbones, compared family by family with the canonical attack of the same
family in the Dev v4.1 runs of the same configuration. Reported separately, descriptive.
Writes ``results/rebuild_c/adaptive_v3target_v1.json``.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

RC = Path(__file__).resolve().parents[1] / "results/rebuild_c"
MODELS = ["qwen35_9b", "gemma4_12b", "llama31_8b"]
CONFIGS = ["A0", "D2P2", "V3P2"]


def recs(name: str) -> list[dict[str, Any]]:
    return list(json.loads((RC / f"{name}_eval_v2.json").read_text())["records"])


def harm_kinds(r: dict[str, Any]) -> list[str]:
    s = r["score"]
    out = []
    if s.get("sink_violations"):
        out.append("sink")
    if s.get("tampered"):
        out.append("tamper")
    if s.get("leaked"):
        out.append("final_leak")
    return out


def main() -> None:
    out: dict[str, Any] = {
        "note": "adaptive v3-target, Dev-val, descriptive (decision log 2026-11-18 20:55)"
    }
    for cfg in CONFIGS:
        row: dict[str, Any] = {}
        union_adv: set[str] = set()
        union_can: set[str] = set()
        for m in MODELS:
            adv = [r for r in recs(f"dev4_1_adv3_{cfg}_{m}") if r["branch"] == "attack"]
            fams = {r["family_id"] for r in adv}
            can = [
                r
                for r in recs(f"dev4_1_{cfg}_{m}")
                if r["branch"] == "attack"
                and r["family_id"] in fams
                and r["variant_type"] == "canonical"
            ]
            h_adv = {r["family_id"] for r in adv if r["score"]["harm_transformed"]}
            h_can = {r["family_id"] for r in can if r["score"]["harm_transformed"]}
            union_adv |= h_adv
            union_can |= h_can
            kinds = Counter(k for r in adv if r["score"]["harm_transformed"] for k in harm_kinds(r))
            denials: Counter[str] = Counter()
            for r in adv:
                for reason, n in r["metrics"]["gate"]["non_allow_reasons"].items():
                    denials[reason.split(":")[0]] += n
            row[m] = {
                "adaptive_harmed": len(h_adv),
                "canonical_harmed": len(h_can),
                "n_adaptive": len(adv),
                "n_canonical_families": len({r["family_id"] for r in can}),
                "only_adaptive": sorted(h_adv - h_can),
                "only_canonical": sorted(h_can - h_adv),
                "harm_kinds_adaptive": dict(kinds),
                "statuses_adaptive": dict(Counter(r["score"]["status"] for r in adv)),
                "gate_non_allow_by_rule": dict(denials),
            }
        row["pooled_families"] = {"adaptive": len(union_adv), "canonical": len(union_can)}
        out[cfg] = row
    (RC / "adaptive_v3target_v1.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    )
    for cfg in CONFIGS:
        r = out[cfg]
        print(
            cfg,
            r["pooled_families"],
            {
                m: (
                    r[m]["adaptive_harmed"],
                    r[m]["canonical_harmed"],
                    r[m]["n_canonical_families"],
                    r[m]["harm_kinds_adaptive"],
                )
                for m in MODELS
            },
        )
        print("   statuses", {m: r[m]["statuses_adaptive"] for m in MODELS})
        print("   gate", {m: r[m]["gate_non_allow_by_rule"] for m in MODELS})


if __name__ == "__main__":
    main()
