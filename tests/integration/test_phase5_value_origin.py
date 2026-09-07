from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    ParentLink,
    Relation,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.value_origin import (
    OriginError,
    ValueOriginIndex,
    ValueType,
    canonical_value,
)
from react_agent.security_v1.value_release import FinalValueRelease, release_final


def source(
    store, content, sensitivity=Sensitivity.CONFIDENTIAL, trust=Trust.TRUSTED, step=1, user=False
):
    return store.create(
        content,
        artifact_type=ArtifactType.USER_INPUT if user else ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.USER if user else SourceType.DOCUMENT,
        source_id="synthetic",
        producer="host_context" if user else "tool_source_snapshot",
        created_step=step,
        sensitivity=sensitivity,
        trust=trust,
    )


def setup(content, sensitivity=Sensitivity.CONFIDENTIAL):
    store = ArtifactStore("synthetic_origin")
    raw = source(store, content, sensitivity)
    index = ValueOriginIndex(store)
    index.add_artifact(raw.artifact_id, observed_step=1)
    return store, raw, index


def proposed(store, raw, text):
    return store.create(
        text,
        artifact_type=ArtifactType.FINAL_RESPONSE,
        source_type=SourceType.MODEL,
        source_id=None,
        producer="model_proposal",
        created_step=2,
        sensitivity=raw.sensitivity,
        trust=raw.trust,
        parents=(ParentLink(parent_id=raw.artifact_id, relation=Relation.GENERATED_USING),),
    )


@pytest.mark.parametrize(
    "field,value,kind",
    [
        ("email", "private@example.test", ValueType.EMAIL),
        ("endpoint", "mock://private/report", ValueType.URL),
        ("student_id", "SV20260017", ValueType.STUDENT_ID),
        ("course_code", "CS101", ValueType.COURSE_CODE),
        ("phone", "+84912345678", ValueType.PHONE),
        ("gpa", 2.13, ValueType.GPA),
        ("amount", 1725.5, ValueType.MONEY),
        ("date", "2026-09-07", ValueType.DATE),
        ("internal_record_id", "REC_PRIVATE_009", ValueType.IDENTIFIER),
        ("content", "Thông tin riêng tổng hợp", ValueType.FREE_TEXT),
    ],
)
def test_typed_origins_and_raw_preservation(field, value, kind):
    store, raw, index = setup({"nested": [{field: value}]})
    before = store.serialize()
    found = index.find_origins(value, kind)
    assert found.known and found.max_sensitivity == Sensitivity.CONFIDENTIAL
    assert found.trust == Trust.TRUSTED
    assert any(r.pointer == "/nested/0/" + field for r in found.origins)
    assert all(r.source_sha256 == raw.content_hash for r in found.origins)
    assert store.serialize() == before


@pytest.mark.parametrize("a", list(Sensitivity))
@pytest.mark.parametrize("b", list(Sensitivity))
@pytest.mark.parametrize("trust", list(Trust))
def test_all_matching_origins_retained_independent_dimensions(a, b, trust):
    store, first, index = setup({"email": "same@example.test"}, a)
    other = source(store, {"email": "same@example.test"}, b, trust)
    index.add_artifact(other.artifact_id, observed_step=1)
    found = index.find_origins("same@example.test", ValueType.EMAIL)
    assert {r.artifact_id for r in found.origins} == {first.artifact_id, other.artifact_id}
    assert found.max_sensitivity == max(a, b) and found.trust == trust


@pytest.mark.parametrize("value", [1, 2, 2026, True, False, None])
def test_untyped_common_scalars_not_indexed(value):
    _, _, index = setup({"value": value})
    assert not index.records
    assert not index.protected_matches("Năm 2026 có 2 mục và 1 ghi chú.")


@pytest.mark.parametrize("value", ["2.130", Decimal("2.13"), "+2.13", 2.13])
def test_decimal_equivalence(value):
    _, _, index = setup({"gpa": 2.13})
    assert index.find_origins(value, ValueType.GPA).known
    assert index.protected_matches("GPA: 2.130")


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), "2,13", "2.13e0", 4.1, -1])
def test_invalid_gpa(value):
    with pytest.raises(ValueError):
        canonical_value(value, ValueType.GPA)


@pytest.mark.parametrize("kind,field", [(ValueType.GPA, "gpa"), (ValueType.MONEY, "amount")])
def test_integral_numeric_requires_typed_cue(kind, field):
    _, _, index = setup({field: 2})
    assert index.find_origins("2.00", kind).known
    assert not index.protected_matches("Có 2 hoặc 2.00 phần công khai")
    assert index.protected_matches(field + ": 2.00")


