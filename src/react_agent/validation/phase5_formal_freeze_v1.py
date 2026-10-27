"""Machine-readable Phase 5 20-DoD closure and no-go freeze.

The validator audits saved metadata and hashes only.  It never opens Test
payloads, private ground truth, model prompts, or model output.  A successful
run means that the current disposition is frozen and auditable; it does not
turn open DoD items into acceptance.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
MAINLINE_RECEIPT = ROOT / "experiments/manifests/phase5_mainline_native_dev.json"
FOLLOWUP_RECEIPT = ROOT / "experiments/manifests/phase5_followup_email_exact_epoch2.json"
ABLATION_RECEIPT = ROOT / "experiments/manifests/phase5_terminal_normalization_ablation_v1.json"
CLOSURE_DOC = ROOT / "docs/evaluation/phase5_closure_no_go_20260929.md"
EVIDENCE_MAP = ROOT / "docs/evaluation/phase5_dod_evidence_map.md"


class FreezeValidationError(ValueError):
    """Raised when closure evidence is missing, malformed, or unsafe."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FreezeValidationError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise FreezeValidationError(f"JSON object required: {path}")
    return value


def _inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()) or candidate.is_symlink():
        raise FreezeValidationError(f"evidence path escapes repository: {relative}")
    if not candidate.is_file():
        raise FreezeValidationError(f"evidence file missing: {relative}")
    return candidate


def _parse_table(path: Path, *, expected_header: str) -> dict[int, dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if expected_header not in "\n".join(lines):
        raise FreezeValidationError(f"expected table header missing: {path}")
    rows: dict[int, dict[str, str]] = {}
    for line in lines:
        match = re.match(
            r"^\|\s*(\d+)(?:\s*—[^|]*)?\s*\|\s*([^|]+)\|\s*([^|]+)\|",
            line,
        )
        if not match:
            continue
        number = int(match.group(1))
        if number in rows:
            raise FreezeValidationError(f"duplicate DoD row: {number}")
        rows[number] = {"status": match.group(2).strip(), "detail": match.group(3).strip()}
    if set(rows) != set(range(1, 21)):
        raise FreezeValidationError(f"expected exactly DoD 1..20, found {sorted(rows)}")
    return rows


def _verify_receipt(path: Path, root: Path, *, require_uncertain_false: bool) -> dict[str, Any]:
    receipt = _read_json(path)
    if receipt.get("phase5_accepted") is not False:
        raise FreezeValidationError(f"receipt must retain phase5_accepted=false: {path}")
    for field in ("test_payloads_read", "private_ground_truth_read"):
        if receipt.get(field) != 0:
            raise FreezeValidationError(f"held-out counter is nonzero: {path}:{field}")
    if require_uncertain_false and receipt.get("uncertain_delivery") is not False:
        raise FreezeValidationError(f"uncertain delivery is not closed: {path}")
    run = receipt.get("run")
    if not isinstance(run, str) or not run:
        raise FreezeValidationError(f"receipt run is missing: {path}")
    run_path = (root / run).resolve()
    if not run_path.is_relative_to(root.resolve()) or any(
        part.lower() in {"test", "private", "heldout", "ground_truth"}
        for part in run_path.relative_to(root.resolve()).parts
    ):
        raise FreezeValidationError(f"unsafe run path: {run}")
    hashes = receipt.get("artifact_sha256")
    if not isinstance(hashes, dict) or not hashes:
        raise FreezeValidationError(f"artifact hashes missing: {path}")
    for relative, expected in hashes.items():
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise FreezeValidationError(f"invalid artifact hash entry: {path}")
        artifact = _inside(root, f"{run}/{relative}")
        if _sha256(artifact) != expected:
            raise FreezeValidationError(f"artifact hash mismatch: {artifact}")
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha256(path),
        "run": run,
        "artifact_count": len(hashes),
        "phase5_accepted": False,
        "test_payloads_read": 0,
        "private_ground_truth_read": 0,
        "uncertain_delivery": receipt.get("uncertain_delivery"),
    }


