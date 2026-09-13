from __future__ import annotations

import pytest

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import derive
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.final_entitlements import EntitlementError
from react_agent.security_v1.final_entitlements_v2 import (
    FinalEntitlement,
    SourceValueGrant,
    extract_final_entitlement,
    release_final_with_entitlement,
    validate_entitlement,
)
from react_agent.security_v1.processing_scope import ScopeError
from react_agent.security_v1.processing_scope_v2 import ProcessingScope
from react_agent.security_v1.value_origin import OriginError, ValueOriginIndex, ValueType
from react_agent.security_v1.value_origin_v2 import ValueOriginIndex as StrictIndex

EMAIL = "synthetic@example.test"


def fixture(
    user: str,
    answer: str,
    *,
    source_id: str = "DOC_A",
    source_type: SourceType = SourceType.DOCUMENT,
    trust: Trust = Trust.TRUSTED,
    untrusted_duplicate: bool = False,
):
    store = ArtifactStore("synthetic_remediation")
    root = store.create(
        user,
        artifact_type=ArtifactType.USER_INPUT,
        source_type=SourceType.USER,
        source_id="synthetic_user",
        producer="host_context",
        created_step=0,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.UNTRUSTED,
    )
    index = ValueOriginIndex(store)
    index.add_artifact(root.artifact_id, observed_step=0)
    parents = [root.artifact_id]
    for step in range(1, 3 if untrusted_duplicate else 2):
        source = store.create(
            {"email": EMAIL, "gpa": 3.2},
            artifact_type=ArtifactType.DOCUMENT_CONTENT,
            source_type=source_type,
            source_id=source_id,
            producer="tool_source_snapshot",
            created_step=step,
            sensitivity=Sensitivity.CONFIDENTIAL,
            trust=trust if step == 1 else Trust.UNTRUSTED,
        )
        index.add_artifact(source.artifact_id, observed_step=step)
        parents.append(source.artifact_id)
    model = derive(
        store, "synthetic", kind=ArtifactType.MODEL_OUTPUT, parents=tuple(parents), step=3
    )
    proposed = derive(
        store, answer, kind=ArtifactType.FINAL_RESPONSE, parents=(model.artifact_id,), step=4
    )
    return store, index, root.artifact_id, proposed.artifact_id


def release(user: str, answer: str = EMAIL, **kwargs):
    store, index, uid, pid = fixture(user, answer, **kwargs)
    decision = release_final_with_entitlement(index, pid, uid, extract_final_entitlement(user))
    return decision, store.get(decision.released_artifact_id)


@pytest.mark.parametrize(
    "user",
    [
        "Show GPA from DOC_A; Show email from DOC_B",
        "Show GPA from DOC_A\nShow email from DOC_B",
        "Show DOC_A; Show email",
        "Show GPA from DOC_A and email from DOC_B",
        "Show email from DOC_B",
        'Quoted: "text; Show email from DOC_A"',
        "Không trả email từ DOC_A",
        "If necessary show email from DOC_A",
    ],
)
def test_no_cartesian_incomplete_ambiguous_or_quoted_grants(user):
    decision, artifact = release(user)
    assert decision.effect == Effect.REDACT
    assert artifact.content() == "[REDACTED]"


@pytest.mark.parametrize(
    "user",
    [
        "Show email from DOC_A",
        "Trả email từ DOC_A",
        "Hiển thị email từ DOC_A",
        "Show email and GPA from DOC_A",
        "Show email from DOC_A; Show GPA from DOC_B",
    ],
)
def test_explicit_exact_grants_keep_legitimate_utility(user):
    decision, artifact = release(user)
    assert decision.effect == Effect.ALLOW
    assert artifact.content() == EMAIL
    assert artifact.sensitivity == Sensitivity.CONFIDENTIAL
    assert artifact.trust == Trust.UNTRUSTED


@pytest.mark.parametrize(
    "answer",
    [
        "synthetic@exam\u200bple.test",
        EMAIL + " / synthetic@exam\u200bple.test",
        "synthetic@exam\u200bple.test / " + EMAIL,
        EMAIL + " / synthetic@exam\u200dple.test",
        "GPA: 3.2 / GPA: 3.\u200b2",
    ],
)
def test_normalized_copies_cannot_hide_behind_authorized_raw_value(answer):
    decision, artifact = release("Show email and GPA from DOC_A", answer)
    assert decision.effect == Effect.DENY
    assert artifact.content() == ""


def test_all_exact_duplicates_are_allowed():
    decision, artifact = release("Show email from DOC_A", EMAIL + " / " + EMAIL)
    assert decision.effect == Effect.ALLOW
    assert artifact.content() == EMAIL + " / " + EMAIL


@pytest.mark.parametrize(
    "update",
    [
        {"explicit": False},
        {"profile": "forged"},
        {"raw_user_sha256": "a" * 64},
        {"grants": ()},
    ],
)
def test_supplied_grant_must_equal_canonical_extraction(update):
    user = "Show email from DOC_A"
    grant = extract_final_entitlement(user).model_copy(update=update)
    with pytest.raises(EntitlementError, match="canonically bound"):
        validate_entitlement(user, grant)


def test_supplied_hash_is_not_an_authorization_token():
    user = "Read DOC_A"
    supplied = FinalEntitlement(
        raw_user_sha256=text_hash(user),
        explicit=False,
        grants=(
            SourceValueGrant(
                source_type=SourceType.DOCUMENT, source_id="DOC_A", value_type=ValueType.EMAIL
            ),
        ),
    )
    store, index, uid, pid = fixture(user, EMAIL)
    count = len(store.all())
    with pytest.raises(EntitlementError):
        release_final_with_entitlement(index, pid, uid, supplied)
    assert len(store.all()) == count


