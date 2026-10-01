"""Join full pair/guard/exit evidence, raw final proof, and actual doc_read dispatch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.artifacts import ArtifactStore, SourceType
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.schemas.agent_output import Action
from react_agent.schemas.trace import TraceEvent
from react_agent.security_v1.doc_read_final_proof_v1 import DocReadApproval
from react_agent.security_v1.doc_read_pair_runtime_v1 import RUNTIME_VERSION
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import clause_pair_audit_v1 as pair_audit
from react_agent.validation import doc_read_final_runtime_audit_v1 as final_audit
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record


def audit_broker(runtime: Path) -> int:
    metadata = read_record(runtime / "run_metadata.json")
    catalog = SourceCatalog.model_validate(metadata["source_catalog"])
    store = ArtifactStore.deserialize(metadata["run_id"],
                                      (runtime / "artifacts/artifacts.jsonl").read_text())
    events = [TraceEvent.model_validate_json(line) for line in
              (runtime / "trace_legacy.jsonl").read_text().splitlines()]
    roots = [a for a in store.all() if a.producer == "tool_source_snapshot"
             and a.source_type == SourceType.DOCUMENT]
    seen: set[str] = set()
    for root in roots:
        info = json.loads(root.metadata_json)
        if info.get("tool") != "doc_read":
            raise ValueError("document snapshot must come from doc_read")
        call_id = info["call_id"]
        if call_id in seen:
            raise ValueError("duplicate snapshot call ID")
        seen.add(call_id)
        by_call = [event for event in events if event.call_id == call_id]
        for name in ("tool_call_proposed", "tool_call_executed", "tool_result"):
            equal(sum(event.event == name for event in by_call), 1, "single broker " + name)
        proposal = next(event for event in by_call if event.event == "tool_call_proposed")
        executed = next(event for event in by_call if event.event == "tool_call_executed")
        result = next(event for event in by_call if event.event == "tool_result")
        equal([event.event for event in by_call],
              ["tool_call_proposed", "tool_call_executed", "tool_result"], "broker event order")
        for event in (proposal, executed, result):
            equal([event.run_id, event.task_id, event.step],
                  [metadata["run_id"], metadata["task_id"], root.created_step],
                  "broker run/task/step identity")
        equal(executed.data, {}, "broker executed event payload")
        arguments = dict(proposal.data)
        equal(arguments.pop("call_id"), call_id, "proposal call identity")
        action = Action.model_validate(arguments)
        equal(action.name, "doc_read", "actual doc_read proposal")
        equal(result.data["tool_name"], "doc_read", "actual doc_read result")
        equal(result.data["call_id"], call_id, "ToolResult call identity")
        equal(result.step, root.created_step, "snapshot step")
        equal(result.data["ok"], info["ok"], "snapshot success")
        equal(root.content(), result.data["content"] if result.data["ok"] else result.data,
              "raw snapshot equals dispatched ToolResult")
        label = catalog.resolve(action)
        equal([root.source_id, root.source_type.value, root.sensitivity.value, root.trust.value],
              [label.source_id, label.source_type.value,
               label.sensitivity.value, label.trust.value],
              "host catalog labels")
    successful_reads = [event for event in events if event.event == "tool_result"
                        and event.data["tool_name"] == "doc_read"]
    equal(sorted(seen), sorted(event.call_id for event in successful_reads),
          "all dispatched doc_read results have a source root")
    return len(roots)


def audit_task(
    output: Path, *, approval: DocReadApproval, expected_approval_sha256: str,
) -> dict[str, Any]:
    before = inventory(output)
    checked = cast(dict[str, Any], bind(
        pair_audit.audit_task, RUNTIME_VERSION=RUNTIME_VERSION
    )(output))
    if checked["runtime_present"]:
        final = bind(final_audit.audit_runtime, RUNTIME_VERSION=RUNTIME_VERSION)(
            output / "runtime", approval=approval,
            expected_approval_sha256=expected_approval_sha256,
        )
        checked = {**checked, "final_proof_audit": final,
                   "doc_read_broker_roots": audit_broker(output / "runtime")}
    equal(inventory(output), before, "doc_read task audit read-only")
    return checked


def audit_join(
    execution: Path, sidecar: Path, witness: Path, *, approval: DocReadApproval,
    expected_approval_sha256: str, expected_runtime: dict[str, str] | None = None,
) -> dict[str, Any]:
    def task(output: Path) -> dict[str, Any]:
        return audit_task(
            output, approval=approval, expected_approval_sha256=expected_approval_sha256
        )

    def exit_audit(output: Path, **kwargs: Any) -> dict[str, Any]:
        return cast(dict[str, Any], bind(pair_audit.audit_exit, audit_task=task)(output, **kwargs))

    joined = bind(pair_audit.audit_join, audit_task=task, audit_exit=exit_audit)(
        execution, sidecar, witness, expected_runtime=expected_runtime,
    )
    return {**joined, "protocol": "doc_read_pair_join_v1",
            "approval_sha256": expected_approval_sha256}
