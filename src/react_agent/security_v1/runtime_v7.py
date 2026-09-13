"""Corrected final release and cumulative A4 scope on the frozen v5 loop.

Only per-run dependencies are substituted; no process-global monkeypatch,
second ReAct loop, model authorization, or benchmark ground truth is used.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from types import FunctionType
from typing import Any, cast

from react_agent.foundation.artifacts import SourceType, canonical_json
from react_agent.foundation.normalization import Profile
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.base import LLMBackend
from react_agent.schemas.agent_output import Action
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.a6_policy import A6Policy
from react_agent.security_v1.contracts import (
    Effect,
    PolicyObservation,
    Reason,
    SecurityConfig,
    configuration,
)
from react_agent.security_v1.final_entitlements import EntitledFinalRelease
from react_agent.security_v1.final_entitlements_v2 import (
    RELEASE_PROFILE,
    FinalEntitlement,
    extract_final_entitlement,
    release_final_with_entitlement,
    validate_entitlement,
)
from react_agent.security_v1.processing_scope import ScopeKind, describe_action
from react_agent.security_v1.processing_scope_v2 import PROFILE as SCOPE_PROFILE
from react_agent.security_v1.processing_scope_v2 import ProcessingScope
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_policy import RuntimeVerdict
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.session_policy import SessionPolicy
from react_agent.security_v1.value_origin_v2 import ValueOriginIndex
from react_agent.security_v1.warm_guard import WarmGuardConfig

RUNTIME_VERSION = "security_runtime_v7"
_V5_RUN_TASK = V5Runtime._run_task


class SecurityRuntime(V5Runtime):
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
        entitlement: FinalEntitlement | None = None,
    ) -> SecurityRun:
        security = security_config or configuration("A0")
        if entitlement is not None:
            if security.level != "A6":
                raise ValueError("final entitlement requires A6")
            validate_entitlement(task.instruction, entitlement)
        # A supplied object cannot change policy. Validate it, then independently
        # derive the canonical grant inside the task; no shared mutable state.
        if security.level == "A6":
            extract_final_entitlement(task.instruction)
        return super().run_instrumented(
            task,
            output=output,
            source_catalog=source_catalog,
            audit_profile=audit_profile,
            security_config=security,
            guard_factory=guard_factory,
            guard_execution=guard_execution,
        )

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        security = kwargs.get("security_config") or configuration("A0")
        catalog = kwargs.get("source_catalog") or SourceCatalog()
        scope = ProcessingScope(task.instruction) if security.session_trust else None
        grant = extract_final_entitlement(task.instruction) if security.level == "A6" else None
        records: list[dict[str, Any]] = []

        class ScopedSessionPolicy(SessionPolicy):
            pending_scope_action: Action | None = None

            def pre_with_artifact(self, action: Action, artifact_id: str | None) -> RuntimeVerdict:
                coarse = super().pre_with_artifact(action, artifact_id)
                if scope is None:
                    return coarse
                self.pending_scope_action = action.model_copy(deep=True)
                bounded = scope.pre(action)
                description = describe_action(action)
                expected_type = {
                    ScopeKind.DOCUMENT: SourceType.DOCUMENT,
                    ScopeKind.CACHED_PAGE: SourceType.CACHED_PAGE,
                }.get(description.kind)
                label = catalog.resolve(action)
                if expected_type is not None and (
                    label.source_type != expected_type
                    or label.source_id not in description.resource_ids
                ):
                    bounded = bounded.model_copy(
                        update={
                            "effect": Effect.DENY,
                            "reasons": (Reason.UNKNOWN_FIELD,),
                            "authorized_by": "unresolved_host_source",
                        }
                    )
                records.append(
                    {
                        "stage": "PRE",
                        "artifact_id": artifact_id,
                        "decision": bounded.model_dump(mode="json"),
                        "scope_sha256": scope.identity,
                    }
                )
                if bounded.effect != Effect.DENY:
                    return coarse
                return coarse.model_copy(
                    update={
                        "effect": Effect.DENY,
                        "reasons": tuple(
                            dict.fromkeys(
                                r
                                for r in (*coarse.reasons, *(v.value for v in bounded.reasons))
                                if r != Reason.PASS.value
                            )
                        ),
                        "component": SCOPE_PROFILE,
                    }
                )

            def post(self, observation: PolicyObservation) -> RuntimeVerdict:
                coarse = super().post(observation)
                if scope is not None:
                    action = self.pending_scope_action
                    if action is None:
                        raise ValueError("scope observation requires a proposed action")
                    label = catalog.resolve(action)
                    if (label.source_type, label.trust) != (
                        observation.source_type,
                        observation.trust,
                    ):
                        raise ValueError("scope observation differs from host source")
                    observed = scope.observe(
                        action,
                        artifact_id=observation.artifact_id,
                        source_type=label.source_type,
                        source_id=label.source_id,
                        trust=label.trust,
                    )
                    records.append(
                        {
                            "stage": "POST",
                            "observation": observed.model_dump(mode="json"),
                            "scope_sha256": scope.identity,
                        }
                    )
                    self.pending_scope_action = None
                return coarse

        # This MRO retains isinstance(SessionPolicy) for session traces and lets
        # A6's existing coarse/value composition retain the new scope veto.
        class ScopedA6Policy(A6Policy, ScopedSessionPolicy):
            pass

        def final_bound(
            index: ValueOriginIndex, proposal_id: str, user_id: str
        ) -> EntitledFinalRelease:
            if grant is None:
                raise ValueError("A6 final grant required")
            return release_final_with_entitlement(index, proposal_id, user_id, grant)

        namespace = dict(_V5_RUN_TASK.__globals__)
        namespace.update(
            SessionPolicy=ScopedSessionPolicy,
            A6Policy=ScopedA6Policy,
            final_bound=final_bound,
            FINAL_POLICY=RELEASE_PROFILE,
            ValueOriginIndex=ValueOriginIndex,
        )
        body = FunctionType(
            _V5_RUN_TASK.__code__,
            namespace,
            _V5_RUN_TASK.__name__,
            _V5_RUN_TASK.__defaults__,
            _V5_RUN_TASK.__closure__,
        )
        body.__kwdefaults__ = _V5_RUN_TASK.__kwdefaults__
        result = cast(SecurityRun, body(self, task, **kwargs))
        output = cast(Path, kwargs["output"]).resolve()
        path = output / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata["runtime_version"] = RUNTIME_VERSION
        metadata["a6_policy_profile"] = "a6_scoped_entitlement_v2" if grant is not None else None
        metadata["final_policy"] = RELEASE_PROFILE if grant is not None else None
        metadata["entitlement_sha256"] = None
        if grant is not None:
            from react_agent.foundation.normalization import text_hash

            metadata["entitlement_sha256"] = text_hash(grant.model_dump_json())
        metadata["processing_scope_profile"] = SCOPE_PROFILE if scope is not None else None
        if scope is not None:
            metadata["processing_scope"] = scope.snapshot()
            with (output / "trace_scope.jsonl").open("x", encoding="utf-8") as stream:
                for sequence, record in enumerate(records, 1):
                    stream.write(
                        canonical_json(
                            {
                                "schema_version": "scope_trace_v2",
                                "run_id": result.result.run_id,
                                "task_id": task.task_id,
                                "sequence": sequence,
                                **record,
                            }
                        )
                        + "\n"
                    )
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
