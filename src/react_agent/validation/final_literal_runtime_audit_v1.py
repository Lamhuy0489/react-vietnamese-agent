"""Read-only final-gate replay from raw artifacts, not declared pass counters.

This checks the CPU final adapter only, not native source admission, the entire
pair lifecycle, or model quality. Replay reuses the policy implementation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import ArtifactStore, ArtifactType, SourceType
from react_agent.foundation.normalization import text_hash
from react_agent.schemas.trace import TraceEvent
from react_agent.security_v1.a6_policy import admit
from react_agent.security_v1.final_entitlements_v2 import extract_final_entitlement
from react_agent.security_v1.final_literal_runtime_v1 import (
    FINAL_PROFILE,
    ROOM_RUNTIME_VERSION,
    RUNTIME_VERSION,
    FinalLiteralGate,
)
from react_agent.security_v1.public_field_ticket_v2 import PROFILE as ROOM_TICKET_PROFILE
from react_agent.security_v1.runtime_policy import SecurityEvent
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record


def audit_runtime(output: Path) -> dict[str, Any]:
    before = inventory(output)
    metadata = read_record(output / "run_metadata.json")
    supplied = read_record(output / "final_literal_gate.json")
    version = metadata["runtime_version"]
    if version not in {RUNTIME_VERSION, ROOM_RUNTIME_VERSION}:
        raise ValueError("unknown CPU final runtime")
    equal(metadata["security_config"]["level"], "A6", "A6 adapter")
    equal(metadata["final_policy"], FINAL_PROFILE, "final dispatcher profile")
    equal({k: v for k, v in supplied.items() if k != "records"}, dict(
        profile=FINAL_PROFILE, runtime_version=version,
        tool_policy_profile=ROOM_TICKET_PROFILE
        if version == ROOM_RUNTIME_VERSION else "clause_a6_v12",
        public_field_runtime_enabled=False, native_admitted=False,
    ), "adapter scope")
    store = ArtifactStore.deserialize(
        metadata["run_id"], (output / "artifacts/artifacts.jsonl").read_text(encoding="utf-8")
    )
    users = [a for a in store.all() if a.artifact_type == ArtifactType.USER_INPUT
             and a.source_type == SourceType.USER and a.producer == "host_context"
             and not a.parents and not a.transformations]
    equal(len(users), 1, "single raw user")
    user = users[0]
    equal(text_hash(str(user.content())), metadata["task_hash"], "raw user hash")
    original = ValueOriginIndex(store)
    rows = [json.loads(line) for line in (output / "trace_value.jsonl").read_text().splitlines()]
    equal(len(rows), metadata["value_trace_count"], "value trace count")
    final_rows = []
    initial = 0
    for sequence, row in enumerate(rows, 1):
        equal(row["sequence"], sequence, "value trace sequence")
        equal(row["run_id"], metadata["run_id"], "value trace run")
        equal(row["task_id"], metadata["task_id"], "value trace task")
        if row["stage"] in {"INITIAL", "POST"}:
            if row["stage"] == "INITIAL":
                initial += 1
                equal(sequence, 1, "initial admission first")
                equal(row["source_artifact_id"], user.artifact_id, "admitted user")
            equal(admit(original, row["source_artifact_id"], row["step"]),
                  row["admission_error"], "raw source admission replay")
        elif row["stage"] == "FINAL":
            final_rows.append(row)
            equal(sequence, len(rows), "final value event last")
        elif row["stage"] != "PRE":
            raise ValueError("unknown value trace stage")
        equal(row["index_sha256"], original.identity, "live PRE/POST index identity")
    equal(initial, 1, "single initial admission")
    equal(read_record(output / "value_index.json"), original.snapshot(), "live index replay")
    equal(metadata["value_index_hash"], original.identity, "live index metadata hash")
    completed = metadata["result"]["status"] == "completed"
    equal(len(final_rows), int(completed), "terminal final trace coverage")
    equal(len(supplied["records"]), int(completed), "terminal final gate coverage")
    legacy = [TraceEvent.model_validate_json(line) for line in
              (output / "trace_legacy.jsonl").read_text().splitlines()]
    finals = [event for event in legacy if event.event == "final_answer"]
    equal(len(finals), int(completed), "observable answer trace coverage")
    security = [SecurityEvent.model_validate_json(line) for line in
                (output / "trace_security.jsonl").read_text().splitlines()]
    proposed = [event for event in security if event.event == "proposed_final"]
    released = [event for event in security if event.event == "released_final"]
    equal(len(proposed), int(completed), "proposed final security trace coverage")
    equal(len(released), int(completed), "released final security trace coverage")
    if completed:
        release = metadata["final_release"]
        equal(finals[0].data, {"answer": metadata["result"]["final_answer"]},
              "observable answer equals screened answer")
        equal(json.loads(proposed[0].data_json),
              {"artifact_id": release["proposed_artifact_id"]}, "proposed sink artifact")
        equal(json.loads(released[0].data_json),
              {"artifact_id": release["released_artifact_id"]}, "released sink artifact")
        equal(final_rows[0]["release"], release, "metadata/trace final release")
        equal(final_rows[0]["policy"], FINAL_PROFILE, "final trace dispatcher")
        released_id = release["released_artifact_id"]
        artifacts = list(store.all())
        stop = next((i for i, a in enumerate(artifacts) if a.artifact_id == released_id), None)
        if stop is None:
            raise ValueError("released artifact absent")
        # The recorded SYSTEM release is excluded. Recompute from the original
        # prefix so deterministic artifact IDs must also match, not just text.
        replay_store = ArtifactStore.deserialize(
            metadata["run_id"], "".join(a.model_dump_json() + "\n" for a in artifacts[:stop])
        )
        replay = ValueOriginIndex(replay_store)
        for row in rows:
            if row["stage"] in {"INITIAL", "POST"}:
                equal(admit(replay, row["source_artifact_id"], row["step"]),
                      row["admission_error"], "prefix admission replay")
        gate = FinalLiteralGate()
        actual = gate(replay, release["proposed_artifact_id"], user.artifact_id,
                      extract_final_entitlement(str(user.content())))
        equal(actual.model_dump(mode="json"), release, "recomputed final decision")
        equal(gate.records, supplied["records"], "recomputed dual-index proof record")
        equal(replay_store.get(released_id).model_dump(mode="json"),
              store.get(released_id).model_dump(mode="json"), "recomputed release artifact")
        equal(store.get(released_id).content(), metadata["result"]["final_answer"],
              "only screened answer exposed")
    else:
        equal(metadata["final_release"], None, "no release on non-final terminal")
        equal(metadata["result"]["final_answer"], None, "no answer on non-final terminal")
    equal(inventory(output), before, "final audit is read-only")
    return dict(
        protocol="final_literal_runtime_audit_v1", runtime_version=version,
        task_id=metadata["task_id"], status=metadata["result"]["status"],
        final_count=len(final_rows), final_effect=metadata["final_release"]["effect"]
        if completed else None,
        raw_sha256=before, native_admitted=False, phase5_accepted=False,
        inventory_admission_reaudited=False,
    )
