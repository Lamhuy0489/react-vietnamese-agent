"""Audit saved synthetic observer probes without rerunning model inference."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_observer_probe_v2 import SCHEDULE, checkpoint

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_probe(root: Path, condition: str, source_commit: str) -> dict[str, Any]:
    no_links(root)
    if not root.is_dir():
        raise ValueError("saved probe directory required")
    if condition not in {"valid", "trailing_comma"}:
        raise ValueError("known CPU condition required")
    if len(source_commit) != 40 or any(c not in "0123456789abcdef" for c in source_commit):
        raise ValueError("explicit source commit required")
    identity = json.loads((root / "identity.json").read_text())
    if identity["protocol"] != "guard_observer_probe_v2" or identity["condition"] != condition:
        raise ValueError("probe identity mismatch")
    if identity["source_commit"] != source_commit:
        raise ValueError("source commit mismatch")
    if identity["backend"] != "stub":
        raise ValueError("CPU audit requires scripted backend")
    if set(p.name for p in (root / "tasks").iterdir()) != set(SCHEDULE):
        raise ValueError("exact four task directories required")
    before = inventory(root)
    results = [checkpoint(root / "tasks" / key) for key in SCHEDULE]
    if inventory(root) != before:
        raise ValueError("probe changed during audit")
    expected_errors = condition == "trailing_comma"
    if any(r["terminal"] != ("model_error" if expected_errors else "completed") for r in results):
        raise ValueError("terminal condition mismatch")
    joins = [json.loads((root / "tasks" / key / "join.json").read_text()) for key in SCHEDULE]
    counts = [j["response_records"] for j in joins]
    if counts != ([1] * 4 if expected_errors else [2] * 4):
        raise ValueError("response coverage mismatch")
    for join in joins:
        if [row["stage"] for row in join["joined"]] != (
            ["PRE"] if expected_errors else ["PRE", "POST"]
        ):
            raise ValueError("guard stage coverage mismatch")
        if any(
            row["diagnostic"]["baseline"]["category"]
            != ("json_syntax" if expected_errors else "valid")
            for row in join["joined"]
        ):
            raise ValueError("guard category mismatch")
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
    if not clean or not all(r["recovered"] for r in results):
        raise ValueError("cleanup/recovery acceptance failed")
    if inventory(root) != before:
        raise ValueError("probe changed during audit")
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
        "execution_source_pins_verified": bool(identity.get("execution_source_sha256")),
        "test_payload_accessed": False,
        "new_inference": False,
        "phase5_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--valid", type=Path, required=True)
    parser.add_argument("--malformed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    no_links(args.output)
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "experiments/manifests") or output.exists():
        raise ValueError("fresh manifest path required")
    commit = args.source_commit
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
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"valid": True, "output": str(output), "sha256": digest(output)}))


if __name__ == "__main__":
    main()
