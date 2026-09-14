"""Backend-bound grouped checkpoint and recovery joins; read-only, never repair."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.validation.guard_diagnostic_audit_v1 import audit as audit_guard
from react_agent.validation.pair_runtime_audit_v3 import audit_task


def audit_checkpoint(root: Path, identity: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    no_links(root)
    before = inventory(root)
    saved: dict[str, Any] = json.loads((root / "checkpoint.json").read_text())
    raw = {key: value for key, value in before.items() if key != "checkpoint.json"}
    if set(saved) != {
        "protocol",
        "identity_sha256",
        "key",
        "terminal",
        "raw_sha256",
        "recovered",
    } or (
        saved["protocol"] != "grouped_dev_checkpoint_v2"
        or saved["identity_sha256"] != text_hash(canonical_json(identity))
        or saved["key"] != task["key"]
        or root.name != task["key"]
        or saved["raw_sha256"] != raw
    ):
        raise ValueError("grouped checkpoint identity or raw hashes differ")
    execution = root / "execution"
    audit_task(execution)
    receipt = json.loads((execution / "pair_runtime.json").read_text())
    meta = json.loads((execution / "runtime/run_metadata.json").read_text())
    paired = task["level"] not in {"A0", "A1"}
    catalog = SourceCatalog.model_validate(task["source_catalog"])
    expected = dict(
        task_id=task["task_id"],
        task_sha256=task["task_sha256"],
        security=identity["security"][task["level"]],
        runtime_config=identity["runtime"],
        generation=identity["generation"],
        terminal=saved["terminal"],
        source_catalog_sha256=text_hash(catalog.model_dump_json()),
        pair_config=identity["pair_config"] if paired else None,
        agent_execution=None if paired else identity["agent_execution"],
        error_class=None,
        cleanup_error_class=None,
    )
    if any(receipt.get(k) != v for k, v in expected.items()) or (
        meta.get("runtime_version") != identity["runtime_version"]
        or meta.get("source_catalog") != task["source_catalog"]
        or meta.get("processing_scope_profile")
        != ("a4_processing_scope_v5" if task["level"] in {"A4", "A5", "A6"} else None)
    ):
        raise ValueError("checkpoint runtime or input binding differs")
    for worker in receipt["snapshot"]["workers"].values():
        if (
            not worker["closed"]
            or worker["handle_pending"]
            or not all(event["reaped"] for event in worker["lifecycle"])
        ):
            raise ValueError("checkpoint worker not closed/reaped")
    sidecar = (
        root / "native/guard_response_diagnostics.jsonl"
        if identity["backend"] == "hf"
        else root / "guard_diagnostics.jsonl"
    )
    if paired:
        audit_guard(execution, sidecar)
    elif sidecar.exists():
        raise ValueError("A0/A1 must not contain guard diagnostic evidence")
    from react_agent.llm.model_pair_probe_v1 import validate_memory

    baseline = json.loads((root / "baseline.json").read_text())["memory"]
    samples = json.loads((root / "recovery.json").read_text())["memory"]
    validate_memory(baseline)
    if len(samples) != identity["recovery"]["samples"]:
        raise ValueError("complete recovery samples required")
    for sample in samples:
        validate_memory(sample)
    recovered = all(
        row[i]["total_bytes"] == baseline[i]["total_bytes"]
        and abs(row[i]["free_bytes"] - baseline[i]["free_bytes"])
        <= identity["recovery"]["tolerance_bytes"]
        for row in samples[-identity["recovery"]["stable_tail"] :]
        for i in (0, 1)
    )
    if type(saved["recovered"]) is not bool or saved["recovered"] != recovered:
        raise ValueError("recovery outcome contradicts observations")
    import math

    timing = json.loads((root / "task_timing.json").read_text())
    elapsed = timing.get("task_wall_seconds_including_setup_cleanup_recovery")
    if set(timing) != {
        "task_wall_seconds_including_setup_cleanup_recovery",
        "backend",
        "quality_scoring",
    } or (
        type(elapsed) not in (int, float)
        or not math.isfinite(elapsed)
        or elapsed < receipt["total_seconds"]
        or timing["backend"] != identity["backend"]
        or timing["quality_scoring"] is not False
    ):
        raise ValueError("task timing/backend binding invalid")
    if inventory(root) != before:
        raise ValueError("checkpoint changed during audit")
    return saved


def audit_prefix(output: Path, identity: dict[str, Any], shard: int) -> list[dict[str, Any]]:
    if type(shard) is not int or not 0 <= shard < 8:
        raise ValueError("known shard required")
    no_links(output)
    no_links(output / "identity.json")
    no_links(output / "tasks")
    if set(p.name for p in output.iterdir()) != {"identity.json", "tasks"}:
        raise ValueError("unexpected grouped output files")
    expected = {"run": identity, "shard": shard}
    if json.loads((output / "identity.json").read_text()) != expected:
        raise ValueError("grouped run identity mismatch")
    tasks = [t for t in identity["tasks"] if t["shard"] == shard]
    entries = sorted((output / "tasks").iterdir())
    present = {p.name for p in entries}
    if present != {t["key"] for t in tasks[: len(entries)]}:
        raise ValueError("completed task keys must form an exact prefix")
    results = []
    for task in tasks[: len(entries)]:
        root = output / "tasks" / task["key"]
        no_links(root)
        if not (root / "checkpoint.json").is_file():
            raise ValueError("partial attempt retained; no automatic retry")
        saved = audit_checkpoint(root, identity, task)
        if not saved["recovered"]:
            raise ValueError("unrecovered checkpoint retained; cannot continue")
        results.append(saved)
    return results
