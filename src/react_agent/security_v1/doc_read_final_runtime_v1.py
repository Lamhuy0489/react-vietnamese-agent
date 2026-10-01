"""Host-approved raw doc_read final proof on the existing paired CPU loop."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from react_agent.foundation.artifacts import SourceType
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1 import clause_pair_runtime_v1 as paired
from react_agent.security_v1 import constrained_runtime_v1 as constrained
from react_agent.security_v1.constrained_host_v1 import ConstrainedRoleBackend
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.doc_read_final_proof_v1 import (
    PROFILE,
    DocReadApproval,
    DocReadLiteralProof,
    issue_doc_read_proof,
    release_doc_read_proof,
    requested_source,
    validate_approval,
    validate_catalog,
)
from react_agent.security_v1.final_entitlements import EntitledFinalRelease
from react_agent.security_v1.final_entitlements_v2 import FinalEntitlement
from react_agent.security_v1.final_literal_proof_v1 import (
    FinalLiteralProof,
    LiteralProofError,
    issue_literal_proof,
    release_final_with_literal_proof,
)
from react_agent.security_v1.final_literal_runtime_v1 import FinalLiteralGate as PreviousGate
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, bind
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime
from react_agent.security_v1.runtime_v12 import SecurityRuntime as V12Runtime
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex as BaselineIndex
from react_agent.security_v1.value_origin_v4 import ValueOriginIndex

RUNTIME_VERSION = "security_runtime_doc_read_final_cpu_v1"
FINAL_PROFILE = "doc_read_final_dispatch_cpu_v1"


class DocReadFinalGate(PreviousGate):
    def __init__(self, approval: DocReadApproval, expected_approval_sha256: str) -> None:
        super().__init__()
        self.approval = validate_approval(approval, expected_approval_sha256)
        self.expected = expected_approval_sha256

    def issue(
        self, index: ValueOriginIndex, user_id: str, source_id: str
    ) -> FinalLiteralProof | DocReadLiteralProof:
        raw = str(index.store.get(user_id).content())
        if requested_source(raw) != self.approval.source_id:
            return issue_literal_proof(index, user_id, source_id)
        candidates = [
            identity for identity in index.snapshot()["source_sha256"]
            if index.store.get(identity).source_type == SourceType.DOCUMENT
            and index.store.get(identity).source_id == self.approval.source_id
        ]
        if len(candidates) != 1:
            raise LiteralProofError("one observed approved doc_read source required")
        return issue_doc_read_proof(
            index, user_id, candidates[0], approval=self.approval,
            expected_approval_sha256=self.expected,
        )

    def release(
        self, index: ValueOriginIndex, proposal_id: str, user_id: str,
        grant: FinalEntitlement, proof: FinalLiteralProof | DocReadLiteralProof,
    ) -> EntitledFinalRelease:
        if isinstance(proof, DocReadLiteralProof):
            return release_doc_read_proof(
                index, proposal_id, user_id, grant, proof, approval=self.approval,
                expected_approval_sha256=self.expected,
            )
        return release_final_with_literal_proof(index, proposal_id, user_id, grant, proof)

    def __call__(
        self, baseline: BaselineIndex, proposal_id: str, user_id: str, grant: FinalEntitlement
    ) -> EntitledFinalRelease:
        result = cast(EntitledFinalRelease, bind(
            PreviousGate.__call__, issue_literal_proof=self.issue,
            release_final_with_literal_proof=self.release,
        )(self, baseline, proposal_id, user_id, grant))
        record = self.records[-1]
        if record["proof"] is not None and record["proof"]["profile"] == PROFILE:
            record["proof_status"] = "issued_doc_read_content"
        return result


class SecurityRuntime(V12Runtime):
    """Internal class bound to an admitted metadata-only approval per task."""

    approval: DocReadApproval
    expected_approval_sha256: str

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        security = kwargs.get("security_config") or configuration("A0")
        if security.level != "A6" or not isinstance(kwargs.get("_worker"), ConstrainedRoleBackend):
            raise ValueError("doc_read final adapter requires A6 and its constrained guard")
        gate = DocReadFinalGate(self.approval, self.expected_approval_sha256)
        loop = SimpleNamespace(_run_task=bind(
            V5Runtime._run_task, WarmModelGuard=constrained.HostClassifier, PROMPT=PROMPT,
        ))
        parent = SimpleNamespace(_run_task=bind(
            V7Runtime._run_task, release_final_with_entitlement=gate, RELEASE_PROFILE=FINAL_PROFILE,
        ))
        body = bind(V12Runtime._run_task, V5Runtime=loop, V7Runtime=parent,
                    RUNTIME_VERSION=RUNTIME_VERSION)
        result = cast(SecurityRun, body(self, task, **kwargs))
        output = Path(kwargs["output"])
        receipt = dict(
            profile=FINAL_PROFILE, runtime_version=RUNTIME_VERSION, records=gate.records,
            tool_policy_profile="clause_a6_v12", public_field_runtime_enabled=True,
            public_final_approval=self.approval.model_dump(mode="json"),
            expected_approval_sha256=self.expected_approval_sha256, native_admitted=False,
        )
        with (output / "final_literal_gate.json").open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        return result


def run_synthetic_pair_task(
    task: RuntimeTask, *, pair: ExitPair, approval: DocReadApproval,
    expected_approval_sha256: str, **kwargs: Any,
) -> SecurityRun:
    """Explicit synthetic CPU only. External approval admission precedes startup."""
    security = kwargs.get("security") or configuration("A0")
    if security.level != "A6":
        raise ValueError("doc_read final adapter requires explicit A6")
    catalog = kwargs.get("source_catalog") or SourceCatalog()
    validate_catalog(approval, expected_approval_sha256, catalog)

    class BoundRuntime(SecurityRuntime):
        pass

    BoundRuntime.approval = validate_approval(approval, expected_approval_sha256)
    BoundRuntime.expected_approval_sha256 = expected_approval_sha256
    return cast(SecurityRun, bind(paired._run, SecurityRuntime=BoundRuntime)(
        task, pair=pair, synthetic=True, **kwargs,
    ))
