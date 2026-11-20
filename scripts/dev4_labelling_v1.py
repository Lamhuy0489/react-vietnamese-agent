"""Labelling sheets and agreement for Dev v4 (rules: ``labelling_rules_v4.md``, frozen 2026-11-15).

``sheet``  writes, under ``data/adversarial/v3_authoring/dev4_labelling/``:
           - ``source_inventory.csv``: every (family, source) of Dev v4 (overlay, documents,
             database rows) with its current sensitivity and trust labels and its branches.
             Ids and labels only, never content.
           - ``labels_owner.csv`` and ``labels_minh.csv``: empty per-value sheets in the format of
             rules §6 (one row per confidential value). Each annotator fills only their own file.
``kappa``  reads the two filled sheets and reports, at source level, Cohen's kappa for the
           derived label (S2 when a source has at least one value row, rules §3) and for each
           category K1-K5, plus the number of disagreeing sources and of ``?`` rows.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/adversarial/release_dev4"
OUT = ROOT / "data/adversarial/v3_authoring/dev4_labelling"
VALUE_FIELDS = ["family_id", "source_id", "value_ref", "category", "user_provided", "note"]
CATEGORIES = ["K1", "K2", "K3", "K4", "K5"]
ANNOTATORS = ["owner", "minh"]


def inventory() -> list[dict[str, str]]:
    sens: dict[tuple[str, str], set[str]] = defaultdict(set)
    trust: dict[tuple[str, str], set[str]] = defaultdict(set)
    branches: dict[tuple[str, str], set[str]] = defaultdict(set)
    kind: dict[tuple[str, str], str] = {}
    for path in sorted(RELEASE.glob("dev_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            row = json.loads(line)
            ov = row["overlay"]
            items = [(ov["source_id"], ov["source_type"], ov["sensitivity"], ov["trust"])]
            items += [(d["identity"], d["kind"], d["sensitivity"], d["trust"])
                      for d in row["resources_docs"]]
            items += [(str(d["note_id"]), "database_row", d["sensitivity"], d["trust"])
                      for d in row["resources_rows"]]
            for sid, k, label, level in items:
                key = (row["family_id"], sid)
                kind.setdefault(key, k)
                sens[key].add(label)
                trust[key].add(level)
                branches[key].add(row["branch"])
    return [{"family_id": fam, "source_id": sid, "kind": kind[(fam, sid)],
             "current_sensitivity": "/".join(sorted(sens[(fam, sid)])),
             "trust": "/".join(sorted(trust[(fam, sid)])),
             "branches": "/".join(sorted(branches[(fam, sid)]))}
            for fam, sid in sorted(kind)]


def write_sheet() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = inventory()
    with (OUT / "source_inventory.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for name in ANNOTATORS:
        path = OUT / f"labels_{name}.csv"
        if path.exists():
            print(f"kept {path.name} (already exists)")
            continue
        path.write_text(",".join(VALUE_FIELDS) + "\n", encoding="utf-8")
    print(f"sources={len(rows)} families={len({r['family_id'] for r in rows})} -> {OUT}")
    return 0


def read_labels(path: Path,
                known: set[tuple[str, str]]) -> tuple[dict[tuple[str, str], set[str]], int]:
    cats: dict[tuple[str, str], set[str]] = defaultdict(set)
    unsure = 0
    with path.open(encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh), 2):
            key = (row["family_id"].strip(), row["source_id"].strip())
            if key not in known:
                raise SystemExit(f"{path.name}:{i}: unknown family/source {key}")
            cat = row["category"].strip()
            if cat == "?":
                unsure += 1
            elif cat not in CATEGORIES:
                raise SystemExit(f"{path.name}:{i}: category must be K1-K5 or ?")
            cats[key].add(cat)
    return cats, unsure


def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def kappa() -> int:
    keys = [(r["family_id"], r["source_id"]) for r in inventory()]
    known = set(keys)
    (ca, ua), (cb, ub) = (read_labels(OUT / f"labels_{n}.csv", known) for n in ANNOTATORS)
    s2a = [bool(ca.get(k)) for k in keys]
    s2b = [bool(cb.get(k)) for k in keys]
    report = {"sources": len(keys), "S2_owner": sum(s2a), "S2_minh": sum(s2b),
              "unsure_rows_owner": ua, "unsure_rows_minh": ub,
              "kappa_S2": round(cohen_kappa(s2a, s2b), 3),
              "disagreeing_sources": sum(x != y for x, y in zip(s2a, s2b, strict=True)),
              "kappa_per_category": {
                  c: round(cohen_kappa([c in ca.get(k, set()) for k in keys],
                                       [c in cb.get(k, set()) for k in keys]), 3)
                  for c in CATEGORIES}}
    print(json.dumps(report, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["sheet", "kappa"])
    args = parser.parse_args(argv)
    return write_sheet() if args.command == "sheet" else kappa()


if __name__ == "__main__":
    raise SystemExit(main())
