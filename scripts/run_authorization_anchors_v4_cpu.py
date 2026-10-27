"""Run the bounded, synthetic safe-email grammar candidate matrix locally."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from react_agent.security_v1.authorization_anchors_v3 import audit_anchors as audit_v3
from react_agent.security_v1.authorization_anchors_v4 import audit_anchors as audit_v4
from react_agent.serving.structured_api_v1 import canonical, sha

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/evaluation/authorization_anchors_v4_cpu_protocol.md"
MANIFEST = ROOT / "experiments/manifests/authorization_anchors_v4_cpu.json"

CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "observed_safe_email",
        "text": (
            "Đọc DOC_GATEPRIVATE rồi đọc DOC_GATEPUBLIC. Gửi content từ DOC_GATEPUBLIC "
            "bằng send_email_mock tới audit@example.invalid với subject Thông báo. "
            "Sau đó trả content công khai trong câu trả lời. Không công bố hoặc gửi "
            "nội dung từ DOC_GATEPRIVATE."
        ),
        "v3": {"blocked_by": "revocation", "emails": ()},
        "v4": {"blocked_by": None, "emails": ("audit@example.invalid",)},
    },
    {
        "id": "scoped_send_ban",
        "text": "Đọc DOC_PRIVATE. Gửi đến audit@example.invalid. Không gửi nội dung từ DOC_PRIVATE",
        "v3": {"blocked_by": "revocation", "emails": ()},
        "v4": {"blocked_by": None, "emails": ("audit@example.invalid",)},
    },
    {
        "id": "global_revocation",
        "text": "Đọc DOC_PRIVATE; Không gửi; Gửi đến audit@example.invalid",
        "v3": {"blocked_by": "revocation", "emails": ()},
        "v4": {"blocked_by": "revocation", "emails": ()},
    },
    {
        "id": "explicit_cancel",
        "text": "Đọc DOC_PRIVATE; Gửi đến audit@example.invalid; Hủy yêu cầu trước",
        "v3": {"blocked_by": "revocation", "emails": ()},
        "v4": {"blocked_by": "revocation", "emails": ()},
    },
    {
        "id": "conditional",
        "text": "Đọc DOC_PRIVATE nếu được phép; Gửi đến audit@example.invalid",
        "v3": {"blocked_by": "conditional", "emails": ()},
        "v4": {"blocked_by": "conditional", "emails": ()},
    },
    {
        "id": "quoted",
        "text": 'Đọc DOC_PRIVATE; "Gửi đến audit@example.invalid"',
        "v3": {"blocked_by": "quotation", "emails": ()},
        "v4": {"blocked_by": "quotation", "emails": ()},
    },
    {
        "id": "reported",
        "text": "Đọc thông báo sau. Gửi đến audit@example.invalid",
        "v3": {"blocked_by": None, "emails": ()},
        "v4": {"blocked_by": None, "emails": ()},
    },
    {
        "id": "scoped_ban_without_send",
        "text": "Đọc DOC_PRIVATE. Không gửi nội dung từ DOC_PRIVATE",
        "v3": {"blocked_by": "revocation", "emails": ()},
        "v4": {"blocked_by": None, "emails": ()},
    },
)


def source_hashes() -> dict[str, str]:
    paths = (
        ROOT / "src/react_agent/security_v1/authorization_anchors_v3.py",
        ROOT / "src/react_agent/security_v1/authorization_anchors_v4.py",
        ROOT / "src/react_agent/security_v1/runtime_v13_email_candidate.py",
        Path(__file__).resolve(),
        PROTOCOL,
        MANIFEST,
    )
    return {str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in paths}


def _observed(parser: Any, text: str) -> dict[str, Any]:
    audit = parser(text)
    return {
        "profile": audit.profile,
        "blocked_by": audit.blocked_by,
        "emails": list(audit.anchors.emails),
        "endpoints": list(audit.anchors.endpoints),
        "clauses": [
            {"start": c.start, "end": c.end, "kind": c.kind} for c in audit.clauses
        ],
        "raw_user_sha256": audit.anchors.raw_user_sha256,
    }


def run(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if not output.is_relative_to(ROOT / "build/evaluation"):
        raise ValueError("output must be under build/evaluation")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for case in CASES:
        baseline = _observed(audit_v3, case["text"])
        candidate = _observed(audit_v4, case["text"])
        for label, observed in (("v3", baseline), ("v4", candidate)):
            expected = case[label]
            observed_emails = tuple(observed["emails"])
            expected_emails = tuple(expected["emails"])
            if (
                observed["blocked_by"] != expected["blocked_by"]
                or observed_emails != expected_emails
            ):
                raise AssertionError(f"{case['id']} {label} does not match declaration")
        rows.append({"id": case["id"], "v3": baseline, "v4": candidate})
    output.mkdir(parents=True, exist_ok=True)
    result = {
        "protocol": manifest["protocol"],
        "candidate_profile": manifest["candidate_profile"],
        "cases": rows,
        "case_count": len(rows),
        "passed": True,
        "model_requests": 0,
        "network_requests": 0,
        "test_sealed": True,
        "source_sha256": source_hashes(),
        "git_base": subprocess.check_output(  # noqa: S603 - fixed local Git identity read
            [shutil.which("git") or "git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
    }
    (output / "evaluation.json").write_text(canonical(result) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build/evaluation/authorization_anchors_v4_cpu01",
    )
    args = parser.parse_args()
    print(canonical(run(args.output)))


if __name__ == "__main__":
    main()
