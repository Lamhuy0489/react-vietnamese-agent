"""Independent synthetic Dev controls for the opt-in embedded-ID candidate."""

import pytest

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.runtime_hooks import derive
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.final_entitlements_v2 import (
    extract_final_entitlement,
    release_final_with_entitlement,
)
from react_agent.security_v1.value_origin import OriginError, ValueType
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex as FrozenIndex
from react_agent.security_v1.value_origin_v4 import PROFILE, ValueOriginIndex


def source(store: ArtifactStore, content: str, sensitivity: Sensitivity):
    return store.create(
        {"content": content},
        artifact_type=ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.DOCUMENT,
        source_id="DEV_SYNTHETIC_NOTE",
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=sensitivity,
        trust=Trust.UNTRUSTED,
    )


def test_sensitive_embedded_code_is_protected_without_changing_frozen_index() -> None:
    store = ArtifactStore("embedded_dev")
    item = source(store, "Mã nội bộ ORBITALPHA5629. Ghi chú synthetic.", Sensitivity.CONFIDENTIAL)
    raw = store.serialize()
    frozen, candidate = FrozenIndex(store), ValueOriginIndex(store)
    for index in (frozen, candidate):
        index.add_artifact(item.artifact_id, observed_step=1)
    assert frozen.protected_matches("ORBITALPHA5629") == ()
    matches = candidate.protected_matches("ORBITALPHA5629")
    assert len(matches) == 1
    assert matches[0].origin.value_type == ValueType.IDENTIFIER
    assert matches[0].origin.sensitivity == Sensitivity.CONFIDENTIAL
    assert matches[0].origin.source_sha256 == item.content_hash
    assert candidate.snapshot()["profile"] == PROFILE
    assert store.serialize() == raw


def test_public_prose_and_common_words_do_not_add_protected_literals() -> None:
    store = ArtifactStore("embedded_dev")
    private = source(
        store, "Archive notebook September progress ORBITALPHA5629", Sensitivity.INTERNAL
    )
    public = source(store, "Public reference MORNINGRAY4837", Sensitivity.PUBLIC)
    index = ValueOriginIndex(store)
    index.add_artifact(private.artifact_id, observed_step=1)
    index.add_artifact(public.artifact_id, observed_step=1)
    assert [match.origin.value for match in index.protected_matches("ORBITALPHA5629")] == [
        "ORBITALPHA5629"
    ]
    assert index.protected_matches("Archive notebook September progress") == ()
    assert index.protected_matches("MORNINGRAY4837") == ()
    assert index.protected_matches("XORBITALPHA5629") == ()
    assert index.protected_matches("ORBITALPHA56290") == ()


def test_already_typed_sensitive_code_is_not_duplicated() -> None:
    store = ArtifactStore("embedded_dev")
    item = source(store, "Course ROOM3176", Sensitivity.CONFIDENTIAL)
    index = ValueOriginIndex(store)
    index.add_artifact(item.artifact_id, observed_step=1)
    matches = index.protected_matches("ROOM3176")
    assert len(matches) == 1
    assert matches[0].origin.value_type == ValueType.COURSE_CODE


def test_embedded_budget_failure_invalidates_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    from react_agent.security_v1 import value_origin_v4 as module

    store = ArtifactStore("embedded_dev")
    item = source(store, "Synthetic private ORBITALPHA5629", Sensitivity.CONFIDENTIAL)
    index = ValueOriginIndex(store)
    monkeypatch.setattr(module, "MAX_EMBEDDED_PER_SOURCE", 0)
    with pytest.raises(OriginError, match="coverage incomplete"):
        index.add_artifact(item.artifact_id, observed_step=1)
    assert not index.complete and not index.records


def test_unentitled_embedded_code_is_redacted_by_existing_final_sink() -> None:
    store = ArtifactStore("embedded_final_dev")
    user_text = "Đọc DEV_SYNTHETIC_NOTE rồi trả lời ngắn."
    user = store.create(
        user_text,
        artifact_type=ArtifactType.USER_INPUT,
        source_type=SourceType.USER,
        source_id="synthetic_user",
        producer="host_context",
        created_step=0,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.UNTRUSTED,
    )
    private = source(store, "Mã nội bộ ORBITALPHA5629.", Sensitivity.CONFIDENTIAL)
    index = ValueOriginIndex(store)
    index.add_artifact(user.artifact_id, observed_step=0)
    index.add_artifact(private.artifact_id, observed_step=1)
    model = derive(
        store,
        "synthetic model output",
        kind=ArtifactType.MODEL_OUTPUT,
        parents=(user.artifact_id, private.artifact_id),
        step=2,
    )
    proposed = derive(
        store,
        "Mã: ORBITALPHA5629",
        kind=ArtifactType.FINAL_RESPONSE,
        parents=(model.artifact_id,),
        step=3,
    )
    decision = release_final_with_entitlement(
        index,
        proposed.artifact_id,
        user.artifact_id,
        extract_final_entitlement(user_text),
    )
    assert decision.effect == Effect.REDACT
    assert store.get(decision.released_artifact_id).content() == "Mã: [REDACTED]"
