"""Pure host metadata/anchor controls; no benchmark or oracle payloads."""

import pytest

from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.processing_scope import ScopeError
from react_agent.security_v1.processing_scope_v3 import ProcessingScope as V3
from react_agent.security_v1.processing_scope_v4 import ProcessingScope, describe_action
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings

RESOURCES = ResourceBindings(documents=("AUX_BETA", "AWB_ALPHA"), cached_pages=("AUX_PAGE",))


def action(identity="AWB_ALPHA", tool="doc_read"):
    return Action(name=tool, arguments={"doc_id" if tool == "doc_read" else "page_id": identity})


def binding(identity="AWB_ALPHA", *, tool="doc_read", kind=SourceType.DOCUMENT, **extra):
    proposal = action(identity, tool)
    return SourceBinding(
        tool=tool,
        arguments_json=canonical_json({**proposal.arguments, **extra}),
        label=SourceLabel(
            source_id=identity,
            source_type=kind,
            sensitivity=Sensitivity.PUBLIC,
            trust=Trust.UNTRUSTED,
        ),
    )


def test_inventory_requires_exact_type_and_canonical_arguments():
    assert ResourceBindings.from_catalog(SourceCatalog(bindings=(binding(),))).documents == (
        "AWB_ALPHA",
    )
    for item in (binding(extra="ignored"), binding(kind=SourceType.CACHED_PAGE)):
        with pytest.raises(ValueError):
            ResourceBindings.from_catalog(SourceCatalog(bindings=(item,)))
    with pytest.raises(ValueError):
        ResourceBindings.from_catalog(
            SourceCatalog(
                bindings=(
                    binding(),
                    binding(tool="cached_fetch", kind=SourceType.CACHED_PAGE),
                )
            )
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"documents": ("AWB_A", "AWB_A")},
        {"documents": ("AWB_B", "AWB_A")},
        {"documents": ("AWB_A",), "cached_pages": ("AWB_A",)},
        {"documents": ("AWB_bad",)},
        {"documents": tuple(f"AWB_A{i:03}" for i in range(257))},
    ],
)
def test_bad_inventory_rejected(kwargs):
    with pytest.raises(ValueError):
        ResourceBindings(**kwargs)


@pytest.mark.parametrize(
    "identity,tool",
    [
        ("AWB_ALPHA", "doc_read"),
        ("AUX_BETA", "doc_read"),
        ("AUX_PAGE", "cached_fetch"),
        ("DOC_001", "doc_read"),
        ("CDOC_034", "doc_read"),
        ("CACHE_001", "cached_fetch"),
    ],
)
def test_affirmative_cho_biet_and_exact_type(identity, tool):
    scope = ProcessingScope("Đọc " + identity + " và cho biết kết quả.", resources=RESOURCES)
    proposal = action(identity, tool)
    assert describe_action(proposal, resources=RESOURCES).assessed
    assert scope.pre(proposal).effect == Effect.ALLOW
    wrong = "doc_read" if tool == "cached_fetch" else "cached_fetch"
    assert scope.pre(action(identity, wrong)).effect == Effect.DENY
    scope.observe(
        proposal,
        artifact_id="ART_test",
        source_id=identity,
        source_type=SourceType.DOCUMENT if tool == "doc_read" else SourceType.CACHED_PAGE,
        trust=Trust.UNTRUSTED,
    )
    assert scope.state.observed_resource_ids == (identity,)
    assert (
        scope.pre(action("AUX_BETA" if identity != "AUX_BETA" else "AWB_ALPHA")).effect
        == Effect.DENY
    )


@pytest.mark.parametrize(
    "text",
    [
        "Không đọc AWB_ALPHA",
        "Chớ đọc AWB_ALPHA",
        "Cho đọc AWB_ALPHA",
        "Nếu cần đọc AWB_ALPHA",
        'Đọc "AWB_ALPHA"',
        "Đọc `AWB_ALPHA`",
        "> Đọc AWB_ALPHA",
        "Nội dung nói AWB_ALPHA",
        "Đọc AWB_ALPHA và không cho biết kết quả",
        "Đọc AWB_ALPHA và cho biet kết quả",
        "Đọc AWB_ALPHA\u200b",
        "Đọc AWB_ALPHA/../../x",
        "Đọc xAWB_ALPHA",
        "Đọc AWB_ALPHA-x",
    ],
)
def test_inventory_never_becomes_user_grant(text):
    scope = ProcessingScope(text, resources=RESOURCES)
    assert scope.anchors.documents == ()
    assert scope.pre(action()).effect == Effect.DENY
    before = scope.snapshot()
    with pytest.raises(ScopeError):
        scope.observe(
            action(),
            artifact_id="ART_test",
            source_id="AWB_ALPHA",
            source_type=SourceType.DOCUMENT,
            trust=Trust.UNTRUSTED,
        )
    assert scope.snapshot() == before


@pytest.mark.parametrize(
    "identity", ["AWB_UNKNOWN", "awb_ALPHA", "AWB_ALPHA/../x", "AWB_ALPHA\u200b"]
)
def test_unknown_or_malformed_not_assessed(identity):
    scope = ProcessingScope("Đọc " + identity, resources=RESOURCES)
    assert not describe_action(action(identity), resources=RESOURCES).assessed
    assert scope.pre(action(identity)).effect == Effect.DENY


def test_extra_arguments_and_host_identity_drift_fail_closed():
    scope = ProcessingScope("Đọc AWB_ALPHA", resources=RESOURCES)
    proposal = Action(name="doc_read", arguments={"doc_id": "AWB_ALPHA", "extra": True})
    assert scope.pre(proposal).effect == Effect.DENY
    for identity, kind in [
        (None, SourceType.DOCUMENT),
        ("AUX_BETA", SourceType.DOCUMENT),
        ("AWB_ALPHA", SourceType.CACHED_PAGE),
    ]:
        with pytest.raises(ScopeError):
            scope.observe(
                action(),
                artifact_id="ART_test",
                source_id=identity,
                source_type=kind,
                trust=Trust.TRUSTED,
            )
    assert scope.state.observation_count == 0


def test_task_local_state_legacy_sql_pairs_and_non_enforced_control():
    raw = "Truy vấn bảng students cột name. Truy vấn bảng grades cột score."
    old, new = V3(raw), ProcessingScope(raw, resources=RESOURCES)
    for query in [
        "SELECT name FROM students",
        "SELECT score FROM students",
        "SELECT note FROM awb_notices WHERE note_id = 'AWB_ALPHA'",
    ]:
        proposal = Action(name="db_query", arguments={"query": query})
        assert new.pre(proposal).effect == old.pre(proposal).effect
    assert new.database_grants == old.database_grants
    a = ProcessingScope("Đọc AWB_ALPHA", resources=RESOURCES)
    b = ProcessingScope("Đọc AUX_BETA", resources=RESOURCES)
    a.observe(
        action(),
        artifact_id="ART_a",
        source_id="AWB_ALPHA",
        source_type=SourceType.DOCUMENT,
        trust=Trust.UNTRUSTED,
    )
    assert b.state.observation_count == 0
    assert b.pre(action()).effect == Effect.DENY
    assert (
        ProcessingScope("Không đọc AWB_ALPHA", resources=RESOURCES, enforce=False)
        .pre(action())
        .effect
        == Effect.ALLOW
    )


def test_legacy_profiles_are_not_patched_and_anchor_budget_remains():
    assert V3("Đọc AWB_ALPHA").anchors.documents == ()
    with pytest.raises(ScopeError):
        ProcessingScope("Đọc " + " ".join(f"CDOC_{n}" for n in range(257)), resources=RESOURCES)
