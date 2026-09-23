#!/usr/bin/env python3
"""Read-only public-Dev root-cause diagnosis of one authenticated A6 false block."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from react_agent.adversarial_release import load_split
from react_agent.foundation.artifacts import ArtifactStore, Sensitivity, Trust
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.schemas.agent_output import Action
from react_agent.schemas.trace import TraceEvent
from react_agent.security_v1.authorization_anchors_v3 import extract_anchors
from react_agent.security_v1.value_gates import PAYLOAD_KEYS
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog
from react_agent.validation.guard_probe_audit_v2 import digest, require

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/adversarial/release_v2"
KEY = "BEN_CAND_SOURCEBINDING_PARAPHRASE__A6"
VARIANT = "BEN_CAND_SOURCEBINDING_PARAPHRASE"
PROTOCOL = ROOT / "docs/evaluation/phase5_clause_falseblock_diagnostic_protocol_v1.md"


def unsupported_payload_keys(action: Action) -> list[str]:
    """Report grammar keys only; no proposed payload values leave the diagnostic."""
    payload = action.arguments.get("payload")
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise ValueError("webhook payload object required")
    return sorted(set(cast(dict[str, Any], payload)) - PAYLOAD_KEYS)


def records(path: Path) -> list[dict[str, Any]]:
    no_links(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def diagnose(audit: dict[str, Any], raw: Path) -> dict[str, Any]:
    require(
        audit["protocol"] == "clause_dev32_gpu_release_audit_v2"
        and audit["valid"] is True
        and audit["source_authenticated"] is True,
        "authenticated Dev32 v2 audit",
    )
    selected = [
        (shard["shard"], task)
        for shard in audit["native"]["shards"]
        for task in shard["tasks"]
        if task["key"] == KEY
    ]
    equal(len(selected), 1, "one frozen diagnostic task")
    shard, task = selected[0]
    equal(task["terminal"], "completed", "terminal source task")
    public = [row for row in load_split(RELEASE) if row.variant_id == VARIANT]
    equal(len(public), 1, "one sealed public Dev fixture")
    fixture = public[0]
    resources = fixture.resources
    if resources is None:
        raise ValueError("public auxiliary resources required")
    equal(len(resources.documents), 1, "one selected auxiliary document")
    aux_id = resources.documents[0].identity
    catalog = fixture_catalog(fixture)
    label = catalog.resolve(Action(name="doc_read", arguments={"doc_id": aux_id}))
    equal(
        label.sensitivity.value,
        Sensitivity.CONFIDENTIAL.value,
        "conservative auxiliary sensitivity",
    )
    equal(label.trust.value, Trust.UNTRUSTED.value, "conservative auxiliary trust")
    directory = raw / "dev32" / f"shard{shard}" / "tasks" / KEY / "execution/runtime"
    meta = read_record(directory / "run_metadata.json")
    equal(meta["source_catalog"], catalog.model_dump(mode="json"), "host public catalog")
    legacy = [
        TraceEvent.model_validate_json(line)
        for line in (directory / "trace_legacy.jsonl").read_text().splitlines()
    ]
    require(
        bool(legacy) and legacy[0].event == "run_start" and legacy[-1].event == "run_end",
        "complete legacy trace",
    )
    run_id = legacy[0].run_id
    require(
        all(e.run_id == run_id and e.task_id == fixture.task.task_id for e in legacy),
        "legacy run/task identity",
    )
    read_calls = {
        e.call_id
        for e in legacy
        if e.event == "tool_call_proposed"
        and e.data["name"] == "doc_read"
        and e.data["arguments"] == {"doc_id": aux_id}
    }
    require(
        any(
            e.event == "tool_result" and e.call_id in read_calls and e.data["ok"] is True
            for e in legacy
        ),
        "selected auxiliary read succeeded",
    )
    security = records(directory / "trace_security.jsonl")
    require(
        all(e["run_id"] == run_id and e["task_id"] == fixture.task.task_id for e in security),
        "security identity",
    )
    proposals = {
        data["proposal_id"]: (Action.model_validate(data["action"]), data["artifact_id"])
        for e in security
        if e["event"] == "proposal"
        for data in [json.loads(e["data_json"])]
    }
    denied = {
        data["proposal_id"]
        for e in security
        if e["event"] == "decision"
        for data in [json.loads(e["data_json"])]
        if data["stage"] == "PRE" and data["effect"] == "DENY"
    }
    webhooks = [
        (pid, action, artifact_id)
        for pid, (action, artifact_id) in proposals.items()
        if pid in denied and action.name == "post_webhook_mock"
    ]
    equal(len(webhooks), 1, "one denied webhook proposal")
    pid, action, artifact_id = webhooks[0]
    require(
        extract_anchors(fixture.task.instruction).authorizes(action),
        "raw-user destination authorization",
    )
    unsupported = unsupported_payload_keys(action)
    require(bool(unsupported), "bounded payload grammar gap")
    values = records(directory / "trace_value.jsonl")
    require(
        all(e["run_id"] == run_id and e["task_id"] == fixture.task.task_id for e in values),
        "value trace identity",
    )
    matches = [e for e in values if e["stage"] == "PRE" and e["proposal_id"] == pid]
    equal(len(matches), 1, "one value PRE join")
    value = matches[0]
    equal(value["value"]["effect"], "DENY", "value gate denied")
    require(
        "PROVENANCE_UNKNOWN_CRITICAL_FIELD" in value["value"]["reasons"], "unknown critical field"
    )
    equal(value["value"]["fields"], [], "no field origin assessment after grammar rejection")
    require(
        "SENSITIVITY_EXCEEDS_SINK_CLEARANCE" in value["coarse"]["reasons"]
        and value["coarse_sensitivity_discharged"] is False,
        "coarse sensitivity veto retained",
    )
    index = read_record(directory / "value_index.json")
    require(index["complete"] is True, "origin index complete")
    store = ArtifactStore.deserialize(run_id, (directory / "artifacts/artifacts.jsonl").read_text())
    source = [
        store.get(identity)
        for identity in index["source_sha256"]
        if store.get(identity).source_id == aux_id
    ]
    equal(len(source), 1, "one admitted auxiliary source")
    equal(source[0].sensitivity.value, Sensitivity.CONFIDENTIAL.value, "source snapshot remains S2")
    equal(source[0].trust.value, Trust.UNTRUSTED.value, "source snapshot remains untrusted")
    require(
        source[0].artifact_id in {a.artifact_id for a in store.ancestors(artifact_id)},
        "auxiliary source is a proposal ancestor",
    )
    payload = action.arguments.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("webhook payload object required")
    payload_values = list(payload.values())
    require(len(payload_values) == 1 and isinstance(payload_values[0], str), "one critical scalar")
    typed_origin_present = any(record["value"] == payload_values[0] for record in index["records"])
    require(not typed_origin_present, "proposed scalar has no typed origin record")
    return {
        "protocol": "phase5_clause_falseblock_diagnostic_v1",
        "task_key": KEY,
        "source_commit": audit["source_commit"],
        "raw_files_verified": len(audit["raw_sha256"]),
        "public_dev_only": True,
        "oracle_records_read": 0,
        "test_payloads_read": 0,
        "new_inference_runs": 0,
        "destination_authorized_by_raw_user": True,
        "auxiliary_read_succeeded": True,
        "auxiliary_host_sensitivity": label.sensitivity.value,
        "auxiliary_host_trust": label.trust.value,
        "auxiliary_source_admitted_and_ancestor": True,
        "origin_index_complete": True,
        "unsupported_payload_keys": unsupported,
        "critical_scalar_typed_origin_present": typed_origin_present,
        "value_reasons": value["value"]["reasons"],
        "coarse_reasons": value["coarse"]["reasons"],
        "coarse_sensitivity_discharged": False,
        "safe_to_relabel_from_this_diagnostic": False,
        "phase5_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    for path in (args.audit, args.raw, args.output):
        no_links(path)
    output = args.output.resolve()
    require(not output.exists() and output.is_relative_to(ROOT / "results"), "fresh result path")
    before = inventory(args.raw)
    audit = read_record(args.audit)
    equal(before, audit["raw_sha256"], "raw audit identity")
    audit_hash = digest(args.audit)
    report = diagnose(audit, args.raw)
    equal(inventory(args.raw), before, "raw unchanged")
    equal(digest(args.audit), audit_hash, "audit unchanged")
    report.update(
        audit_sha256=audit_hash,
        protocol_sha256=digest(PROTOCOL),
        script_sha256=digest(Path(__file__)),
    )
    output.mkdir()
    write_receipt(output / "diagnostic.json", report)
    print("PHASE5_FALSEBLOCK_DIAGNOSTIC_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
