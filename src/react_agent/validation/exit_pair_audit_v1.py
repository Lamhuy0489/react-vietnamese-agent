"""Read-only role/task/PID join for the opt-in paired exit diagnostic."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.exit_pair_v1 import ExitPairConfig
from react_agent.llm.model_pair_v1 import ModelIdentity, Role
from react_agent.security_v1.exit_milestones_v1 import EVENTS, runtime_identity
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import constrained_runtime_audit_v1 as baseline
from react_agent.validation import pair_runtime_audit_v3 as pair_audit
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.exit_milestones_v1 import audit_milestones
from react_agent.validation.guard_probe_audit_v2 import require


def audit_task(output: Path) -> dict[str, Any]:
    inventory(output)  # Reject linked descendants before frozen auditors read them.
    shutdown = bind(pair_audit.audit_shutdown_bindings, ShutdownPairConfig=ExitPairConfig)
    original = bind(pair_audit.audit_task, audit_shutdown_bindings=shutdown)
    return cast(dict[str, Any], bind(baseline.audit_task, original_task=original)(output))


def checked_runtime(value: Any) -> dict[str, str]:
    """Validate measured identity shape, not publisher/remote authenticity."""
    expected = {
        "implementation",
        "version",
        "system",
        "machine",
        "bootstrap_sha256",
        "finalizers_sha256",
        "threads_sha256",
    }
    require(type(value) is dict and set(value) == expected, "interpreter fields")
    require(all(type(v) is str and v for v in value.values()), "interpreter strings")
    equal(value["implementation"], "CPython", "interpreter implementation")
    require(
        re.fullmatch(r"3\.\d+\.\d+[\w.+-]*", value["version"]) is not None, "interpreter version"
    )
    for key in ("bootstrap_sha256", "finalizers_sha256", "threads_sha256"):
        require(re.fullmatch(r"[0-9a-f]{64}", value[key]) is not None, "interpreter hash")
    return dict(value)


def audit_exit(output: Path, *, expected_runtime: dict[str, str] | None = None) -> dict[str, Any]:
    runtime = checked_runtime(runtime_identity() if expected_runtime is None else expected_runtime)
    before = inventory(output)
    audit_task(output)
    receipt = read_record(output / "pair_runtime.json")
    record = read_record(output / "exit_milestones.json")
    equal(
        sorted(record),
        sorted(
            (
                "protocol",
                "task_id",
                "task_sha256",
                "owner_pid",
                "pair_config_sha256",
                "pair_runtime_sha256",
                "pair_snapshot_sha256",
                "observed_until",
                "workers",
                "phase5_accepted",
            )
        ),
        "exit task fields",
    )
    values = dict(receipt["pair_config"])
    for role in ("agent", "guard"):
        values[role] = ModelIdentity(**values[role])
    config = ExitPairConfig(**values)
    for name, expected in dict(
        protocol="exit_pair_task_v1",
        task_id=receipt["task_id"],
        task_sha256=receipt["task_sha256"],
        owner_pid=receipt["owner_pid"],
        pair_config_sha256=config.sha256,
        pair_runtime_sha256=before["pair_runtime.json"],
        pair_snapshot_sha256=text_hash(canonical_json(receipt["snapshot"])),
        phase5_accepted=False,
    ).items():
        equal(record[name], expected, "exit binding " + name)
    end = record["observed_until"]
    require(type(end) is float and math.isfinite(end) and end > 0, "observation end")
    equal(sorted(record["workers"]), ["agent", "guard"], "observer roles")
    roles = {}
    for role in ("agent", "guard"):
        observed = record["workers"][role]
        equal(sorted(observed), ["milestones", "status"], "role fields")
        equal(observed["status"], "reaped", "unreaped observer is not accepted")
        worker = receipt["snapshot"]["workers"][role]
        warmed = any(
            e["stage"] == "warm_deadline" and e["role"] == role
            for e in receipt["snapshot"]["events"]
        )
        execution = config.execution(cast(Role, role), cold=not warmed)
        markers = observed["milestones"]
        equal(markers["runtime"], runtime, "observer interpreter")
        equal(markers["execution_config_sha256"], execution.identity, "last worker config")
        events = worker["lifecycle"]
        if not events:
            require(not worker["attempts"], "started worker lacks lifecycle")
            equal(
                markers,
                dict(
                    protocol="exit_milestones_v1",
                    runtime=runtime,
                    execution_config_sha256=execution.identity,
                    events=dict.fromkeys(EVENTS),
                ),
                "unstarted observer",
            )
            boundary = "not_started"
        else:
            require(len(events) == 1, "single worker shutdown required")
            boundary = audit_milestones(
                markers,
                events[0],
                runtime=runtime,
                config_sha256=execution.identity,
                observed_until=end,
            )
        roles[role] = dict(
            boundary=boundary,
            pid=events[0]["pid"] if events else None,
            method=events[0]["method"] if events else "NOT_STARTED",
        )
    equal(inventory(output), before, "exit audit read-only")
    return dict(
        protocol="exit_pair_join_v1",
        valid=True,
        roles=roles,
        exit_receipt_sha256=before["exit_milestones.json"],
        native_cause_identified=False,
        phase5_accepted=False,
    )


def audit_join(
    execution: Path, sidecar: Path, witness: Path, *, expected_runtime: dict[str, str] | None = None
) -> dict[str, Any]:
    # The old join itself binds its guard observer to audit_task.
    result = bind(baseline.audit_join, audit_task=audit_task)(
        execution, sidecar, witness, execution.parent / "constraints"
    )
    return dict(
        protocol="exit_constrained_join_v1",
        constrained=result,
        exit=audit_exit(execution, expected_runtime=expected_runtime),
        valid=True,
        phase5_accepted=False,
    )
