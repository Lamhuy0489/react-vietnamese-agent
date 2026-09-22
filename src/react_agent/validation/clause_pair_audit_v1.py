"""Read-only candidate runtime joins, raw authority binding and origin replay."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from react_agent.foundation.artifacts import ArtifactStore, ArtifactType, SourceType
from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.a6_policy import admit
from react_agent.security_v1.authorization_anchors_v3 import PROFILE as ANCHORS
from react_agent.security_v1.authorization_anchors_v3 import audit_anchors
from react_agent.security_v1.clause_pair_runtime_v1 import RUNTIME_VERSION
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.processing_scope_v5 import PROFILE as SCOPE
from react_agent.security_v1.value_origin_v3 import PROFILE as ORIGIN
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex
from react_agent.validation import constrained_runtime_audit_v1 as constrained
from react_agent.validation import exit_pair_audit_v1 as observed
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record


def audit_task(output: Path) -> dict[str, Any]:
    before = inventory(output)
    baseline = SimpleNamespace(
        audit_task=bind(constrained.audit_task, RUNTIME_VERSION=RUNTIME_VERSION)
    )
    result = cast(dict[str, Any], bind(observed.audit_task, baseline=baseline)(output))
    if result["runtime_present"]:
        runtime = output / "runtime"
        meta = read_record(runtime / "run_metadata.json")
        receipt = read_record(output / "pair_runtime.json")
        equal(
            meta["clause_pair_profiles"],
            dict(anchors=ANCHORS, scope=SCOPE, origin=ORIGIN),
            "candidate component profiles",
        )
        equal(
            meta["processing_scope_profile"],
            SCOPE if receipt["security"]["session_trust"] else None,
            "candidate processing scope",
        )
        store = ArtifactStore.deserialize(
            meta["run_id"], (runtime / "artifacts/artifacts.jsonl").read_text()
        )
        users = [
            a
            for a in store.all()
            if a.source_type == SourceType.USER
            and a.artifact_type == ArtifactType.USER_INPUT
            and a.producer == "host_context"
            and not a.parents
            and not a.transformations
        ]
        equal(len(users), 1, "single raw host user")
        raw = users[0].content()
        if not isinstance(raw, str):
            raise ValueError("raw instruction string required")
        equal(text_hash(raw), receipt["task_sha256"], "raw host user identity")
        authority = audit_anchors(raw)
        equal(
            meta["authorization"],
            dict(
                profile=authority.profile,
                raw_user_sha256=text_hash(raw),
                blocked_by=authority.blocked_by,
                clauses=[asdict(c) for c in authority.clauses],
                anchors=authority.anchors.model_dump(mode="json"),
            ),
            "recomputed raw authorization",
        )
        if receipt["security"]["level"] == "A6":
            index = ValueOriginIndex(store)
            rows = [
                json.loads(line)
                for line in (runtime / "trace_value.jsonl").read_text().splitlines()
            ]
            equal(len(rows), meta["value_trace_count"], "value trace count")
            initial = 0
            for sequence, row in enumerate(rows, 1):
                for field, expected in dict(
                    sequence=sequence, run_id=meta["run_id"], task_id=meta["task_id"]
                ).items():
                    equal(row[field], expected, "value trace " + field)
                if row["stage"] in {"INITIAL", "POST"}:
                    if row["stage"] == "INITIAL":
                        initial += 1
                        equal(sequence, 1, "initial value admission first")
                        equal(row["source_artifact_id"], users[0].artifact_id, "initial user root")
                    equal(
                        admit(index, row["source_artifact_id"], row["step"]),
                        row["admission_error"],
                        "origin admission replay",
                    )
                elif row["stage"] == "PRE":
                    equal(row["value"]["index_sha256"], index.identity, "pre origin identity")
                elif row["stage"] != "FINAL":
                    raise ValueError("unknown value trace stage")
            equal(initial, 1, "single initial admission")
            equal(
                read_record(runtime / "value_index.json"), index.snapshot(), "replayed origin index"
            )
            equal(meta["value_index_hash"], index.identity, "final origin identity")
    equal(inventory(output), before, "candidate audit read-only")
    return result


def audit_exit(output: Path, *, expected_runtime: dict[str, str] | None = None) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        bind(observed.audit_exit, audit_task=audit_task)(
            output,
            expected_runtime=expected_runtime,
        ),
    )


def audit_join(
    execution: Path, sidecar: Path, witness: Path, *, expected_runtime: dict[str, str] | None = None
) -> dict[str, Any]:
    value = bind(observed.audit_join, audit_task=audit_task, audit_exit=audit_exit)(
        execution,
        sidecar,
        witness,
        expected_runtime=expected_runtime,
    )
    return {**value, "protocol": "clause_exit_constrained_join_v1"}
