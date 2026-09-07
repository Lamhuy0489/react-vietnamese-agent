"""CPU Replay plumbing parity, separate from benchmark model/utility evaluation."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from typing import Any

from react_agent.adversarial_release import ReleasedFixture, load_split
from react_agent.agent import AgentRuntime
from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
)
from react_agent.foundation.dev_validation import prerequisites
from react_agent.foundation.normalization import Profile, text_hash
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.foundation.runtime_v1 import FoundationRuntime
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.replay import ReplayBackend
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action, ActionTurn, FinalAnswer, FinalTurn
from react_agent.schemas.clean_task import CleanPublicTask, FaultSpec
from react_agent.schemas.task import RuntimeTask
from react_agent.schemas.trace import TraceEvent
from react_agent.tools.factory import build_clean_registry, build_smoke_registry
from react_agent.tools.registry import ToolRegistry


class RecordingBackend(ReplayBackend):
    def __init__(self, responses: list[str]) -> None:
        super().__init__(responses)
        self.messages: list[list[dict[str, str]]] = []

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.messages.append([dict(m) for m in messages])
        return super().generate(messages, config)


def final_response(answer: str = "Đã hoàn tất kiểm tra cấu trúc luồng thực thi.") -> str:
    return FinalTurn(final_answer=FinalAnswer(answer=answer)).model_dump_json()


def action_response(action: Action) -> str:
    return ActionTurn(action=action).model_dump_json()


def compare(
    task: RuntimeTask,
    responses: list[str],
    registry_factory: Callable[[Path], ToolRegistry],
    output: Path,
    *,
    catalog: SourceCatalog | None = None,
    config: RuntimeConfig | None = None,
    audit_profile: Profile = "raw_v1",
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("parity output must be fresh")
    output.mkdir(parents=True)
    backends = [RecordingBackend(responses), RecordingBackend(responses)]
    legacy_registry = registry_factory(output / "legacy_env")
    instrumented_registry = registry_factory(output / "foundation_env")
    started = perf_counter()
    old = AgentRuntime(backends[0], legacy_registry, runtime_config=config).run(
        task, trace_path=output / "legacy.jsonl"
    )
    legacy_seconds = perf_counter() - started
    started = perf_counter()
    new = FoundationRuntime(
        backends[1], instrumented_registry, runtime_config=config
    ).run_instrumented(
        task, output=output / "foundation", source_catalog=catalog, audit_profile=audit_profile
    )
    foundation_seconds = perf_counter() - started
    if old.model_dump(exclude={"run_id"}) != new.result.model_dump(exclude={"run_id"}):
        raise ValueError("A0 terminal/outcome parity mismatch")
    if backends[0].messages != backends[1].messages or backends[1].messages != [
        b.model_messages() for b in new.contexts
    ]:
        raise ValueError("A0 exact model-context parity mismatch")
    traces = [
        [TraceEvent.model_validate_json(s) for s in p.read_text(encoding="utf-8").splitlines()]
        for p in (output / "legacy.jsonl", output / "foundation/trace_legacy.jsonl")
    ]
    observables = [
        [e.model_dump(mode="json", exclude={"run_id", "timestamp"}) for e in events]
        for events in traces
    ]
    if observables[0] != observables[1]:
        raise ValueError("A0 observable action/result/final/parse parity mismatch")
    store = ArtifactStore.deserialize(
        new.result.run_id,
        (output / "foundation/artifacts/artifacts.jsonl").read_text(encoding="utf-8"),
    )
    if store.all() != new.artifacts:
        raise ValueError("runtime artifact serialization mismatch")
    raw_outputs = [
        a
        for a in new.artifacts
        if a.artifact_type == ArtifactType.MODEL_OUTPUT
        and a.producer == "runtime_v1"
        and all(p.relation.value == "GENERATED_USING" for p in a.parents)
    ]
    successful_bundles = new.contexts[: len(raw_outputs)]
    if len(raw_outputs) != sum(e.event == "model_output" for e in traces[1]):
        raise ValueError("missing observable model artifacts")
    for model, bundle in zip(raw_outputs, successful_bundles, strict=True):
        if tuple(p.parent_id for p in model.parents) != bundle.artifact_ids:
            raise ValueError("model lineage differs from actual context")
    if new.control.tool_call_count != len(old.tool_sequence) or new.control.model_turn_count != len(
        backends[0].messages
    ):
        raise ValueError("control counters mismatch")
    if new.control.parse_error_count != old.parse_errors:
        raise ValueError("parse counter mismatch")
    finals = [a for a in new.artifacts if a.artifact_type == ArtifactType.FINAL_RESPONSE]
    if len(finals) != int(old.status == "completed"):
        raise ValueError("final artifact completeness mismatch")
    expected_hooks = Counter(
        {"pre": len(old.tool_sequence), "post": len(old.tool_sequence), "final": len(finals)}
    )
    actual_hooks = Counter(
        json.loads(e.data_json)["stage"] for e in new.events if e.event == "policy_decision"
    )
    if +expected_hooks != actual_hooks:
        raise ValueError("hook coverage mismatch")
    for artifact in new.artifacts:
        if not artifact.parents and artifact.source_type not in {
            SourceType.USER,
            SourceType.SYSTEM,
        }:
            if artifact.producer != "tool_source_snapshot":
                raise ValueError("unexplained provenance root")
    return {
        "task_id": task.task_id,
        "valid": True,
        "status": old.status,
        "tool_sequence": old.tool_sequence,
        "parse_errors": old.parse_errors,
        "model_calls": len(backends[0].messages),
        "real_model_runs": 0,
        "replay_runs": 2,
        "artifact_count": len(new.artifacts),
        "edge_count": len(store.edges()),
        "artifact_types": dict(Counter(a.artifact_type.value for a in new.artifacts)),
        "hook_counts": dict(actual_hooks),
        "audit_profile": audit_profile,
        "exact_context_parity": True,
        "exact_observable_parity": True,
        "conservative_lineage_valid": True,
        "context_sha256": text_hash(canonical_json(backends[0].messages)),
        "observable_sha256": text_hash(canonical_json(observables[0])),
        "legacy_seconds": legacy_seconds,
        "foundation_seconds": foundation_seconds,
        "timing_scope": "single CPU Replay with logging; not controlled model benchmark",
        "serialized_artifact_bytes": len(store.serialize().encode("utf-8")),
    }


def dev_selection(rows: list[ReleasedFixture]) -> list[ReleasedFixture]:
    chosen: list[ReleasedFixture] = []
    for source in ("document", "cached_page", "database_text_field", "tool_output"):
        families = sorted({r.family_id for r in rows if r.overlay.source_type == source})[:3]
        for i, family in enumerate(families):
            kind = ("zero_width", "code_mix", "paraphrase")[i]
            chosen.extend(r for r in rows if r.family_id == family and r.variant_type == kind)
    if len(chosen) != 24 or Counter(r.branch for r in chosen) != {"attack": 12, "benign": 12}:
        raise ValueError("24 paired stratified Dev probes required")
    return sorted(chosen, key=lambda r: r.variant_id)


def fixture_catalog(row: ReleasedFixture) -> SourceCatalog:
    source = {
        "document": SourceType.DOCUMENT,
        "cached_page": SourceType.CACHED_PAGE,
        "database_text_field": SourceType.DATABASE,
        "tool_output": SourceType.CALCULATOR,
    }[row.overlay.source_type]
    label = SourceLabel(
        source_type=source,
        source_id=row.overlay.source_id,
        sensitivity=Sensitivity(row.overlay.sensitivity),
        trust=Trust.TRUSTED if row.overlay.trust == "T0" else Trust.UNTRUSTED,
        legacy_trust=row.overlay.trust,
    )
    return SourceCatalog(
        bindings=(
            SourceBinding(
                tool=row.overlay.trigger.name,
                arguments_json=canonical_json(row.overlay.trigger.arguments),
                label=label,
            ),
        )
    )


def run_suite(root: Path, output: Path) -> dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(root / "results"):
        raise ValueError("suite output must be fresh under results")
    before = prerequisites(root)
    smoke_hashes = {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((root / "data/smoke").rglob("*"))
        if p.is_file()
    }
    output.mkdir(parents=True)
    checks = []
    smoke_root = root / "data/smoke"
    smoke = [
        json.loads(s) for s in (smoke_root / "tasks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    responses = json.loads((smoke_root / "replay_responses.json").read_text(encoding="utf-8"))
    for row in smoke:
        task = PublicWorkbenchTask.model_construct(
            task_id=row["task_id"], instruction=row["instruction"]
        )

        def smoke_factory(destination: Path) -> ToolRegistry:
            shutil.copytree(smoke_root, destination)
            return build_smoke_registry(destination)

        check = compare(task, responses[task.task_id], smoke_factory, output / task.task_id)
        check["suite"] = "smoke"
        checks.append(check)
    # QA-only Dev references; only the public task goes to either runtime.
    clean_root = root / "data/clean/v1_1"
    clean_tasks = {
        r.task_id: r
        for r in (
            CleanPublicTask.model_validate_json(s)
            for s in (clean_root / "splits/dev.jsonl").read_text(encoding="utf-8").splitlines()
        )
    }
    ids = json.loads((clean_root / "dev_pilot/task_ids.json").read_text(encoding="utf-8"))[
        "task_ids"
    ]
    if len(ids) != 21 or not set(ids) <= set(clean_tasks):
        raise ValueError("preselected clean Dev IDs invalid")
    truth = {
        r["task_id"]: r
        for r in (
            json.loads(s)
            for s in (clean_root / "private/dev_ground_truth.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
    }
    for identity in ids:
        reference = truth[identity]
        actions = [
            Action(name=s["tool"], arguments=s["arguments"]) for s in reference["oracle_steps"]
        ]
        faults = [FaultSpec.model_validate(f) for f in reference["fault_plan"]]

        def clean_factory(destination: Path, faults: list[FaultSpec] = faults) -> ToolRegistry:
            shutil.copytree(clean_root / "environment", destination)
            return build_clean_registry(destination, fault_plan=faults)

        check = compare(
            clean_tasks[identity],
            [*(action_response(a) for a in actions), final_response()],
            clean_factory,
            output / identity,
        )
        check["suite"] = "clean_dev_reference_actions"
        checks.append(check)
    dev = dev_selection(load_split(root / "data/adversarial/release_v2"))
    for row in dev:

        def fixture_factory(destination: Path, row: ReleasedFixture = row) -> ToolRegistry:
            return row.registry(clean_root / "environment", destination)

        check = compare(
            row.task,
            [action_response(row.overlay.trigger), final_response()],
            fixture_factory,
            output / row.variant_id,
            catalog=fixture_catalog(row),
            audit_profile="security_v1",
        )
        trace = (output / row.variant_id / "foundation/trace_legacy.jsonl").read_text(
            encoding="utf-8"
        )
        # Decode results instead of matching escaped JSON raw bytes.
        actual = "\n".join(
            json.dumps(json.loads(s)["data"], ensure_ascii=False)
            for s in trace.splitlines()
            if json.loads(s)["event"] == "tool_result"
        )
        if getattr(row.overlay, row.branch + "_text") not in actual:
            raise ValueError("Dev source probe did not expose full payload")
        check.update(
            {
                "suite": "adversarial_dev_source_probe",
                "variant_id": row.variant_id,
                "branch": row.branch,
                "source_type": row.overlay.source_type,
            }
        )
        checks.append(check)
    if len(checks) != 65 or any(c["status"] != "completed" for c in checks):
        raise ValueError("65 terminal suite trajectories required")
    if prerequisites(root) != before:
        raise ValueError("frozen data changed during runtime QA")
    if any(
        hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
        for name, digest in smoke_hashes.items()
    ):
        raise ValueError("smoke inputs changed during runtime QA")
    stable = [
        {k: v for k, v in c.items() if k not in {"legacy_seconds", "foundation_seconds"}}
        for c in checks
    ]
    return {
        "schema_version": "phase4_runtime_dev_qa_v1",
        "valid": True,
        "phase4_accepted": False,
        "smoke_tasks": 20,
        "clean_dev_tasks": 21,
        "adversarial_dev_probes": 24,
        "paired_conditions": 65,
        "fresh_replay_runs": 130,
        "real_model_runs": 0,
        "test_payloads_parsed": 0,
        "private_dev_reference_use": "QA action/fault scripts only; never runtime inputs",
        "adversarial_scope": "source exposure + fixed final; not ASR/utility scoring",
        "prerequisites": before,
        "smoke_input_sha256": smoke_hashes,
        "checks": checks,
        "stable_summary_sha256": text_hash(canonical_json(stable)),
        "remaining": [
            "full source metadata/search propagation audit and sensitive/multi-step Dev coverage",
            "reproducible overhead/memory study and full Phase 4 acceptance review",
        ],
    }
