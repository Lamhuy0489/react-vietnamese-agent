"""Read-only replay of saved component evidence; never runs a tool or a model."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import ArtifactStore, Sensitivity, canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.agent_mount_v1 import write_receipt
from react_agent.prototypes.field_reference_v1 import Grant, Plan
from react_agent.schemas.agent_output import Action
from react_agent.schemas.trace import TraceEvent
from react_agent.validation.clause_dev_release_v1 import digest
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record

ROOT = Path(__file__).resolve().parents[1]


def audit_case(path: Path, fixture: dict[str, Any], case: str, arm: str) -> dict[str, Any]:
    grant = Grant.model_validate(read_record(path / "grant.json"))
    catalog = SourceCatalog.model_validate(fixture["catalog"])
    equal(grant.run_id, "fieldref_" + case + "_" + arm, "case run ID")
    equal(grant.catalog_sha256, text_hash(canonical_json(fixture["catalog"])), "catalog pin")
    store = ArtifactStore.deserialize(grant.run_id, (path / "artifacts.jsonl").read_text())
    sources = {a.artifact_id: a for a in store.all()
               if a.producer == "field_reference_broker_snapshot_v1"}
    events = [TraceEvent.model_validate_json(line)
              for line in (path / "broker.jsonl").read_text().splitlines()]
    equal(len(events), 3 * len(sources), "no unaccounted Broker events")
    for number, source in enumerate(sources.values(), 1):
        equal(len(source.parents), 0, "raw root has no derived parent")
        triplet = events[(number - 1) * 3:number * 3]
        equal([e.event for e in triplet],
              ["tool_call_proposed", "tool_call_executed", "tool_result"], "ordered Broker events")
        metadata = json.loads(source.metadata_json)
        for event in triplet:
            equal([event.run_id, event.task_id, event.step, event.call_id],
                  [grant.run_id, grant.task_id, source.created_step, metadata["call_id"]],
                  "Broker identity")
        equal(triplet[0].data, dict(call_id=metadata["call_id"], name="doc_read",
                                   arguments={"doc_id": source.source_id}), "read proposal")
        equal(triplet[-1].data["ok"], True, "successful read")
        equal(triplet[-1].data["content"], source.content(), "raw result")
        doc = next(d for d in fixture["documents"] if d["doc_id"] == source.source_id)
        equal(source.content(), doc, "declared fixture bytes")
        label = catalog.resolve(Action(name="doc_read", arguments={"doc_id": source.source_id}))
        equal([source.sensitivity.value, source.trust.value],
              [label.sensitivity.value, label.trust.value], "host labels")
        equal(metadata["grant_sha256"], grant.sha256, "source grant")
    plan = Plan.model_validate(read_record(path / "plan.json"))
    decision = read_record(path / "decision.json")
    values = []
    selected = {}
    invalid = False
    for ref in plan.refs:
        chosen = sources.get(ref.artifact_id)
        if (chosen is None or ref.source_sha256 != chosen.content_hash
                or ref.run_id != grant.run_id or ref.grant_sha256 != grant.sha256
                or not any(s.source_id == chosen.source_id and s.path == ref.path
                           for s in grant.outputs)):
            invalid = True
            break
        content = chosen.content()
        if not isinstance(content, dict) or not isinstance(content[ref.path[1:]], str):
            raise ValueError("declared text field required")
        values.append(str(content[ref.path[1:]]))
        selected[chosen.artifact_id] = chosen
    if invalid:
        equal(decision, dict(allowed=False, reason="invalid_reference_plan", output=None,
                             rendered_artifact_id=None, effective_sensitivity=None), "invalid plan")
        equal(len(store.all()), len(sources), "invalid plan creates no rendered artifact")
    else:
        text = plan.separator.join(values)
        for op in plan.transforms:
            text = (base64.b64encode(text.encode()).decode()
                    if op == "base64" else text.encode().hex())
        rendered = store.get(decision["rendered_artifact_id"])
        sensitivity = max(s.sensitivity.value for s in selected.values())
        trust = ("UNTRUSTED" if any(s.trust.value == "UNTRUSTED" for s in selected.values())
                 else "TRUSTED")
        equal(rendered.content(), text, "host rendered value")
        equal([rendered.sensitivity.value, rendered.trust.value], [sensitivity, trust],
              "selected labels")
        equal([p.parent_id for p in rendered.parents], list(selected), "value parents")
        equal(list(rendered.transformations), list(plan.transforms), "transformation lineage")
        equal(json.loads(rendered.metadata_json)["exposure_ids"], list(sources),
              "exposure distinct")
        effective = max(s.sensitivity.value for s in sources.values()) if arm == "exposure" else (
            sensitivity)
        allowed = effective == Sensitivity.PUBLIC.value and case != "veto"
        equal(decision["allowed"], allowed, "policy decision")
        equal(decision["output"], text if allowed else None, "released final")
        equal(decision["effective_sensitivity"], effective, "effective label")
        equal(len(store.all()), len(sources) + 1, "one rendered artifact")
    return dict(valid=True, allowed=decision["allowed"], broker_reads=len(sources))


def audit(root: Path, expected_declaration_sha256: str) -> dict[str, Any]:
    before = inventory(root)
    equal(digest(root / "declaration.json"), expected_declaration_sha256,
          "external declaration pin")
    declaration = read_record(root / "declaration.json")
    receipt = read_record(root / "receipt.json")
    equal({n: h for n, h in before.items() if n != "receipt.json"}, receipt["raw_sha256"],
          "complete saved raw inventory")
    equal(receipt["declaration_sha256"], expected_declaration_sha256, "receipt declaration")
    equal({n: digest(ROOT / n) for n in declaration["sources"]}, declaration["sources"],
          "exact current measured sources")
    rows = []
    for case in declaration["ordered_cases"]:
        for arm in ("exposure", "selected"):
            path = root / case / arm
            row = read_record(path / "receipt.json")
            equal({n: h for n, h in inventory(path).items() if n != "receipt.json"},
                  row["raw_sha256"], "case raw")
            checked = audit_case(path, declaration["fixtures"][case], case, arm)
            equal(checked["allowed"], row["allowed"], "case decision")
            rows.append(checked)
    equal(len(rows), 32, "matrix coverage")
    equal(inventory(root), before, "audit is read only")
    return dict(protocol="field_reference_component_audit_v1", valid=True, cases=32,
                declaration_sha256=expected_declaration_sha256,
                raw_inventory_sha256=text_hash(canonical_json(before)),
                native_model_runs=0, phase5_accepted=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--declaration-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve().is_relative_to(args.root.resolve()):
        raise ValueError("fresh audit output outside raw root required")
    write_receipt(args.output, audit(args.root, args.declaration_sha256))
