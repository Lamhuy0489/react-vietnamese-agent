"""Independent ordinary A/B/A supervisor audit; artifact consistency, no inference."""

from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig
from react_agent.llm.model_pair_probe_v1 import MIN_RESIDENT, TOLERANCE, validate_memory
from react_agent.llm.model_pair_v1 import READY_COMMAND, ModelIdentity, PairConfig, Role
from react_agent.llm.ordinary_pair_probe_v1 import inputs, native_config
from react_agent.validation.context_stress_audit_v1 import equal, fields, inventory, sha
from react_agent.validation.efficient_requests_audit_v1 import _integer, _record, _seconds
from react_agent.validation.guard_probe_audit_v2 import require

ROLES: tuple[Role, ...] = ("agent", "guard")
ORDER = tuple((label, role) for label in ("A", "B", "A") for role in ROLES)


def read(path: Path) -> dict[str, Any]:
    return _record(path.read_text())


def hashed(value: Any) -> str:
    return text_hash(canonical_json(value))


def audit_worker(worker: dict[str, Any], role: Role, config: PairConfig) -> int:
    fields(worker, {"attempts", "lifecycle", "closed", "handle_pending"}, "worker")
    require(worker["closed"] is True and worker["handle_pending"] is False, "closed worker")
    attempts, lifecycle = worker["attempts"], worker["lifecycle"]
    require(len(attempts) == 4 and len(lifecycle) == 1, "one ready/three requests/one cleanup")
    event = lifecycle[0]
    fields(event, {"pid", "sequence", "reaped", "method", "exitcode", "elapsed_seconds"}, "cleanup")
    pid = _integer(event["pid"], 1, 2**31 - 1, "worker PID")
    _seconds(event["elapsed_seconds"], "cleanup time")
    equal(event["sequence"], 1, "cleanup sequence")
    require(event["reaped"] is True and type(event["exitcode"]) is int, "reaped exit")
    require(
        (event["method"], event["exitcode"]) in {("GRACEFUL", 0), ("TERMINATE", -15), ("KILL", -9)},
        "recognized cleanup",
    )
    fixtures = inputs()
    for index, attempt in enumerate(attempts):
        cold = index == 0
        execution = config.execution(role, cold=cold)
        generation = GenerationConfig(max_new_tokens=512 if cold or role == "agent" else 128)
        messages = (
            [{"role": "user", "content": READY_COMMAND}]
            if cold
            else fixtures[("A", "B", "A")[index - 1]][role]
        )
        expected = dict(
            pid=pid,
            sequence=index + 1,
            cold_start=cold,
            status="OK",
            reaped=False,
            worker_retained=True,
            execution_config_sha256=execution.identity,
            request_sha256=hashed(messages),
            generation_sha256=hashed(generation.model_dump()),
        )
        fields(
            attempt,
            set(expected) | {"load_seconds", "generation_seconds", "elapsed_seconds"},
            "attempt",
        )
        equal({k: attempt[k] for k in expected}, expected, "attempt identity")
        elapsed = _seconds(attempt["elapsed_seconds"], "attempt duration")
        duration = _seconds(attempt["generation_seconds"], "worker generation duration")
        if cold:
            load = _seconds(attempt["load_seconds"], "worker load duration")
        else:
            require(
                type(attempt["load_seconds"]) in (int, float) and attempt["load_seconds"] == 0,
                "one model load per worker",
            )
            load = 0.0
        require(load + duration <= elapsed < execution.timeout_seconds, "worker timing/deadline")
    return pid


def snapshot(closed: dict[str, Any], completed: int) -> dict[str, Any]:
    """Expected immutable prefix before cleanup, with READY excluded from ordinary count."""
    workers = {
        role: dict(
            attempts=closed["workers"][role]["attempts"][
                : 1 + sum(r == role for _, r in ORDER[:completed])
            ],
            lifecycle=[],
            closed=False,
            handle_pending=True,
        )
        for role in ROLES
    }
    return {
        **closed,
        "state": "READY",
        "events": closed["events"][: 4 + completed],
        "workers": workers,
    }


