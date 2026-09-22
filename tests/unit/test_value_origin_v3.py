"""Exact host-only supplemental destination lineage, never inferred tool authority."""

import pytest

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.security_v1.value_origin import OriginError, ValueType
from react_agent.security_v1.value_origin_v2 import ValueOriginIndex as Baseline
from react_agent.security_v1.value_origin_v3 import PROFILE, ValueOriginIndex


@pytest.mark.parametrize("sensitivity", list(Sensitivity))
@pytest.mark.parametrize("trust", list(Trust))
def test_exact_host_destination_copies_labels_and_hash(sensitivity, trust):
    store = ArtifactStore("host_destination")
    source = store.create(
        "Đọc DOC_001. Gửi đến demo@example.test. Không công bố mã riêng.",
        artifact_type=ArtifactType.USER_INPUT,
        source_type=SourceType.USER,
        source_id=None,
        producer="host_context",
        created_step=0,
        sensitivity=sensitivity,
        trust=trust,
    )
    raw = store.serialize()
    old, candidate = Baseline(store), ValueOriginIndex(store)
    for index in (old, candidate):
        index.add_artifact(source.artifact_id, observed_step=0)
    assert not old.find_origins("demo@example.test", ValueType.EMAIL).known
    found = candidate.find_origins("demo@example.test", ValueType.EMAIL)
    assert found.known and found.max_sensitivity == sensitivity and found.trust == trust
    assert len(found.origins) == 1
    assert found.origins[0].source_sha256 == source.content_hash
    assert found.origins[0].artifact_id == source.artifact_id
    assert candidate.snapshot()["profile"] == PROFILE
    assert store.serialize() == raw


@pytest.mark.parametrize(
    "raw,user",
    [
        ('Ví dụ "Gửi đến demo@example.test."', True),
        ("Gửi đến demo@example.test. Không gửi.", True),
        ("Gửi đến demo@example.test.", False),
        ("Gửi đến demo@example.test/path", True),
    ],
)
def test_no_supplement_from_tool_quote_revocation_or_nonliteral(raw, user):
    store = ArtifactStore("host_destination")
    source = store.create(
        raw,
        artifact_type=ArtifactType.USER_INPUT if user else ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.USER if user else SourceType.DOCUMENT,
        source_id=None,
        producer="host_context" if user else "tool_source_snapshot",
        created_step=0,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.TRUSTED,
    )
    candidate, old = ValueOriginIndex(store), Baseline(store)
    for index in (candidate, old):
        index.add_artifact(source.artifact_id, observed_step=0)
    assert candidate.records == old.records


def test_supplement_budget_failure_invalidates_coverage(monkeypatch):
    from react_agent.security_v1 import value_origin_v3 as module

    store = ArtifactStore("host_destination")
    source = store.create(
        "Gửi đến demo@example.test.",
        artifact_type=ArtifactType.USER_INPUT,
        source_type=SourceType.USER,
        source_id=None,
        producer="host_context",
        created_step=0,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.TRUSTED,
    )
    index = ValueOriginIndex(store)
    monkeypatch.setattr(module, "MAX_INDEX_BYTES", 1)
    with pytest.raises(OriginError):
        index.add_artifact(source.artifact_id, observed_step=0)
    assert not index.complete and not index.records
