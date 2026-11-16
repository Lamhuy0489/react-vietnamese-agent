"""BrokerGuard v3 runtime: D2 (v1) with C1 intent policy, C2 value labels, C3 pinning.

Design: ``docs/project/brokerguard_v3_extension_design.md`` section 3. Developed on Dev
v4.1 only; Test-4 stays sealed until ``final_config_v5`` is frozen.

v3 keeps everything of v1 (D2+P2) except the parts each component replaces, so the
ablations (-C1, -C2, -C3) differ from v3 in exactly one place:

- **C1** replaces D2 rule 2 (destination occurs as a substring of u) with the intent policy
  P(u) (``intent_policy_v1``): a sink runs only if P(u) grants its tool and target. A
  CONFIRM verdict is enforced as a denial with reasons ("CONFIRMATION_REQUIRED", sub-reason)
  so ``run_metrics_v1`` counts it once as a confirmation. Without C1 the D2 rule 2 applies.
- **C2** adds value-level labels (``value_labels_v1``): every value in any tool output is
  labelled by its type, independently of the source label, and R-Flow v2 checks those
  values in light transformed forms at every sink argument and in the final answer (which
  is redacted, as in D2 rule 4). Without C2 only D2 rule 3 applies.
- **C3** pins the literals the user stated in the granting clause (``param_pinning_v1``):
  a sink call that drops one of them or flips a pinned boolean is denied. C3 reads the
  grants of P(u); in the -C1 ablation P(u) is still extracted for C3 but does not
  authorise anything.

The A1 rule layer, D2 rules 1, 3 and 4 (reads free, sensitive payload, final redaction),
the sandwich prompt and the denial feedback are those of v1. Pinned files are not edited:
the policy class is swapped in with ``bind`` as in ``d3``.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar

from react_agent.foundation.artifacts import Sensitivity
from react_agent.schemas.agent_output import Action
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import Effect, SecurityConfig
from react_agent.security_v1.control_data_policy_v1 import (
    COMPONENT as D2_COMPONENT,
)
from react_agent.security_v1.control_data_policy_v1 import (
    SINK_DESTINATION,
    ControlDataState,
    _flatten,
    destination_allowed,
    leaked_values,
)
from react_agent.security_v1.control_data_policy_v1 import redact as d2_redact
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.phase5_runtime import Phase5Runtime
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_d2_v1 import (
    D2Runtime,
    _D2Phase5Runtime,
    _make_parser,
    _RegisteredD2GuardPolicy,
    _RegisteredD2Policy,
)
from react_agent.security_v1.runtime_policy import RuntimeVerdict
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v14_email_origin_candidate import (
    SecurityRuntime as EmailRuntime,
)
from react_agent.security_v3 import intent_policy_v1 as intent_mod
from react_agent.security_v3 import param_pinning_v1 as pinning_mod
from react_agent.security_v3 import value_labels_v1 as labels_mod
from react_agent.security_v3.intent_policy_v1 import Decision, IntentConfig, IntentPolicy

DEFENSE = "BrokerGuard-v3"
PROFILE = "brokerguard_v3_v1"
COMPONENT = "brokerguard_v3_v1"
CONFIRMATION = "CONFIRMATION_REQUIRED"
ALL_COMPONENTS = frozenset({"C1", "C2", "C3"})
# Optional, measured on Dev before any choice: "C1A" also lets P(u) replace the v4 anchors
# of the A1 rule layer (after an injection signal, v1 denies every sink the v4 anchor
# grammar does not authorise, including the user's own).
OPTIONAL_COMPONENTS = frozenset({"C1A"})
# Chosen on Dev-val (decision log 2026-11-16 12:30): the default IntentConfig.
INTENT_CONFIG = IntentConfig()


@dataclass
class V3State(ControlDataState):
    """D2 per-run state; with C1 the destination check is the intent policy."""

    intent: IntentPolicy | None = None
    authorize: bool = True  # C1: P(u) decides sinks (else D2 rule 2)
    pinning: bool = False  # C3
    confirm_reason: str | None = None
    value_labels: bool = False
    labelled: dict[str, str] = field(default_factory=dict)  # compact value -> label

    def observe(self, artifact_id: str, content: str, sensitivity: Sensitivity) -> None:
        super().observe(artifact_id, content, sensitivity)
        if self.value_labels:
            found = labels_mod.label_values(content)
            self.labelled.update(found)
            self.sources.setdefault(artifact_id, set()).update(found)

    def leaks(self, text: str) -> list[str]:
        """D2 rule 3 values plus, with C2, labelled values in any light form."""
        out = leaked_values(text, self.protected, self.user_text)
        if self.value_labels:
            out += [v for v in labels_mod.flows(text, self.labelled, self.user_text)
                    if v not in out]
        return out

    def check_final(self, answer: str) -> list[str]:
        return self.leaks(answer)

    def check_action(self, action: Action) -> tuple[str, list[str]] | None:
        self.confirm_reason = None
        key = SINK_DESTINATION.get(action.name)
        if key is None:
            return None  # rule 1: reads are free
        if self.intent is None or not self.authorize:  # -C1: D2 rule 2
            if not destination_allowed(_flatten(action.arguments.get(key)), self.user_text):
                return "UNTRUSTED_CONTROL_INFLUENCE", []
        else:
            verdict = self.intent.decide(action.name, action.arguments)
            if verdict.decision is Decision.CONFIRM:
                self.confirm_reason = verdict.reason
                return CONFIRMATION, []
            if verdict.decision is Decision.DENY:
                return verdict.reason, []
        if self.pinning and self.intent is not None:
            changed = pinning_mod.check(action.name, action.arguments, self.intent.grants)
            if changed:
                return changed
        payload = _flatten({k: v for k, v in action.arguments.items() if k != key})
        leaked = self.leaks(payload)
        if leaked:
            return "PROVENANCE_SENSITIVE_PAYLOAD", leaked
        return None


@dataclass(frozen=True)
class IntentAnchors:
    """Duck-typed ``AuthorizationAnchors`` for the A1 rule layer, backed by P(u)."""

    intent: IntentPolicy

    def authorizes(self, action: Action) -> bool:
        return self.intent.decide(action.name, action.arguments).decision is Decision.ALLOW


_HOLDER: ContextVar[list[BrokerGuardV3Policy]] = ContextVar("brokerguard_v3_holder")


class BrokerGuardV3Policy(_RegisteredD2Policy):
    """D2 policy whose state applies the enabled v3 components."""

    components: ClassVar[frozenset[str]] = ALL_COMPONENTS

    def __init__(self, config: SecurityConfig, raw_user: str) -> None:
        super().__init__(config, raw_user)
        intent = (intent_mod.extract(raw_user, INTENT_CONFIG)
                  if self.components & {"C1", "C3"} else None)
        self.v3_state = V3State(raw_user, self.state.threshold, intent=intent,
                                authorize="C1" in self.components,
                                pinning="C3" in self.components,
                                value_labels="C2" in self.components)
        self.state = self.v3_state
        if "C1A" in self.components and intent is not None:
            self.component.anchors = IntentAnchors(intent)  # type: ignore[assignment]
        self.confirmations = 0
        holder = _HOLDER.get(None)
        if holder is not None:
            holder.append(self)

    def redact_final(self, answer: str) -> str:
        values = self.final_redactions(answer)
        self.redactions.append(values)
        if not values:
            return answer
        labelled = [v for v in values if v in self.v3_state.labelled]
        out = d2_redact(answer, [v for v in values if v not in labelled])
        return labels_mod.redact(out, labelled) if labelled else out

    def pre(self, action: Action) -> RuntimeVerdict:
        verdict = super().pre(action)
        if verdict.effect != Effect.DENY or verdict.component != D2_COMPONENT:
            return verdict
        reasons = verdict.reasons
        if reasons == (CONFIRMATION,) and self.v3_state.confirm_reason:
            reasons = (CONFIRMATION, self.v3_state.confirm_reason)
            self.confirmations += 1
        return verdict.model_copy(update={"reasons": reasons, "component": COMPONENT})


def policy_class(components: frozenset[str]) -> type[BrokerGuardV3Policy]:
    unknown = components - ALL_COMPONENTS - OPTIONAL_COMPONENTS
    if unknown:
        raise ValueError(f"unknown v3 components: {sorted(unknown)}")
    if components == ALL_COMPONENTS:
        return BrokerGuardV3Policy
    name = "BrokerGuardV3Policy_" + "_".join(sorted(components) or ["none"])
    return type(name, (BrokerGuardV3Policy,), {"components": components})


def _bound_task(policy: type[BrokerGuardV3Policy]) -> Any:
    return bind(
        Phase5Runtime._run_task,
        EmailRuntime=SimpleNamespace(_run_task=bind(
            EmailRuntime._run_task,
            V5Runtime=SimpleNamespace(
                _run_task=bind(V5Runtime._run_task, StructuredParser=_make_parser)),
            CandidateRuntimePolicy=policy,
            CandidateA2Policy=_RegisteredD2GuardPolicy,
        )),
    )


class _V3Metadata(D2Runtime):
    components: ClassVar[frozenset[str]] = ALL_COMPONENTS

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        holder: list[BrokerGuardV3Policy] = []
        token = _HOLDER.set(holder)
        try:
            result = super()._run_task(task, **kwargs)
        finally:
            _HOLDER.reset(token)
        path = Path(kwargs["output"]) / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        policy = holder[0] if len(holder) == 1 else None
        intent = policy.v3_state.intent if policy else None
        metadata["defense_v2"].update({
            "defense": DEFENSE, "v3_profile": PROFILE,
            "components": sorted(self.components),
            "intent_profile": intent_mod.PROFILE if intent else None,
            "intent_config": INTENT_CONFIG.__dict__ if intent else None,
            "intent_grants": len(intent.grants) if intent else None,
            "confirmations": policy.confirmations if policy else None,
            "value_labels_profile": labels_mod.PROFILE if "C2" in self.components else None,
            "pinning_profile": pinning_mod.PROFILE if "C3" in self.components else None,
            "labelled_value_count": len(policy.v3_state.labelled) if policy else None,
        })
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        return result


def runtime_class(components: frozenset[str] = ALL_COMPONENTS) -> type[D2Runtime]:
    """v3 runtime with the given components (v3 = all; ablations drop one)."""
    policy = policy_class(components)
    phase5 = type("_V3Phase5Runtime", (_D2Phase5Runtime,), {"_run_task": _bound_task(policy)})
    return type("BrokerGuardV3Runtime", (_V3Metadata, phase5), {"components": components})


BrokerGuardV3Runtime = runtime_class()
