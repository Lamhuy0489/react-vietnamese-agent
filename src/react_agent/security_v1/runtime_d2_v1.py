"""D2 runtime: the A1 configuration with the control/data policy (design section 3).

D2 runs the same closure runtime path as A1 (rule layer on, LLM guard off, no session
gates); only the per-task policy changes to ``ControlDataPolicy`` (rules 1-3). Rule 4
redacts the final answer value by value. The pinned runtimes are not edited: the
policy and parser are injected with ``bind`` (private copies of function globals).

Rule 4 is applied when the model's final turn is parsed, so the answer that the frozen
loop releases, logs and scores is already redacted; the FINAL decision records which
values were removed. The raw model output stays in the trace as model output.

The user root keeps the frozen label ``Trust.UNTRUSTED`` (``runtime_v5``). At A1 no
session gate reads that label, so it does not change D2 behaviour.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from react_agent.parser import StructuredParser
from react_agent.schemas.agent_output import AgentTurn, FinalAnswer, FinalTurn
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import Effect, SecurityConfig, Stage, configuration
from react_agent.security_v1.control_data_policy_v1 import (
    COMPONENT,
    PROFILE,
    ControlDataPolicy,
    redact,
)
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.phase5_closure_runtime_v1 import Phase5ClosureRuntime
from react_agent.security_v1.phase5_runtime import Phase5Runtime
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_policy import RuntimeVerdict
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v14_email_origin_candidate import (
    CandidateRuntimePolicy,
)
from react_agent.security_v1.runtime_v14_email_origin_candidate import (
    SecurityRuntime as EmailRuntime,
)

RUNTIME_VERSION = "security_runtime_d2_v1"
DEFENSE = "D2"


class D2Policy(ControlDataPolicy, CandidateRuntimePolicy):
    """Rules 1-4 on top of the A1 rule layer with the same raw-user anchors as A1."""

    def __init__(self, config: SecurityConfig, raw_user: str) -> None:
        super().__init__(config, raw_user)
        self.redactions: list[list[str]] = []

    def redact_final(self, answer: str) -> str:
        values = self.final_redactions(answer)
        self.redactions.append(values)
        return redact(answer, values) if values else answer

    def final(self) -> RuntimeVerdict:
        values = self.redactions[-1] if self.redactions else []
        if not values:
            return super().final()
        return RuntimeVerdict(
            stage=Stage.FINAL, effect=Effect.REDACT,
            reasons=("PROVENANCE_SENSITIVE_FINAL",),
            related_artifact_ids=self.state.related_artifacts(values), component=COMPONENT)


class _RedactingParser:
    """Parses like ``StructuredParser``; a final turn passes through rule 4."""

    def __init__(self, inner: StructuredParser, holder: list[D2Policy]) -> None:
        self.inner, self.holder = inner, holder

    def parse(self, text: str) -> AgentTurn:
        turn = self.inner.parse(text)
        if not isinstance(turn, FinalTurn):
            return turn
        answer = self.holder[-1].redact_final(turn.final_answer.answer)
        return FinalTurn(final_answer=FinalAnswer(answer=answer))


_HOLDER: ContextVar[list[D2Policy]] = ContextVar("d2_policy_holder")


def _make_policy(security: SecurityConfig, raw_user: str) -> D2Policy:
    policy = D2Policy(security, raw_user)
    _HOLDER.get().append(policy)
    return policy


def _make_parser(registry: Any) -> _RedactingParser:
    return _RedactingParser(StructuredParser(registry), _HOLDER.get())


class _D2Phase5Runtime(Phase5Runtime):
    """Phase5Runtime whose A1 path builds ``D2Policy`` and the redacting parser."""

    _run_task = bind(
        Phase5Runtime._run_task,
        EmailRuntime=SimpleNamespace(_run_task=bind(
            EmailRuntime._run_task,
            V5Runtime=SimpleNamespace(
                _run_task=bind(V5Runtime._run_task, StructuredParser=_make_parser)),
            CandidateRuntimePolicy=_make_policy,
        )),
    )


class D2Runtime(Phase5ClosureRuntime, _D2Phase5Runtime):
    """Closure runtime (same metadata as A1) with D2; A1 configuration only."""

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        config = kwargs.get("security_config") or configuration("A0")
        if config.level != "A1" or config.llm_guard:
            raise ValueError("D2 runs on the A1 configuration (rules on, guard off)")
        holder: list[D2Policy] = []
        token = _HOLDER.set(holder)
        try:
            result = super()._run_task(task, **kwargs)
        finally:
            _HOLDER.reset(token)
        if len(holder) != 1:
            raise RuntimeError("D2 policy was not installed exactly once")
        policy = holder[0]
        path = Path(kwargs["output"]) / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata["defense_v2"] = {
            "defense": DEFENSE, "profile": PROFILE, "runtime_version": RUNTIME_VERSION,
            "base_configuration": "A1", "llm_guard": False,
            "threshold": policy.state.threshold.value,
            "protected_value_count": len(policy.state.protected),
            "final_redacted_values": sum(len(v) for v in policy.redactions),
            "user_root_trust_label": "UNTRUSTED (frozen runtime_v5; unused at A1)",
        }
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        return result
