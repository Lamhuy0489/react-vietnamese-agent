#!/usr/bin/env python3
"""Build, check or seal the Test-2 release (design C; decision log 2026-10-28).

``build`` writes fixtures, private oracles and a QA/novelty report from the authored
canonicals; ``seal`` refuses while QA or novelty reports a problem and records hashes.
After the seal nothing under data/adversarial/release_test2 may change.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from react_agent.authoring import test2_v1

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "seal", "check"))
    parser.add_argument("--approved-by", default="")
    args = parser.parse_args()
    if args.action == "build":
        rows, privates = test2_v1.build_rows(ROOT)
        canonicals, _ = test2_v1.load_canonicals(ROOT)
        with tempfile.TemporaryDirectory() as scratch:
            report = {"qa": test2_v1.qa(ROOT, rows, privates, Path(scratch)),
                      "novelty": test2_v1.novelty(ROOT, canonicals)}
        test2_v1.write_release(ROOT, rows, privates, report)
        novelty = report["novelty"]
        print("fixtures", len(rows), "replays", report["qa"]["replays"],
              "problems", len(report["qa"]["problems"]))
        print("novelty max", novelty["max_observed"], "over", novelty["over_threshold"],
              "reused", novelty["reused_v1_literals"])
        for problem in report["qa"]["problems"][:15]:
            print(" ", problem)
    elif args.action == "seal":
        if not args.approved_by:
            raise SystemExit("--approved-by is required (owner spot-check of canonicals)")
        print(json.dumps(test2_v1.seal(ROOT, args.approved_by), indent=1))
    else:
        fixtures, families = test2_v1.load_test2(ROOT)
        print("sealed Test-2 OK:", len(fixtures), "fixtures,", len(families), "families")


if __name__ == "__main__":
    main()
