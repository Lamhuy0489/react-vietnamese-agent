#!/usr/bin/env python3
"""Adaptive round against BrokerGuard v3 on the Dev-val families (design step 5).

Two commands, both infrastructure only (Claude never reads or writes attack text):

- ``worksheet``: writes ``data/adversarial/v3_authoring/adaptive_v3target_worksheet.md`` for the
  authors (owner, Minh): per Dev-val family its mechanism, detail, the user task, the source the
  injection sits in and the original canonical attack, so an attack can be written against v3.
- ``build``: reads the authors' ``data/adversarial/v3_authoring/adaptive_v3target.json``
  (``{family_id: text}`` or ``{family_id: [text, ...]}``), takes the Dev v4.1 canonical attack
  fixture of each listed family, swaps its attack text for the new text and writes
  ``data/adversarial/adaptive_v3/adaptive_v3target_attack.jsonl`` (variants ``ATK_<fam>_ADV_A``,
  ``_ADV_B``, ..., split ``dev``). Every row is validated with ``FixtureV3``; the original
  attack text must occur exactly once in the fixture content. Prints counts only.

Run with ``run_v3_api_v3.py --fixtures`` on
``data/adversarial/adaptive_v3/adaptive_v3target_attack.jsonl``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import react_agent.authoring.v3.release as rel

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/adversarial/release_dev4_1/dev_attack.jsonl"
VAL = ROOT / "results/rebuild_c/dev4_1_val_fixtures.jsonl"
AUTHORING = ROOT / "data/adversarial/v3_authoring"
ATTACKS = AUTHORING / "adaptive_v3target.json"
WORKSHEET = AUTHORING / "adaptive_v3target_worksheet.md"
OUTPUT = ROOT / "data/adversarial/adaptive_v3/adaptive_v3target_attack.jsonl"


def val_families() -> list[str]:
    rows = [json.loads(line) for line in VAL.read_text(encoding="utf-8").splitlines() if line]
    return sorted({r["family_id"] for r in rows if r["branch"] == "attack"})


def canonical_rows() -> dict[str, dict[str, Any]]:
    out = {}
    for line in RELEASE.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        if row["variant_type"] == "canonical":
            out[row["family_id"]] = row
    return out


def worksheet() -> int:
    rows = canonical_rows()
    fams = val_families()
    lines = [
        "# Phiếu soạn: tấn công thích nghi nhắm BrokerGuard v3 (Dev-val)",
        "",
        "Sinh bằng `scripts/build_adaptive_v3target.py worksheet`. Mỗi họ: cơ chế, nhãn chi tiết,",
        "yêu cầu người dùng, nguồn chứa đoạn tiêm, và văn bản tấn công gốc (để tham khảo).",
        "Viết văn bản mới vào `adaptive_v3target.json` theo hướng dẫn `AUTHORING_ADAPTIVE_V3.md`.",
        "",
    ]
    for fam in fams:
        r = rows[fam]
        ov = r["overlay"]
        lines += [
            f"## {fam}",
            "",
            f"- Cơ chế: {ov['attack_category']} | nguồn: {ov['source_type']} `{ov['source_id']}` "
            f"(trust {ov['trust']}, sensitivity {ov['sensitivity']})",
            f"- Yêu cầu người dùng: {r['task']['instruction']}",
            f"- Văn bản tấn công gốc: {ov['attack_text']}",
            "",
        ]
    WORKSHEET.write_text("\n".join(lines), encoding="utf-8")
    print(f"worksheet: {len(fams)} families -> {WORKSHEET.relative_to(ROOT)}")
    return 0


def build() -> int:
    data = json.loads(ATTACKS.read_text(encoding="utf-8"))
    rows = canonical_rows()
    fams = set(val_families())
    unknown = sorted(set(data) - fams)
    if unknown:
        raise SystemExit(f"families not in Dev-val: {unknown}")
    out: list[str] = []
    for fam in sorted(data):
        texts = data[fam] if isinstance(data[fam], list) else [data[fam]]
        base = rows[fam]
        old = base["overlay"]["attack_text"]
        if base["content"].count(old) != 1:
            raise SystemExit(f"{fam}: original attack text not found exactly once in content")
        for k, text in enumerate(texts, 1):
            if not isinstance(text, str) or not text.strip():
                raise SystemExit(f"{fam}: empty attack text #{k}")
            row = json.loads(json.dumps(base))
            row["variant_id"] = f"ATK_{fam}_ADV_{chr(64 + k)}"  # A, B, ... (pattern has no digits)
            row["overlay"]["attack_text"] = text.strip()
            row["content"] = base["content"].replace(old, text.strip())
            fixture = rel.FixtureV3.model_validate(row)
            if fixture.split != "dev" or fixture.branch != "attack":
                raise SystemExit(f"{fam}: not a Dev attack row")
            out.append(fixture.model_dump_json())
    OUTPUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print(f"built {len(out)} fixtures over {len(data)}/{len(fams)} Dev-val families")
    print(f"{OUTPUT.relative_to(ROOT)} sha256 {digest}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["worksheet", "build"])
    args = parser.parse_args()
    return worksheet() if args.command == "worksheet" else build()


if __name__ == "__main__":
    raise SystemExit(main())
