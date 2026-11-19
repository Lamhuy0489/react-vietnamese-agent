"""Dev v4.1 supplementary baselines (decision log 2026-11-19 00:25): counts per config and model.

Reads ``results/rebuild_c/dev4_1_<cfg>_<model>_eval_v2.json`` for the supplementary configs R1, D2,
P1, MEL, G1 and the reference rows A0, D2P2 (v1), V3P2 (v3); writes
``results/rebuild_c/dev4_1_supp_baselines_v1.json``. Descriptive only (Dev v4.1 is in-sample
for v3).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "rebuild_c"
MODELS = ("qwen35_9b", "gemma4_12b", "llama31_8b")
CONFIGS = ("A0", "R1", "D2", "P1", "MEL", "G1", "D2P2", "V3P2")
KEYS = (
    "attack_harmful_families_transformed",
    "attack_harmful_fixtures_transformed",
    "benign_plain_utility",
    "false_block_any_denial",
)


def frac(text: str) -> tuple[int, int]:
    a, b = text.split("/")
    return int(a), int(b)


def main() -> None:
    out: dict[str, Any] = {}
    for cfg in CONFIGS:
        row: dict[str, Any] = {}
        pooled = {k: [0, 0] for k in KEYS}
        for m in MODELS:
            d = json.loads((RES / f"dev4_1_{cfg}_{m}_eval_v2.json").read_text())
            if d["executions"] != 1960:
                raise SystemExit(f"{cfg} {m}: {d['executions']} executions")
            (s,) = d["summary"].values()
            row[m] = {k: s[k] for k in KEYS} | {"statuses": s["statuses"]}
            for k in KEYS:
                a, b = frac(s[k])
                pooled[k][0] += a
                pooled[k][1] += b
        row["pooled"] = {k: f"{a}/{b}" for k, (a, b) in pooled.items()}
        out[cfg] = row
    text = json.dumps(out, indent=2, ensure_ascii=False)
    (RES / "dev4_1_supp_baselines_v1.json").write_text(text)
    for cfg, row in out.items():
        print(cfg, row["pooled"], *(row[m]["attack_harmful_families_transformed"] for m in MODELS))


if __name__ == "__main__":
    main()
