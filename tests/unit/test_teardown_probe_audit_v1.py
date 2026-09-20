"""Deterministic negative controls for CPU-only teardown records."""

import copy
import hashlib
import json

import pytest

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.teardown_probe_v1 import MODEL, PLAN, REVISION, worker_config
from react_agent.validation.teardown_probe_audit_v1 import audit, audit_case


def good():
    response = ModelResponse(text="public", model_id=MODEL, model_revision=REVISION).model_dump(
        mode="json"
    )
    return dict(
        protocol="teardown_case_v1",
        mode="fast",
        synthetic=True,
        actual_model_loads=0,
        generation_error=None,
        execution_config_sha256=worker_config().identity,
        writer_pid=123,
        responses=[response, response],
        close_started=10.0,
        close_finished=10.1,
        stop_received_at=10.01,
        serve_returned_at=10.04,
        stages=dict(
            destructor_entered=10.02,
            destructor_completed=10.03,
            finalizer_entered=10.05,
            finalizer_completed=10.06,
            thread_entered=None,
            thread_completed=None,
        ),
        lifecycle=[
            dict(
                schema_version="worker_shutdown_v2",
                sequence=1,
                pid=123,
                method="GRACEFUL",
                exitcode=0,
                reaped=True,
                graceful_requested=True,
                graceful_shutdown_seconds=2.0,
                elapsed_seconds=0.09,
                stop_received=True,
                stop_received_seconds=0.01,
                serve_returned=True,
                serve_returned_after_stop_seconds=0.04,
            )
        ],
        attempts=[
            dict(
                sequence=i,
                status="OK",
                pid=123,
                cold_start=i == 1,
                reaped=False,
                worker_retained=True,
                load_seconds=0.01,
                generation_seconds=0.01,
                elapsed_seconds=0.03,
                execution_config_sha256=worker_config().identity,
                request_sha256=text_hash(canonical_json([])),
                generation_sha256=text_hash(canonical_json(GenerationConfig().model_dump())),
            )
            for i in (1, 2)
        ],
    )


def test_synthetic_record_readonly():
    value = good()
    before = copy.deepcopy(value)
    result = audit_case(value, "fast")
    assert result["method"] == "GRACEFUL" and value == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("synthetic", False),
        ("actual_model_loads", True),
        ("generation_error", "RuntimeError"),
        ("mode", "bounded"),
        ("writer_pid", True),
        ("execution_config_sha256", "0" * 64),
        ("responses", []),
        ("attempts", []),
        ("close_finished", 9.0),
        ("serve_returned_at", 10.08),
        ("stop_received_at", float("nan")),
        ("close_started", True),
    ],
)
def test_invalid_case_rejected(field, value):
    record = good()
    record[field] = value
    with pytest.raises(ValueError):
        audit_case(record, "fast")


@pytest.mark.parametrize(
    "field,value",
    [
        ("finalizer_entered", 10.035),
        ("finalizer_completed", None),
        ("destructor_entered", 10.005),
        ("destructor_completed", 10.09),
        ("thread_entered", 10.01),
        ("finalizer_completed", float("inf")),
    ],
)
def test_stage_order_or_completeness_rejected(field, value):
    record = good()
    record["stages"][field] = value
    with pytest.raises(ValueError):
        audit_case(record, "fast")


@pytest.mark.parametrize(
    "field,value",
    [
        ("sequence", True),
        ("pid", 456),
        ("cold_start", False),
        ("generation_seconds", -1),
        ("load_seconds", True),
        ("request_sha256", "wrong"),
    ],
)
def test_attempt_binding(field, value):
    record = good()
    record["attempts"][0][field] = value
    with pytest.raises(ValueError):
        audit_case(record, "fast")


@pytest.mark.parametrize(
    "field,value",
    [
        ("graceful_shutdown_seconds", 3.0),
        ("method", "TERMINATE"),
        ("serve_returned", False),
        ("reaped", False),
        ("elapsed_seconds", 3),
        ("serve_returned_after_stop_seconds", 0.06),
        ("serve_returned_after_stop_seconds", None),
    ],
)
def test_lifecycle_binding(field, value):
    record = good()
    record["lifecycle"][0][field] = value
    with pytest.raises(ValueError):
        audit_case(record, "fast")


def test_schedule_rejects_missing_extra_and_links(tmp_path):
    (tmp_path / "identity.json").write_text("{}")
    with pytest.raises(ValueError, match="schedule"):
        audit(tmp_path)
    (tmp_path / "extra").symlink_to(tmp_path / "identity.json")
    with pytest.raises(ValueError):
        audit(tmp_path)


def test_plan_has_fixed_independent_conditions():
    assert PLAN["repetitions"] == 3 and len(set(PLAN["modes"])) == 6
    assert PLAN["graceful_seconds"] == worker_config().graceful_shutdown_seconds == 2.0
    assert len(hashlib.sha256(canonical_json(PLAN).encode()).hexdigest()) == 64
    assert json.loads(canonical_json(PLAN))["calls_per_worker"] == 2
