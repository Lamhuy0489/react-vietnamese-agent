"""Raw A0-compatible runtime with explicit context/artifact/hook plumbing."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from react_agent.agent import AgentRuntime
from react_agent.agent.context import ContextBuilder
from react_agent.agent.runtime import FORMAT_CORRECTION
from react_agent.agent.state import RunResult, TerminalStatus
from react_agent.broker import ToolBroker
from react_agent.foundation.artifacts import (
    Artifact,
    ArtifactStore,
    ArtifactType,
    Relation,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
)
from react_agent.foundation.normalization import PROFILES, Profile, normalize, text_hash
from react_agent.foundation.runtime_contracts import (
    ContextBundle,
    ContextMessage,
    ControlState,
    Decision,
    FoundationEvent,
)
from react_agent.foundation.runtime_hooks import (
    AllowAllFinalHook,
    AllowAllPreHook,
    FinalResponseHook,
    PostExecutionHook,
    PreExecutionHook,
    RecordOnlyPostHook,
    SourceCatalog,
    derive,
)
from react_agent.logging import TraceLogger
from react_agent.parser import ParseError, StructuredParser
from react_agent.schemas.agent_output import ActionTurn, FinalTurn
from react_agent.schemas.task import RuntimeTask


@dataclass(frozen=True)
class FoundationRun:
    result: RunResult
    control: ControlState
    artifacts: tuple[Artifact, ...]
    contexts: tuple[ContextBundle, ...]
    events: tuple[FoundationEvent, ...]


class FoundationRuntime(AgentRuntime):
    """Inherited config and legacy logging helpers; original loop remains untouched."""

    def run(self, task: RuntimeTask, *, trace_path: Path | None = None) -> RunResult:
        raise ValueError("use run_instrumented with a fresh output directory; no legacy bypass")

    def run_instrumented(
        self,
        task: RuntimeTask,
        *,
        output: Path,
        source_catalog: SourceCatalog | None = None,
        audit_profile: Profile = "raw_v1",
        pre_hook: PreExecutionHook | None = None,
        post_hook: PostExecutionHook | None = None,
        final_hook: FinalResponseHook | None = None,
    ) -> FoundationRun:
        if audit_profile not in PROFILES or self.runtime_config.config_id != "A0":
            raise ValueError("Phase 4 runtime supports raw A0 and known audit-only profiles")
        output = output.resolve()
        frozen_data = Path(__file__).resolve().parents[3] / "data"
        if output.exists() or output.is_relative_to(frozen_data):
            raise ValueError("instrumented output must be fresh and outside frozen data")
        output.mkdir(parents=True)
        run_id = "run_" + uuid4().hex
        state = ControlState(run_id=run_id, task_id=task.task_id)
        store = ArtifactStore(run_id)
        catalog = source_catalog or SourceCatalog()
        pre, post, final_gate = (
            pre_hook or AllowAllPreHook(),
            post_hook or RecordOnlyPostHook(),
            final_hook or AllowAllFinalHook(),
        )
        logger = TraceLogger(output / "trace_legacy.jsonl")
        broker = ToolBroker(
            self.registry, logger, timeout_seconds=self.runtime_config.tool_timeout_seconds
        )
        parser = StructuredParser(self.registry)
        bundles: list[ContextBundle] = []
        events: list[FoundationEvent] = []
        exported_count = 0

        def event(name: Any, data: object) -> None:
            events.append(
                FoundationEvent(
                    run_id=run_id,
                    task_id=task.task_id,
                    sequence=len(events) + 1,
                    step=state.step,
                    event=name,
                    data_json=canonical_json(data),
                )
            )

        def collect_artifacts() -> None:
            nonlocal exported_count
            for artifact in store.all()[exported_count:]:
                event(
                    "artifact",
                    {"artifact_id": artifact.artifact_id, "content_hash": artifact.content_hash},
                )
            exported_count = len(store.all())

        def root(content: str, kind: ArtifactType, source: SourceType, trust: Trust) -> Artifact:
            return store.create(
                content,
                artifact_type=kind,
                source_type=source,
                source_id=task.task_id if source == SourceType.USER else None,
                producer="host_context",
                created_step=state.step,
                sensitivity=Sensitivity.PUBLIC,
                trust=trust,
            )

        def audit_view(artifact: Artifact) -> None:
            if audit_profile != "raw_v1" and isinstance(artifact.content(), str):
                normalized = normalize(str(artifact.content()), audit_profile)
                view = store.normalized_view(artifact.artifact_id, normalized)
                collect_artifacts()
                event(
                    "normalization",
                    {
                        "raw_artifact_id": artifact.artifact_id,
                        "view_artifact_id": view.artifact_id,
                        "profile": normalized.profile,
                        "version": normalized.normalizer_version,
                        "unicode_version": normalized.unicode_version,
                        "input_hash": normalized.input_hash,
                        "output_hash": normalized.output_hash,
                        "operations": [asdict(o) for o in normalized.operations],
                        "features": json.loads(json.dumps(asdict(normalized.features))),
                    },
                )

        def decision(stage: str, value: Decision, artifact_id: str) -> None:
            if value != Decision():
                raise ValueError("non-pass-through hook unsupported in Phase 4 A0")
            event(
                "policy_decision",
                {"stage": stage, "artifact_id": artifact_id, **value.model_dump()},
            )

        def finish(
            status: TerminalStatus, steps: int, answer: str | None = None, error: str | None = None
        ) -> FoundationRun:
            nonlocal state
            state = state.model_copy(
                update={
                    "status": status,
                    "terminal_reason": status,
                    "proposed_tool": None,
                    "active_call_id": None,
                }
            )
            result = self._finish(
                logger,
                run_id,
                task.task_id,
                status,
                steps,
                list(state.called_tools),
                state.parse_error_count,
                final_answer=answer,
                error=error,
            )
            collect_artifacts()
            event("control", state.model_dump(mode="json"))
            store.export(output / "artifacts")
            with (output / "trace_v2.jsonl").open("x", encoding="utf-8") as stream:
                stream.write("".join(e.model_dump_json() + "\n" for e in events))
            metadata = {
                "runtime_version": "foundation_runtime_v1",
                "artifact_schema": "artifact_v1",
                "trace_schema": "foundation_trace_v2",
                "model_input_profile": "raw_v1",
                "audit_profile": audit_profile,
                "normalizer_version": "normalizer_v1",
                "provenance_mode": "conservative_context",
                "run_id": run_id,
                "task_id": task.task_id,
                "task_hash": text_hash(task.instruction),
                "runtime_config": self.runtime_config.model_dump(),
                "generation_config": self.generation_config.model_dump(),
                "model_id": self.backend.model_id,
                "model_revision": self.backend.model_revision,
                "source_catalog": catalog.model_dump(mode="json"),
                "source_catalog_hash": text_hash(catalog.model_dump_json()),
                "control": state.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
                "artifact_count": len(store.all()),
                "edge_count": len(store.edges()),
                "source_dataset_identity": "must be bound by experiment/QA launch receipt",
            }
            with (output / "run_metadata.json").open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
            return FoundationRun(result, state, store.all(), tuple(bundles), tuple(events))

        initial = ContextBuilder(self.registry.definitions()).build(task, [])
        system = root(
            initial[0]["content"], ArtifactType.USER_INPUT, SourceType.SYSTEM, Trust.TRUSTED
        )
        user = root(task.instruction, ArtifactType.USER_INPUT, SourceType.USER, Trust.UNTRUSTED)
        audit_view(user)
        base_messages = [
            ContextMessage(
                role="system", content=str(system.content()), artifact_id=system.artifact_id
            ),
            ContextMessage(role="user", content=str(user.content()), artifact_id=user.artifact_id),
        ]
        history: list[ContextMessage] = []
        collect_artifacts()
        self._log(
            logger,
            run_id,
            task.task_id,
            0,
            "run_start",
            {
                "config_id": self.runtime_config.config_id,
                "model_id": self.backend.model_id,
                "model_revision": self.backend.model_revision,
                "generation": self.generation_config.model_dump(),
            },
        )
        for step in range(1, self.runtime_config.max_steps + 1):
            state = state.model_copy(update={"step": step})
            correction: ContextMessage | None = None
            for retry in range(self.runtime_config.max_format_retries_per_step + 1):
                state = state.model_copy(
                    update={
                        "model_turn_count": state.model_turn_count + 1,
                        "format_retry_count": state.format_retry_count + int(retry > 0),
                    }
                )
                bundle = ContextBundle(
                    run_id=run_id,
                    step=step,
                    model_turn=state.model_turn_count,
                    messages=tuple(
                        [*base_messages, *history, *([correction] if correction else [])]
                    ),
                )
                bundles.append(bundle)
                collect_artifacts()
                event("context", bundle.model_dump(mode="json"))
                event("control", state.model_dump(mode="json"))
                try:
                    response = self.backend.generate(
                        bundle.model_messages(), self.generation_config
                    )
                except Exception as exc:  # same terminal boundary as frozen A0
                    return finish("model_error", step - 1, error=f"{type(exc).__name__}: {exc}")
                model = derive(
                    store,
                    response.text,
                    kind=ArtifactType.MODEL_OUTPUT,
                    parents=bundle.artifact_ids,
                    step=step,
                    relation=Relation.GENERATED_USING,
                    trust=Trust.UNTRUSTED,
                )
                self._log(
                    logger,
                    run_id,
                    task.task_id,
                    step,
                    "model_output",
                    {"raw_output": response.text, "retry": retry},
                )
                try:
                    turn = parser.parse(response.text)
                except ParseError as exc:
                    state = state.model_copy(
                        update={"parse_error_count": state.parse_error_count + 1}
                    )
                    self._log(
                        logger,
                        run_id,
                        task.task_id,
                        step,
                        "parse_error",
                        {"code": exc.code, "message": exc.message, "retry": retry},
                    )
                    if retry >= self.runtime_config.max_format_retries_per_step:
                        return finish("parse_failure", step - 1)
                    correction_art = root(
                        FORMAT_CORRECTION, ArtifactType.USER_INPUT, SourceType.SYSTEM, Trust.TRUSTED
                    )
                    correction = ContextMessage(
                        role="user",
                        content=FORMAT_CORRECTION,
                        artifact_id=correction_art.artifact_id,
                    )
                    continue
                break

            if isinstance(turn, FinalTurn):
                answer = turn.final_answer.answer
                artifact = derive(
                    store,
                    answer,
                    kind=ArtifactType.FINAL_RESPONSE,
                    parents=(model.artifact_id,),
                    step=step,
                )
                audit_view(artifact)
                collect_artifacts()
                decision("final", final_gate.evaluate(state, artifact), artifact.artifact_id)
                self._log(logger, run_id, task.task_id, step, "final_answer", {"answer": answer})
                return finish("completed", step, answer)

            if isinstance(turn, ActionTurn):
                action_json = turn.model_dump_json()
                action_art = derive(
                    store,
                    action_json,
                    kind=ArtifactType.MODEL_OUTPUT,
                    parents=(model.artifact_id,),
                    step=step,
                    relation=Relation.EXTRACTED_FROM,
                )
                fields = {
                    "send_email_mock": ("to", "subject", "body"),
                    "post_webhook_mock": ("endpoint", "payload"),
                }.get(turn.action.name, ())
                argument_artifacts = [
                    derive(
                        store,
                        turn.action.arguments,
                        kind=ArtifactType.TOOL_ARGUMENT,
                        parents=(action_art.artifact_id,),
                        step=step,
                        relation=Relation.ARGUMENT_DERIVED_FROM,
                    )
                ]
                for field in fields:
                    if field in turn.action.arguments:
                        argument_artifacts.append(
                            derive(
                                store,
                                {"field": field, "value": turn.action.arguments[field]},
                                kind=ArtifactType.TOOL_ARGUMENT,
                                parents=(action_art.artifact_id,),
                                step=step,
                                relation=Relation.ARGUMENT_DERIVED_FROM,
                            )
                        )
                state = state.model_copy(
                    update={
                        "proposed_tool": turn.action.name,
                        "active_call_id": f"call_{state.tool_call_count + 1:06d}",
                    }
                )
                collect_artifacts()
                proposed_copy = turn.action.model_copy(deep=True)
                value = pre.evaluate(state, proposed_copy, tuple(argument_artifacts))
                if proposed_copy != turn.action:
                    raise ValueError("pre-hook mutated A0 action")
                decision("pre", value, action_art.artifact_id)
                result = broker.execute(
                    turn.action.name,
                    turn.action.arguments,
                    run_id=run_id,
                    task_id=task.task_id,
                    step=step,
                )
                state = state.model_copy(
                    update={
                        "tool_call_count": state.tool_call_count + 1,
                        "called_tools": (*state.called_tools, turn.action.name),
                    }
                )
                posted = post.process(
                    state,
                    turn.action.model_copy(deep=True),
                    result.model_copy(deep=True),
                    store,
                    action_art.artifact_id,
                    catalog,
                )
                observation = store.get(posted.result_artifact_id)
                if (
                    posted.result_json != result.model_dump_json()
                    or observation.content() != posted.result_json
                ):
                    raise ValueError("post-hook mutated A0 result")
                source = store.get(posted.source_artifact_id)
                label = catalog.resolve(turn.action)
                if (
                    {p.parent_id for p in observation.parents}
                    != {source.artifact_id, action_art.artifact_id}
                    or source.parents
                    or (source.source_type, source.source_id, source.sensitivity, source.trust)
                    != (label.source_type, label.source_id, label.sensitivity, label.trust)
                    or source.content()
                    != (result.content if result.ok else result.model_dump(mode="json"))
                ):
                    raise ValueError("post-hook lost host source identity or action/source lineage")
                audit_view(observation)
                collect_artifacts()
                decision("post", Decision(), observation.artifact_id)
                history.extend(
                    (
                        ContextMessage(
                            role="assistant",
                            content=action_json,
                            artifact_id=action_art.artifact_id,
                        ),
                        ContextMessage(
                            role="user",
                            content="OBSERVATION: " + posted.result_json,
                            artifact_id=observation.artifact_id,
                        ),
                    )
                )
                state = state.model_copy(update={"proposed_tool": None, "active_call_id": None})
                event("control", state.model_dump(mode="json"))
        return finish("max_steps", self.runtime_config.max_steps)
