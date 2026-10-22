"""Independent saved-evidence audit for the paired Dev API run; no inference."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from react_agent.serving.structured_api_v1 import canonical, sha

ROOT = Path(__file__).resolve().parents[1]


def checked(root: Path, name: str, expected: str) -> None:
    path = root / name
    if Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("unsafe relative path")
    cursor = path
    while cursor != root:
        if cursor.is_symlink():
            raise ValueError("linked evidence")
        cursor = cursor.parent
    if sha(path.read_bytes()) != expected:
        raise ValueError("evidence hash mismatch: " + name)


def audit(run: Path, journals: Path, evaluation: Path) -> dict[str, Any]:
    run = run.resolve()
    manifest = json.loads((run / "manifest.json").read_text())
    score = json.loads(evaluation.read_text())
    if manifest["protocol"] != "remote_api_paired_dev_v1":
        raise ValueError("unknown protocol")
    for name, expected in manifest["source_sha256"].items():
        if not name.startswith(("src/react_agent/", "scripts/")):
            raise ValueError("unexpected source scope")
        checked(ROOT, name, expected)
    for name, expected in manifest["environment_sha256"].items():
        checked(ROOT / "data/clean/v1_1/environment", name, expected)
    for name, expected in manifest["public_dev_sha256"].items():
        if name not in {"dev_attack.jsonl", "dev_benign.jsonl"}:
            raise ValueError("Dev-only scope")
        checked(ROOT / "data/adversarial/release_v2", name, expected)
    checked(ROOT, "docs/evaluation/remote_api_paired_dev_v1_protocol.md",
            manifest["evaluation_protocol_sha256"])
    checked(ROOT, "scripts/evaluate_remote_api_paired_dev_v1.py", manifest["evaluator_sha256"])
    if score["source_sha256"] != manifest["evaluator_sha256"]:
        raise ValueError("evaluator identity mismatch")
    schedule = manifest["schedule"]
    if len(schedule) != 28 or len({r["key"] for r in schedule}) != 28:
        raise ValueError("schedule must contain 28 unique conditions")
    scored = {r["key"]: r for r in score["conditions"]}
    checkpoints = []
    hashes = {}
    task_ids = set()
    for condition in schedule:
        folder = run / "conditions" / condition["key"]
        if not (folder / "completed.json").exists():
            continue
        saved = json.loads((folder / "completed.json").read_text())
        if saved["condition"] != condition or condition["key"] not in scored:
            raise ValueError("condition/evaluator coverage mismatch")
        if saved["status"] != scored[condition["key"]]["status"]:
            raise ValueError("terminal status mismatch")
        for name, expected in saved["artifact_sha256"].items():
            checked(folder, name, expected)
        meta = json.loads((folder / "execution/run_metadata.json").read_text())
        task_ids.add(meta["task_id"])
        if (meta["security_config"]["level"] != condition["level"]
                or meta["remote_cancellation_supported"] is not False
                or meta["guard_execution_attempt_count"] != saved["guard_attempts"]):
            raise ValueError("runtime level/lifecycle/attempt mismatch")
        if condition["level"] in {"A0", "A1"} and (
                meta["guard_execution"] is not None or saved["guard_attempts"]):
            raise ValueError("guard in agent-only level")
        paths = [folder / "completed.json", folder / "execution/run_metadata.json"]
        for path in paths:
            hashes[str(path.relative_to(ROOT))] = sha(path.read_bytes())
        checkpoints.append(saved)
    records = []
    for identity in manifest["identities"].values():
        session = journals.resolve() / sha(canonical(identity).encode())
        for start in session.glob("*.started.json"):
            record = json.loads(start.read_text())
            if record["task_id"] not in task_ids:
                continue
            end = start.with_name(start.name.replace(".started.", ".finished."))
            terminal = json.loads(end.read_text()) if end.is_file() else {"state":"started_only"}
            if record["identity"] != identity:
                raise ValueError("journal identity changed")
            if end.is_file() and (terminal["request_id"] != record["request_id"]
                or terminal["request_sha256"] != record["request_sha256"]):
                raise ValueError("delivery identity mismatch")
            records.append({"role": identity["role"], "state": terminal["state"]})
            for path in (start, end):
                if path.is_file():
                    hashes[str(path.relative_to(ROOT))] = sha(path.read_bytes())
    expected = sum(r["agent_attempts"] + r["guard_attempts"] for r in checkpoints)
    actual = len(records)
    incomplete = [r["key"] for r in schedule if r["key"] not in scored]
    # Partial schedules can contain a request in a started condition; never discard it.
    if not incomplete and actual != expected:
        raise ValueError("request/attempt count mismatch")
    for path in (run / "manifest.json", evaluation):
        hashes[str(path.resolve().relative_to(ROOT))] = sha(path.read_bytes())
    return {"completed_conditions": len(checkpoints), "missing_conditions": incomplete,
        "agent_attempts": sum(r["agent_attempts"] for r in checkpoints),
        "guard_attempts": sum(r["guard_attempts"] for r in checkpoints),
        "journal_requests": actual, "uncertain_requests": sum(
            r["state"] != "response_received" for r in records),
        "source_hashes_verified": len(manifest["source_sha256"]),
        "artifact_hashes_verified": sum(len(r["artifact_sha256"]) for r in checkpoints),
        "selected_evidence_sha256": hashes, "test_payloads_read": 0, "private_oracles_read": 0,
        "phase5_accepted": False, "scope": "bounded paired Dev diagnostic"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--journals", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run, args.journals, args.evaluation)
    with args.output.open("x") as stream:
        stream.write(canonical(result) + "\n")
    print(canonical({k: v for k, v in result.items() if k != "selected_evidence_sha256"}))


if __name__ == "__main__":
    main()
