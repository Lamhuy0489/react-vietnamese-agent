#!/usr/bin/env python3
"""Build unapproved linguistic drafts; approval is a separate semantic review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.authoring.linguistic_variants import build_linguistic

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inputs", type=Path, default=ROOT / "data/adversarial/linguistic_authoring_v1"
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build_linguistic(ROOT, args.inputs, args.output), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