@pytest.mark.parametrize("text", ["12.13", "2.1301", "x2.13", "2.13x", "2.13.4"])
def test_numeric_boundaries(text):
    _, _, index = setup({"gpa": 2.13})
    assert not index.protected_matches(text)


@pytest.mark.parametrize(
    "value", ["PRIVATE@example.test", "private@example.test.evil", "prefixprivate@example.test"]
)
def test_exact_email_queries_do_not_authorize_substrings_or_case(value):
    _, _, index = setup({"email": "private@example.test"})
    assert not index.find_origins(value, ValueType.EMAIL).known
    assert not index.protected_matches(value)


def test_duplicate_admission_fresh_state_and_pointer_escape():
    store, raw, index = setup({"a/b~c": {"email": "private@example.test"}})
    before = index.identity
    index.add_artifact(raw.artifact_id, observed_step=1)
    assert index.identity == before
    assert index.records[0].pointer == "/a~1b~0c/email"
    assert not ValueOriginIndex(store).records


@pytest.mark.parametrize(
    "kind",
    [
        ArtifactType.MODEL_OUTPUT,
        ArtifactType.TOOL_ARGUMENT,
        ArtifactType.FINAL_RESPONSE,
        ArtifactType.NORMALIZED_VIEW,
    ],
)
def test_generated_origins_cannot_launder_values(kind):
    store = ArtifactStore("synthetic_laundering")
    fake = store.create(
        "private@example.test",
        artifact_type=kind,
        source_type=SourceType.DOCUMENT,
        source_id=None,
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.TRUSTED,
    )
    index = ValueOriginIndex(store)
    with pytest.raises(OriginError):
        index.add_artifact(fake.artifact_id, observed_step=1)
    assert not index.complete and not index.records


def test_transformed_root_cannot_claim_raw_origin():
    store = ArtifactStore("synthetic_transformed_root")
    transformed = store.create(
        {"email": "private@example.test"},
        artifact_type=ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.DOCUMENT,
        source_id="synthetic",
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.TRUSTED,
        transformations=("security_v1",),
    )
    index = ValueOriginIndex(store)
    with pytest.raises(OriginError):
        index.add_artifact(transformed.artifact_id, observed_step=1)
    assert not index.complete and not index.records


@pytest.mark.parametrize("text", ["Public announcement", "", "\u200b" * 12])
def test_empty_normalized_value_denies_without_empty_span_or_crash(text):
    store, raw, index = setup({"content": "\u200b" * 12})
    final = proposed(store, raw, text)
    decision = release_final(index, final.artifact_id)
    assert decision.effect == Effect.DENY
    assert store.get(decision.released_artifact_id).content() == ""
    assert store.get(final.artifact_id).content() == text


def test_user_root_indexed_without_treating_presence_as_authorization():
    store = ArtifactStore("synthetic_user")
    raw = source(
        store, "Không gửi đến demo@example.test", Sensitivity.PUBLIC, Trust.UNTRUSTED, user=True
    )
    index = ValueOriginIndex(store)
    index.add_artifact(raw.artifact_id, observed_step=1)
    found = index.find_origins("demo@example.test", ValueType.EMAIL)
    assert found.known and found.trust == Trust.UNTRUSTED
    assert not hasattr(found, "authorized")


@pytest.mark.parametrize("mode", ["future", "backward", "cross_run"])
def test_bad_observation_retires_index(mode):
    store, raw, index = setup({"email": "private@example.test"})
    old = index.records
    next_source = source(store, {"email": "other@example.test"}, step=3)
    with pytest.raises(OriginError):
        index.add_artifact(
            "ART_other_000001" if mode == "cross_run" else next_source.artifact_id,
            observed_step=0 if mode == "backward" else 2,
        )
    assert index.records == old and not index.complete
    with pytest.raises(OriginError):
        index.add_artifact(raw.artifact_id, observed_step=3)


@pytest.mark.parametrize(
    "limit", ["MAX_BYTES", "MAX_DEPTH", "MAX_RECORDS", "MAX_SOURCES", "MAX_INDEX_BYTES"]
)
def test_atomic_limits_fail_closed(limit, monkeypatch):
    from react_agent.security_v1 import value_origin

    store, raw, index = setup({"email": "private@example.test"})
    before = index.records
    monkeypatch.setattr(value_origin, limit, 1)
    second = source(store, {"nested": {"email": "other@example.test"}})
    with pytest.raises(OriginError):
        index.add_artifact(second.artifact_id, observed_step=1)
    assert index.records == before and not index.complete
    final = proposed(store, raw, "Thông tin công khai")
    result = release_final(index, final.artifact_id)
    assert result.effect == Effect.DENY
    assert store.get(result.released_artifact_id).content() == ""


