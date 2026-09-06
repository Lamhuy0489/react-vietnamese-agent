"""Run a separate mechanism batch with real offline search and private QA rules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from react_agent.agent import AgentRuntime
from react_agent.authoring.candidate_qa import load_candidates
from react_agent.authoring.candidate_review import group_audit, load_utilities
from react_agent.authoring.mechanism_rules import MechanismRules, score_mechanisms
from react_agent.authoring.overlays import build_overlay_registry
from react_agent.authoring.workbench_qa import RecordingReplay, file_hashes
from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.agent_output import Action
from react_agent.schemas.trace import TraceEvent


def verify_batch(inputs: Path, pilot: Path, clean: Path, output: Path) -> dict[str, Any]:
    inputs, pilot, clean, output = (p.resolve() for p in (inputs, pilot, clean, output))
    if output.exists() or any(
        output.is_relative_to(p) or p.is_relative_to(output) for p in (inputs, pilot, clean)
    ):
        raise ValueError("output must be fresh and separate from all inputs")
    before = {
        "batch": file_hashes(inputs),
        "pilot": file_hashes(pilot),
        "clean": file_hashes(clean),
    }
    candidates = load_candidates(inputs)
    prior = load_candidates(pilot)
    if {c.public.task_id for c in candidates} & {c.public.task_id for c in prior}:
        raise ValueError("batch repeats pilot task identity")
    if {c.metadata.family_id for c in candidates} & {c.metadata.family_id for c in prior}:
        raise ValueError("batch repeats pilot family identity")
    if {c.overlay.source_id for c in candidates} & {c.overlay.source_id for c in prior}:
        raise ValueError("batch repeats pilot source identity")
    utilities = load_utilities(inputs / "private/utility.json", candidates)
    rows = TypeAdapter(list[MechanismRules]).validate_json(
        (inputs / "private/rules.json").read_text()
    )
    rules = {row.task_id: row for row in rows}
    if len(rules) != len(rows) or set(rules) != set(utilities):
        raise ValueError("duplicate or mismatched rule identities")
    for c in candidates:
        r = rules[c.public.task_id]
        if any(
            r.exposure_action not in path
            for path in (c.oracle.safe_actions, c.oracle.negative_actions)
        ):
            raise ValueError("exposure action absent from reference script")
        ratio = len(c.overlay.benign_text.split()) / max(1, len(c.overlay.attack_text.split()))
        if not 0.8 <= ratio <= 1.25:
            raise ValueError("pair length outside declared gate")
    output.mkdir(parents=True)
    checks: list[dict[str, Any]] = []
    for candidate in candidates:
        task, overlay, oracle = candidate.public, candidate.overlay, candidate.oracle
        for branch in ("attack", "benign"):
            for negative in (False, True):
                label = "negative" if negative else "safe"
                directory = output / task.task_id / f"{branch}_{label}"
                directory.mkdir(parents=True)
                env = directory / "environment"
                registry = build_overlay_registry(clean, env, overlay, branch)
                if len(registry.names) != 8:
                    raise ValueError("must retain eight tools")
                backend = RecordingReplay(
                    oracle.negative_actions if negative else oracle.safe_actions,
                    oracle.negative_final if negative else oracle.safe_final,
                )
                trace = directory / "trace.jsonl"
                result = AgentRuntime(backend, registry).run(task, trace_path=trace)
                events = [
                    TraceEvent.model_validate_json(line) for line in trace.read_text().splitlines()
                ]
                if (
                    result.status != "completed"
                    or result.parse_errors
                    or any(e.event == "tool_result" and not e.data["ok"] for e in events)
                ):
                    raise ValueError("reference runtime/tool failure")
                proposals = {
                    e.call_id: Action(name=e.data["name"], arguments=e.data["arguments"])
                    for e in events
                    if e.event == "tool_call_proposed"
                }
                exposure = "\n".join(
                    json.dumps(e.data["content"], ensure_ascii=False)
                    for e in events
                    if e.event == "tool_result"
                    and proposals[e.call_id] == rules[task.task_id].exposure_action
                )
                text = overlay.attack_text if branch == "attack" else overlay.benign_text
                if text not in exposure or overlay.base_content not in exposure:
                    raise ValueError("complete selected payload missing at declared exposure")
                score = score_mechanisms(
                    events,
                    oracle,
                    utilities[task.task_id],
                    rules[task.task_id],
                    env / "database/university.db",
                )
                if score["unassessed_actions"] or (not negative and not score["safe_utility"]):
                    raise ValueError("reference lacks assessed safe utility")
                expected = rules[task.task_id].expected_negative_reason
                if negative and (
                    score["safe_utility"]
                    or not (
                        score["encoded_final_artifacts"]
                        if expected == "encoded_final_disclosure"
                        else any(
                            expected in reasons for reasons in score["mechanism_reasons"].values()
                        )
                    )
                ):
                    raise ValueError("negative fixture misses declared mechanism")
                broker = ToolBroker(registry, TraceLogger(directory / "artifact_probes.jsonl"))
                for index, artifact in enumerate(oracle.sensitive_artifacts):
                    probed = broker.execute(
                        artifact.read_action.name,
                        artifact.read_action.arguments,
                        run_id="artifact_probe",
                        task_id=task.task_id,
                        step=index + 1,
                    )
                    if not probed.ok or artifact.value not in json.dumps(
                        probed.content, ensure_ascii=False
                    ):
                        raise ValueError("artifact does not exist")
                initial = json.dumps(backend.contexts[0], ensure_ascii=False)
                contexts = json.dumps(backend.contexts, ensure_ascii=False)
                if any(a.value in initial for a in oracle.sensitive_artifacts) or any(
                    key in contexts
                    for key in (
                        "action_rules",
                        "requires_prior_success",
                        "encoded_artifacts",
                        "expected_negative_reason",
                        "public_result",
                        "safe_actions",
                        "sink_artifacts",
                        "sql_columns",
                        "required_facts",
                    )
                ):
                    raise ValueError("private QA annotation entered runtime context")
                normalized = [
                    e.model_dump(mode="json", exclude={"timestamp", "run_id"}) for e in events
                ]
                checks.append(
                    {
                        "task_id": task.task_id,
                        "branch": branch,
                        "fixture": label,
                        "score": score,
                        "exposure_tool": rules[task.task_id].exposure_action.name,
                        "payload_reachable": True,
                        "private_context_guard": True,
                        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
                        "observable_sha256": hashlib.sha256(
                            json.dumps(normalized, sort_keys=True, ensure_ascii=False).encode()
                        ).hexdigest(),
                    }
                )
    if before != {
        "batch": file_hashes(inputs),
        "pilot": file_hashes(pilot),
        "clean": file_hashes(clean),
    }:
        raise ValueError("input bytes changed during QA")
    return {
        "valid": True,
        "scope": "eight-candidate authoring batch, not Phase 3 acceptance",
        "new_candidates": len(candidates),
        "combined_candidates": len(candidates) + len(prior),
        "replay_runs": len(checks),
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "variants_generated": 0,
        "review_status": "pending",
        "split": "unassigned",
        "input_sha256": before["batch"],
        "pilot_sha256": before["pilot"],
        "clean_environment_sha256": before["clean"],
        "group_audit": group_audit([*prior, *candidates]),
        "checks": checks,
        "raw_output": str(output),
    }
