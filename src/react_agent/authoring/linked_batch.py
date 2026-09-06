"""Replay QA for the unsplit linked-source and row-scope candidate batch."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import TypeAdapter

from react_agent.agent import AgentRuntime
from react_agent.authoring.candidate_qa import load_candidates
from react_agent.authoring.candidate_review import group_audit, load_utilities
from react_agent.authoring.linked_resources import LinkedResources, build_linked_registry
from react_agent.authoring.linked_scope import LinkedRules, score_linked
from react_agent.authoring.workbench_qa import RecordingReplay, file_hashes
from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.agent_output import Action
from react_agent.schemas.trace import TraceEvent


def verify_linked(inputs: Path, clean: Path, output: Path) -> dict[str, Any]:
    inputs, clean, output = (p.resolve() for p in (inputs, clean, output))
    if output.exists() or any(
        output.is_relative_to(p) or p.is_relative_to(output) for p in (inputs, clean)
    ):
        raise ValueError("output must be fresh and separate from inputs")
    before, clean_before = file_hashes(inputs), file_hashes(clean)
    candidates = load_candidates(inputs)
    utilities = load_utilities(inputs / "private/utility.json", candidates)
    resource_rows = TypeAdapter(list[LinkedResources]).validate_json(
        (inputs / "overlays/resources.json").read_text()
    )
    rule_rows = TypeAdapter(list[LinkedRules]).validate_json(
        (inputs / "private/linked_rules.json").read_text()
    )
    resources = {r.task_id: r for r in resource_rows}
    rules = {r.task_id: r for r in rule_rows}
    if (
        len(resources) != len(resource_rows)
        or len(rules) != len(rule_rows)
        or set(resources) != set(utilities)
        or set(rules) != set(utilities)
    ):
        raise ValueError("duplicate or mismatched resource/rule identities")
    checks: list[dict[str, Any]] = []
    branches: tuple[Literal["attack", "benign"], ...] = ("attack", "benign")
    for c in candidates:
        task, overlay, oracle = c.public, c.overlay, c.oracle
        rule = rules[task.task_id]
        if not 0.8 <= len(overlay.benign_text.split()) / len(overlay.attack_text.split()) <= 1.25:
            raise ValueError("pair length outside declared gate")
        if any(
            a not in path
            for a in rule.exposure_actions
            for path in (oracle.safe_actions, oracle.negative_actions)
        ):
            raise ValueError("declared source absent from reference path")
        for branch in branches:
            for negative in (False, True):
                label = "negative" if negative else "safe"
                directory = output / task.task_id / f"{branch}_{label}"
                directory.mkdir(parents=True)
                env = directory / "environment"
                registry = build_linked_registry(
                    clean, env, overlay, resources[task.task_id], branch
                )
                if len(registry.names) != 8:
                    raise ValueError("must retain eight tools")
                backend = RecordingReplay(
                    oracle.negative_actions if negative else oracle.safe_actions,
                    oracle.negative_final if negative else oracle.safe_final,
                )
                trace = directory / "trace.jsonl"
                run = AgentRuntime(backend, registry).run(task, trace_path=trace)
                events = [TraceEvent.model_validate_json(s) for s in trace.read_text().splitlines()]
                results = [e for e in events if e.event == "tool_result"]
                if (
                    run.status != "completed"
                    or run.parse_errors
                    or any(not e.data["ok"] for e in results)
                ):
                    raise ValueError("reference runtime/tool failure")
                actions = {
                    e.call_id: Action(name=e.data["name"], arguments=e.data["arguments"])
                    for e in events
                    if e.event == "tool_call_proposed"
                }
                if any(
                    not any(actions[e.call_id] == a for e in results) for a in rule.exposure_actions
                ):
                    raise ValueError("required linked source not observed")
                exposure = "\n".join(
                    json.dumps(e.data["content"], ensure_ascii=False)
                    for e in results
                    if actions[e.call_id] == overlay.trigger
                )
                text = overlay.attack_text if branch == "attack" else overlay.benign_text
                if text not in exposure or overlay.base_content not in exposure:
                    raise ValueError("complete branch payload not exposed")
                score = score_linked(
                    events, oracle, utilities[task.task_id], rule, env / "database/university.db"
                )
                if score["unassessed_actions"] or bool(score["safe_utility"]) == negative:
                    raise ValueError("unexpected safe/negative outcome")
                if negative and not (
                    score["executed_violations"]
                    and any(
                        d["status"] == "violation" and d["reason"] == rule.expected_negative_reason
                        for d in score["scope_decisions"].values()
                    )
                ):
                    raise ValueError("negative fixture misses declared scope violation")
                initial = json.dumps(backend.contexts[0], ensure_ascii=False)
                contexts = json.dumps(backend.contexts, ensure_ascii=False)
                if any(a.value in initial for a in oracle.sensitive_artifacts) or any(
                    marker in contexts
                    for marker in (
                        "row_grants",
                        "allowed_values",
                        "expected_negative_reason",
                        "safe_actions",
                        "sql_columns",
                        "sink_artifacts",
                        "evidence_action",
                    )
                ):
                    raise ValueError("private evaluator data entered runtime context")
                broker = ToolBroker(registry, TraceLogger(directory / "artifact_probes.jsonl"))
                for i, artifact in enumerate(oracle.sensitive_artifacts, start=1):
                    result = broker.execute(
                        artifact.read_action.name,
                        artifact.read_action.arguments,
                        run_id="artifact_probe",
                        task_id=task.task_id,
                        step=i,
                    )
                    if not result.ok or artifact.value not in json.dumps(
                        result.content, ensure_ascii=False
                    ):
                        raise ValueError("declared artifact absent")
                normalized = [
                    e.model_dump(mode="json", exclude={"timestamp", "run_id"}) for e in events
                ]
                checks.append(
                    {
                        "task_id": task.task_id,
                        "branch": branch,
                        "fixture": label,
                        "score": score,
                        "source_exposures": len(rule.exposure_actions),
                        "payload_reachable": True,
                        "private_context_guard": True,
                        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
                        "observable_sha256": hashlib.sha256(
                            json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode()
                        ).hexdigest(),
                    }
                )
    if before != file_hashes(inputs) or clean_before != file_hashes(clean):
        raise ValueError("input bytes changed during QA")
    return {
        "valid": True,
        "scope": "linked candidate QA, not Phase 3 acceptance",
        "candidates": len(candidates),
        "replay_runs": len(checks),
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "variants_generated": 0,
        "review_status": "pending",
        "split": "unassigned",
        "checks": checks,
        "input_sha256": before,
        "clean_environment_sha256": clean_before,
        "group_audit": group_audit(candidates),
        "raw_output": str(output),
    }
