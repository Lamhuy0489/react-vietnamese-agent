"""Build Dev v4.1: apply errata (dev4_errata.csv) to release_dev4.

Rules: labelling_rules_v4.md (frozen 2026-11-15).
Input: data/adversarial/release_dev4 (stays frozen and untouched).
Errata: data/adversarial/v3_authoring/dev4_errata.csv.
Output: data/adversarial/release_dev4_1 (dev_*.jsonl, private/oracles.json, manifest, qa, seal).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import react_agent.authoring.v3.release as rel

ROOT = Path(__file__).resolve().parents[1]
IN_RELEASE = ROOT / "data/adversarial/release_dev4"
ERRATA_PATH = ROOT / "data/adversarial/v3_authoring/dev4_errata.csv"
OUT_RELEASE = ROOT / "data/adversarial/release_dev4_1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_input_seal(folder: Path) -> None:
    seal = json.loads((folder / "seal.json").read_text(encoding="utf-8"))["files_sha256"]
    for name, expected in seal.items():
        actual = sha256(folder / name)
        if actual != expected:
            raise SystemExit(f"Input file {name} failed seal check: {actual} != {expected}")


def load_errata() -> dict[tuple[str, str], dict[str, str]]:
    """Map (family_id, source_id) -> {field: new_val}."""
    errata: dict[tuple[str, str], dict[str, str]] = {}
    with ERRATA_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["family_id"].strip(), row["source_id"].strip())
            field = row["field"].strip()
            errata.setdefault(key, {})[field] = row["new"].strip()
    return errata


def apply_errata_to_fixture(fixture: rel.FixtureV3,
                            errata: dict[tuple[str, str], dict[str, str]],
                            changed_counts: Counter[str]) -> rel.FixtureV3:
    fam = fixture.family_id

    # Overlay
    ov = fixture.overlay
    ov_key = (fam, ov.source_id)
    if ov_key in errata:
        patch = errata[ov_key]
        if "sensitivity" in patch:
            ov = ov.model_copy(update={"sensitivity": patch["sensitivity"]})
            changed_counts["overlay"] += 1

    # Resources docs
    new_docs = []
    for doc in fixture.resources_docs:
        doc_key = (fam, doc.identity)
        if doc_key in errata:
            patch = errata[doc_key]
            if "sensitivity" in patch:
                doc = doc.model_copy(update={"sensitivity": patch["sensitivity"]})
                changed_counts["doc"] += 1
        new_docs.append(doc)

    # Resources rows
    new_rows = []
    for row in fixture.resources_rows:
        row_key = (fam, str(row.note_id))
        if row_key in errata:
            patch = errata[row_key]
            if "sensitivity" in patch:
                row = row.model_copy(update={"sensitivity": patch["sensitivity"]})
                changed_counts["row"] += 1
        new_rows.append(row)

    return fixture.model_copy(update={
        "overlay": ov,
        "resources_docs": new_docs,
        "resources_rows": new_rows,
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify errata application without writing")
    args = parser.parse_args(argv)

    check_input_seal(IN_RELEASE)
    errata = load_errata()
    print(f"Loaded {len(errata)} errata rules from {ERRATA_PATH.name}")

    changed_counts: Counter[str] = Counter()
    fixtures: list[rel.FixtureV3] = []

    for branch in rel.BRANCH_CODE:
        file_name = f"dev_{branch}.jsonl"
        lines = (IN_RELEASE / file_name).read_text(encoding="utf-8").splitlines()
        for line in lines:
            if not line:
                continue
            f = rel.FixtureV3.model_validate_json(line)
            f_patched = apply_errata_to_fixture(f, errata, changed_counts)
            fixtures.append(f_patched)

    print(f"Applied errata to fixtures: {dict(changed_counts)}")

    # Load oracles
    oracles_raw = json.loads((IN_RELEASE / "private/oracles.json").read_text(encoding="utf-8"))
    oracles = [rel.PrivateV3.model_validate(o) for o in oracles_raw]

    # Load manifest and qa
    manifest = json.loads((IN_RELEASE / "manifest.json").read_text(encoding="utf-8"))
    manifest["schema_version"] = "dev4_1_manifest_v1"
    manifest["errata_applied"] = str(ERRATA_PATH.name)
    manifest["errata_count"] = len(errata)

    qa_report = json.loads((IN_RELEASE / "qa.json").read_text(encoding="utf-8"))
    qa_report["schema_version"] = "dev4_1_qa_v1"
    qa_report["errata_applied"] = dict(changed_counts)

    if args.check:
        print("Check completed successfully. No files written.")
        return 0

    OUT_RELEASE.mkdir(parents=True, exist_ok=True)
    rel.write_release(OUT_RELEASE, fixtures, oracles, qa_report)

    (OUT_RELEASE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    names = [f"dev_{b}.jsonl" for b in rel.BRANCH_CODE] + [
        "private/oracles.json", "manifest.json", "qa.json"
    ]
    seal = {
        "schema_version": "dev4_1_seal_v1",
        "approved_by": "owner (decision log 2026-11-15 18:00)",
        "files_sha256": {n: sha256(OUT_RELEASE / n) for n in names},
    }
    (OUT_RELEASE / "seal.json").write_text(json.dumps(seal, indent=1) + "\n", encoding="utf-8")
    print(f"Successfully built {OUT_RELEASE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
