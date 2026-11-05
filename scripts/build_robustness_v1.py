#!/usr/bin/env python3
"""Build, QA or seal the 250 RQ3 clean robustness variants (decision log 2026-10-26).

``--seal`` writes ``review_status=approved`` and seal.json; afterwards ``--write`` refuses.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.authoring.robustness_v1 import OUTPUT, SEAL, build, load_sealed, seal

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write variants.jsonl")
    parser.add_argument("--seal", metavar="APPROVED_BY", help="approve and seal")
    parser.add_argument("--check", action="store_true", help="verify the sealed release")
    args = parser.parse_args()
    if args.check:
        print("sealed robustness v1 OK:", len(load_sealed(ROOT)), "variants")
        return 0
    if args.seal:
        print(json.dumps(seal(ROOT, args.seal), ensure_ascii=False, indent=1))
        return 0
    rows, report = build(ROOT)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["problems"] or report["duplicates"] or len(rows) != 250:
        return 1
    if args.write:
        if (ROOT / SEAL).exists():
            raise SystemExit("sealed: variants.jsonl must not be rewritten")
        (ROOT / OUTPUT).write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
