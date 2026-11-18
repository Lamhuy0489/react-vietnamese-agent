"""Gemini 3 Flash reference column on Test-4 (decision log 2026-11-18 19:30): counts only, no tests.

Reads the frozen ``test4[_adaptive]_<cfg>_gemini3_flash_eval_v3.json`` and writes
``results/rebuild_c/test4_gemini_ref_v1.json``. Same metrics as ``test4_analysis_v1.py``.
"""

from __future__ import annotations

import json
from typing import Any

import test4_analysis_v1 as t4a

RC = t4a.RC
MODEL = "gemini3_flash"
CONFIGS = ["A0", "P2", "PRG", "D2P2", "V3P2"]


def main() -> None:
    out: dict[str, Any] = {
        "model": MODEL,
        "note": "reference column, not tested (decision log 19:30)",
    }
    rows: dict[str, Any] = {}
    for cfg in CONFIGS:
        recs = t4a.t4(cfg, MODEL)
        s = t4a.summary(cfg, MODEL)
        adv = t4a.t4(cfg, MODEL, adaptive=True)
        rows[cfg] = {
            "families_harmed_transformed": len(t4a.harmed(recs, "harm_transformed")),
            "families_harmed_verbatim": len(t4a.harmed(recs, "side_effect_harm_v3")),
            "sink_violations": s["attack_sink_violations"],
            "utility_plain": s["benign_plain_utility"],
            "utility_auth": s["benign_auth_utility"],
            "false_block": s["false_block_any_denial"],
            "confirmation_benign": s["confirmation_rate_benign"],
            "cost_all": t4a.cost(recs),
            "adaptive24_harmed_fixtures": sum(
                1 for r in adv if r["branch"] == "attack" and r["score"]["harm_transformed"]
            ),
            "statuses": s["statuses"],
        }
    out["configs"] = rows
    v1, v3 = (t4a.harmed(t4a.t4(c, MODEL), "harm_transformed") for c in ("D2P2", "V3P2"))
    out["v1_vs_v3_families"] = {
        "only_v1": sorted(v1 - v3),
        "only_v3": sorted(v3 - v1),
        "both": sorted(v1 & v3),
    }
    path = RC / "test4_gemini_ref_v1.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(out, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