@pytest.mark.parametrize(
    "source_type,user,expected",
    [
        (SourceType.DATABASE, "Show email from DOC_A", Effect.REDACT),
        (SourceType.DOCUMENT, "Show email from table DOC_A", Effect.REDACT),
        (SourceType.DATABASE, "Show email from table DOC_A", Effect.ALLOW),
        (SourceType.CACHED_PAGE, "Show email from DOC_A", Effect.REDACT),
    ],
)
def test_source_namespace_is_part_of_the_grant(source_type, user, expected):
    assert release(user, source_type=source_type)[0].effect == expected


@pytest.mark.parametrize("kwargs", [{"trust": Trust.UNTRUSTED}, {"untrusted_duplicate": True}])
def test_trusted_match_does_not_authorize_untrusted_origin(kwargs):
    assert release("Show email from DOC_A", **kwargs)[0].effect == Effect.REDACT


def test_mixed_authorized_and_unauthorized_output():
    decision, artifact = release("Show GPA from DOC_A", "GPA: 3.2 / " + EMAIL)
    assert decision.effect == Effect.REDACT
    assert artifact.content() == "GPA: 3.2 / [REDACTED]"


def test_missing_source_coverage_denies():
    user = "Show email from DOC_A"
    store, _, uid, pid = fixture(user, EMAIL)
    partial = ValueOriginIndex(store)
    partial.add_artifact(uid, observed_step=0)
    result = release_final_with_entitlement(partial, pid, uid, extract_final_entitlement(user))
    assert result.effect == Effect.DENY


@pytest.mark.parametrize(
    "query,expected",
    [
        ("SELECT gpa FROM grades", Effect.ALLOW),
        ("SELECT email FROM contacts", Effect.ALLOW),
        ("SELECT email FROM grades", Effect.DENY),
        ("SELECT gpa FROM contacts", Effect.DENY),
        ("SELECT * FROM grades", Effect.DENY),
    ],
)
def test_a4_table_columns_stay_paired(query, expected):
    scope = ProcessingScope("Read table grades column gpa; Read table contacts column email")
    assert scope.pre(Action(name="db_query", arguments={"query": query})).effect == expected


def test_a4_observed_table_columns_stay_paired():
    scope = ProcessingScope("Summarize available records")
    for table, query in [
        ("grades", "SELECT gpa FROM grades"),
        ("contacts", "SELECT email FROM contacts"),
    ]:
        action = Action(name="db_query", arguments={"query": query})
        scope.observe(
            action,
            artifact_id=table,
            source_type=SourceType.DATABASE,
            source_id=table,
            trust=Trust.UNTRUSTED,
        )
    assert (
        scope.pre(Action(name="db_query", arguments={"query": "SELECT email FROM grades"})).effect
        == Effect.DENY
    )


def test_a4_malformed_resource_observation_is_sanitized():
    scope = ProcessingScope("Read DOC_A")
    with pytest.raises(ScopeError, match="unassessed"):
        scope.observe(
            Action(name="doc_read", arguments={"doc_id": "bad"}),
            artifact_id="x",
            source_type=SourceType.DOCUMENT,
            source_id="bad",
            trust=Trust.UNTRUSTED,
        )


@pytest.mark.parametrize(
    "content",
    [
        {"student_id": "SV_SYN_001"},
        {"columns": ["student_id"], "rows": [["SV_SYN_001"]]},
        "SV_SYN_001",
        "Synthetic record: SV_SYN_001",
    ],
)
def test_synthetic_student_ids_are_indexed_in_structured_and_text_sources(content):
    store = ArtifactStore("synthetic_origin_v2")
    artifact = store.create(
        content,
        artifact_type=ArtifactType.DB_RESULT,
        source_type=SourceType.DATABASE,
        source_id="scholarships",
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=Sensitivity.CONFIDENTIAL,
        trust=Trust.TRUSTED,
    )
    index = StrictIndex(store)
    index.add_artifact(artifact.artifact_id, observed_step=1)
    assert index.find_origins("SV_SYN_001", ValueType.STUDENT_ID).known
    assert index.protected_matches("SV_SYN_001")
    assert index.snapshot()["profile"] == "typed_value_origin_v2"


@pytest.mark.parametrize(
    "content",
    [
        {"gpa": "unsupported"},
        {"gpa": True},
        {"student_id": "not-a-valid-id"},
        {"columns": ["email"], "rows": [["invalid-email"]]},
        {"email": {"nested": "ignored"}},
    ],
)
def test_unsupported_typed_values_invalidate_coverage(content):
    store = ArtifactStore("synthetic_origin_failure")
    artifact = store.create(
        content,
        artifact_type=ArtifactType.DB_RESULT,
        source_type=SourceType.DATABASE,
        source_id="records",
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=Sensitivity.CONFIDENTIAL,
        trust=Trust.TRUSTED,
    )
    index = StrictIndex(store)
    with pytest.raises(OriginError):
        index.add_artifact(artifact.artifact_id, observed_step=1)
    assert not index.complete


def test_multiline_quoted_scope_does_not_grant_resources():
    scope = ProcessingScope('Quoted: "example; Read DOC_A"')
    assert not scope.anchors.explicit_scope
    assert scope.anchors.documents == ()
