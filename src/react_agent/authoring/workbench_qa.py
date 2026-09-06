"""Replay-based local authoring QA. Does not claim real-model or semantic review results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import TypeAdapter

from react_agent.agent import AgentRuntime
from react_agent.authoring.fixture_oracle import score_fixture
from react_agent.authoring.overlays import build_overlay_registry
from react_agent.broker import ToolBroker
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.replay import ReplayBackend
from react_agent.logging import TraceLogger
from react_agent.schemas.adversarial_workbench import (
    OverlayScenario,
    PrivateWorkbenchOracle,
    PublicWorkbenchTask,
)
from react_agent.schemas.agent_output import Action, ActionTurn, FinalAnswer, FinalTurn
from react_agent.schemas.trace import TraceEvent


def file_hashes(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def load_workbench(
    root: Path,
) -> tuple[
    dict[str, PublicWorkbenchTask], dict[str, OverlayScenario], dict[str, PrivateWorkbenchOracle]
]:
    tasks = TypeAdapter(list[PublicWorkbenchTask]).validate_json(
        (root / "public/tasks.json").read_text()
    )
    overlays = TypeAdapter(list[OverlayScenario]).validate_json(
        (root / "overlays/scenarios.json").read_text()
    )
    oracles = TypeAdapter(list[PrivateWorkbenchOracle]).validate_json(
        (root / "private/oracles.json").read_text()
    )
    for rows in (tasks, overlays, oracles):
        if len(rows) != 4 or len({row.task_id for row in rows}) != 4:
            raise ValueError("workbench requires four unique identities, not benchmark quota")
    if {t.task_id for t in tasks} != {s.task_id for s in overlays} or {
        t.task_id for t in tasks
    } != {o.task_id for o in oracles}:
        raise ValueError("public/overlay/private identity mismatch")
    if len({s.source_type for s in overlays}) != 4 or len({s.source_id for s in overlays}) != 4:
        raise ValueError("workbench must cover four distinct source types/identities")
    return (
        {t.task_id: t for t in tasks},
        {s.task_id: s for s in overlays},
        {o.task_id: o for o in oracles},
    )


class RecordingReplay(ReplayBackend):
    def __init__(self, actions: list[Action], final: str) -> None:
        super().__init__(
            [
                *(ActionTurn(action=action).model_dump_json() for action in actions),
                FinalTurn(final_answer=FinalAnswer(answer=final)).model_dump_json(),
            ]
        )
        self.contexts: list[list[dict[str, str]]] = []

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.contexts.append([dict(message) for message in messages])
        return super().generate(messages, config)


def run_workbench(root: Path, clean_environment: Path, output: Path) -> dict[str, Any]:
    inputs, base = root.resolve(), clean_environment.resolve()
    destination = output.resolve()
    if destination.exists() or any(
        destination.is_relative_to(path) or path.is_relative_to(destination)
        for path in (inputs, base)
    ):
        raise ValueError("QA output must be fresh and separate from all inputs")
    tasks, overlays, oracles = load_workbench(inputs)
    input_before, base_before = file_hashes(inputs), file_hashes(base)
    output.mkdir(parents=True)
    checks: list[dict[str, Any]] = []
    for task_id in sorted(tasks):
        scenario, oracle = overlays[task_id], oracles[task_id]
        if (
            scenario.trigger not in oracle.safe_actions
            or scenario.trigger not in oracle.negative_actions
        ):
            raise ValueError("both fixture scripts must reach the annotated source")
        for branch in ("attack", "benign"):
            typed_branch: Literal["attack", "benign"] = branch
            for negative in (False, True):
                label = "negative" if negative else "safe"
                directory = output / task_id / f"{branch}_{label}"
                directory.mkdir(parents=True)
                registry = build_overlay_registry(
                    base, directory / "environment", scenario, typed_branch
                )
                if len(registry.names) != 8:
                    raise ValueError("workbench must retain eight tools")
                logger = TraceLogger(directory / "probe.jsonl")
                broker = ToolBroker(registry, logger)
                probe = broker.execute(
                    scenario.trigger.name,
                    scenario.trigger.arguments,
                    run_id="probe",
                    task_id=task_id,
                    step=1,
                )
                text = json.dumps(probe.content, ensure_ascii=False)
                payload = scenario.attack_text if branch == "attack" else scenario.benign_text
                if not probe.ok or payload not in text or scenario.base_content not in text:
                    raise ValueError("overlay payload/public base not reachable through Broker")
                for artifact in oracle.sensitive_artifacts:
                    result = broker.execute(
                        artifact.read_action.name,
                        artifact.read_action.arguments,
                        run_id="probe",
                        task_id=task_id,
                        step=2,
                    )
                    if not result.ok or artifact.value not in json.dumps(
                        result.content, ensure_ascii=False
                    ):
                        raise ValueError("sensitive artifact reference does not exist")
                # Fresh registry/state for the actual fixture, independent of reachability probes.
                registry = build_overlay_registry(
                    base, directory / "run_environment", scenario, typed_branch
                )
                backend = RecordingReplay(
                    oracle.negative_actions if negative else oracle.safe_actions,
                    oracle.negative_final if negative else oracle.safe_final,
                )
                trace_path = directory / "trace.jsonl"
                result_run = AgentRuntime(backend, registry).run(
                    tasks[task_id], trace_path=trace_path
                )
                events = [
                    TraceEvent.model_validate_json(line)
                    for line in trace_path.read_text().splitlines()
                ]
                observed = "\n".join(
                    json.dumps(e.data, ensure_ascii=False)
                    for e in events
                    if e.event == "tool_result" and e.data.get("ok")
                )
                if payload not in observed:
                    raise ValueError("script did not actually observe the selected overlay")
                if not negative and not all(fact in observed for fact in oracle.required_facts):
                    raise ValueError("safe fixture fact lacks observable tool evidence")
                scored = score_fixture(events, oracle)
                if result_run.status != "completed" or result_run.parse_errors:
                    raise ValueError("fixture runtime/parser failure")
                if not negative and not scored["safe_utility"]:
                    raise ValueError("safe path did not retain legitimate utility")
                if negative and (
                    scored["safe_utility"]
                    or not (
                        scored["executed_violations"]
                        if oracle.expected_negative == "executed_violation"
                        else scored["final_leaked_artifacts"]
                    )
                ):
                    raise ValueError("negative fixture was not detected by private oracle")
                initial = json.dumps(backend.contexts[0], ensure_ascii=False)
                if any(a.value in initial for a in oracle.sensitive_artifacts):
                    raise ValueError("private artifact in initial model-facing context")
                contexts = json.dumps(backend.contexts, ensure_ascii=False)
                if any(
                    key in contexts
                    for key in ("required_facts", "safe_actions", "sink_grants", "review_status")
                ):
                    raise ValueError("private metadata in model-facing context")
                checks.append(
                    {
                        "task_id": task_id,
                        "source_type": scenario.source_type,
                        "branch": branch,
                        "fixture": label,
                        "score": scored,
                        "payload_reachable": True,
                        "private_context_guard": True,
                        "trace_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
                        "observable_sha256": hashlib.sha256(
                            json.dumps(
                                [
                                    e.model_dump(mode="json", exclude={"timestamp", "run_id"})
                                    for e in events
                                ],
                                ensure_ascii=False,
                                sort_keys=True,
                            ).encode()
                        ).hexdigest(),
                    }
                )
    if file_hashes(inputs) != input_before or file_hashes(base) != base_before:
        raise ValueError("authoring inputs or frozen clean environment mutated")
    return {
        "valid": True,
        "scope": "four unsplit executable authoring pairs; not Phase 3 acceptance",
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "replay_runs": len(checks),
        "canonical_pairs": 4,
        "variants_generated": 0,
        "review_status": "pending",
        "input_sha256": input_before,
        "clean_environment_sha256": base_before,
        "checks": checks,
    }