@pytest.mark.parametrize(
    "text,effect",
    [
        ("Email private@example.test; GPA: 2.13", Effect.REDACT),
        ("Thông báo công khai khác", Effect.ALLOW),
        ("private@exam\u200bple.test", Effect.DENY),
        ("GPA: ２.１３", Effect.DENY),
        ("GPA: 2.1300", Effect.REDACT),
        ('{"private@example.test":"public"}', Effect.REDACT),
        ("private@example.test và private@exam\u200bple.test", Effect.DENY),
    ],
)
def test_final_release_keeps_raw_and_conservative_lineage(text, effect):
    store, raw, index = setup({"email": "private@example.test", "gpa": 2.13})
    final = proposed(store, raw, text)
    before = store.serialize()
    result = release_final(index, final.artifact_id)
    assert result.effect == effect
    assert store.serialize().startswith(before)
    assert store.get(final.artifact_id).content() == text
    released = store.get(result.released_artifact_id)
    assert released.sensitivity == Sensitivity.CONFIDENTIAL and released.trust == raw.trust
    assert final.artifact_id in {p.parent_id for p in released.parents}
    assert not index.protected_matches(str(released.content()))
    assert FinalValueRelease.model_validate_json(result.model_dump_json()) == result
    assert ArtifactStore.deserialize(store.run_id, store.serialize()).all() == store.all()


def test_overlap_and_repeated_spans_are_deterministic():
    store, raw, index = setup(
        {"content": "Contact private@example.test now", "email": "private@example.test"}
    )
    final = proposed(store, raw, "Contact private@example.test now; private@example.test")
    result = release_final(index, final.artifact_id)
    assert result.effect == Effect.REDACT and len(result.redacted_spans) == 2
    assert store.get(result.released_artifact_id).content() == "[REDACTED]; [REDACTED]"


def test_replacement_collision_denies():
    store, raw, index = setup({"internal_record_id": "REDACTED", "email": "private@example.test"})
    final = proposed(store, raw, "private@example.test")
    result = release_final(index, final.artifact_id)
    assert result.effect == Effect.DENY and store.get(result.released_artifact_id).content() == ""


def test_release_rejects_nonfinal_and_derived_origin():
    store, raw, index = setup({"email": "private@example.test"})
    with pytest.raises(ValueError):
        release_final(index, raw.artifact_id)
    final = proposed(store, raw, "public")
    result = release_final(index, final.artifact_id)
    with pytest.raises(ValueError):
        release_final(index, result.released_artifact_id)
    with pytest.raises(OriginError):
        index.add_artifact(final.artifact_id, observed_step=2)


def test_oversized_scan_denies_without_truncation():
    store, raw, index = setup({"email": "private@example.test"})
    final = proposed(store, raw, "x" * 131073)
    result = release_final(index, final.artifact_id)
    assert result.effect == Effect.DENY


def test_raw_unicode_normalization_never_authorizes_destination():
    _, _, index = setup({"content": "Không gửi đến demo@exam\u200bple.test"}, Sensitivity.PUBLIC)
    assert not index.find_origins("demo@example.test", ValueType.EMAIL).known


