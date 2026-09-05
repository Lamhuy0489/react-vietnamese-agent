"""Per-task durable checkpoints with identity-safe, missing-only resume."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from react_agent.agent.runtime import AgentRuntime
from react_agent.agent.state import RunResult
from react_agent.schemas.task import RuntimeTask
from react_agent.schemas.trace import TraceEvent


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def run_checkpointed(
    tasks: list[RuntimeTask],
    runtime_factory: Callable[[RuntimeTask], AgentRuntime],
    output: Path,
    identity: dict[str, Any],
    *,
    resume: bool = False,
) -> list[RunResult]:
    ids = [task.task_id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task IDs")
    expected_identity = {**identity, "task_ids": ids}
    if output.exists():
        if not resume:
            raise ValueError("output exists; choose a fresh directory or explicit --resume")
        identity_path = output / "identity.json"
        if (
            not identity_path.is_file()
            or json.loads(identity_path.read_text()) != expected_identity
        ):
            raise ValueError("resume identity differs from frozen inputs")
    else:
        output.mkdir(parents=True)
        atomic_json(output / "identity.json", expected_identity)
    checkpoint_root = output / "tasks"
    checkpoint_root.mkdir(exist_ok=True)
    results: list[RunResult] = []
    for task in tasks:
        # Task IDs are identifiers, never arbitrary output paths.
        if not task.task_id.replace("_", "").isalnum():
            raise ValueError("unsafe task ID")
        task_root = checkpoint_root / task.task_id
        receipt = task_root / "result.json"
        trace = task_root / "trace.jsonl"
        if receipt.exists():
            checkpoint = json.loads(receipt.read_text())
            if (
                not trace.is_file()
                or hashlib.sha256(trace.read_bytes()).hexdigest() != checkpoint["trace_sha256"]
            ):
                raise ValueError("checkpoint trace hash mismatch")
            result = RunResult.model_validate(checkpoint["result"])
            if result.task_id != task.task_id:
                raise ValueError("checkpoint task identity mismatch")
            # Preserve every terminal result, including semantic/model errors.
            results.append(result)
            continue
        if task_root.exists():
            raise ValueError(
                f"incomplete attempt retained for {task.task_id}; archive it with a deviation "
                "record before retrying infrastructure failure"
            )
        task_root.mkdir()
        result = runtime_factory(task).run(task, trace_path=trace)
        events = [TraceEvent.model_validate_json(line) for line in trace.read_text().splitlines()]
        if not events or events[0].event != "run_start" or events[-1].event != "run_end":
            raise ValueError("task did not produce a complete trace")
        atomic_json(
            receipt,
            {
                "result": result.model_dump(mode="json"),
                "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
            },
        )
        results.append(result)
        print(f"{task.task_id}: {result.status}", flush=True)
    atomic_json(output / "results.json", [result.model_dump(mode="json") for result in results])
    return results
