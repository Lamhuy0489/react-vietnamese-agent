"""CDOC parsing is exact, bounded and does not relax v2 authorization."""

import pytest

from react_agent.foundation.artifacts import SourceType, Trust
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.processing_scope import ScopeError
from react_agent.security_v1.processing_scope_v2 import ProcessingScope as V2
from react_agent.security_v1.processing_scope_v3 import ProcessingScope, describe_action


def action(identity):
    return Action(name="doc_read", arguments={"doc_id": identity})


@pytest.mark.parametrize("identity", ["CDOC_034", "DOC_034", "CDOC_abc-1", "CDOC_" + "x" * 64])
def test_exact_anchors_and_no_namespace_alias(identity):
    scope = ProcessingScope("Đọc tài liệu " + identity)
    assert scope.anchors.documents == (identity,)
    assert scope.pre(action(identity)).effect == Effect.ALLOW
    assert scope.pre(action("DOC_other")).effect == Effect.DENY
    observation = scope.observe(
        action(identity),
        artifact_id="ART_public",
        source_type=SourceType.DOCUMENT,
        source_id=identity,
        trust=Trust.TRUSTED,
    )
    assert observation.action_scope.resource_ids == (identity,)
    assert scope.state.observed_resource_ids == (identity,)
    with pytest.raises(ScopeError, match="identity"):
        scope.observe(
            action(identity),
            artifact_id="ART_wrong",
            source_type=SourceType.DOCUMENT,
            source_id="DOC_other",
            trust=Trust.TRUSTED,
        )


@pytest.mark.parametrize(
    "identity",
    [
        "CDOC_",
        "CDOC_" + "x" * 65,
        "xCDOC_034",
        "cdoc_034",
        "CDOC_034/../../x",
        "CDOC_034\u200b",
        34,
        None,
    ],
)
def test_malformed_actions_not_admitted(identity):
    assert not describe_action(action(identity)).assessed
    scope = ProcessingScope("Đọc CDOC_034")
    assert scope.pre(action(identity)).effect == Effect.DENY
    with pytest.raises(ScopeError):
        scope.observe(
            action(identity),
            artifact_id="ART_x",
            source_type=SourceType.DOCUMENT,
            source_id=None,
            trust=Trust.TRUSTED,
        )


@pytest.mark.parametrize(
    "instruction",
    ['Đọc "CDOC_034"', "Không đọc CDOC_034", "Nếu cần đọc CDOC_034", "> đọc CDOC_034"],
)
def test_indirect_text_is_not_a_grant(instruction):
    assert ProcessingScope(instruction).anchors.documents == ()


def test_anchor_budget_and_database_pairs_retained():
    with pytest.raises(ScopeError, match="budget"):
        ProcessingScope("Đọc " + " ".join(f"CDOC_{i}" for i in range(257)))
    instruction = "Truy vấn bảng students cột name. Truy vấn bảng grades cột score."
    old, new = V2(instruction), ProcessingScope(instruction)
    assert new.database_grants == old.database_grants
    for query in ["SELECT name FROM students", "SELECT score FROM students"]:
        proposal = Action(name="db_query", arguments={"query": query})
        assert new.pre(proposal).effect == old.pre(proposal).effect
    assert V2("Đọc CDOC_034").anchors.documents == ()


def test_doc_and_cdoc_are_not_aliased():
    scope = ProcessingScope("Đọc CDOC_034")
    assert scope.pre(action("DOC_034")).effect == Effect.DENY
