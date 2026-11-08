#!/usr/bin/env python3
"""WP8 summary: adaptive Dev attack fixtures (owner/Minh) vs static Dev attack, same families.

Reads ``results/rebuild_b/v3_dev_<cfg>_adaptive_<model>_eval.json`` (48 attack fixtures, one
per family) and the static ``v3_dev_<CFG>_<model>_eval.json``. Prints counts only (no fixture
text): harmful families /48 per mechanism for adaptive, static CANONICAL, static any-variant.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "results/rebuild_b"
CONFIGS = ("A0", "D2P2", "D2SAN", "D2P2SAN", "SAN")
MECHS = ("M1", "M2", "M3", "M4", "M5", "M6")


def harmful(path: Path, variant: str | None) -> dict[str, set[str]] | None:
    if not path.exists():
        return None
    out: dict[str, set[str]] = defaultdict(set)
    for r in json.loads(path.read_text(encoding="utf-8"))["records"]:
        if r["branch"] != "attack" or (variant and not r["variant_id"].endswith("_" + variant)):
            continue
        out["_all"].add(r["family_id"])  # families seen
        if r["score"]["side_effect_harm_v3"]:
            out[r["mechanism"]].add(r["family_id"])
    return out


def fmt(h: dict[str, set[str]] | None) -> dict[str, object] | None:
    if h is None:
        return None
    total = sum(len(h[m]) for m in MECHS)
    return {"harmful_families": f"{total}/{len(h['_all'])}", **{m: len(h[m]) for m in MECHS}}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--models", nargs="+", default=["gemma4_12b", "llama31_8b", "qwen35_9b"])
    p.add_argument("--tag", default="adaptive", help="adaptive (round 1) or adaptive2")
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    out: dict[str, dict[str, dict[str, dict[str, object] | None]]] = {}
    for model in args.models:
        for cfg in CONFIGS:
            static = ROOT / f"v3_dev_{cfg}_{model}_eval.json"
            adaptive = ROOT / f"v3_dev_{cfg.lower()}_{args.tag}_{model}_eval.json"
            row = {"adaptive": fmt(harmful(adaptive, None)),
                   "static_canonical": fmt(harmful(static, "CANONICAL")),
                   "static_any_variant": fmt(harmful(static, None))}
            out.setdefault(model, {})[cfg] = row
    text = json.dumps(out, indent=1)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    for model, rows in out.items():
        for cfg, row in rows.items():
            parts = []
            for k, v in row.items():
                if isinstance(v, dict):
                    mechs = " ".join(f"{m}={v[m]}" for m in MECHS)
                    parts.append(f"{k}: {v['harmful_families']} {mechs}")
                else:
                    parts.append(f"{k}: -")
            print(model, cfg, " | ".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
