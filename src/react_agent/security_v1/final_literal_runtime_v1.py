"""CPU-only final-sink ablation; frozen v12 PRE/POST and v3 index stay intact.

This adapter exposes no native launcher and no public-field approvals. It is
not a replacement for the source-frozen room pilot or a Phase 5 release.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1 import clause_pair_runtime_v1 as paired
from react_agent.security_v1 import constrained_runtime_v1 as constrained
from react_agent.security_v1 import room_ticket_pair_runtime_v1 as room_pair
from react_agent.security_v1.constrained_host_v1 import ConstrainedRoleBackend
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.final_entitlements import EntitledFinalRelease
from react_agent.security_v1.final_entitlements_v2 import (
    FinalEntitlement,
    release_final_with_entitlement,
)
from react_agent.security_v1.final_literal_proof_v1 import (
    LiteralProofError,
    issue_literal_proof,
    release_final_with_literal_proof,
)
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, bind
from react_agent.security_v1.public_field_ticket_policy_v2 import DatedTicketA6Policy
from react_agent.security_v1.public_field_ticket_v2 import PROFILE as ROOM_TICKET_PROFILE
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime
from react_agent.security_v1.runtime_v12 import ClauseA6Policy
from react_agent.security_v1.runtime_v12 import SecurityRuntime as V12Runtime
from react_agent.security_v1.value_origin import OriginError
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex as BaselineIndex
from react_agent.security_v1.value_origin_v4 import ValueOriginIndex

RUNTIME_VERSION = "security_runtime_final_literal_cpu_v1"
ROOM_RUNTIME_VERSION = "security_runtime_room_final_literal_cpu_v1"
FINAL_PROFILE = "final_literal_dispatch_cpu_v1"


class FinalLiteralGate:
    """Task-local callable; records both index identities for an independent audit."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def __call__(
        self, baseline: BaselineIndex, proposal_id: str, user_id: str, grant: FinalEntitlement
    ) -> EntitledFinalRelease:
        before = baseline.snapshot()
        proof = None
        candidate: ValueOriginIndex | None = None
        admission_error = None
        proof_status = "not_eligible"
        if not baseline.complete:
            admission_error = "baseline_coverage_incomplete"
            release = release_final_with_entitlement(baseline, proposal_id, user_id, grant)
        else:
            candidate = ValueOriginIndex(baseline.store)
            try:
                for identity, sha256 in before["source_sha256"].items():
                    if baseline.store.get(identity).content_hash != sha256:
                        raise OriginError("admitted source hash changed")
                    candidate.add_artifact(
                        identity, observed_step=baseline.last_observed_step
                    )
            except OriginError:
                # Extraction/budget errors are DENY, never a v3 fallback ALLOW.
                admission_error = "candidate_source_admission_failed"
                if candidate.complete:
                    raise OriginError("candidate integrity failure before admission") from None
            if admission_error is None:
                try:
                    proof = issue_literal_proof(candidate, user_id, user_id)
                except LiteralProofError:
                    # Unsupported raw-user grammar grants nothing. No external
                    # proof/pin is accepted by this CPU-only adapter.
                    proof_status = "not_eligible"
                else:
                    proof_status = "issued_raw_user"
            release = (
                release_final_with_literal_proof(candidate, proposal_id, user_id, grant, proof)
                if proof is not None else
                release_final_with_entitlement(candidate, proposal_id, user_id, grant)
            )
        if baseline.snapshot() != before:
            raise OriginError("final adapter mutated PRE/POST index")
        self.records.append(dict(
            baseline_index=before,
            baseline_index_sha256=baseline.identity,
            final_index=candidate.snapshot() if candidate is not None else before,
            final_index_sha256=candidate.identity if candidate is not None else baseline.identity,
            user_artifact_id=user_id,
            proposal_artifact_id=proposal_id,
            entitlement=grant.model_dump(mode="json"),
            proof_status=proof_status,
            proof=proof.model_dump(mode="json") if proof is not None else None,
            proof_sha256=proof.identity if proof is not None else None,
            admission_error=admission_error,
            release=release.model_dump(mode="json"),
        ))
        return release


class SecurityRuntime(V12Runtime):
    """A6-only CPU development entry point; other levels use frozen runtimes."""

    runtime_version = RUNTIME_VERSION
    tool_policy_profile = "clause_a6_v12"

    def run_instrumented(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        security = kwargs.get("security_config") or configuration("A0")
        if security.level != "A6":
            raise ValueError("final literal CPU adapter requires explicit A6")
        return super().run_instrumented(task, **kwargs)

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        security = kwargs.get("security_config") or configuration("A0")
        if security.level != "A6":
            raise ValueError("final literal CPU adapter requires explicit A6")
        gate = FinalLiteralGate()
        parent = SimpleNamespace(_run_task=bind(
            V7Runtime._run_task,
            release_final_with_entitlement=gate,
            RELEASE_PROFILE=FINAL_PROFILE,
        ))
        body = bind(V12Runtime._run_task, V7Runtime=parent, RUNTIME_VERSION=self.runtime_version)
        result = cast(SecurityRun, body(self, task, **kwargs))
        output = Path(kwargs["output"])
        with (output / "final_literal_gate.json").open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(dict(
                profile=FINAL_PROFILE, runtime_version=self.runtime_version, records=gate.records,
                tool_policy_profile=self.tool_policy_profile,
                public_field_runtime_enabled=False, native_admitted=False,
            ), ensure_ascii=False, indent=2) + "\n")
        return result


class PairedSecurityRuntime(SecurityRuntime):
    a6_policy_type = ClauseA6Policy

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        if not isinstance(kwargs.get("_worker"), ConstrainedRoleBackend):
            raise ValueError("final literal pair requires its constrained guard")
        loop = SimpleNamespace(_run_task=bind(
            V5Runtime._run_task, WarmModelGuard=constrained.HostClassifier, PROMPT=PROMPT,
        ))
        parent = SimpleNamespace(_run_task=bind(
            V12Runtime._run_task, V5Runtime=loop, ClauseA6Policy=self.a6_policy_type,
        ))
        return cast(SecurityRun, bind(
            SecurityRuntime._run_task, V12Runtime=parent,
        )(self, task, **kwargs))


def run_synthetic_pair_task(task: RuntimeTask, *, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    """Explicit CPU route only; not exported through a native launcher."""
    security = kwargs.get("security") or configuration("A0")
    if security.level != "A6":
        raise ValueError("final literal CPU adapter requires explicit A6")
    return cast(SecurityRun, bind(paired._run, SecurityRuntime=PairedSecurityRuntime)(
        task, pair=pair, synthetic=True, **kwargs,
    ))


class RoomPairedSecurityRuntime(PairedSecurityRuntime):
    a6_policy_type = DatedTicketA6Policy
    runtime_version = ROOM_RUNTIME_VERSION
    tool_policy_profile = ROOM_TICKET_PROFILE


def run_synthetic_room_pair_task(
    task: RuntimeTask, *, pair: ExitPair, **kwargs: Any
) -> SecurityRun:
    """Preserve room pin admission/ticket PRE; new final hook, CPU fixtures only."""
    return cast(SecurityRun, bind(room_pair._run, SecurityRuntime=RoomPairedSecurityRuntime)(
        task, pair=pair, synthetic=True, **kwargs,
    ))
