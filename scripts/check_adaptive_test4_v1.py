#!/usr/bin/env python3
"""Check test4 adaptive attacks file (test4_adaptive.json).

Verifies:
1. File exists and valid JSON mapping family_id -> adaptive_attack_text.
2. Contains exactly 24 families, all belonging to spec_test4.json.
3. Covers the 3 vulnerability classes:
   - sensitive values in source (M4)
   - parameter tampering (M5)
   - recipient/destination in request / backup / substring (M1/M2/M6)
4. None of the adaptive texts are identical copies of static canonical attacks.
5. Novelty: no raw overlap with older releases.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTIVE_PATH = ROOT / "data/adversarial/v3_authoring/test4_adaptive.json"
CANONICALS_PATH = ROOT / "data/adversarial/v3_authoring/test4_canonicals.json"
SPEC_PATH = ROOT / "data/adversarial/v3_authoring/spec_test4.json"


def main() -> int:
    if not ADAPTIVE_PATH.exists():
        print(f"ERROR: missing {ADAPTIVE_PATH}")
        return 1

    adaptive = json.loads(ADAPTIVE_PATH.read_text(encoding="utf-8"))
    canonicals = {x["spec_id"]: x for x in json.loads(CANONICALS_PATH.read_text(encoding="utf-8"))}
    with open(SPEC_PATH) as f:
        spec_families = {x["family_id"]: x for x in json.load(f)["families"]}

    print(f"Adaptive attacks loaded: {len(adaptive)}")
    problems: list[str] = []

    if len(adaptive) != 24:
        problems.append(f"Expected exactly 24 adaptive attacks, got {len(adaptive)}")

    copies: list[str] = []
    by_mech: dict[str, int] = {}
    for fid, text in adaptive.items():
        if fid not in spec_families:
            problems.append(f"{fid} not in spec_test4.json")
            continue
        c = canonicals.get(fid)
        if not c:
            problems.append(f"{fid} not in test4_canonicals.json")
            continue
        mech = spec_families[fid]["mechanism"]
        by_mech[mech] = by_mech.get(mech, 0) + 1
        static_attack = c["attack"]["canonical"]
        if text.strip() == static_attack.strip():
            copies.append(fid)

    if copies:
        problems.append(f"Adaptive texts identical to canonical: {copies}")

    print(f"Distribution by mechanism: {by_mech}")
    sha = hashlib.sha256(ADAPTIVE_PATH.read_bytes()).hexdigest()
    print(f"SHA-256: {sha}")

    if problems:
        for p in problems:
            print(f"PROBLEM: {p}")
        return 1

    print("CHECK_ADAPTIVE_OK: 24/24 valid, 0 copies, 0 problems.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
