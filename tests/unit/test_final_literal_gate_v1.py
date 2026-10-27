"""Final-only index replay must never repair missing evidence or affect PRE."""

import pytest

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.runtime_hooks import derive
from react_agent.security_v1.final_entitlements_v2 import extract_final_entitlement
from react_agent.security_v1.final_literal_runtime_v1 import FinalLiteralGate
from react_agent.security_v1.value_origin import OriginError
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex

TOKEN = "GATEPRIVATE8642"  # noqa: S105 - synthetic fixture


def fixture(*, user_text="Đọc nguồn riêng.", private_text=None, include_private=True):
    store = ArtifactStore("final_only_gate")
    user = store.create(
        user_text, artifact_type=ArtifactType.USER_INPUT, source_type=SourceType.USER,
        source_id="synthetic_user", producer="host_context", created_step=0,
        sensitivity=Sensitivity.PUBLIC, trust=Trust.UNTRUSTED,
    )
    private = store.create(
        {"content": private_text or f"Mã riêng là {TOKEN} dùng nội bộ."},
        artifact_type=ArtifactType.DOCUMENT_CONTENT, source_type=SourceType.DOCUMENT,
        source_id="GATE_PRIVATE", producer="tool_source_snapshot", created_step=1,
        sensitivity=Sensitivity.CONFIDENTIAL, trust=Trust.UNTRUSTED,
    )
    index = ValueOriginIndex(store)
    index.add_artifact(user.artifact_id, observed_step=0)
    if include_private:
        index.add_artifact(private.artifact_id, observed_step=1)
    proposal = derive(store, TOKEN, kind=ArtifactType.FINAL_RESPONSE,
                      parents=(user.artifact_id, private.artifact_id), step=2)
    return store, index, proposal, user, extract_final_entitlement(user_text)


@pytest.mark.parametrize("fault", ["none", "missing", "incomplete", "budget"])
def test_failure_never_downgrades_to_leaky_v3_and_pre_index_unchanged(fault):
    private_text = " ".join(f"BUDGETTOKEN{i:04d}" for i in range(65)) + f" {TOKEN}"
    store, index, proposal, user, grant = fixture(
        private_text=private_text if fault == "budget" else None,
        include_private=fault != "missing",
    )
    if fault == "incomplete":
        with pytest.raises(OriginError):
            index.add_artifact(proposal.artifact_id, observed_step=2)
    before = index.snapshot()
    gate = FinalLiteralGate()
    release = gate(index, proposal.artifact_id, user.artifact_id, grant)
    assert TOKEN not in str(store.get(release.released_artifact_id).content())
    assert release.effect.value == ("REDACT" if fault == "none" else "DENY")
    assert index.snapshot() == before
    record = gate.records[0]
    if fault == "budget":
        assert record["admission_error"] == "candidate_source_admission_failed"
        assert record["final_index"]["complete"] is False
    elif fault == "incomplete":
        assert record["admission_error"] == "baseline_coverage_incomplete"
        assert record["final_index"] == before


def test_composed_gate_preserves_authorized_raw_user_collision():
    store, index, proposal, user, grant = fixture(user_text=f"Nhắc lại nhãn {TOKEN}.")
    gate = FinalLiteralGate()
    release = gate(index, proposal.artifact_id, user.artifact_id, grant)
    assert release.effect.value == "ALLOW"
    assert store.get(release.released_artifact_id).content() == TOKEN
    assert gate.records[0]["proof_status"] == "issued_raw_user"
    assert store.get(release.released_artifact_id).sensitivity == Sensitivity.CONFIDENTIAL
