"""The owner review must precede content and bind exact public/private roles."""

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from react_agent.validation.room_inventory_review_v1 import (
    RoomInventoryReview,
    pinned_room_catalog,
)

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "experiments/manifests/phase5_room_prospective_inventory_review_v1.json"
DRAFT = ROOT / "experiments/manifests/phase5_room_prospective_inventory_review_draft_v1.json"


def test_approved_content_free_draft_binds_exact_roles() -> None:
    review = RoomInventoryReview.model_validate_json(REVIEW.read_bytes())
    annotations = review.admit_draft(DRAFT.read_bytes())
    labels = [
        (entry.source_id, entry.sensitivity.value, entry.trust.value)
        for entry in annotations.entries
    ]
    assert labels == [
        ("AUX_FUTUREPRIVATE", "S2", "UNTRUSTED"),
        ("AUX_FUTUREROOM", "S0", "UNTRUSTED"),
    ]
    assert all("content" not in entry for entry in json.loads(DRAFT.read_text())["entries"])


def test_review_rejects_changed_draft_even_if_labels_appear_equivalent() -> None:
    review = RoomInventoryReview.model_validate_json(REVIEW.read_bytes())
    raw = DRAFT.read_bytes()
    with pytest.raises(ValueError, match="owner-reviewed bytes"):
        review.admit_draft(raw + b"\n")
    changed = raw.replace(b'"sensitivity": "S0"', b'"sensitivity": "S2"')
    with pytest.raises(ValueError, match="owner-reviewed bytes"):
        review.admit_draft(changed)
    altered_review = review.model_copy(update={"draft_sha256": "0" * 64})
    with pytest.raises(ValueError, match="owner-reviewed bytes"):
        altered_review.admit_draft(raw)


def test_review_rejects_wrong_roles_even_with_matching_draft_hash() -> None:
    import hashlib

    review = RoomInventoryReview.model_validate_json(REVIEW.read_bytes())
    changed = DRAFT.read_bytes().replace(b'"sensitivity": "S0"', b'"sensitivity": "S2"')
    forged = review.model_copy(update={"draft_sha256": hashlib.sha256(changed).hexdigest()})
    with pytest.raises(ValueError, match="approved source roles"):
        forged.admit_draft(changed)


def test_run_pin_requires_actual_commit_and_timestamp_after_review() -> None:
    review = RoomInventoryReview.model_validate_json(REVIEW.read_bytes())
    draft = DRAFT.read_bytes()
    after = review.recorded_at_utc + timedelta(minutes=1)
    pin = review.prepare_pin(draft, source_commit="a" * 40, declared_at_utc=after)
    assert pin.annotations == review.admit_draft(draft)
    assert pin.source_commit == "a" * 40
    with pytest.raises(ValidationError):
        review.prepare_pin(draft, source_commit="uncommitted", declared_at_utc=after)
    with pytest.raises(ValueError, match="cannot predate"):
        review.prepare_pin(
            draft,
            source_commit="a" * 40,
            declared_at_utc=review.recorded_at_utc - timedelta(seconds=1),
        )
    with pytest.raises(ValidationError):
        review.prepare_pin(draft, source_commit="a" * 40, declared_at_utc=datetime.now())


def test_review_rejects_local_time_and_missing_decision_reference() -> None:
    fields = json.loads(REVIEW.read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        RoomInventoryReview.model_validate({**fields, "recorded_at_utc": datetime(2026, 9, 23)})
    with pytest.raises(ValidationError):
        RoomInventoryReview.model_validate(
            {
                **fields,
                "recorded_at_utc": datetime(2026, 9, 23, tzinfo=timezone(timedelta(hours=7))),
            }
        )
    with pytest.raises(ValidationError):
        RoomInventoryReview.model_validate({**fields, "review_ref": ""})
    assert RoomInventoryReview.model_validate(
        {**fields, "recorded_at_utc": datetime(2026, 9, 23, tzinfo=UTC)}
    )


def test_pinned_room_catalog_checks_review_pin_run_and_exact_inventory() -> None:
    review = RoomInventoryReview.model_validate_json(REVIEW.read_bytes())
    draft = DRAFT.read_bytes()
    pin = review.prepare_pin(
        draft,
        source_commit="a" * 40,
        declared_at_utc=review.recorded_at_utc + timedelta(seconds=1),
    )
    ids = ("BASE_DOCUMENT", "AUX_FUTUREPRIVATE", "AUX_FUTUREROOM")
    admitted = pinned_room_catalog(
        review,
        draft,
        pin,
        expected_pin_sha256=pin.identity,
        source_commit="a" * 40,
        document_ids=ids,
    )
    assert [binding.label.sensitivity.value for binding in admitted.bindings] == ["S2", "S0"]
    assert all(binding.label.trust.value == "UNTRUSTED" for binding in admitted.bindings)
    with pytest.raises(ValueError, match="frozen run identity"):
        pinned_room_catalog(
            review,
            draft,
            pin,
            expected_pin_sha256="0" * 64,
            source_commit="a" * 40,
            document_ids=ids,
        )
    with pytest.raises(ValueError, match="source commit"):
        pinned_room_catalog(
            review,
            draft,
            pin,
            expected_pin_sha256=pin.identity,
            source_commit="b" * 40,
            document_ids=ids,
        )
    for bad_ids in (
        ("BASE_DOCUMENT", "AUX_FUTUREROOM"),
        (*ids, "AUX_UNKNOWN"),
        (*ids, "AUX_FUTUREROOM"),
    ):
        with pytest.raises(ValueError, match="inventory|duplicate"):
            pinned_room_catalog(
                review,
                draft,
                pin,
                expected_pin_sha256=pin.identity,
                source_commit="a" * 40,
                document_ids=bad_ids,
            )


def test_pinned_room_catalog_rejects_changed_review_reference() -> None:
    review = RoomInventoryReview.model_validate_json(REVIEW.read_bytes())
    draft = DRAFT.read_bytes()
    pin = review.prepare_pin(
        draft,
        source_commit="a" * 40,
        declared_at_utc=review.recorded_at_utc + timedelta(seconds=1),
    )
    altered = pin.model_copy(update={"review_ref": "another_review"})
    with pytest.raises(ValueError, match="frozen run identity"):
        pinned_room_catalog(
            review,
            draft,
            altered,
            expected_pin_sha256=pin.identity,
            source_commit="a" * 40,
            document_ids=("AUX_FUTUREPRIVATE", "AUX_FUTUREROOM"),
        )
