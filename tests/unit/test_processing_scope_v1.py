from __future__ import annotations

import pytest

from react_agent.foundation.artifacts import SourceType, Trust
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect, Reason
from react_agent.security_v1.processing_scope import (
    PROFILE,
    ProcessingScope,
    ScopeError,
    ScopeKind,
    extract_scope_anchors,
    parse_sql_scope,
)


def read_doc(doc_id: str) -> Action:
    return Action(name="doc_read", arguments={"doc_id": doc_id})


def fetch_page(page_id: str) -> Action:
    return Action(name="cached_fetch", arguments={"page_id": page_id})


def db(query: str) -> Action:
    return Action(name="db_query", arguments={"query": query})


def observe(scope: ProcessingScope, action: Action, *, artifact: str, trust: Trust) -> None:
    source_id = action.arguments.get("doc_id") if action.name == "doc_read" else None
    if not isinstance(source_id, str):
        source_id = None
    scope.observe(
        action,
        artifact_id=artifact,
        source_type=SourceType.DOCUMENT,
        source_id=source_id,
        trust=trust,
    )


def test_extracts_only_affirmative_exact_scope_anchors() -> None:
    anchors = extract_scope_anchors(
        "Đọc tài liệu DOC_001 và trang CACHE_002. "
        "Không đọc DOC_003; nếu cần xem DOC_004. "
        "Đọc tài liệu 'DOC_005'."
    )
    assert anchors.documents == ("DOC_001",)
    assert anchors.cached_pages == ("CACHE_002",)
    assert not anchors.database_tables and not anchors.database_columns
    assert anchors.explicit_scope
    assert len(anchors.raw_user_sha256) == 64


def test_database_anchors_are_casefolded_and_bounded() -> None:
    anchors = extract_scope_anchors("Truy vấn table Courses với column Course_ID và column GPA")
    assert anchors.database_tables == ("courses",)
    assert anchors.database_columns == ("course_id", "gpa")
    assert anchors.explicit_scope


@pytest.mark.parametrize(
    "query, assessed, table, columns",
    [
        ("SELECT course_id, gpa FROM courses", True, "courses", ("course_id", "gpa")),
        (" SELECT name FROM students ", True, "students", ("name",)),
        ("SELECT * FROM courses", False, None, ()),
        ("SELECT name FROM courses; DROP TABLE students", False, None, ()),
        ("SELECT name FROM (SELECT name FROM students)", False, None, ()),
        ("SELECT name, lower(gpa) FROM students", False, None, ()),
    ],
)
def test_sql_scope_parser_is_non_executing_and_conservative(
    query: str, assessed: bool, table: str | None, columns: tuple[str, ...]
) -> None:
    result = parse_sql_scope(query)
    assert result.kind == ScopeKind.DATABASE
    assert result.assessed is assessed
    assert result.table == table
    assert result.columns == columns


def test_explicit_document_scope_is_hard_boundary() -> None:
    scope = ProcessingScope("Đọc tài liệu DOC_001")
    assert scope.pre(read_doc("DOC_001")).effect == Effect.ALLOW
    decision = scope.pre(read_doc("DOC_002"))
    assert decision.effect == Effect.DENY
    assert decision.authorized_by == "scope_expansion"
    assert decision.reasons == (Reason.CONTROL, Reason.ACTION)


def test_untrusted_source_cannot_expand_unanchored_scope() -> None:
    scope = ProcessingScope("Tóm tắt tài liệu công khai")
    assert scope.pre(read_doc("DOC_001")).authorized_by == "no_scope_trigger"
    observe(scope, read_doc("DOC_001"), artifact="ART_001", trust=Trust.UNTRUSTED)
    assert scope.pre(read_doc("DOC_001")).authorized_by == "prior_observation"
    decision = scope.pre(read_doc("DOC_002"))
    assert decision.effect == Effect.DENY
    assert decision.authorized_by == "untrusted_scope_expansion"
    assert decision.reasons == (Reason.CONTROL, Reason.ACTION)


def test_trusted_observation_does_not_trigger_scope_veto() -> None:
    scope = ProcessingScope("Tóm tắt tài liệu công khai")
    observe(scope, read_doc("DOC_001"), artifact="ART_001", trust=Trust.TRUSTED)
    assert not scope.state.untrusted_seen
    assert scope.pre(read_doc("DOC_002")).effect == Effect.ALLOW


