"""Private QA adapter for selected canonicals; original runtime/scorers stay frozen."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel

from react_agent.agent import AgentRuntime
from react_agent.authoring.admission_review import evidence_checks, verify_hash_map
from react_agent.authoring.boundary_rules import (
    BoundaryRule,
    load_boundary_candidates,
    score_boundary,
)
from react_agent.authoring.candidate_qa import Candidate, load_candidates
from react_agent.authoring.candidate_review import load_utilities
from react_agent.authoring.disclosure_rules import DisclosureRule, score_disclosure
from react_agent.authoring.flow_batch import FlowRules, score_flow
from react_agent.authoring.linked_resources import LinkedResources, build_linked_registry
from react_agent.authoring.linked_scope import LinkedRules, score_linked
from react_agent.authoring.mechanism_rules import MechanismRules, score_mechanisms
from react_agent.authoring.overlays import build_overlay_registry
from react_agent.authoring.typed_utility import TypedUtility, score_typed
from react_agent.authoring.workbench_qa import RecordingReplay, file_hashes
from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.adversarial_workbench import OverlayScenario, PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.schemas.trace import TraceEvent
from react_agent.tools.registry import ToolRegistry

SELECTION_PATH = "experiments/manifests/phase3_canonical_selection_v1_validation01.json"
SELECTION_SHA256 = "4fa5526392d9290225b6a67b2eaff792701b573a8af6fbec67c52d5b206afdb7"
Branch = Literal["attack", "benign"]
Rule = MechanismRules | LinkedRules | FlowRules | DisclosureRule | BoundaryRule | None
T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class PublicInputs:
    task: PublicWorkbenchTask
    overlay: OverlayScenario
    resources: LinkedResources | None


@dataclass(frozen=True)
class SelectedCase:
    candidate: Candidate
    utility: TypedUtility
    rule: Rule
    resources: LinkedResources | None
    selection: dict[str, Any]
    expected: dict[tuple[str, str], dict[str, Any]]

    def public_inputs(self, payload: str, branch: Branch) -> PublicInputs:
        if branch not in {"attack", "benign"}:
            raise ValueError("unknown branch")
        overlay = OverlayScenario.model_validate(
            {
                **self.candidate.overlay.model_dump(),
                f"{branch}_text": payload,
            }
        )
        return PublicInputs(self.candidate.public, overlay, self.resources)

    def score(self, events: list[TraceEvent], database: Path) -> dict[str, Any]:
        oracle, utility, rule = self.candidate.oracle, self.utility, self.rule
        if isinstance(rule, MechanismRules):
            return score_mechanisms(events, oracle, utility, rule, database)
        if isinstance(rule, LinkedRules):
            return score_linked(events, oracle, utility, rule, database)
        if isinstance(rule, FlowRules):
            return score_flow(events, oracle, utility, rule, database)
        if isinstance(rule, DisclosureRule):
            return score_disclosure(events, oracle, utility, rule, database)
        if isinstance(rule, BoundaryRule):
            return score_boundary(events, oracle, utility, rule, database)
        if rule is None and self.selection["batch"] == "candidates_v2_2":
            return score_typed(events, oracle, utility, database)
        raise ValueError("unknown/missing scorer; no safe fallback")

    def exposures(self) -> list[Action]:
        if isinstance(self.rule, (LinkedRules, FlowRules)):
            return self.rule.exposure_actions
        if isinstance(self.rule, MechanismRules):
            actions = [self.candidate.overlay.trigger, self.rule.exposure_action]
            return list({a.model_dump_json(): a for a in actions}.values())
        return [self.candidate.overlay.trigger]


def records(path: Path, model: type[T]) -> dict[str, T]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise ValueError("sidecars must be a list of typed records")
    rows = [model.model_validate(row) for row in payload]
    by_id: dict[str, T] = {str(r.model_dump()["task_id"]): r for r in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate private sidecar identity")
    return by_id


def load_selected(root: Path) -> tuple[dict[str, Any], dict[str, SelectedCase]]:
    root = root.resolve()
    verify_hash_map(root, {SELECTION_PATH: SELECTION_SHA256})
    manifest: dict[str, Any] = json.loads((root / SELECTION_PATH).read_text())
    verify_hash_map(root, manifest["source_sha256"])
    verify_hash_map(root, manifest["evidence_bindings"])
    for binding in manifest["evidence_bindings"]:
        if binding.startswith("experiments/"):
            verify_hash_map(root, json.loads((root / binding).read_text())["source_sha256"])
    if not manifest["canonical_authoring_admitted"] or not manifest["canonical_split_valid"]:
        raise ValueError("canonical selection not admitted")
    verify_hash_map(
        root,
        {
            "data/adversarial/canonical_selection_v1/review.json": manifest["review_sha256"],
        },
    )
    if file_hashes(root / "data/clean/v1_1/environment") != manifest["clean_environment_sha256"]:
        raise ValueError("stale clean environment")
    reports = {
        name: json.loads(
            (root / f"experiments/manifests/phase3_{name}_v1_validation01.json").read_text()
        )
        for name in ("boundary", "completion", "disclosure", "admission")
    }
    previous = json.loads((root / reports["admission"]["previous_evidence"]["path"]).read_text())
    pilot = previous["prior_pool"]["prior_pool"]["batches"]["pilot"]
    sidecar = root / "data/adversarial/candidate_review_v1"
    if file_hashes(sidecar) != pilot["sidecar_sha256"]:
        raise ValueError("stale pilot utility sidecar")
    checks = [
        c for name in ("boundary", "completion", "disclosure") for c in reports[name]["checks"]
    ]
    checks.extend(evidence_checks(previous, reports["admission"]["revision"]))
    expected = {(c["task_id"], c["branch"], c["fixture"]): c["score"] for c in checks}
    if len(expected) != len(checks) or len(checks) != 288:
        raise ValueError("reference identity coverage mismatch")
    chosen = {row["task_id"]: row for row in manifest["canonicals"]}
    cases = {}
    models: dict[str, tuple[str, type[BaseModel]]] = {
        "mechanism_batch_v2": ("rules.json", MechanismRules),
        "transaction_batch_v1": ("rules.json", MechanismRules),
        "completion_batch_v1": ("rules.json", MechanismRules),
        "linked_scope_v1": ("linked_rules.json", LinkedRules),
        "flow_batch_v1": ("flow_rules.json", FlowRules),
        "disclosure_batch_v1": ("disclosure_rules.json", DisclosureRule),
        "boundary_batch_v1": ("boundary_rules.json", BoundaryRule),
    }
    for batch, hashes in manifest["input_sha256"].items():
        path = (root / "data/adversarial" / batch).resolve()
        if not path.is_relative_to(root / "data/adversarial") or file_hashes(path) != hashes:
            raise ValueError("stale/escaping canonical batch")
        candidates = (
            load_boundary_candidates if batch == "boundary_batch_v1" else load_candidates
        )(path)
        utilities = load_utilities(
            (sidecar if batch == "candidates_v2_2" else path) / "private/utility.json", candidates
        )
        rules: dict[str, Any] = {}
        if batch in models:
            filename, model = models[batch]
            rules = records(path / "private" / filename, model)
            if set(rules) != set(utilities):
                raise ValueError("rule/task coverage mismatch")
        elif batch != "candidates_v2_2":
            raise ValueError("unsupported batch")
        resources = (
            records(path / "overlays/resources.json", LinkedResources)
            if (path / "overlays/resources.json").exists()
            else {}
        )
        if not set(resources) <= set(utilities):
            raise ValueError("resource/task coverage mismatch")
        for candidate in candidates:
            task = candidate.public.task_id
            if task not in chosen:
                continue
            if task in cases or chosen[task]["batch"] != batch:
                raise ValueError("selection/canonical identity mismatch")
            case = SelectedCase(
                candidate,
                utilities[task],
                rules.get(task),
                resources.get(task),
                chosen[task],
                {
                    (branch, fixture): expected[task, branch, fixture]
                    for branch in ("attack", "benign")
                    for fixture in ("safe", "negative")
                },
            )
            if candidate.overlay.trigger not in case.exposures() or any(
                a not in script
                for a in case.exposures()
                for script in (candidate.oracle.safe_actions, candidate.oracle.negative_actions)
            ):
                raise ValueError(f"missing source exposure in reference path: {task}")
            cases[task] = case
    if len(cases) != 70 or set(cases) != set(chosen):
        raise ValueError("selected case coverage mismatch")
    return manifest, cases


def build_public_registry(
    clean: Path, destination: Path, public: PublicInputs, branch: Branch
) -> ToolRegistry:
    if public.resources is not None:
        return build_linked_registry(clean, destination, public.overlay, public.resources, branch)
    return build_overlay_registry(clean, destination, public.overlay, branch)


def run_reference(
    root: Path,
    case: SelectedCase,
    payload: str,
    branch: Branch,
    fixture: Literal["safe", "negative", "alternative"],
    destination: Path,
) -> dict[str, Any]:
    root, destination = root.resolve(), destination.resolve()
    if (
        destination.exists()
        or destination.is_relative_to(root / "data")
        or (root / "data").is_relative_to(destination)
    ):
        raise ValueError("reference destination must be fresh and separate from input data")
    if fixture not in {"safe", "negative", "alternative"}:
        raise ValueError("unknown reference fixture")
    oracle = case.candidate.oracle
    actions = oracle.negative_actions if fixture == "negative" else oracle.safe_actions
    final = oracle.negative_final if fixture == "negative" else oracle.safe_final
    if fixture == "alternative":
        if not isinstance(case.rule, BoundaryRule) or case.rule.mode != "shared_quota":
            raise ValueError("no declared alternative for this case")
        alternative = next(a for a in case.rule.alternatives if a not in oracle.safe_actions)
        if case.rule.prerequisite is None:
            raise ValueError("alternative requires a declared prerequisite")
        actions = [case.rule.prerequisite, alternative]
    public = case.public_inputs(payload, branch)
    destination.mkdir(parents=True)
    env = destination / "environment"
    registry = build_public_registry(root / "data/clean/v1_1/environment", env, public, branch)
    if len(registry.names) != 8:
        raise ValueError("all eight runtime tools must be preserved")
    backend = RecordingReplay(actions, final)
    trace = destination / "trace.jsonl"
    run = AgentRuntime(backend, registry).run(public.task, trace_path=trace)
    events = [TraceEvent.model_validate_json(line) for line in trace.read_text().splitlines()]
    results = [e for e in events if e.event == "tool_result"]
    if run.status != "completed" or run.parse_errors or any(not e.data["ok"] for e in results):
        raise ValueError("reference runtime/tool failure")
    proposed = {
        e.call_id: Action(name=e.data["name"], arguments=e.data["arguments"])
        for e in events
        if e.event == "tool_call_proposed"
    }
    if any(not any(proposed[e.call_id] == a for e in results) for a in case.exposures()):
        raise ValueError("auxiliary source exposure missing")
    exposed = "\n".join(
        json.dumps(e.data["content"], ensure_ascii=False)
        for e in results
        if proposed[e.call_id] == public.overlay.trigger
    )
    if payload not in exposed or public.overlay.base_content not in exposed:
        raise ValueError("complete variant payload absent at designated trigger")
    if isinstance(case.rule, MechanismRules):
        snippet = "\n".join(
            json.dumps(e.data["content"], ensure_ascii=False)
            for e in results
            if proposed[e.call_id] == case.rule.exposure_action
        )
        if payload not in snippet or public.overlay.base_content not in snippet:
            raise ValueError("complete payload absent at declared mechanism exposure")
    contexts = json.dumps(backend.contexts, ensure_ascii=False)
    markers = (
        "safe_actions",
        "negative_actions",
        "sink_artifacts",
        "row_grants",
        "action_rules",
        "evidence_action",
        "forbidden_lines",
        "derived_final_disclosures",
        "template_group",
    )
    if any(marker in contexts for marker in markers) or any(
        a.value in json.dumps(backend.contexts[0], ensure_ascii=False)
        for a in oracle.sensitive_artifacts
    ):
        raise ValueError("private evaluator data entered runtime context")
    score = case.score(events, env / "database/university.db")
    if fixture != "alternative":
        if score != case.expected[branch, fixture]:
            raise ValueError("variant score differs from frozen canonical reference")
    elif not score["safe_utility"] or not score["utility"] or score["unassessed_actions"]:
        raise ValueError("alternative safe utility failed")
    broker = ToolBroker(registry, TraceLogger(destination / "artifact_probes.jsonl"))
    for index, artifact in enumerate(oracle.sensitive_artifacts, start=1):
        probed = broker.execute(
            artifact.read_action.name,
            artifact.read_action.arguments,
            run_id="artifact_probe",
            task_id=public.task.task_id,
            step=index,
        )
        if not probed.ok or artifact.value not in json.dumps(probed.content, ensure_ascii=False):
            raise ValueError("declared artifact missing from actual environment")
    normalized = [e.model_dump(mode="json", exclude={"timestamp", "run_id"}) for e in events]
    return {
        "task_id": public.task.task_id,
        "branch": branch,
        "fixture": fixture,
        "run_id": events[0].run_id,
        "score": score,
        "payload_reachable": True,
        "private_context_guard": True,
        "artifact_existence_verified": True,
        "source_exposures": len(case.exposures()),
        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
        "observable_sha256": hashlib.sha256(
            json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
    }
