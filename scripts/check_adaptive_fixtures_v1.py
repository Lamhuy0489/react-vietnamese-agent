#!/usr/bin/env python3
"""Pre-submission check for WP8 adaptive Dev fixtures (counts and IDs only, no text printed).

For each adaptive fixture, compares the SHA-256 of every field with the CANONICAL static Dev
fixture of the same family. An adaptive fixture whose ``content`` and ``overlay`` both equal
the canonical one is a copy of the static set, not a new attack.

Usage: python scripts/check_adaptive_fixtures_v1.py [FILE]
Exit code 1 when the file has a structural problem or any fixture is a canonical copy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "data/adversarial/adaptive_v3/adaptive_dev_attack.jsonl"
STATIC = ROOT / "data/adversarial/release_v3/dev_attack.jsonl"
INJECTED = ("content", "overlay")


def _h(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(text.encode()).hexdigest()


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", nargs="?", type=Path, default=DEFAULT)
    args = p.parse_args(argv)
    print("sha256", hashlib.sha256(args.file.read_bytes()).hexdigest())
    canon = {r["family_id"]: r for r in _rows(STATIC) if r["variant_id"].endswith("_CANONICAL")}
    rows = _rows(args.file)
    families = Counter(r.get("family_id") for r in rows)
    problems = [f"duplicate family {f}" for f, n in families.items() if n > 1]
    problems += [f"not a Dev family {f}" for f in families if f not in canon]
    other: Counter[str] = Counter()
    copies: list[str] = []
    changed: list[str] = []
    for r in rows:
        c = canon.get(r.get("family_id"))
        if c is None:
            continue
        if r.get("task") != c.get("task"):
            problems.append(f"task differs from Dev oracle task: {r['family_id']}")
        diff = {k for k in set(r) | set(c) if _h(r.get(k)) != _h(c.get(k))}
        other.update(diff - set(INJECTED) - {"variant_id"})
        (changed if diff & set(INJECTED) else copies).append(r["family_id"])
    print(f"fixtures {len(rows)}, families {len(families)}/{len(canon)}")
    print(f"new injected text: {len(changed)}; identical to canonical: {len(copies)}")
    if copies:
        print("copies of canonical:", " ".join(sorted(copies)))
    if other:
        print("other fields changed (check they match the oracle):", dict(other))
    for line in problems:
        print("PROBLEM", line)
    return 1 if problems or copies else 0


if __name__ == "__main__":
    raise SystemExit(main())
