"""Build and check VN-AgentInject v3 releases from authored canonicals (Study 2, WP3/WP4).

  check   validate a canonical file against the approved spec (schema, coverage, sinks,
          secrets, tamper checks) and build the fixtures in memory; prints counts only.
  qa      check + replay every fixture with the oracle paths (safe and negative) and
          compute novelty against release_v2/release_test2; writes the QA report.
  write   qa + write the unsealed release folder (pilot_v3, release_v3 or release_test3).

The script prints counts and problem identifiers, never authored text.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from react_agent.authoring.v3 import release as rel

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "qa", "write"])
    parser.add_argument("--file", default="pilot_canonicals.json",
                        help="file name under data/adversarial/v3_authoring")
    parser.add_argument("--split", default="pilot", choices=["pilot", "dev", "test", "test3"])
    args = parser.parse_args(argv)
    variants: tuple[rel.Variant, ...] = (
        ("canonical",) if args.split == "pilot"
        else ("canonical", "paraphrase", "code_mix", "no_diacritic", "english"))
    if not (ROOT / rel.AUTHORING / args.file).exists():
        print(f"CHECK_FAILED missing {rel.AUTHORING / args.file}")
        return 1
    try:
        fixtures, privates = rel.build(ROOT, args.file, args.split, variants)
    except ValueError as error:  # pydantic ValidationError is a ValueError
        print(f"CHECK_FAILED {type(error).__name__}")
        print(str(error)[:4000])
        return 1
    counts: dict[str, int] = {}
    for f in fixtures:
        counts[f.branch] = counts.get(f.branch, 0) + 1
    print(f"CHECK_OK families={len(privates)} fixtures={len(fixtures)} by_branch={counts}")
    if args.command == "check":
        return 0
    with tempfile.TemporaryDirectory() as scratch:
        report = rel.qa(ROOT, fixtures, privates, Path(scratch))
    refs = rel.NOVELTY_REFERENCES_TEST3 if args.split == "test3" else rel.NOVELTY_REFERENCES
    report["novelty"] = rel.novelty(ROOT, rel.load_canonicals(ROOT, args.file), refs)
    nov = report["novelty"]
    print(f"QA replays={report['replays']} problems={len(report['problems'])}")
    for problem in report["problems"][:40]:
        print("  " + problem.split(":")[0])
    print(f"NOVELTY max={nov['max_observed']} over={nov['over_threshold']} "
          f"reused_literals={nov['reused_literals']}")
    ok = not report["problems"] and not nov["over_threshold"] and not nov["reused_literals"]
    if args.command == "write":
        if not ok:
            print("WRITE_REFUSED: fix QA/novelty problems first")
            return 1
        folder = ROOT / rel.release_folder(args.split)
        rel.write_release(folder, fixtures, privates, report)
        print(f"WROTE {folder.relative_to(ROOT)}")
    else:
        out = ROOT / "build" / f"v3_qa_{args.split}.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"REPORT {out.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
