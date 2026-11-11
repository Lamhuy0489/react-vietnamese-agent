#!/usr/bin/env python3
"""Check and QA the Test-3 canonicals (``test3_canonicals.json``) before sealing.

Same checks as ``build_v3_release.py check|qa`` (schema, spec coverage, sinks, secrets,
tamper, safe and negative replays, novelty), against ``spec_test3.json``. ``release.py``
is not edited while D3 Dev runs are active (its hash is part of their identity), so the
Test-3 ids ``T4_NN`` are relabelled ``T3_4NN`` in memory only; nothing is written to a
release folder. Novelty also covers pilot_v3 and release_v3 (Dev + Test v3).

Prints counts and family ids only, never authored text. Writes ``build/v3_qa_test3.json``
(problem codes and novelty scores per family field).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from react_agent.authoring.v3 import release as rel
from react_agent.authoring.v3 import spec_test3 as t3
from react_agent.security_v1.guard_bare_json_v1 import bind

ROOT = Path(__file__).resolve().parents[1]
FILE = "test3_canonicals.json"
REFERENCES = (*rel.NOVELTY_REFERENCES, Path("data/adversarial/pilot_v3"), rel.RELEASE)


def relabel(spec_id: str) -> str:
    prefix, number = spec_id.split("_")
    return f"T3_4{number}" if prefix == "T4" else spec_id


def spec_rows(root: Path) -> dict[str, rel.SpecRow]:
    spec = json.loads((root / t3.SPEC_PATH).read_text(encoding="utf-8"))
    if problems := t3.validate_spec(spec):
        raise ValueError(f"spec_test3 invalid: {problems[:5]}")
    return {relabel(f["family_id"]): rel.SpecRow.model_validate(
        {**{k: f[k] for k in rel.SpecRow.model_fields}, "family_id": relabel(f["family_id"]),
         "split": "test"}) for f in spec["families"]}


def canonicals(root: Path, name: str) -> list[rel.Canonical]:
    rows = json.loads((root / rel.AUTHORING / name).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("file must be a JSON array")
    bad = sorted({str(r.get("spec_id")) for r in rows if not str(r.get("spec_id", "")).startswith(
        "T4_")})
    if bad:
        raise ValueError(f"spec_id must be T4_xx: {bad[:10]}")
    out = [rel.Canonical.model_validate({**r, "spec_id": relabel(r["spec_id"])}) for r in rows]
    if len({c.family for c in out}) != len(out):
        raise ValueError("duplicate family name")
    return out


def reused_families(root: Path, mine: list[rel.Canonical]) -> list[str]:
    """Family names already used by pilot/Dev/Test v3 canonicals."""
    old: set[str] = set()
    for name in ("pilot_canonicals.json", "dev_canonicals.json", "test_canonicals.json"):
        path = root / rel.AUTHORING / name
        if path.exists():
            old |= {r["family"] for r in json.loads(path.read_text(encoding="utf-8"))}
    return sorted(c.spec_id for c in mine if c.family in old)


def per_family(name: str) -> int:
    """Build each family alone; print its id and the error kind (no text)."""
    rows = json.loads((ROOT / rel.AUTHORING / name).read_text(encoding="utf-8"))
    specs, words = spec_rows(ROOT), rel.glossary(ROOT)
    variants: tuple[rel.Variant, ...] = ("canonical", "paraphrase", "code_mix", "no_diacritic",
                                         "english")
    bad = 0
    for row in sorted(rows, key=lambda r: str(r.get("spec_id"))):
        sid = str(row.get("spec_id"))
        try:
            c = rel.Canonical.model_validate({**row, "spec_id": relabel(sid)})
            spec = specs[c.spec_id]
            if (spec.user_sink == "none") != (not c.sinks):
                raise ValueError("sinks disagree with spec user_sink")
            if spec.mechanism in ("M3", "M4") and len(c.secrets) != 1:
                raise ValueError("M3/M4 need exactly one secret")
            if spec.mechanism == "M5" and not c.tamper:
                raise ValueError("M5 needs a tamper check")
            rel.build_fixtures(c, spec, words, variants)
        except (ValueError, KeyError) as error:
            bad += 1
            kind = re.sub(r"\[[^\]]*\]|'[^']*'", "<...>", str(error).splitlines()[0])
            print(f"{sid} {type(error).__name__}: {kind[:160]}")
    print(f"families={len(rows)} failing={bad}")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["check", "qa"])
    p.add_argument("--file", default=FILE)
    p.add_argument("--per-family", action="store_true",
                   help="check each family alone and list every failing family id")
    args = p.parse_args(argv)
    variants: tuple[rel.Variant, ...] = ("canonical", "paraphrase", "code_mix", "no_diacritic",
                                         "english")
    if args.per_family:
        return per_family(args.file)
    build = bind(rel.build, load_spec_rows=spec_rows, load_canonicals=canonicals)
    try:
        fixtures, privates = build(ROOT, args.file, "test", variants)
        mine = canonicals(ROOT, args.file)
    except (ValueError, OSError) as error:  # pydantic ValidationError is a ValueError
        print(f"CHECK_FAILED {type(error).__name__}")
        # error kinds only: quoted literals (destinations, values) are masked
        print(re.sub(r"\[[^\]]*\]|'[^']*'", "<...>", str(error)).replace("T3_4", "T4_")[:4000])
        print("per-family list: run with --per-family")
        return 1
    counts: dict[str, int] = {}
    for f in fixtures:
        counts[f.branch] = counts.get(f.branch, 0) + 1
    reused = reused_families(ROOT, mine)
    print(f"CHECK_OK families={len(privates)} fixtures={len(fixtures)} by_branch={counts}"
          + (f" REUSED_FAMILY_NAMES={[s.replace('T3_4', 'T4_') for s in reused]}" if reused
             else ""))
    if args.command == "check":
        return 1 if reused else 0
    with tempfile.TemporaryDirectory() as scratch:
        report: dict[str, Any] = rel.qa(ROOT, fixtures, privates, Path(scratch))
    report["novelty"] = bind(rel.novelty, NOVELTY_REFERENCES=REFERENCES)(ROOT, mine)
    report = json.loads(json.dumps(report).replace("T3_4", "T4_"))
    nov = report["novelty"]
    print(f"QA replays={report['replays']} problems={len(report['problems'])}")
    for problem in report["problems"][:60]:
        print("  " + problem.split(":")[0])
    print(f"NOVELTY max={nov['max_observed']} over={nov['over_threshold']} "
          f"reused_literals={nov['reused_literals']}")
    out = ROOT / "build/v3_qa_test3.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"REPORT {out.relative_to(ROOT)}")
    ok = not report["problems"] and not nov["over_threshold"] and not nov["reused_literals"]
    return 0 if ok and not reused else 1


if __name__ == "__main__":
    sys.exit(main())
