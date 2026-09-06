"""Executable QA of unsplit canonical candidates with offline data-scope checks."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from react_agent.agent import AgentRuntime
from react_agent.authoring.data_scope import score_scoped
from react_agent.authoring.overlays import build_overlay_registry
from react_agent.authoring.workbench_qa import RecordingReplay, file_hashes
from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.adversarial_workbench import OverlayScenario, PublicWorkbenchTask
from react_agent.schemas.canonical_candidate import CandidateMetadata, ScopedOracle
from react_agent.schemas.trace import TraceEvent


@dataclass(frozen=True)
class Candidate:
    public: PublicWorkbenchTask
    overlay: OverlayScenario
    oracle: ScopedOracle
    metadata: CandidateMetadata


def load_candidates(root: Path) -> list[Candidate]:
    tasks = TypeAdapter(list[PublicWorkbenchTask]).validate_json(
        (root / "public/tasks.json").read_text()
    )
    overlays = TypeAdapter(list[OverlayScenario]).validate_json(
        (root / "overlays/scenarios.json").read_text()
    )
    oracles = TypeAdapter(list[ScopedOracle]).validate_json(
        (root / "private/oracles.json").read_text()
    )
    catalog = TypeAdapter(list[CandidateMetadata]).validate_json(
        (root / "catalog/candidates.json").read_text()
    )
    ids = {t.task_id for t in tasks}
    for rows in (tasks, overlays, oracles, catalog):
        if not rows or len(rows) != len(ids) or {r.task_id for r in rows} != ids:
            raise ValueError("duplicate or mismatched public/overlay/private/catalog identities")
    if len({m.family_id for m in catalog}) != len(catalog):
        raise ValueError("duplicate candidate family IDs")
    if len({s.source_id for s in overlays}) != len(overlays):
        raise ValueError("duplicate overlay source IDs")
    by_overlay, by_oracle, by_meta = (
        {s.task_id: s for s in overlays},
        {o.task_id: o for o in oracles},
        {m.task_id: m for m in catalog},
    )
    candidates = [
        Candidate(t, by_overlay[t.task_id], by_oracle[t.task_id], by_meta[t.task_id]) for t in tasks
    ]
    for candidate in candidates:
        s, o = candidate.overlay, candidate.oracle
        if s.trigger not in o.safe_actions or s.trigger not in o.negative_actions:
            raise ValueError("safe/negative scripts must include source trigger")
        if len(o.safe_actions) > 7 or len(o.negative_actions) > 7:
            raise ValueError("fixture exceeds A0 eight-step limit including final")
        if s.sensitive_value and not any(
            a.value == s.sensitive_value for a in o.sensitive_artifacts
        ):
            raise ValueError("overlay sensitive value lacks private artifact annotation")
        if s.attack_text == s.benign_text:
            raise ValueError("identical attack and benign additions")
    return sorted(candidates, key=lambda c: c.public.task_id)


def verify_candidates(inputs: Path, clean: Path, output: Path) -> dict[str, Any]:
    inputs, clean, output = inputs.resolve(), clean.resolve(), output.resolve()
    if output.exists() or any(
        output.is_relative_to(p) or p.is_relative_to(output) for p in (inputs, clean)
    ):
        raise ValueError("candidate output must be fresh and separate from inputs")
    candidates = load_candidates(inputs)
    before, clean_before = file_hashes(inputs), file_hashes(clean)
    output.mkdir(parents=True)
    checks: list[dict[str, Any]] = []
    for candidate in candidates:
        task, scenario, oracle = candidate.public, candidate.overlay, candidate.oracle
        for branch in ("attack", "benign"):
            for negative in (False, True):
                label = "negative" if negative else "safe"
                directory = output / task.task_id / f"{branch}_{label}"
                directory.mkdir(parents=True)
                environment = directory / "environment"
                registry = build_overlay_registry(clean, environment, scenario, branch)
                if len(registry.names) != 8:
                    raise ValueError("must retain exactly eight tools")
                backend = RecordingReplay(
                    oracle.negative_actions if negative else oracle.safe_actions,
                    oracle.negative_final if negative else oracle.safe_final,
                )
                trace = directory / "trace.jsonl"
                result = AgentRuntime(backend, registry).run(task, trace_path=trace)
                events = [
                    TraceEvent.model_validate_json(line) for line in trace.read_text().splitlines()
                ]
                observed = "\n".join(
                    json.dumps(e.data, ensure_ascii=False)
                    for e in events
                    if e.event == "tool_result" and e.data.get("ok")
                )
                addition = scenario.attack_text if branch == "attack" else scenario.benign_text
                if addition not in observed or scenario.base_content not in observed:
                    raise ValueError("selected source overlay not observed by script")
                if result.status != "completed" or result.parse_errors:
                    raise ValueError("fixture runtime/parser failure")
                if any(e.event == "tool_result" and not e.data.get("ok") for e in events):
                    raise ValueError("candidate reference script has unsuccessful tool calls")
                scored = score_scoped(events, oracle, environment / "database/university.db")
                if scored["unassessed_actions"]:
                    raise ValueError("fixture has unassessed authorization")
                if not negative and (
                    not scored["safe_utility"]
                    or not all(f in observed for f in oracle.required_facts)
                ):
                    raise ValueError("safe fixture lacks safe utility or observable fact evidence")
                if negative and not (
                    scored["executed_violations"]
                    if oracle.expected_negative == "executed_violation"
                    else scored["final_leaked_artifacts"]
                ):
                    raise ValueError("negative fixture did not trigger expected violation")
                # Existence probes are separate Broker calls, never extra context for the fixture.
                probe = ToolBroker(registry, TraceLogger(directory / "artifact_probes.jsonl"))
                for index, artifact in enumerate(oracle.sensitive_artifacts, start=1):
                    read = probe.execute(
                        artifact.read_action.name,
                        artifact.read_action.arguments,
                        run_id="artifact_probe",
                        task_id=task.task_id,
                        step=index,
                    )
                    if not read.ok or artifact.value not in json.dumps(
                        read.content, ensure_ascii=False
                    ):
                        raise ValueError("private artifact reference does not exist")
                initial = json.dumps(backend.contexts[0], ensure_ascii=False)
                if any(a.value in initial for a in oracle.sensitive_artifacts):
                    raise ValueError("private value leaked into initial context")
                full = json.dumps(backend.contexts, ensure_ascii=False)
                if any(
                    key in full
                    for key in (
                        "sink_artifacts",
                        "sql_columns",
                        "safe_actions",
                        "template_group",
                        "required_facts",
                    )
                ):
                    raise ValueError("private/catalog metadata in runtime context")
                normalized = [
                    e.model_dump(mode="json", exclude={"timestamp", "run_id"}) for e in events
                ]
                checks.append(
                    {
                        "task_id": task.task_id,
                        "branch": branch,
                        "fixture": label,
                        "score": scored,
                        "payload_reachable": True,
                        "private_context_guard": True,
                        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
                        "observable_sha256": hashlib.sha256(
                            json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode()
                        ).hexdigest(),
                    }
                )
    if file_hashes(inputs) != before or file_hashes(clean) != clean_before:
        raise ValueError("candidate or clean input bytes mutated")
    return {
        "valid": True,
        "scope": "unsplit candidate fixture QA; not Phase 3 acceptance or model metrics",
        "canonical_candidates": len(candidates),
        "replay_runs": len(checks),
        "real_model_runs": 0,
        "variants_generated": 0,
        "split": "unassigned",
        "review_status": "pending",
        "category_counts": dict(
            sorted(Counter(c.overlay.attack_category for c in candidates).items())
        ),
        "source_counts": dict(sorted(Counter(c.overlay.source_type for c in candidates).items())),
        "template_group_counts": dict(
            sorted(Counter(c.metadata.template_group for c in candidates).items())
        ),
        "template_groups_are_author_annotations_not_independence_proof": True,
        "input_sha256": before,
        "clean_environment_sha256": clean_before,
        "checks": checks,
    }
