"""Read-only native load/policy/timing/response audit for the four-task observer probe."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_observer_probe_v2 import (
    SCHEDULE,
    checkpoint,
    execution_sources,
    fixed_identity,
)
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v1 import Role
from react_agent.validation.context_policy_audit_v1 import publisher_policy
from react_agent.validation.context_stress_audit_v1 import audit_memory, equal
from react_agent.validation.efficient_requests_audit_v1 import _record
from react_agent.validation.guard_diagnostic_audit_v2 import audit as audit_guard
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.ordinary_native_audit_v1 import load, memory
from react_agent.validation.request_policy_audit_v1 import audit as audit_policy
from react_agent.validation.tokenizer_metadata_v1 import authenticate


def role_evidence(
    root: Path,
    role: Role,
    worker: dict[str, Any],
    identity: dict[str, Any],
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
    totals: list[int],
) -> dict[str, Any]:
    tokenizer = authenticate(tokenizers / f"{role}_tokenizer_config.json", role)
    publisher = publisher_policy(publishers / f"{role}_generation_config.json", role)
    metrics = root / "native" / f"{role}_hf_metrics.jsonl"
    rows = [_record(line) for line in metrics.read_text().splitlines()]
    require(bool(rows), "native load record required")
    load(rows[0], role, pin, totals)
    attempts = worker["attempts"]
    require(bool(attempts), "worker readiness required")
    require(
        rows[0]["load_seconds_including_hashes"] <= attempts[0]["load_seconds"],
        "startup includes load",
    )
    for field in ("model_id", "model_revision"):
        equal(rows[0][field], identity["pair_config"][role][field], "loaded model identity")
    files = (
        rows[0]["runtime_admission"]["files"]
        if role == "agent"
        else [f.model_dump() for f in pin.files]
    )
    for filename, evidence in (
        ("tokenizer_config.json", tokenizer),
        ("generation_config.json", publisher),
    ):
        matches = [f for f in files if f["name"] == filename]
        require(len(matches) == 1, "one admitted metadata file")
        for field in ("size", "sha256"):
            equal(matches[0][field], evidence["identity"][field], "metadata admission")
    require(
        tokenizer["eos_token_id"] in publisher["publisher_json"]["eos_token_id"],
        "tokenizer EOS binding",
    )
    requests = attempts[1:]
    calls = []
    verified = False
    if requests and all(r["status"] == "OK" for r in requests):
        joined = audit_policy(
            root / "policy" / role,
            root / "attention" / role,
            metrics,
            role=role,
            worker_pid=attempts[0]["pid"],
            expected_requests=len(requests),
            publisher=publisher["observed_publisher_expected"],
            pad_token_id=tokenizer["pad_token_id"],
        )
        for index, (row, attempt) in enumerate(zip(rows[1:], requests, strict=True), 1):
            require(
                row["call_seconds"] <= attempt["generation_seconds"], "native within worker call"
            )
            require(row["generate_seconds"] > 0, "positive measured generation time")
            if role == "guard":
                memory(row, role, totals)
            else:
                audit_memory(row["memory_before"], role, totals)
                audit_memory(row["memory_after"], role, totals)
            calls.append(
                dict(
                    index=index,
                    input_tokens=row["input_tokens"],
                    output_tokens=row["output_tokens"],
                    generate_seconds=row["generate_seconds"],
                    call_seconds=row["call_seconds"],
                    tokens_per_generate_second=row["output_tokens"] / row["generate_seconds"],
                )
            )
        verified = joined["valid"]
    elif not requests:
        require(len(rows) == 1, "no hidden generation")
        require(
            not (root / "policy" / role).exists() and not (root / "attention" / role).exists(),
            "no hidden request sidecars",
        )
    # Failed transport may leave partial metrics; keep it explicit and exclude
    # unjoined generation from timing denominators.
    return dict(
        worker_attempts=len(requests),
        load_verified=True,
        policy_attention_verified=verified,
        failed_or_partial=bool(requests) and not verified,
        calls=calls,
    )


def audit(
    probe: Path,
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
    commit: str,
    model_inventory: Path,
    environment: Path,
) -> dict[str, Any]:
    roots = dict(probe=probe, tokenizers=tokenizers, publishers=publishers, environment=environment)
    before = {name: inventory(path) for name, path in roots.items()}
    inventory_hash = hashlib.sha256(model_inventory.read_bytes()).hexdigest()
    identity = _record((probe / "identity.json").read_text())
    require(
        len(commit) == 40 and all(c in "0123456789abcdef" for c in commit), "source commit required"
    )
    for key, value in fixed_identity("hf", "valid").items():
        equal(identity.get(key), value, "fixed native protocol")
    for key, value in dict(
        source_commit=commit,
        snapshot_sha256=pin.sha256,
        model_inventory_sha256=inventory_hash,
        environment_sha256=before["environment"],
        execution_source_sha256=execution_sources(),
    ).items():
        equal(identity.get(key), value, "native input identity")
    equal(sorted(p.name for p in (probe / "tasks").iterdir()), sorted(SCHEDULE), "four tasks")
    tasks = []
    for key in SCHEDULE:
        root = probe / "tasks" / key
        saved = checkpoint(root)
        receipt = _record((root / "execution/pair_runtime.json").read_text())
        workers = receipt["snapshot"]["workers"]
        equal(sorted(workers), ["agent", "guard"], "paired workers")
        names = {"agent_hf_metrics.jsonl", "guard_hf_metrics.jsonl"}
        sidecar = root / "native/guard_response_diagnostics.jsonl"
        if sidecar.exists():
            names.add(sidecar.name)
        equal(
            sorted(p.name for p in (root / "native").iterdir()), sorted(names), "exact native files"
        )
        totals = [r["total_bytes"] for r in _record((root / "baseline.json").read_text())["memory"]]
        roles = {
            name: role_evidence(
                root, cast(Role, name), worker, identity, tokenizers, publishers, pin, totals
            )
            for name, worker in workers.items()
        }
        joined = audit_guard(root / "execution", sidecar, root / "witness.jsonl")
        legacy = [
            _record(line)
            for line in (root / "execution/runtime/trace_legacy.jsonl").read_text().splitlines()
        ]
        tools = sum(row["event"] == "tool_call_executed" for row in legacy)
        tasks.append(
            dict(
                key=key,
                terminal=saved["terminal"],
                recovered=saved["recovered"],
                roles=roles,
                guard_diagnostics=joined,
                executed_tool_calls=tools,
                startup_seconds=receipt["startup_seconds"],
                total_seconds=receipt["total_seconds"],
                observed_graceful=all(
                    w["lifecycle"] and all(e["method"] == "GRACEFUL" for e in w["lifecycle"])
                    for w in workers.values()
                ),
            )
        )
    equal({name: inventory(path) for name, path in roots.items()}, before, "audit inputs unchanged")
    equal(
        hashlib.sha256(model_inventory.read_bytes()).hexdigest(),
        inventory_hash,
        "inventory unchanged",
    )
    return dict(
        protocol="observer_native_audit_v2",
        artifact_integrity_valid=True,
        tasks=tasks,
        complete=True,
        expected=4,
        completed=4,
        source_commit=commit,
        raw_sha256=before,
        source_authenticated=False,
        guard_quality_validated=False,
        phase5_accepted=False,
    )
