#!/usr/bin/env python3
"""Per-variant breakdown of Dev v3 results (Study 2): canonical vs paraphrase, no_diacritic,
code_mix, english. Same families, same oracles, so the variants compare languages under
control. Reads ``results/rebuild_b/v3_dev_<CONFIG>_<model>_eval.json``; prints counts only.

Harmful = attack fixtures (one per family per variant, /48) with ``side_effect_harm_v3``;
utility = benign_plain fixtures with ``utility`` (/48 per variant).
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("CANONICAL", "PARAPHRASE", "NO_DIACRITIC", "CODE_MIX", "ENGLISH")


def breakdown(path: Path) -> dict[str, dict[str, str]]:
    records = json.loads(path.read_text(encoding="utf-8"))["records"]
    harm: dict[str, list[bool]] = defaultdict(list)
    util: dict[str, list[bool]] = defaultdict(list)
    for r in records:
        variant = next((v for v in VARIANTS if r["variant_id"].endswith("_" + v)), None)
        if variant is None:
            continue
        if r["branch"] == "attack":
            harm[variant].append(bool(r["score"]["side_effect_harm_v3"]))
        elif r["branch"] == "benign_plain":
            util[variant].append(bool(r["score"]["utility"]))
    return {v: {"harmful": f"{sum(harm[v])}/{len(harm[v])}",
                "plain_utility": f"{sum(util[v])}/{len(util[v])}"} for v in VARIANTS if harm[v]}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--configs", nargs="+", default=["A0", "P2", "PRG", "D2", "D2P2"])
    p.add_argument("--models", nargs="+",
                   default=["gemma4_12b", "llama31_8b", "qwen35_9b", "qwen3_8b",
                            "qwen36_35b_a3b_awq", "secalign_8b"])
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    out: dict[str, dict[str, dict[str, dict[str, str]]]] = {}
    for config in args.configs:
        for model in args.models:
            path = ROOT / f"results/rebuild_b/v3_dev_{config}_{model}_eval.json"
            if path.exists():
                out.setdefault(config, {})[model] = breakdown(path)
    text = json.dumps(out, indent=1, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
