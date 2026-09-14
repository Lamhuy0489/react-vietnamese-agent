"""Audit actual spawned response diagnostics and detect missing/misbound evidence."""

import json

import pytest
from test_guard_diagnostic_pair_v1 import SAFE, invoke

from react_agent.validation.guard_diagnostic_audit_v1 import audit


@pytest.fixture
def case(tmp_path):
    execution = tmp_path / "observed"
    invoke(execution, "A6", SAFE, True)
    return execution, tmp_path / "observed_diagnostics.jsonl"


def test_real_join_is_readonly_and_repeatable(case):
    first = audit(*case)
    assert first == audit(*case)
    assert first["response_records"] == 2
    assert [r["stage"] for r in first["joined"]] == ["PRE", "POST"]


@pytest.mark.parametrize(
    "mutation",
    [
        "pid",
        "request",
        "generation",
        "sequence",
        "missing",
        "extra",
        "category",
        "identity",
        "unsafe_field",
    ],
)
def test_sidecar_mutations_rejected(case, mutation):
    execution, path = case
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if mutation == "pid":
        rows[0]["worker_pid"] += 1
    elif mutation == "request":
        rows[0]["request_sha256"] = "0" * 64
    elif mutation == "generation":
        rows[0]["generation_sha256"] = "0" * 64
    elif mutation == "sequence":
        rows[0]["sequence"] = 2
    elif mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows.append(rows[0])
    elif mutation == "category":
        rows[0]["diagnostic"]["category"] = "schema"
    elif mutation == "identity":
        rows[0]["response_identity_matches"] = False
    elif mutation == "unsafe_field":
        rows[0]["diagnostic"]["raw_text"] = "SYNTHETIC_PRIVATE"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    with pytest.raises(ValueError):
        audit(execution, path)


def test_schema_failure_join_preserves_retirement(tmp_path):
    execution = tmp_path / "bad"
    invoke(execution, "A6", "{}", True)
    result = audit(execution, tmp_path / "bad_diagnostics.jsonl")
    assert result["response_records"] == 1
    assert result["joined"][0]["classification_status"] == "ERROR"
    assert result["joined"][0]["diagnostic"]["category"] == "schema"