def test_no_benchmark_payload_reads(monkeypatch):
    original = Path.open

    def checked(path, *args, **kwargs):
        assert "data/clean" not in str(path) and "data/adversarial" not in str(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", checked)
    store, raw, index = setup({"gpa": 2.13})
    assert (
        release_final(index, proposed(store, raw, "GPA: 2.13").artifact_id).effect == Effect.REDACT
    )


@pytest.mark.parametrize("limit", ["MAX_MATCHES", "MAX_SCAN_WORK"])
def test_scan_limits_deny_without_partial_redaction(limit, monkeypatch):
    from react_agent.security_v1 import value_origin

    store, raw, index = setup({"email": "private@example.test"})
    monkeypatch.setattr(value_origin, limit, 1)
    final = proposed(store, raw, "private@example.test private@example.test")
    decision = release_final(index, final.artifact_id)
    assert decision.effect == Effect.DENY
    assert store.get(decision.released_artifact_id).content() == ""


@pytest.mark.parametrize("text", ["2026-99-99", "2026-02-30", "2025-02-29"])
def test_invalid_calendar_dates(text):
    with pytest.raises(ValueError):
        canonical_value(text, ValueType.DATE)


def test_exposure_does_not_prove_sensitive_value_origin():
    store, raw, index = setup({"email": "private@example.test"})
    public = source(store, {"content": "Lịch công khai học phần"}, Sensitivity.PUBLIC)
    index.add_artifact(public.artifact_id, observed_step=1)
    found = index.find_origins("Lịch công khai học phần", ValueType.FREE_TEXT)
    assert found.known and found.max_sensitivity == Sensitivity.PUBLIC
    final = proposed(store, raw, "Lịch công khai học phần")
    decision = release_final(index, final.artifact_id)
    assert decision.effect == Effect.ALLOW
    # Exposure labels remain conservative; release evidence is a separate dimension.
    assert store.get(decision.released_artifact_id).sensitivity == Sensitivity.CONFIDENTIAL


def test_same_value_public_and_sensitive_cannot_declassify():
    store, raw, index = setup({"email": "private@example.test"})
    public = source(store, {"email": "private@example.test"}, Sensitivity.PUBLIC)
    index.add_artifact(public.artifact_id, observed_step=1)
    final = proposed(store, raw, "private@example.test")
    assert release_final(index, final.artifact_id).effect == Effect.REDACT


def test_allow_means_profile_no_match_not_complete_leak_detection():
    store, raw, index = setup({"name": "An", "count": 2})
    final = proposed(store, raw, "An có 2 mục")
    assert not index.records
    assert release_final(index, final.artifact_id).effect == Effect.ALLOW


def test_too_long_scalar_retires_instead_of_silently_skipping():
    store = ArtifactStore("synthetic_limit")
    raw = source(store, {"content": "x" * 32769})
    index = ValueOriginIndex(store)
    with pytest.raises(OriginError):
        index.add_artifact(raw.artifact_id, observed_step=1)
    assert not index.complete


def test_release_before_latest_observation_rejected():
    store, raw, index = setup({"email": "private@example.test"})
    final = proposed(store, raw, "public")
    other = source(store, {"email": "later@example.test"}, step=3)
    index.add_artifact(other.artifact_id, observed_step=3)
    with pytest.raises(ValueError):
        release_final(index, final.artifact_id)


@pytest.mark.parametrize(
    "columns,rows,valid",
    [
        (["student_id", "gpa"], [["SV20260017", 2.13]], True),
        (["student_id", "GPA"], [["SV20260017", 2.13]], True),
        (["gpa", "gpa"], [[2.13, 3.0]], False),
        (["student_id", "gpa"], [["SV20260017"]], False),
        ([42], [[2.13]], False),
        (["gpa"], [{"gpa": 2.13}], False),
    ],
)
def test_native_database_columns_rows(columns, rows, valid):
    store = ArtifactStore("synthetic_table")
    raw = store.create(
        {"columns": columns, "rows": rows},
        artifact_type=ArtifactType.DB_RESULT,
        source_type=SourceType.DATABASE,
        source_id="synthetic",
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=Sensitivity.CONFIDENTIAL,
        trust=Trust.TRUSTED,
    )
    index = ValueOriginIndex(store)
    if not valid:
        with pytest.raises(OriginError):
            index.add_artifact(raw.artifact_id, observed_step=1)
        assert not index.complete
    else:
        index.add_artifact(raw.artifact_id, observed_step=1)
        origin = index.find_origins(2.13, ValueType.GPA)
        assert origin.known and origin.origins[0].pointer == "/rows/0/1"
        assert (
            release_final(index, proposed(store, raw, "GPA: 2.13").artifact_id).effect
            == Effect.REDACT
        )


def test_component_table_reproduces_exactly(tmp_path):
    from react_agent.security_v1.value_origin_qa import component_cases

    first = component_cases(tmp_path / "first")
    second = component_cases(tmp_path / "second")
    assert first == second and len(first) == 24
    assert sum(r["effect"] == "REDACT" for r in first) == 8
    assert sum(r["effect"] == "DENY" for r in first) == 4
    assert sum(r["effect"] == "ALLOW" for r in first) == 12
    for path in (tmp_path / "first").rglob("*"):
        if path.is_file():
            assert (
                path.read_bytes()
                == (tmp_path / "second" / path.relative_to(tmp_path / "first")).read_bytes()
            )
