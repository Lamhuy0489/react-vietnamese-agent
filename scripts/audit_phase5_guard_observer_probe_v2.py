"""Audit saved synthetic observer probes without rerunning model inference."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_observer_probe_v2 import SCHEDULE, checkpoint

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_probe(root: Path, condition: str, source_commit: str) -> dict[str, Any]:
    if not root.is_relative_to(ROOT / "results") or not root.is_dir():
        raise ValueError("saved probe must be under results")
    identity = json.loads((root / "identity.json").read_text())
    if identity["protocol"] != "guard_observer_probe_v2" or identity["condition"] != condition:
        raise ValueError("probe identity mismatch")
    if identity["source_commit"] != source_commit:
        raise ValueError("source commit mismatch")
    before = inventory(root)
    results = [checkpoint(root / "tasks" / key) for key in SCHEDULE]
    if inventory(root) != before:
        raise ValueError("probe changed during audit")
    expected_errors = condition == "trailing_comma"
    if any((r["terminal"] == "model_error") != expected_errors for r in results):
        raise ValueError("terminal condition mismatch")
    joins = [json.loads((root / "tasks" / key / "join.json").read_text()) for key in SCHEDULE]
    counts = [j["response_records"] for j in joins]
    if counts != ([1] * 4 if expected_errors else [2] * 4):
        raise ValueError("response coverage mismatch")
    lifecycle = []
    for key in SCHEDULE:
        receipt = json.loads((root / "tasks" / key / "execution/pair_runtime.json").read_text())
        lifecycle.extend(receipt["snapshot"]["workers"].values())
    clean = all(
        worker["closed"]
        and not worker["handle_pending"]
        and all(event["reaped"] for event in worker["lifecycle"])
        for worker in lifecycle
    )
    return {
        "condition": condition,
        "tasks": len(results),
        "completed": sum(r["terminal"] == "completed" for r in results),
        "model_errors": sum(r["terminal"] == "model_error" for r in results),
        "guard_response_records": sum(counts),
        "pre_post_pairs": sum(len(j["joined"]) == 2 for j in joins),
        "lifecycle_reaped": clean,
        "raw_file_count": len(before),
        "raw_sha256": {name: digest(root / name) for name in sorted(before)},
        "source_commit": source_commit,
        "test_payload_accessed": False,
        "new_inference": False,
        "phase5_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--valid", type=Path, required=True)
    parser.add_argument("--malformed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "experiments/manifests") or output.exists():
        raise ValueError("fresh manifest path required")
    commit = (
        __import__("subprocess")
        .check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True)
        .strip()
    )
    report = {
        "protocol": "guard_observer_probe_v2_cpu_audit",
        "valid": True,
        "source_commit": commit,
        "probes": [
            audit_probe(args.valid.resolve(), "valid", commit),
            audit_probe(args.malformed.resolve(), "trailing_comma", commit),
        ],
        "model_loads": 0,
        "gpu_runs": 0,
        "test_payload_accessed": False,
        "new_inference": False,
        "guard_quality_validated": False,
        "native_model_authenticated": False,
        "phase5_accepted": False,
        "scope": "four-task synthetic CPU observer probe per condition; no native HF/GPU inference",
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"valid": True, "output": str(output), "sha256": digest(output)}))


if __name__ == "__main__":
    main()
