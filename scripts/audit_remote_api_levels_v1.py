"""Audit saved seven-level transport diagnostic without inference or evaluator data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from react_agent.serving.structured_api_v1 import canonical, sha

ROOT = Path(__file__).resolve().parents[1]


def digest_checked(root: Path, name: str) -> str:
    relative = Path(name)
    path = root / relative
    if relative.is_absolute() or ".." in relative.parts or not path.resolve().is_relative_to(root):
        raise ValueError("unsafe evidence path")
    if any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        raise ValueError("linked evidence refused")
    return sha(path.read_bytes())


def audit(output: Path, journals: Path) -> dict[str, Any]:
    output = output.resolve()
    inventory = json.loads((output / "artifact_sha256.json").read_text())
    for name, expected in inventory.items():
        if digest_checked(output, name) != expected:
            raise ValueError("artifact hash mismatch")
    declaration = json.loads((output / "declaration.json").read_text())
    summary = json.loads((output / "summary.json").read_text())
    for name, expected in declaration["sources"].items():
        if not name.startswith(("src/react_agent/", "scripts/")):
            raise ValueError("source path outside declaration scope")
        if digest_checked(ROOT, name) != expected:
            raise ValueError("declared source changed after inference")
    expected_levels = [f"A{i}" for i in range(7)]
    if declaration["levels"] != expected_levels or summary["missing_levels"]:
        raise ValueError("incomplete declared schedule")
    if [r["level"] for r in summary["conditions"]] != expected_levels:
        raise ValueError("duplicate or out-of-order conditions")
    rows = []
    for row in summary["conditions"]:
        level = row["level"]
        saved = json.loads((output / f"{level}.completed.json").read_text())
        if row != saved:
            raise ValueError("checkpoint/summary mismatch")
        meta = json.loads((output / level / "run_metadata.json").read_text())
        if meta["security_config"]["level"] != level:
            raise ValueError("level mismatch")
        events = [json.loads(line) for line in (output / level / "trace_security.jsonl")
                  .read_text().splitlines()]
        stages = sorted({json.loads(e["data_json"])["stage"] for e in events
                         if e["event"] == "decision"})
        if stages != row["decision_stages"]:
            raise ValueError("decision stage mismatch")
        if row["guard_attempts"] != meta["guard_execution_attempt_count"]:
            raise ValueError("guard count mismatch")
        if level in {"A0", "A1"} and (row["guard_attempts"] or meta["guard_execution"]):
            raise ValueError("agent-only level received guard")
        if meta["remote_cancellation_supported"] is not False:
            raise ValueError("remote cancellation overclaim")
        lifecycle = meta["guard_lifecycle_events"]
        rows.append({"level": level, "terminal_status": row["status"],
            "tool_sequence": row["tool_sequence"], "final_answer": row["final_answer"],
            "decision_stages": stages, "agent_attempts": row["agent_attempts"],
            "guard_attempts": row["guard_attempts"],
            "local_cleanup_methods": [e["method"] for e in lifecycle],
            "all_local_workers_reaped": all(e["reaped"] for e in lifecycle)})
    receipts = {}
    requests = 0
    for identity in declaration["identities"].values():
        root = journals.resolve() / sha(canonical(identity).encode())
        for started in root.glob("*.started.json"):
            record = json.loads(started.read_text())
            if record["task_id"] != declaration["task"]["task_id"]:
                continue
            finished = started.with_name(started.name.replace(".started.", ".finished."))
            terminal = json.loads(finished.read_text())
            if (record["identity"] != identity or terminal["state"] != "response_received"
                    or terminal["request_sha256"] != record["request_sha256"]):
                raise ValueError("uncertain or mismatched delivery")
            for path in (started, finished):
                receipts[str(path.relative_to(ROOT))] = sha(path.read_bytes())
            requests += 1
    if requests != sum(r["agent_attempts"] + r["guard_attempts"] for r in rows):
        raise ValueError("delivery/attempt count mismatch")
    return {"conditions": rows, "artifact_hashes_verified": len(inventory),
        "source_hashes_verified": len(declaration["sources"]), "http_response_records": requests,
        "journal_artifact_sha256": receipts, "remote_cancellation_proven": False,
        "test_payloads_read": 0, "phase5_accepted": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--journals", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.run, args.journals)
    if args.output.resolve().is_relative_to(ROOT / "data"):
        raise ValueError("audit output cannot overlap data")
    with args.output.open("x") as stream:
        stream.write(canonical(result) + "\n")
    print(canonical({k: v for k, v in result.items() if k != "journal_artifact_sha256"}))


if __name__ == "__main__":
    main()
