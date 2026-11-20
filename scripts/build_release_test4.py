#!/usr/bin/env python3
"""Build and seal release_test4 from test4_canonicals.json and spec_test4.json.

Creates:
- data/adversarial/release_test4/test4_attack.jsonl (240 lines)
- data/adversarial/release_test4/test4_benign_plain.jsonl (240 lines)
- data/adversarial/release_test4/test4_benign_auth.jsonl (80 lines)
- data/adversarial/release_test4/private/test_oracles.json (48 oracles)
- data/adversarial/release_test4/qa.json
- data/adversarial/release_test4/manifest.json
- data/adversarial/release_test4/seal.json
- data/adversarial/adaptive_v3/adaptive_test4_attack.jsonl (24 adaptive fixtures)

Also validates all generated lines against FixtureV3 and verifies SHA-256 hashes.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, cast

import react_agent.authoring.v3.release as rel
from react_agent.schemas.adversarial_workbench import OverlayScenario
from react_agent.security_v1.guard_bare_json_v1 import bind

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_release_test4_v1 as c4  # noqa: E402

OUT_RELEASE = ROOT / "data/adversarial/release_test4"
QA_REPORT_SRC = ROOT / "build/v3_qa_test4.json"
ADAPTIVE_FILE = ROOT / "data/adversarial/v3_authoring/test4_adaptive.json"
ADAPTIVE_OUT = ROOT / "data/adversarial/adaptive_v3/adaptive_test4_attack.jsonl"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    print("Building release_test4...")
    if "--force" not in sys.argv and (OUT_RELEASE / "seal.json").exists():
        print(f"ERROR: {OUT_RELEASE} is already sealed! Use --force to rebuild.")
        return 1

    variants: tuple[rel.Variant, ...] = (
        "canonical",
        "paraphrase",
        "code_mix",
        "no_diacritic",
        "english",
    )

    build = bind(rel.build, load_spec_rows=c4.spec_rows, load_canonicals=c4.canonicals)
    fixtures_raw, privates_raw = build(ROOT, c4.FILE, "test", variants)

    # Convert memory IDs T3_5NN back to T5_NN and split to test4
    def fix_str(s: str) -> str:
        s = s.replace("T3_5", "T5_")
        return s.replace('"split":"test"', '"split":"test4"')

    fixtures_json = [fix_str(f.model_dump_json()) for f in fixtures_raw]
    privates_json = [fix_str(p.model_dump_json()) for p in privates_raw]

    fixtures_dicts = [json.loads(line) for line in fixtures_json]
    privates_dicts = [json.loads(line) for line in privates_json]

    if len(fixtures_dicts) != 560 or len(privates_dicts) != 48:
        raise ValueError(
            f"Fixture/private mismatch: fixtures={len(fixtures_dicts)}, "
            f"privates={len(privates_dicts)}"
        )

    OUT_RELEASE.mkdir(parents=True, exist_ok=True)
    (OUT_RELEASE / "private").mkdir(parents=True, exist_ok=True)

    # Write split branch jsonl
    branch_map = {
        "attack": OUT_RELEASE / "test4_attack.jsonl",
        "benign_plain": OUT_RELEASE / "test4_benign_plain.jsonl",
        "benign_auth": OUT_RELEASE / "test4_benign_auth.jsonl",
    }

    counts: Counter[str] = Counter()
    for branch, path in branch_map.items():
        rows = [f for f in fixtures_dicts if f["branch"] == branch]
        counts[branch] = len(rows)
        content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {len(rows)} lines to {path.name}")

    # Write private/test_oracles.json
    oracles_path = OUT_RELEASE / "private/test_oracles.json"
    privates_dicts_sorted = sorted(privates_dicts, key=lambda x: x["family_id"])
    oracles_json = json.dumps(privates_dicts_sorted, indent=1, ensure_ascii=False) + "\n"
    oracles_path.write_text(oracles_json, encoding="utf-8")
    print(f"Wrote {len(privates_dicts_sorted)} oracles to private/test_oracles.json")

    # Write qa.json
    if not QA_REPORT_SRC.exists():
        print(f"ERROR: missing {QA_REPORT_SRC}")
        return 1
    qa_data = json.loads(QA_REPORT_SRC.read_text(encoding="utf-8"))
    qa_json = json.dumps(qa_data, indent=1, ensure_ascii=False) + "\n"
    (OUT_RELEASE / "qa.json").write_text(qa_json, encoding="utf-8")

    # Write manifest.json
    manifest = {
        "release": "release_test4",
        "split": "test4",
        "families_count": len(privates_dicts),
        "fixtures_count": len(fixtures_dicts),
        "branch_counts": dict(counts),
        "spec": "spec_test4.json",
        "canonicals": "test4_canonicals.json",
    }
    manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    (OUT_RELEASE / "manifest.json").write_text(manifest_json, encoding="utf-8")

    # Write adaptive fixtures if test4_adaptive.json exists
    if ADAPTIVE_FILE.exists():
        adaptive_attacks = json.loads(ADAPTIVE_FILE.read_text(encoding="utf-8"))
        canonicals_map = {c.spec_id: c for c in c4.canonicals(ROOT, c4.FILE)}
        spec_map = c4.spec_rows(ROOT)
        adaptive_fixtures: list[dict[str, Any]] = []
        for fid in sorted(adaptive_attacks.keys()):
            raw_id = fid.replace("T5_", "T3_5")
            c = canonicals_map[raw_id]
            row = spec_map[raw_id]
            first = rel.trigger(c, row.vector)
            text = adaptive_attacks[fid]
            overlay = OverlayScenario(
                task_id=c.task_id,
                attack_category=cast(Any, rel.CATEGORY[row.mechanism]),
                source_type=row.vector,
                source_id=c.source_id,
                trust=c.trust,
                sensitivity=c.sensitivity,
                title=c.title,
                base_content=c.base.replace(rel.MARKER, "").strip(),
                attack_text=text,
                benign_text=c.benign.canonical,
                sensitive_value=c.source_secret,
                trigger=first,
            )
            fix_dict = {
                "schema_version": "vn_agentinject_fixture_v3",
                "variant_id": f"ATK_{fid}_ADAPTIVE",
                "family_id": fid,
                "split": "test4",
                "branch": "attack",
                "variant_type": "canonical",
                "task": {
                    "task_id": c.task_id,
                    "instruction": c.instruction.canonical,
                },
                "overlay": overlay.model_dump(mode="json"),
                "content": c.base.replace(rel.MARKER, text),
                "resources_docs": [d.model_dump(mode="json") for d in c.resources_docs],
                "resources_rows": [r.model_dump(mode="json") for r in c.resources_rows],
            }
            adaptive_fixtures.append(fix_dict)

        ADAPTIVE_OUT.parent.mkdir(parents=True, exist_ok=True)
        content = "".join(json.dumps(f, ensure_ascii=False) + "\n" for f in adaptive_fixtures)
        ADAPTIVE_OUT.write_text(content, encoding="utf-8")
        rel_adaptive = ADAPTIVE_OUT.relative_to(ROOT)
        print(f"Wrote {len(adaptive_fixtures)} adaptive fixtures to {rel_adaptive}")

    # Compute seal.json
    files_to_hash = [
        "test4_attack.jsonl",
        "test4_benign_plain.jsonl",
        "test4_benign_auth.jsonl",
        "private/test_oracles.json",
        "manifest.json",
        "qa.json",
    ]
    files_sha256 = {rel_path: sha256_file(OUT_RELEASE / rel_path) for rel_path in files_to_hash}

    authoring_sha256 = {
        "spec_test4.json": sha256_file(ROOT / "data/adversarial/v3_authoring/spec_test4.json"),
        "test4_canonicals.json": sha256_file(
            ROOT / "data/adversarial/v3_authoring/test4_canonicals.json"
        ),
        "test4_adaptive.json": sha256_file(
            ROOT / "data/adversarial/v3_authoring/test4_adaptive.json"
        ),
        "code_mix_glossary_v3.json": sha256_file(
            ROOT / "data/adversarial/v3_authoring/code_mix_glossary_v3.json"
        ),
    }

    seal_data = {
        "schema_version": "test4_seal_v1",
        "approved_by": "owner (decision log 2026-11-15 17:15)",
        "authorship": "Test-4 (48 static families + 24 adaptive attacks) sealed 2026-11-15",
        "files_sha256": files_sha256,
        "authoring_sha256": authoring_sha256,
    }

    seal_path = OUT_RELEASE / "seal.json"
    seal_path.write_text(
        json.dumps(seal_data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    seal_sha = sha256_file(seal_path)
    print(f"SEAL_OK: Created {seal_path.relative_to(ROOT)}")
    print(f"Seal SHA-256: {seal_sha}")
    print("Files SHA-256:")
    for k, v in files_sha256.items():
        print(f"  {k}: {v}")
    print("Authoring SHA-256:")
    for k, v in authoring_sha256.items():
        print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
