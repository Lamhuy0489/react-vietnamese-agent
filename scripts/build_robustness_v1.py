#!/usr/bin/env python3
"""Build and QA the 250 RQ3 clean robustness variants (review pending, not sealed)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.authoring.robustness_v1 import OUTPUT, build

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write variants.jsonl")
    args = parser.parse_args()
    rows, report = build(ROOT)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["problems"] or report["duplicates"] or len(rows) != 250:
        return 1
    if args.write:
        (ROOT / OUTPUT).write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
