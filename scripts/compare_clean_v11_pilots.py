#!/usr/bin/env python3
"""Compare audited Dev results; explicitly retain missing model conditions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.llm.pilot_profiles import PROFILES


def comparison(pairs: list[tuple[Path, Path]]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    reference: dict[str, Any] | None = None
    for evaluation_path, audit_path in pairs:
        evaluation = json.loads(evaluation_path.read_text())
        audit = json.loads(audit_path.read_text())
        if (
            not audit["valid"]
            or audit["evaluation_sha256"]
            != hashlib.sha256(evaluation_path.read_bytes()).hexdigest()
        ):
            raise ValueError("evaluation lacks a valid matching audit")
        identity = evaluation["source_identity"]
        source = identity["model_id"] + "/" + identity["model_revision"]
        matches = [key for key, profile in PROFILES.items() if profile.source == source]
        if len(matches) != 1 or matches[0] in rows:
            raise ValueError("unknown or duplicate model condition")
        key = matches[0]
        comparable = {
            "task_ids": identity["task_ids"],
            "file_sha256": identity["file_sha256"],
            "generation": identity["generation"],
            "evaluator": evaluation["evaluator"],
        }
        if reference is not None and comparable != reference:
            raise ValueError("incompatible tasks, inputs, generation, or evaluator")
        reference = comparable
        if (
            evaluation["test_tasks_read"] != 0
            or evaluation["evaluated_tasks"] != 21
            or len({row["task_id"] for row in evaluation["results"]}) != 21
        ):
            raise ValueError("comparison requires the complete 21-task Dev selection")
        rows[key] = {
            "status": "audited",
            "source": source,
            "successes": evaluation["successes"],
            "tasks": 21,
            "success_rate": evaluation["successes"] / 21,
            "schema_validity_rate": audit["schema_validity_rate"],
            "terminal_statuses": audit["statuses"],
            "failure_reasons": evaluation["failures"],
            "task_seconds_mean": audit.get("task_seconds_mean"),
            "git_commit": identity["git_commit"],
            "chat_adapter": identity.get("chat_adapter", "native"),
            "evaluation_sha256": audit["evaluation_sha256"],
            "audit_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        }
    for key, profile in PROFILES.items():
        rows.setdefault(key, {"status": "not_run", "source": profile.source})
    return {
        "scope": "21-task Dev diagnostic; no Test or final model ranking",
        "complete": all(row["status"] == "audited" for row in rows.values()),
        "conditions": rows,
        "shared_inputs": reference,
        "limitations": [
            "Historical Qwen is reused; source commits/software images can differ.",
            "Gemma merges system text into first user turn and consecutive user turns.",
            "Different parameter counts; latency is descriptive, not a controlled speed rank.",
            "Fixed evaluator may reject valid unannotated answers/tool paths.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result",
        nargs=2,
        type=Path,
        action="append",
        required=True,
        metavar=("EVALUATION", "AUDIT"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("choose a fresh comparison output")
    report = comparison(args.result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"complete": report["complete"], "models": list(report["conditions"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
