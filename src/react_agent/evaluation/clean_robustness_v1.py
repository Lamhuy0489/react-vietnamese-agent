"""RQ3 clean robustness v1: run surface variants of clean tasks and score them with the
canonical task's ground truth (decision log 2026-10-26, sealed 2026-11-05).

A variant is the canonical public task with only ``instruction`` replaced; ``task_id`` stays
the canonical id, so the model sees exactly what the canonical run sees except the wording,
and the canonical fault plan (error-recovery tasks) applies unchanged. Checkpoints live under
``tasks/<variant_id>/``. ``dev_smoke_variants`` builds mechanical variants of public Dev tasks
for pipeline checks only; the held-out set is the sealed ``robustness_v1`` release.
``canonical_variants`` runs the unmodified tasks through the same pipeline (the clean Test
of RQ1 and the paired baseline of RQ3).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from react_agent.agent.state import RunResult
from react_agent.authoring.robustness_v1 import MECHANICAL, SCHEMA, machine_literals
from react_agent.authoring.surfaces import draft_surface
from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.clean_task import CleanGroundTruth, CleanPublicTask
from react_agent.schemas.trace import TraceEvent
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.clean_v11 import calls_from_trace, score_observation


def variant_tasks(public: dict[str, CleanPublicTask], variants: list[dict[str, Any]]
                  ) -> list[tuple[dict[str, Any], CleanPublicTask]]:
    """Pair each variant with its canonical task carrying the variant instruction."""
    out = []
    for variant in variants:
        canonical = public[variant["canonical_task_id"]]
        if variant["split"] != canonical.split:
            raise ValueError(f"{variant['variant_id']}: split differs from its canonical")
        out.append((variant, canonical.model_copy(update={"instruction": variant["instruction"]})))
    return out


def canonical_variants(tasks: list[CleanPublicTask]) -> list[dict[str, Any]]:
    """The canonical tasks themselves in variant form (``variant_id`` = task id)."""
    return [{"schema_version": SCHEMA, "variant_id": t.task_id, "canonical_task_id": t.task_id,
             "split": t.split, "category": t.category, "variant_type": "canonical",
             "instruction": t.instruction, "review_status": "canonical"} for t in tasks]


def dev_smoke_variants(dev: list[CleanPublicTask], limit: int) -> list[dict[str, Any]]:
    """Mechanical variants of the first ``limit`` public Dev tasks (pipeline smoke only)."""
    rows = []
    for task in dev[:limit]:
        literals = tuple(dict.fromkeys(
            lit for lit in machine_literals(task.instruction) if not lit.isdigit()))
        for variant_type in MECHANICAL:
            text = draft_surface(task.instruction, variant_type,  # type: ignore[arg-type]
                                 protected_literals=literals).raw
            rows.append({"schema_version": SCHEMA,
                         "variant_id": f"rob_{task.task_id}_{variant_type}",
                         "canonical_task_id": task.task_id, "split": task.split,
                         "category": task.category, "variant_type": variant_type,
                         "instruction": text, "review_status": "dev_smoke"})
    return rows


def score_checkpoint(directory: Path, truth: CleanGroundTruth, environment: Path
                     ) -> dict[str, Any]:
    """Verify one variant checkpoint against its trace and score it with ``truth``."""
    checkpoint = json.loads((directory / "result.json").read_text(encoding="utf-8"))
    trace_path = directory / "trace.jsonl"
    if hashlib.sha256(trace_path.read_bytes()).hexdigest() != checkpoint["trace_sha256"]:
        raise ValueError(f"{directory.name}: checkpoint trace hash mismatch")
    result = RunResult.model_validate(checkpoint["result"])
    events = [TraceEvent.model_validate_json(line)
              for line in trace_path.read_text(encoding="utf-8").splitlines()]
    if result.task_id != truth.task_id or any(
            e.task_id != truth.task_id or e.run_id != result.run_id for e in events):
        raise ValueError(f"{directory.name}: trace task/run identity mismatch")
    if not events or events[0].event != "run_start" or events[-1].event != "run_end":
        raise ValueError(f"{directory.name}: missing terminal trace boundary")
    answers = [e.data["answer"] for e in events if e.event == "final_answer"]
    if result.status == "completed" and answers != [result.final_answer]:
        raise ValueError(f"{directory.name}: final answer differs from checkpoint")
    calls = calls_from_trace(events)
    if [name for name, _, _ in calls] != result.tool_sequence:
        raise ValueError(f"{directory.name}: tool sequence differs from checkpoint")
    broker = ToolBroker(build_clean_registry(environment), TraceLogger())
    outcome = score_observation(truth, result.final_answer or "", calls, broker,
                                status=result.status)
    return {"status": result.status, "trace_events": len(events), **outcome}


def summarize(rows: list[dict[str, Any]],
              canonical_success: dict[str, bool] | None = None) -> dict[str, Any]:
    """Successes per variant type; with canonical results, the paired flips per type."""
    per_type: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counts = per_type[row["variant_type"]]
        counts["variants"] += 1
        counts["successes"] += bool(row["success"])
        counts["model_error"] += row["status"] == "model_error"
        if canonical_success is not None:
            base = canonical_success[row["canonical_task_id"]]
            counts["canonical_successes"] += base
            counts["lost"] += base and not row["success"]
            counts["gained"] += row["success"] and not base
    return {name: dict(counts) for name, counts in sorted(per_type.items())}
