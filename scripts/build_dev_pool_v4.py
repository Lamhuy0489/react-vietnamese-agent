"""Build Dev v4: the merged development pool for BrokerGuard v3 (decision log 2026-11-15 16:30).

Dev v4 = Dev v3 (``D3_*``) + Test v3 / "Test-I" (``T3_*``) + Test-3 / "Test-II" (``T4_*``). The two
old Test sets were used to analyse v1 bypasses, so they are development data now; Test-4 is the
only held-out set.

The script reads only sealed releases, checks every input file against its seal before use,
and never edits them. Fixture texts are copied, not read or changed: only ids, branches and the
``split`` field (set to ``dev``) are touched. Output goes to ``data/adversarial/release_dev4``
(``dev_*.jsonl``, ``private/oracles.json``, ``manifest.json``, ``qa.json``, ``seal.json``).

Dev-val: per mechanism, the first ``VAL_PER_MECHANISM`` families by sha256(SALT + family_id).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import react_agent.authoring.v3.release as rel

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("data/adversarial/release_dev4")
SALT = "dev4-val-2026-11-15"
VAL_PER_MECHANISM = 7
SOURCES: list[dict[str, Any]] = [
    {"origin": "dev_v3", "folder": "data/adversarial/release_v3", "split": "dev",
     "oracles": "private/oracles.json", "prefix": "D3_"},
    {"origin": "test_v3 (Test-I)", "folder": "data/adversarial/release_v3", "split": "test",
     "oracles": "private/test_oracles.json", "prefix": "T3_"},
    {"origin": "test3 (Test-II)", "folder": "data/adversarial/release_test3", "split": "test3",
     "oracles": "private/test_oracles.json", "prefix": "T4_"},
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_seal(folder: Path, names: list[str]) -> None:
    sealed = json.loads((folder / "seal.json").read_text(encoding="utf-8"))["files_sha256"]
    for name in names:
        if sealed.get(name) != sha256(folder / name):
            raise SystemExit(f"{folder / name} does not match its seal; refusing to merge")


def val_families(mechanism_of: dict[str, str]) -> list[str]:
    by_mech: dict[str, list[str]] = defaultdict(list)
    for fam, mech in mechanism_of.items():
        by_mech[mech].append(fam)
    out: list[str] = []
    for mech in sorted(by_mech):
        ranked = sorted(by_mech[mech],
                        key=lambda f: hashlib.sha256((SALT + f).encode()).hexdigest())
        out += ranked[:VAL_PER_MECHANISM]
    return sorted(out)


def build(root: Path) -> dict[str, Any]:
    fixtures: list[rel.FixtureV3] = []
    privates: dict[str, rel.PrivateV3] = {}
    origin: dict[str, str] = {}
    for src in SOURCES:
        folder = root / src["folder"]
        files = [f"{src['split']}_{b}.jsonl" for b in rel.BRANCH_CODE]
        check_seal(folder, [*files, src["oracles"]])
        for name in files:
            for line in (folder / name).read_text(encoding="utf-8").splitlines():
                if not line:
                    continue
                row = rel.FixtureV3.model_validate_json(line)
                if row.split != src["split"] or not row.family_id.startswith(src["prefix"]):
                    raise SystemExit(f"unexpected row {row.variant_id} in {name}")
                fixtures.append(row.model_copy(update={"split": "dev"}))
                origin.setdefault(row.family_id, src["origin"])
        for item in json.loads((folder / src["oracles"]).read_text(encoding="utf-8")):
            private = rel.PrivateV3.model_validate(item)
            if private.family_id in privates:
                raise SystemExit(f"duplicate oracle {private.family_id}")
            privates[private.family_id] = private
            origin.setdefault(private.family_id, src["origin"])
    return {"fixtures": fixtures, "privates": privates, "origin": origin}


def qa(fixtures: list[rel.FixtureV3], privates: dict[str, rel.PrivateV3],
       origin: dict[str, str], val: list[str]) -> dict[str, Any]:
    variant_ids = Counter(f.variant_id for f in fixtures)
    if dup := sorted(v for v, n in variant_ids.items() if n > 1):
        raise SystemExit(f"duplicate variant ids: {dup[:5]}")
    families = {f.family_id for f in fixtures}
    if families != set(privates):
        raise SystemExit("fixture families and oracle families differ")
    attack_fams = {f.family_id for f in fixtures if f.branch == "attack"}
    plain_fams = {f.family_id for f in fixtures if f.branch == "benign_plain"}
    if attack_fams != plain_fams:  # every attack family keeps its benign pair inside Dev v4
        raise SystemExit("attack families without their benign_plain pair (or the reverse)")
    mech = {fam: privates[fam].mechanism for fam in families}
    val_set = set(val)

    def counts(fams: set[str]) -> dict[str, Any]:
        rows = [f for f in fixtures if f.family_id in fams]
        return {"families": len(fams),
                "fixtures": dict(sorted(Counter(f.branch for f in rows).items())),
                "per_mechanism": dict(sorted(Counter(mech[f] for f in fams).items())),
                "per_origin": dict(sorted(Counter(origin[f] for f in fams).items()))}

    return {"schema_version": "dev4_qa_v1", "all": counts(families),
            "dev_train": counts(families - val_set), "dev_val": counts(val_set),
            "checks": ["input files match their seals", "unique variant ids",
                       "fixture and oracle families equal",
                       "each attack family has its benign_plain pair", "split field = dev"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="build and print QA, write nothing")
    args = parser.parse_args(argv)
    built = build(ROOT)
    fixtures, privates, origin = built["fixtures"], built["privates"], built["origin"]
    val = val_families({f: p.mechanism for f, p in privates.items()})
    report = qa(fixtures, privates, origin, val)
    print(json.dumps(report["all"], ensure_ascii=False))
    print("dev_val:", json.dumps(report["dev_val"], ensure_ascii=False))
    if args.check:
        return 0
    folder = ROOT / OUT
    rel.write_release(folder, fixtures, list(privates.values()), report)
    manifest = {"schema_version": "dev4_manifest_v1", "decision": "decision log 2026-11-15 16:30",
                "salt": SALT, "val_per_mechanism": VAL_PER_MECHANISM,
                "origin": dict(sorted(origin.items())), "dev_val": val,
                "sources": {s["origin"]: s["folder"] for s in SOURCES}}
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n",
                                          encoding="utf-8")
    names = [f"dev_{b}.jsonl" for b in rel.BRANCH_CODE] + [
        "private/oracles.json", "manifest.json", "qa.json"]
    seal = {"schema_version": "dev4_seal_v1",
            "approved_by": "owner (decision log 2026-11-15 16:30)",
            "files_sha256": {n: sha256(folder / n) for n in names}}
    (folder / "seal.json").write_text(json.dumps(seal, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
