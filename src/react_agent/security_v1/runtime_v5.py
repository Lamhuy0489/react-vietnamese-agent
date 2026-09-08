"""Versioned A0–A6 loop with an explicitly task-owned warm guard lifecycle."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict
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
    FoundationEvent,
)
from react_agent.foundation.runtime_hooks import RecordOnlyPostHook, SourceCatalog, derive
from react_agent.llm.base import LLMBackend
from react_agent.logging import TraceLogger
from react_agent.parser import ParseError, StructuredParser
from react_agent.schemas.agent_output import ActionTurn, FinalTurn
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.a2_policy import A2Policy
from react_agent.security_v1.a6_policy import FINAL_POLICY, A6Policy, admit, final_bound
from react_agent.security_v1.contracts import (
    Effect,
    PolicyObservation,
    SecurityConfig,
    Stage,
    configuration,
)
from react_agent.security_v1.guard import PROMPT
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_policy import (
    DENIAL_FEEDBACK,
    RuntimePolicy,
    RuntimeVerdict,
    SecurityEvent,
)
from react_agent.security_v1.session_policy import SessionPolicy
from react_agent.security_v1.value_gates import post_data_view
from react_agent.security_v1.value_origin import ValueOriginIndex
from react_agent.security_v1.warm_guard import (
    WarmGuardBackend,
    WarmGuardConfig,
    WarmModelGuard,
)


class SecurityRuntime(AgentRuntime):
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
        security_config: SecurityConfig | None = None,
        guard_factory: Callable[[], LLMBackend] | None = None,
        guard_execution: WarmGuardConfig | None = None,
    ) -> SecurityRun:
        security = security_config or configuration("A0")
        worker = None
        if security.llm_guard:
            if guard_factory is None or guard_execution is None:
                raise ValueError("A2–A6 require explicit warm guard factory and identity")
            if not isinstance(guard_execution, WarmGuardConfig):
                raise ValueError("warm runtime requires WarmGuardConfig; no silent cold migration")
            worker = WarmGuardBackend(guard_factory, guard_execution)
        elif guard_factory is not None or guard_execution is not None:
            raise ValueError("A0/A1 must not receive a guard")
        try:
            return self._run_task(
                task,
                output=output,
                source_catalog=source_catalog,
                audit_profile=audit_profile,
                security_config=security,
                guard_factory=guard_factory,
                guard_execution=guard_execution,
                _worker=worker,
            )
        finally:
            if worker is not None:
                worker.close()

    def _run_task(
        self,
        task: RuntimeTask,
        *,
        output: Path,
        source_catalog: SourceCatalog | None = None,
        audit_profile: Profile = "raw_v1",
        security_config: SecurityConfig | None = None,
        guard_factory: Callable[[], LLMBackend] | None = None,
        guard_execution: WarmGuardConfig | None = None,
        _worker: WarmGuardBackend | None = None,
    ) -> SecurityRun:
        if audit_profile not in PROFILES or self.runtime_config.config_id != "A0":
            raise ValueError("baseline runtime mechanics must stay A0 with known audit profiles")
        security = security_config or configuration("A0")
        worker: WarmGuardBackend | None = _worker
        policy: RuntimePolicy
        if security.level in {"A2", "A3", "A4", "A5", "A6"}:
            if guard_factory is None or guard_execution is None:
                raise ValueError("A2–A6 require explicit guard factory and execution identity")
            if worker is None:
                raise ValueError("task-owned warm guard required")
            policy = (
                A6Policy(security, task.instruction, WarmModelGuard(worker))
                if security.level == "A6"
                else A2Policy(security, task.instruction, WarmModelGuard(worker))
                if security.level == "A2"
                else SessionPolicy(security, task.instruction, WarmModelGuard(worker))
            )
        else:
            if guard_factory is not None or guard_execution is not None:
                raise ValueError("A0/A1 must not receive a guard")
            policy = RuntimePolicy(security, task.instruction)
        output = output.resolve()
        frozen_data = Path(__file__).resolve().parents[3] / "data"
        if output.exists() or output.is_relative_to(frozen_data):
            raise ValueError("instrumented output must be fresh and outside frozen data")
        output.mkdir(parents=True)
        run_id = "run_" + uuid4().hex
        state = ControlState(run_id=run_id, task_id=task.task_id)
        store = ArtifactStore(run_id)
        index = ValueOriginIndex(store) if isinstance(policy, A6Policy) else None
        value_count = 0
        final_release: dict[str, Any] | None = None
        if index is not None:
            (output / "trace_value.jsonl").touch(exist_ok=False)

        def value_audit(stage: str, data: dict[str, Any]) -> None:
            nonlocal value_count
            if index is None:
                return
            value_count += 1
            row = {
                "schema_version": "a6_value_trace_v1",
                "sequence": value_count,
                "run_id": run_id,
                "task_id": task.task_id,
                "step": state.step,
                "stage": stage,
                "index_sha256": index.identity,
                **data,
            }
            with (output / "trace_value.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(canonical_json(row) + "\n")

        catalog = source_catalog or SourceCatalog()
        post = RecordOnlyPostHook()
        security_events: list[SecurityEvent] = []
        proposals = 0
        denials = 0
        guard_count = 0
        attempt_count = 0
        session_count = 0
        if worker is not None:
            (output / "trace_guard.jsonl").touch(exist_ok=False)
        if isinstance(policy, SessionPolicy):
            (output / "trace_session.jsonl").touch(exist_ok=False)

        def session_audit(
            stage: str, artifact_id: str | None = None, proposal_id: str | None = None
        ) -> None:
            nonlocal session_count
            if not isinstance(policy, SessionPolicy):
                return
            session_count += 1
            row = {
                "schema_version": "session_trace_v1",
                "run_id": run_id,
                "task_id": task.task_id,
                "sequence": session_count,
                "step": state.step,
                "stage": stage,
                "candidate_artifact_id": artifact_id,
                "proposal_id": proposal_id,
                "state": policy.session.model_dump(mode="json"),
            }
            with (output / "trace_session.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(canonical_json(row) + "\n")

        session_audit("INITIAL")

        def guard_audit(artifact_id: str, proposal_id: str) -> None:
            nonlocal guard_count, attempt_count
            if not isinstance(policy, A2Policy) or worker is None:
                return
            for record in policy.guard_records[guard_count:]:
                row = {
                    **record,
                    "schema_version": "guard_trace_warm_v1",
                    "run_id": run_id,
                    "task_id": task.task_id,
                    "step": state.step,
                    "candidate_artifact_id": artifact_id,
                    "proposal_id": proposal_id,
                    "execution_attempts": worker.attempts[attempt_count:],
                }
                with (output / "trace_guard.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(canonical_json(row) + "\n")
                attempt_count = len(worker.attempts)
            guard_count = len(policy.guard_records)

        def security_event(name: Any, data: object) -> None:
            security_events.append(
                SecurityEvent(
                    run_id=run_id,
                    task_id=task.task_id,
                    step=state.step,
                    sequence=len(security_events) + 1,
                    event=name,
                    data_json=canonical_json(data),
                )
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

        def decision(
            value: RuntimeVerdict, artifact_id: str, proposal_id: str | None = None
        ) -> None:
            data = {
                "artifact_id": artifact_id,
                "proposal_id": proposal_id,
                **value.model_dump(mode="json"),
            }
            security_event("decision", data)
            event("policy_decision", data)

        def finish(
            status: TerminalStatus, steps: int, answer: str | None = None, error: str | None = None
        ) -> SecurityRun:
            nonlocal state
            if worker is not None:
                worker.close()
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
            if index is not None:
                with (output / "value_index.json").open("x", encoding="utf-8") as stream:
                    stream.write(canonical_json(index.snapshot()) + "\n")
            with (output / "trace_v2.jsonl").open("x", encoding="utf-8") as stream:
                stream.write("".join(e.model_dump_json() + "\n" for e in events))
            with (output / "trace_security.jsonl").open("x", encoding="utf-8") as stream:
                stream.write("".join(e.model_dump_json() + "\n" for e in security_events))
            metadata = {
                "runtime_version": "security_runtime_v5",
                "guard_lifecycle_events": worker.lifecycle_events if worker else [],
                "guard_closed": worker.closed if worker else None,
                "a6_policy_profile": "a6_composition_v1" if index is not None else None,
                "final_policy": FINAL_POLICY if index is not None else None,
                "final_release": final_release,
                "value_trace_count": value_count,
                "value_index_hash": index.identity if index is not None else None,
                "session_trace_schema": "session_trace_v1"
                if isinstance(policy, SessionPolicy)
                else None,
                "session_snapshot_count": session_count,
                "session_state": policy.session.model_dump(mode="json")
                if isinstance(policy, SessionPolicy)
                else None,
                "security_trace_schema": "security_trace_v1",
                "guard_trace_schema": "guard_trace_warm_v1" if worker else None,
                "guard_execution": asdict(worker.config) if worker else None,
                "guard_execution_hash": worker.config.identity if worker else None,
                "guard_prompt_hash": text_hash(PROMPT) if worker else None,
                "guard_generation": policy.guard.generation.model_dump()
                if isinstance(policy, A2Policy)
                else None,
                "guard_classification_count": guard_count,
                "guard_execution_attempt_count": len(worker.attempts) if worker else 0,
                "security_config": security.model_dump(mode="json"),
                "security_config_hash": security.identity,
                "policy_feedback_version": "denial_feedback_v1",
                "proposed_tool_count": proposals,
                "denied_tool_count": denials,
                "detector_error_count": len(policy.errors),
                "artifact_schema": "artifact_v1",
                "trace_schema": "foundation_trace_v2",
                "model_input_profile": "untrusted_data_view_v1" if index is not None else "raw_v1",
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
            return SecurityRun(
                result,
                state,
                store.all(),
                tuple(bundles),
                tuple(events),
                tuple(security_events),
                proposals,
                denials,
            )

        initial = ContextBuilder(self.registry.definitions()).build(task, [])
        system = root(
            initial[0]["content"], ArtifactType.USER_INPUT, SourceType.SYSTEM, Trust.TRUSTED
        )
        user = root(task.instruction, ArtifactType.USER_INPUT, SourceType.USER, Trust.UNTRUSTED)
        audit_view(user)
        if index is not None:
            admission_error = admit(index, user.artifact_id, state.step)
            value_audit(
                "INITIAL",
                {"source_artifact_id": user.artifact_id, "admission_error": admission_error},
            )
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
                "config_id": security.level,
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
                security_event("proposed_final", {"artifact_id": artifact.artifact_id})
                released_id = artifact.artifact_id
                if index is not None:
                    release = final_bound(index, artifact.artifact_id, user.artifact_id)
                    final_release = release.model_dump(mode="json")
                    value_audit("FINAL", {"release": final_release, "policy": FINAL_POLICY})
                    released_id = release.released_artifact_id
                    answer = str(store.get(released_id).content())
                    final_verdict = RuntimeVerdict(
                        stage=Stage.FINAL,
                        effect=release.effect,
                        reasons=tuple(r.value for r in release.reasons),
                        related_artifact_ids=(artifact.artifact_id, released_id),
                        component=FINAL_POLICY,
                    )
                    decision(final_verdict, artifact.artifact_id)
                else:
                    decision(policy.final(), artifact.artifact_id)
                session_audit("FINAL", artifact.artifact_id)
                security_event("released_final", {"artifact_id": released_id})
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
                proposals += 1
                proposal_id = f"proposal_{proposals:06d}"
                security_event(
                    "proposal",
                    {
                        "proposal_id": proposal_id,
                        "artifact_id": action_art.artifact_id,
                        "argument_artifact_ids": [a.artifact_id for a in argument_artifacts],
                        "action": turn.action.model_dump(mode="json"),
                    },
                )
                value = (
                    policy.pre_bound(
                        turn.action, action_art.artifact_id, user.artifact_id, index, self.registry
                    )
                    if isinstance(policy, A6Policy) and index is not None
                    else policy.pre_with_artifact(turn.action, action_art.artifact_id)
                    if isinstance(policy, SessionPolicy)
                    else policy.pre(turn.action)
                )
                if isinstance(policy, A6Policy):
                    value_audit("PRE", {"proposal_id": proposal_id, **policy.value_records[-1]})
                session_audit("PRE", action_art.artifact_id, proposal_id)
                guard_audit(action_art.artifact_id, proposal_id)
                decision(value, action_art.artifact_id, proposal_id)
                if value.effect == Effect.DENY:
                    denials += 1
                    feedback = derive(
                        store,
                        DENIAL_FEEDBACK,
                        kind=ArtifactType.TOOL_RESULT,
                        parents=tuple(
                            dict.fromkeys((action_art.artifact_id, *value.related_artifact_ids))
                        ),
                        step=step,
                        source_type=SourceType.SYSTEM,
                        producer="policy_feedback_v1",
                    )
                    security_event(
                        "denied",
                        {
                            "proposal_id": proposal_id,
                            "artifact_id": action_art.artifact_id,
                            "feedback_artifact_id": feedback.artifact_id,
                        },
                    )
                    history.extend(
                        (
                            ContextMessage(
                                role="assistant",
                                content=action_json,
                                artifact_id=action_art.artifact_id,
                            ),
                            ContextMessage(
                                role="user",
                                content=DENIAL_FEEDBACK,
                                artifact_id=feedback.artifact_id,
                            ),
                        )
                    )
                    state = state.model_copy(update={"proposed_tool": None, "active_call_id": None})
                    collect_artifacts()
                    event("control", state.model_dump(mode="json"))
                    continue
                result = broker.execute(
                    turn.action.name,
                    turn.action.arguments,
                    run_id=run_id,
                    task_id=task.task_id,
                    step=step,
                )
                security_event(
                    "broker_result",
                    {
                        "proposal_id": proposal_id,
                        "call_id": result.call_id,
                        "tool": turn.action.name,
                        "ok": result.ok,
                    },
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
                context_observation = observation
                context_result_json = posted.result_json
                if index is not None:
                    admission_error = admit(index, source.artifact_id, step)
                    context_observation = post_data_view(
                        store, source.artifact_id, observation.artifact_id
                    )
                    context_result_json = str(context_observation.content())
                    value_audit(
                        "POST",
                        {
                            "proposal_id": proposal_id,
                            "source_artifact_id": source.artifact_id,
                            "raw_observation_id": observation.artifact_id,
                            "context_view_id": context_observation.artifact_id,
                            "admission_error": admission_error,
                        },
                    )
                audit_view(observation)
                collect_artifacts()
                previous_errors = len(policy.errors)
                previous_signals = len(policy.component.signals)
                verdict = policy.post(
                    PolicyObservation(
                        artifact_id=source.artifact_id,
                        content=source.raw_json,
                        source_type=source.source_type,
                        sensitivity=source.sensitivity,
                        trust=source.trust,
                    )
                )
                session_audit("POST", source.artifact_id, proposal_id)
                guard_audit(source.artifact_id, proposal_id)
                decision(verdict, observation.artifact_id, proposal_id)
                for signal in policy.component.signals[previous_signals:]:
                    security_event("rule_signal", signal.model_dump(mode="json"))
                for identity, error_class in policy.errors[previous_errors:]:
                    security_event(
                        "detector_error", {"artifact_id": identity, "error_class": error_class}
                    )
                history.extend(
                    (
                        ContextMessage(
                            role="assistant",
                            content=action_json,
                            artifact_id=action_art.artifact_id,
                        ),
                        ContextMessage(
                            role="user",
                            content="OBSERVATION: " + context_result_json,
                            artifact_id=context_observation.artifact_id,
                        ),
                    )
                )
                state = state.model_copy(update={"proposed_tool": None, "active_call_id": None})
                event("control", state.model_dump(mode="json"))
        return finish("max_steps", self.runtime_config.max_steps)