def audit(root: Path, *, commit: str, backend: Literal["stub", "hf"]) -> dict[str, Any]:
    """Expected commit/backend are supplied by the release owner, never taken from raw claims."""
    require(
        type(commit) is str and re.fullmatch(r"[0-9a-f]{40}", commit) is not None,
        "expected source commit",
    )
    require(backend in ("stub", "hf"), "explicit expected backend")
    before = inventory(root)
    expected_files = {
        "inputs.json",
        "manifest.json",
        "baseline.json",
        "ready.json",
        "closed.json",
        "summary.json",
    }
    expected_files.update(
        f"call_{i:02d}_{stage}.json"
        for i in range(1, 7)
        for stage in ("submitted", "returned", "memory")
    )
    expected_files.update(f"recovery_{i}.json" for i in range(6))
    expected_files.update(
        f"{role}_{'hf_metrics.jsonl' if backend == 'hf' else 'synthetic_load.json'}"
        for role in ROLES
    )
    equal(sorted(before), sorted(expected_files), "exact ordinary probe files")
    equal(sorted(p.name for p in root.iterdir()), sorted(expected_files), "flat probe tree")
    config = (
        native_config()
        if backend == "hf"
        else PairConfig(
            ModelIdentity("synthetic-agent", "v1"), ModelIdentity("synthetic-guard", "v1")
        )
    )
    fixtures = inputs()
    generation = {
        role: GenerationConfig(max_new_tokens=512 if role == "agent" else 128).model_dump()
        for role in ROLES
    }
    identity: dict[str, Any] = dict(backend=backend, source_commit=commit)
    if backend == "hf":
        identity.update(
            snapshot_sha256=config.guard.model_revision.split("snapshot-sha256:")[1],
            environment=dict(torch="2.10.0+cu128", cuda="12.8", transformers="5.5.0"),
            progress_policy="worker_thread_progress_v1",
        )
    equal(read(root / "inputs.json"), fixtures, "frozen public inputs")
    equal(
        read(root / "manifest.json"),
        dict(
            protocol="ordinary_pair_probe_v1",
            identity=identity,
            pair_config=asdict(config),
            pair_config_sha256=config.sha256,
            inputs_sha256=hashed(fixtures),
            generation=generation,
            generation_sha256={role: hashed(value) for role, value in generation.items()},
            order=[list(row) for row in ORDER],
            automatic_retry=False,
            benchmark_tasks=0,
            test_payloads_parsed=0,
            min_resident_bytes=list(MIN_RESIDENT),
            recovery_tolerance_bytes=TOLERANCE,
            recovery_samples=6,
            sample_interval_seconds=1.0 if backend == "hf" else 0.0,
        ),
        "manifest matches declared protocol",
    )
    closed = read(root / "closed.json")
    equal(sorted(closed["workers"]), sorted(ROLES), "role coverage")
    pids = {role: audit_worker(closed["workers"][role], role, config) for role in ROLES}
    owner = _integer(closed["owner_pid"], 1, 2**31 - 1, "owner PID")
    require(len({owner, *pids.values()}) == 3, "distinct owner/worker PIDs")
    events: list[dict[str, Any]] = []
    for role in ROLES:
        events.extend(
            [
                dict(
                    sequence=len(events) + 1,
                    stage="ready",
                    role=role,
                    pid=pids[role],
                    cold_execution_sha256=config.execution(role, cold=True).identity,
                ),
                dict(
                    sequence=len(events) + 2,
                    stage="warm_deadline",
                    role=role,
                    execution_sha256=config.execution(role, cold=False).identity,
                ),
            ]
        )
    for _, role in ORDER:
        events.append(dict(sequence=len(events) + 1, stage="generate", role=role, status="OK"))
    for role in reversed(ROLES):
        events.append(dict(sequence=len(events) + 1, stage="cleanup", role=role, reaped=True))
    equal(
        closed,
        dict(
            protocol="model_pair_v1",
            state="CLOSED",
            config_sha256=config.sha256,
            owner_pid=owner,
            events=events,
            workers=closed["workers"],
            phase5_accepted=False,
        ),
        "closed snapshot",
    )
    baseline_record = read(root / "baseline.json")
    fields(baseline_record, {"memory"}, "baseline")
    baseline = baseline_record["memory"]
    validate_memory(baseline)
    totals = [row["total_bytes"] for row in baseline]

    def memory(rows: Any, *, resident: bool) -> list[int]:
        validate_memory(rows)
        equal([r["total_bytes"] for r in rows], totals, "stable device totals")
        residual = [baseline[i]["free_bytes"] - rows[i]["free_bytes"] for i in (0, 1)]
        if resident:
            require(all(residual[i] >= MIN_RESIDENT[i] for i in (0, 1)), "both models resident")
        return residual

    ready = read(root / "ready.json")
    fields(ready, {"pair", "memory"}, "ready")
    equal(ready["pair"], snapshot(closed, 0), "ready snapshot")
    residency = memory(ready["memory"], resident=True)
    calls = []
    response_hashes: dict[str, list[str]] = {role: [] for role in ROLES}
    for index, (label, role) in enumerate(ORDER, 1):
        request_index = (index + 1) // 2
        equal(
            read(root / f"call_{index:02d}_submitted.json"),
            dict(
                index=index,
                label=label,
                role=role,
                request_index=request_index,
                messages_sha256=hashed(fixtures[label][role]),
                pair=snapshot(closed, index - 1),
            ),
            "submitted snapshot continuity",
        )
        returned = read(root / f"call_{index:02d}_returned.json")
        fields(
            returned,
            {"index", "label", "role", "response_sha256", "call_seconds", "pair"},
            "returned",
        )
        equal(
            {key: returned[key] for key in ("index", "label", "role", "pair")},
            dict(index=index, label=label, role=role, pair=snapshot(closed, index)),
            "returned snapshot continuity",
        )
        sha(returned["response_sha256"])
        response_hashes[role].append(returned["response_sha256"])
        host_seconds = _seconds(returned["call_seconds"], "host call duration")
        attempt = closed["workers"][role]["attempts"][request_index]
        require(attempt["elapsed_seconds"] <= host_seconds, "worker time within host call")
        observed = read(root / f"call_{index:02d}_memory.json")
        fields(observed, {"memory"}, "call memory")
        memory(observed["memory"], resident=True)
        calls.append(
            dict(
                index=index,
                role=role,
                label=label,
                request_index=request_index,
                worker_pid=pids[role],
                host_call_seconds=host_seconds,
                worker_seconds=attempt["generation_seconds"],
                response_sha256=returned["response_sha256"],
            )
        )
    recovery_times, residuals = [], []
    for index in range(6):
        row = read(root / f"recovery_{index}.json")
        fields(row, {"memory", "elapsed_seconds"}, "recovery")
        recovery_times.append(_seconds(row["elapsed_seconds"], "recovery time"))
        residuals.append(memory(row["memory"], resident=False))
    require(
        all(b > a for a, b in zip(recovery_times, recovery_times[1:], strict=False)),
        "recovery order",
    )
    require(all(abs(n) <= TOLERANCE for row in residuals[-3:] for n in row), "memory recovered")
    repeated = {role: values[0] == values[2] for role, values in response_hashes.items()}
    equal(
        read(root / "summary.json"),
        dict(
            protocol="ordinary_pair_probe_v1",
            status="EXECUTION_COMPLETE",
            execution_valid=True,
            phase5_accepted=False,
            native_validated=False,
            independent_audit_pending=backend == "hf",
            calls_submitted=6,
            responses_returned=6,
            actual_model_generation_calls=None if backend == "hf" else 0,
            reaped=True,
            recovery_valid=True,
            cleanup_error=False,
            repeated_a_equal=repeated,
            scope="Transport/residency observations only. A equality is descriptive, "
            "not an acceptance filter; native policy/source/memory audit and "
            "runtime/quality gates remain.",
        ),
        "summary recomputed from raw records",
    )
    if backend == "stub":
        for role in ROLES:
            equal(
                read(root / f"{role}_synthetic_load.json"),
                dict(pid=pids[role], actual_model_load=False, role=role),
                "stub load identity",
            )
    equal(inventory(root), before, "raw changed during audit")
    equal(sorted(p.name for p in root.iterdir()), sorted(expected_files), "probe tree changed")
    return dict(
        protocol="ordinary_pair_supervisor_audit_v1",
        valid=True,
        phase5_accepted=False,
        source_commit=commit,
        source_authenticated=False,
        backend=backend,
        supervisor_records_consistent=True,
        native_validated=False,
        native_model_calls=0 if backend == "stub" else None,
        calls=calls,
        workers=closed["workers"],
        worker_pids=pids,
        graceful_workers=sum(
            w["lifecycle"][0]["method"] == "GRACEFUL" for w in closed["workers"].values()
        ),
        worker_handles_reaped=2,
        repeated_a_equal=repeated,
        resident_bytes=residency,
        recovery_signed_residual_bytes=residuals,
        raw_sha256=before,
        scope="Independent artifact continuity audit. Native/source authentication, "
        "policy/attention/metric join and GPU release checks remain separate.",
    )
