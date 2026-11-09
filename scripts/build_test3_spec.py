#!/usr/bin/env python3
"""Write or check the Test-3 authoring spec (``data/adversarial/v3_authoring/spec_test3.json``)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.authoring.v3 import spec as v3
from react_agent.authoring.v3 import spec_test3 as t3

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["write", "check"])
    args = p.parse_args(argv)
    path, spec = ROOT / t3.SPEC_PATH, t3.build_spec()
    if args.command == "write":
        path.write_text(v3.dumps(spec), encoding="utf-8")
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    problems = t3.validate_spec(on_disk) + ([] if on_disk == spec else ["file differs from build"])
    print(f"{'OK' if not problems else 'PROBLEMS'} families={len(on_disk['families'])} "
          f"fixtures={t3.fixture_count(on_disk)} sha256={v3.spec_sha256(path)[:12]}")
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
