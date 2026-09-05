"""Dataset identity and fail-closed protection for sealed clean benchmarks."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from react_agent.schemas.clean_task import CleanGroundTruth

FROZEN_COMPONENTS = frozenset(
    {
        "splits/dev.jsonl",
        "splits/test.jsonl",
        "private/dev_ground_truth.jsonl",
        "private/test_ground_truth.jsonl",
        "environment/documents/documents.json",
        "environment/cached_pages/pages.json",
        "environment/database/seed.json",
        "environment/database/university.db",
        "manifests/environment_manifest.json",
        "manifests/source_catalog.json",
        "reviews/review_log.jsonl",
        "schemas/clean_task.py",
    }
)


def assert_clean_version_writable(clean_root: Path) -> None:
    """Refuse regeneration as soon as any split/seal artifact exists.

    Presence, not a mutable ``frozen`` flag, is the guard. Malformed manifests
    and partially written splits must not reopen a version for overwriting.
    There is intentionally no force option: repairs require a new version.
    """
    markers = (
        "manifests/benchmark_manifest.json",
        "manifests/split_manifest.json",
        "splits/dev.jsonl",
        "splits/test.jsonl",
        "private/dev_ground_truth.jsonl",
        "private/test_ground_truth.jsonl",
    )
    if any(
        (clean_root / marker).exists() or (clean_root / marker).is_symlink() for marker in markers
    ):
        raise RuntimeError(
            f"Refusing to overwrite sealed or partially split clean version: {clean_root}. "
            "Preserve the existing artifacts; use an explicitly approved new dataset version."
        )


def semantic_instance_signature(item: CleanGroundTruth) -> str:
    """Compare fact/evidence identities independently of task-local labels.

    Recovery instructions and tool paths do not make an underlying answer
    instance independent. Equal signatures require group isolation; unequal
    signatures are NOT proof that two natural-language tasks are unrelated.
    This is a deterministic leakage screen, not a semantic-equivalence model.
    """
    facts = [
        fact.model_dump(mode="json", exclude={"fact_id"}) for fact in item.required_answer_facts
    ]
    evidence = [entry.model_dump(mode="json") for entry in item.required_evidence]
    return json.dumps(
        {
            "facts": sorted(facts, key=lambda entry: json.dumps(entry, sort_keys=True)),
            "retrieval_targets": sorted(item.retrieval_targets),
            "evidence": sorted(evidence, key=lambda entry: json.dumps(entry, sort_keys=True)),
            "missing_slots": sorted(item.missing_slots),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def semantic_instance_groups(items: list[CleanGroundTruth]) -> list[list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for item in items:
        groups[semantic_instance_signature(item)].append(item.task_id)
    return sorted(sorted(task_ids) for task_ids in groups.values() if len(task_ids) > 1)


def dataset_digest(component_hashes: dict[str, str]) -> str:
    return hashlib.sha256(
        "".join(f"{name}:{digest}\n" for name, digest in sorted(component_hashes.items())).encode()
    ).hexdigest()


def validate_frozen_components(
    clean_root: Path, schema_path: Path, manifest: dict[str, Any]
) -> list[str]:
    """Verify the complete required hash inventory and its aggregate identity."""
    failures: list[str] = []
    component_hashes = manifest.get("component_hashes")
    if not isinstance(component_hashes, dict):
        return ["frozen component_hashes must be an object"]
    if set(component_hashes) != FROZEN_COMPONENTS:
        failures.append("frozen component inventory does not match the required component set")
    well_formed = all(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
        for value in component_hashes.values()
    )
    if not well_formed:
        failures.append("frozen component hashes must be lowercase SHA-256 values")
    elif manifest.get("dataset_hash") != dataset_digest(component_hashes):
        failures.append("aggregate dataset hash mismatch")
    # Do not follow unknown manifest-controlled paths, even when they exist.
    for relative in sorted(FROZEN_COMPONENTS & component_hashes.keys()):
        path = schema_path if relative == "schemas/clean_task.py" else clean_root / relative
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != component_hashes[relative]
        ):
            failures.append(f"frozen component hash mismatch: {relative}")
    return failures
