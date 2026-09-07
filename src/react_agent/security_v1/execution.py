"""A0/A1 guarded execution adapter; shared ReAct loop integration is subsequent."""

from __future__ import annotations

from dataclasses import dataclass

from react_agent.broker import ToolBroker
from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
)
from react_agent.foundation.runtime_contracts import ControlState
from react_agent.foundation.runtime_hooks import RecordOnlyPostHook, SourceCatalog, derive
from react_agent.schemas.agent_output import Action
from react_agent.schemas.tool import ToolResult
from react_agent.security_v1.contracts import (
    Effect,
    PolicyObservation,
    SecurityConfig,
    SecurityDecision,
)
from react_agent.security_v1.rules import RulePolicy


@dataclass(frozen=True)
class ExecutionOutcome:
    decision: SecurityDecision
    result: ToolResult | None
    post_decision: SecurityDecision | None


class GuardedBrokerSession:
    def __init__(
        self,
        *,
        run_id: str,
        task_id: str,
        raw_user: str,
        config: SecurityConfig,
        broker: ToolBroker,
        catalog: SourceCatalog,
    ) -> None:
        self.policy = RulePolicy(config, raw_user)
        self.broker = broker
        self.catalog = catalog
        self.run_id, self.task_id = run_id, task_id
        self.store = ArtifactStore(run_id)
        self._step = 0
        self._calls = 0
        self._events: list[str] = []
        self.user = self.store.create(
            raw_user,
            artifact_type=ArtifactType.USER_INPUT,
            source_type=SourceType.USER,
            source_id=task_id,
            producer="host_user",
            created_step=0,
            sensitivity=Sensitivity.PUBLIC,
            trust=Trust.UNTRUSTED,
        )

    @property
    def events(self) -> tuple[str, ...]:
        return tuple(self._events)

    def _record(self, event: str, data: object) -> None:
        self._events.append(
            canonical_json(
                {
                    "version": "security_execution_v1",
                    "run_id": self.run_id,
                    "task_id": self.task_id,
                    "sequence": len(self._events) + 1,
                    "step": self._step,
                    "event": event,
                    "data": data,
                }
            )
        )

    def execute(self, action: Action, *, step: int) -> ExecutionOutcome:
        if step <= self._step:
            raise ValueError("strictly increasing host step required")
        self._step = step
        # Micro-adapter captures the supplied proposal, not fabricated model reasoning.
        proposal = derive(
            self.store,
            action.model_dump(mode="json"),
            kind=ArtifactType.TOOL_ARGUMENT,
            parents=(self.user.artifact_id,),
            step=step,
            producer="host_action_proposal",
        )
        self._record(
            "action_proposed",
            {"artifact_id": proposal.artifact_id, **action.model_dump(mode="json")},
        )
        decision = self.policy.pre(action)
        self._record("pre_decision", decision.model_dump(mode="json"))
        if decision.effect == Effect.DENY:
            self._record("action_denied", {"artifact_id": proposal.artifact_id})
            return ExecutionOutcome(decision, None, None)
        result = self.broker.execute(
            action.name, action.arguments, run_id=self.run_id, task_id=self.task_id, step=step
        )
        self._calls += 1
        self._record("broker_result", {"call_id": result.call_id, "ok": result.ok})
        posted = RecordOnlyPostHook().process(
            ControlState(
                run_id=self.run_id, task_id=self.task_id, step=step, tool_call_count=self._calls
            ),
            action,
            result,
            self.store,
            proposal.artifact_id,
            self.catalog,
        )
        source = self.store.get(posted.source_artifact_id)
        observed = PolicyObservation(
            artifact_id=source.artifact_id,
            content=source.raw_json,
            source_type=source.source_type,
            sensitivity=source.sensitivity,
            trust=source.trust,
        )
        post_decision = self.policy.post(observed)
        self._record("post_decision", post_decision.model_dump(mode="json"))
        if self.policy.signals:
            self._record("rule_signal", self.policy.signals[-1].model_dump(mode="json"))
        return ExecutionOutcome(decision, result, post_decision)
