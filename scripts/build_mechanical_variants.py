#!/usr/bin/env python3
"""Create unapproved mechanical drafts from the immutable canonical assignment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.authoring.mechanical_variants import build_drafts

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build_drafts(ROOT, args.output), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
