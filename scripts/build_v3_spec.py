#!/usr/bin/env python3
"""Write or check the VN-AgentInject v3 authoring spec (WP1, rebuild_b_plan.md).

``write`` regenerates ``data/adversarial/v3_authoring/spec.json`` deterministically and
refuses to overwrite a different committed spec unless ``--force`` is given (the spec is
fixed before generation). ``check`` validates the committed spec, confirms it equals the
deterministic build, and prints counts and the sha256 to record in the decision log.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from react_agent.authoring.v3 import spec as v3

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("write", "check"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    path = ROOT / v3.SPEC_PATH
    text = v3.dumps(v3.build_spec())
    if args.action == "write":
        if path.exists() and path.read_text(encoding="utf-8") != text and not args.force:
            print("spec exists and differs; refusing without --force", file=sys.stderr)
            return 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    import json

    spec = json.loads(path.read_text(encoding="utf-8"))
    problems = v3.validate_spec(spec)
    if path.read_text(encoding="utf-8") != text:
        problems.append("committed spec differs from the deterministic build")
    fams = spec["families"]
    print("families", dict(Counter(f["split"] for f in fams)))
    print("b_auth", dict(Counter(f["split"] for f in fams if f["b_auth"])))
    print("fixtures", v3.fixture_counts(spec))
    print("sha256", v3.spec_sha256(path))
    for problem in problems:
        print("PROBLEM", problem)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
