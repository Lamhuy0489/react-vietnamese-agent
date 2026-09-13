"""Mutation tests for observable stop/return/exit consistency, not native proof."""

import pytest

from react_agent.validation.worker_shutdown_audit_v2 import audit_event


def good() -> dict:
    return dict(
        schema_version="worker_shutdown_v2",
        sequence=1,
        pid=123,
        method="GRACEFUL",
        reaped=True,
        exitcode=0,
        elapsed_seconds=0.9,
        graceful_requested=True,
        graceful_shutdown_seconds=2.0,
        stop_received=True,
        stop_received_seconds=0.1,
        serve_returned=True,
        serve_returned_after_stop_seconds=0.5,
    )


def test_consistent_observations() -> None:
    audit_event(good())
    row = good()
    row.update(
        method="TERMINATE",
        exitcode=-15,
        serve_returned=False,
        serve_returned_after_stop_seconds=None,
    )
    audit_event(row)


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "v1"),
        ("sequence", True),
        ("pid", -1),
        ("exitcode", 9),
        ("stop_received", False),
        ("stop_received_seconds", None),
        ("stop_received_seconds", 2.0),
        ("serve_returned", False),
        ("serve_returned_after_stop_seconds", None),
        ("serve_returned_after_stop_seconds", 0.01),
        ("elapsed_seconds", float("nan")),
        ("graceful_shutdown_seconds", float("inf")),
        ("graceful_requested", False),
        ("reaped", False),
        ("method", "NOT_STARTED"),
    ],
)
def test_inconsistent_evidence_rejected(key: str, value: object) -> None:
    row = good()
    row[key] = value
    with pytest.raises(ValueError):
        audit_event(row)
