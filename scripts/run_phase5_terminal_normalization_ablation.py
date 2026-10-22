"""Run the predeclared CPU-only terminal-line-ending ablation.

The ablation consumes synthetic strings only.  It is intentionally separate
from the frozen API runner and makes no model, Kaggle, or network request.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.security_v1.terminal_line_normalization_v1 import (
    PROFILE,
    canonical_email_equivalent,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "build/evaluation/phase5_terminal_normalization_ablation_v1"
DEFAULT_MANIFEST = ROOT / "experiments/manifests/phase5_terminal_normalization_ablation_v1.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output: Path = DEFAULT_OUT, manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    expected = "Phòng tiếp nhận hồ sơ: G204."
    cases = (
        ("exact", expected, True),
        ("terminal_lf", expected + "\n", True),
        ("terminal_crlf", expected + "\r\n", True),
        ("terminal_cr", expected + "\r", True),
        ("repeated_lf", expected + "\n\n", False),
        ("trailing_space", expected + " ", False),
        ("extra_text", expected + "\nGhi chú ngoài hồ sơ", False),
        ("private_marker", expected + " private@example.test", False),
        ("embedded_newline", "Phòng tiếp nhận\nhồ sơ: G204.", False),
    )
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for name, candidate, expected_allow in cases:
        result = canonical_email_equivalent(candidate, expected)
        actual_allow = result.status != "reject"
        if actual_allow != expected_allow:
            raise AssertionError(f"ablation control mismatch: {name}")
        rows.append(
            {
                "case": name,
                "expected_allow": expected_allow,
                "actual_allow": actual_allow,
                "status": result.status,
                "operation": result.operation,
                "raw_sha256": result.raw_sha256,
                "released_sha256": result.released_sha256,
                "raw_bytes": len(candidate.encode("utf-8")),
                "released_bytes": len(result.released_text.encode("utf-8")),
            }
        )
    evaluation = {
        "schema": "phase5_terminal_line_normalization_ablation_v1",
        "profile": PROFILE,
        "expected_canonical_sha256": hashlib.sha256(expected.encode("utf-8")).hexdigest(),
        "cases": rows,
        "allow_count": sum(row["actual_allow"] for row in rows),
        "deny_count": sum(not row["actual_allow"] for row in rows),
        "network_requests": 0,
        "model_requests": 0,
        "uncertain_delivery": False,
        "test_payloads_read": 0,
        "private_ground_truth_read": 0,
        "phase5_accepted": False,
    }
    evaluation_path = output / "evaluation.json"
    report_path = output / "report.md"
    evaluation_path.write_text(
        json.dumps(evaluation, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    report = "\n".join(
        [
            "# Phase 5 terminal-line normalization ablation — CPU",
            "",
            "Profile `terminal_line_ending_v1` removes at most one terminal LF, CRLF, or CR.",
            "It preserves raw/released hashes, rejects repeated endings and all other mismatches,",
            "and is not enabled in the frozen mainline runtime.",
            "",
            f"- Cases: {len(rows)}; allowed canonical equivalents: {evaluation['allow_count']}; "
            f"denied: {evaluation['deny_count']}",
            "- Model/API/network requests: 0; Test/private ground truth read: 0",
            "- Phase 5 acceptance: **false** (component ablation only)",
            "",
            "| Case | Result | Operation |",
            "|---|---|---|",
            *[
                f"| `{row['case']}` | {'ALLOW' if row['actual_allow'] else 'DENY'} | "
                f"`{row['operation']}` |"
                for row in rows
            ],
            "",
        ]
    )
    report_path.write_text(report, encoding="utf-8")
    artifact_sha256 = {
        "evaluation.json": _sha256(evaluation_path),
        "report.md": _sha256(report_path),
    }
    receipt = {
        "schema": "phase5_terminal_line_normalization_ablation_receipt_v1",
        "protocol": "docs/evaluation/phase5_terminal_normalization_ablation_v1_protocol.md",
        "run": output.relative_to(ROOT).as_posix(),
        "profile": PROFILE,
        "cases": len(rows),
        "allow_count": evaluation["allow_count"],
        "deny_count": evaluation["deny_count"],
        "network_requests": 0,
        "model_requests": 0,
        "uncertain_delivery": False,
        "test_payloads_read": 0,
        "private_ground_truth_read": 0,
        "artifact_sha256": artifact_sha256,
        "phase5_accepted": False,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.manifest), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