def build_freeze(root: Path = ROOT) -> dict[str, Any]:
    """Build a deterministic formal freeze object without writing files."""

    root = root.resolve()
    closure = root / CLOSURE_DOC.relative_to(ROOT)
    evidence_map = root / EVIDENCE_MAP.relative_to(ROOT)
    rows = _parse_table(
        closure,
        expected_header="| DoD | Current disposition | Why it is still open |",
    )
    evidence_rows = _parse_table(
        evidence_map,
        expected_header=(
            "| DoD | Bằng chứng/đầu mối hiện có | Cổng còn phải đóng với candidate mới |"
        ),
    )
    for number in range(1, 21):
        if not evidence_rows[number]["status"] or not evidence_rows[number]["detail"]:
            raise FreezeValidationError(f"empty evidence-map row: {number}")

    mainline = _verify_receipt(
        root / MAINLINE_RECEIPT.relative_to(ROOT), root, require_uncertain_false=True
    )
    followup = _verify_receipt(
        root / FOLLOWUP_RECEIPT.relative_to(ROOT), root, require_uncertain_false=True
    )
    ablation = _verify_receipt(
        root / ABLATION_RECEIPT.relative_to(ROOT), root, require_uncertain_false=False
    )

    source_paths = (
        "src/react_agent/validation/phase5_formal_freeze_v1.py",
        "src/react_agent/security_v1/terminal_line_normalization_v1.py",
        "scripts/run_phase5_terminal_normalization_ablation.py",
        "docs/evaluation/phase5_closure_no_go_20260929.md",
        "docs/evaluation/phase5_dod_evidence_map.md",
        "docs/evaluation/phase5_terminal_normalization_ablation_v1_protocol.md",
    )
    source_sha256 = {relative: _sha256(_inside(root, relative)) for relative in source_paths}
    open_dod = [
        number
        for number, row in rows.items()
        if not row["status"].lower().startswith("accepted")
    ]
    if len(open_dod) != 20:
        raise FreezeValidationError("closure document must keep all 20 DoD open for this no-go")
    payload: dict[str, Any] = {
        "schema": "phase5_formal_freeze_receipt_v1",
        "freeze_date": "2026-09-29",
        "decision": "NO_GO",
        "phase5_accepted": False,
        "scope": "metadata/hash closure audit; no Test/private-ground-truth access; no inference",
        "dod_count": 20,
        "open_dod": open_dod,
        "dod_disposition": {
            str(number): {
                "current_disposition": rows[number]["status"],
                "closure_reason": rows[number]["detail"],
                "evidence_map": evidence_rows[number]["status"],
                "evidence_gate": evidence_rows[number]["detail"],
            }
            for number in range(1, 21)
        },
        "receipts": {
            "mainline": mainline,
            "followup_epoch2": followup,
            "normalization_ablation": ablation,
        },
        "source_sha256": source_sha256,
        "test_payloads_read": 0,
        "private_ground_truth_read": 0,
        "inference_performed": False,
        "uncertain_delivery_in_current_receipts": False,
    }
    payload["payload_sha256"] = _sha256_bytes(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    )
    return payload


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_freeze(root: Path = ROOT, output: Path | None = None) -> dict[str, Any]:
    if output is None:
        output = root / "experiments/manifests/phase5_formal_freeze_receipt_20260929.json"
    result = build_freeze(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    report = root / "docs/evaluation/phase5_formal_freeze_report_20260929.md"
    lines = [
        "# Phase 5 formal 20-DoD freeze — 2026-09-29",
        "",
        "The validator completed a metadata and hash audit of the declared closure evidence.",
        "It did not read Test payloads/private ground truth and did not perform inference.",
        "",
        f"- Decision: **{result['decision']}**",
        f"- Phase 5 accepted: **{str(result['phase5_accepted']).lower()}**",
        f"- DoD mapped: **{result['dod_count']}/20**",
        f"- Open DoD: **{len(result['open_dod'])}/20**",
        "- Current receipts: mainline native, exact-email recovery epoch 2, and the "
        "CPU normalization ablation",
        "- Test payloads/private ground truth read: **0/0**; inference performed: **false**",
        "",
        "| DoD | Current disposition | Evidence gate |",
        "|---:|---|---|",
    ]
    for number in range(1, 21):
        row = result["dod_disposition"][str(number)]
        lines.append(
            f"| {number} | {row['current_disposition']} | {row['evidence_gate']} |"
        )
    lines.extend(
        [
            "",
            "The receipt freezes a **NO_GO** disposition; it is not an acceptance claim.",
            "The next native experiment, if authorized, must name an open DoD and use "
            "a new protocol.",
            "",
        ]
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    return result