def test_search_is_unassessed_after_untrusted_source() -> None:
    scope = ProcessingScope("Tóm tắt tài liệu công khai")
    read = read_doc("DOC_001")
    observe(scope, read, artifact="ART_001", trust=Trust.UNTRUSTED)
    decision = scope.pre(Action(name="doc_search", arguments={"query": "học phí"}))
    assert decision.effect == Effect.DENY
    assert decision.authorized_by == "unassessed_scope"
    assert decision.reasons == (Reason.CONTROL, Reason.UNKNOWN_FIELD)


def test_database_scope_requires_exact_table_and_columns() -> None:
    scope = ProcessingScope("Truy vấn table courses với column course_id và column gpa")
    assert scope.pre(db("SELECT course_id, gpa FROM courses")).effect == Effect.ALLOW
    assert scope.pre(db("SELECT name FROM students")).effect == Effect.DENY
    assert scope.pre(db("SELECT course_id FROM courses")).effect == Effect.ALLOW


def test_database_scope_reuses_only_prior_observed_shape_after_untrusted() -> None:
    scope = ProcessingScope("Tóm tắt")
    query = db("SELECT course_id, gpa FROM courses")
    scope.observe(
        query,
        artifact_id="ART_DB",
        source_type=SourceType.DATABASE,
        source_id="database:courses",
        trust=Trust.UNTRUSTED,
    )
    assert scope.pre(db("SELECT course_id FROM courses")).authorized_by == "prior_observation"
    assert scope.pre(db("SELECT name FROM courses")).effect == Effect.DENY


@pytest.mark.parametrize(
    "action",
    [
        Action(name="calculator", arguments={"expression": "1+1"}),
        Action(
            name="send_email_mock",
            arguments={"to": "demo@example.test", "subject": "s", "body": "b"},
        ),
        Action(
            name="post_webhook_mock",
            arguments={"endpoint": "mock://report", "payload": {"message": "b"}},
        ),
    ],
)
def test_non_scope_actions_are_delegated_to_their_existing_gates(action: Action) -> None:
    scope = ProcessingScope("Tóm tắt")
    observe(scope, read_doc("DOC_001"), artifact="ART_001", trust=Trust.UNTRUSTED)
    decision = scope.pre(action)
    assert decision.effect == Effect.ALLOW and decision.authorized_by == "delegated"


def test_unknown_action_fails_closed() -> None:
    decision = ProcessingScope("Tóm tắt").pre(Action(name="shell", arguments={}))
    assert decision.effect == Effect.DENY
    assert decision.scope_kind == ScopeKind.UNKNOWN
    assert decision.reasons == (Reason.ACTION, Reason.UNKNOWN_FIELD)


def test_state_is_monotone_serializable_and_identity_changes_on_observation() -> None:
    scope = ProcessingScope("Tóm tắt")
    initial_identity = scope.identity
    observe(scope, read_doc("DOC_001"), artifact="ART_001", trust=Trust.UNTRUSTED)
    snapshot = scope.snapshot()
    assert snapshot["profile"] == PROFILE
    assert scope.identity != initial_identity
    assert scope.state.observation_count == 1
    assert scope.state.untrusted_artifact_ids == ("ART_001",)
    restored = ProcessingScope("Tóm tắt")
    assert restored.anchors == scope.anchors
    assert type(scope.state).model_validate(snapshot["state"]) == scope.state


def test_observation_identity_mismatch_does_not_mutate_state() -> None:
    scope = ProcessingScope("Tóm tắt")
    before = scope.snapshot()
    with pytest.raises(ScopeError, match="document source identity"):
        scope.observe(
            read_doc("DOC_001"),
            artifact_id="ART_001",
            source_type=SourceType.DOCUMENT,
            source_id="DOC_002",
            trust=Trust.UNTRUSTED,
        )
    assert scope.snapshot() == before


def test_raw_user_and_enforce_budget_checks() -> None:
    with pytest.raises(ScopeError, match="non-empty"):
        ProcessingScope(" ")
    with pytest.raises(ScopeError, match="boolean"):
        ProcessingScope("Tóm tắt", enforce=1)  # type: ignore[arg-type]
    bypass = ProcessingScope("Đọc DOC_001", enforce=False)
    assert bypass.pre(read_doc("DOC_002")).authorized_by == "not_enforced"
