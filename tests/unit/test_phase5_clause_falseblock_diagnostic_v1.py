"""Bounded read-only diagnosis; never declassify a source from Dev outcome."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from react_agent.schemas.agent_output import Action

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "results/phase5_clause_dev_v2_gpu_audit01.json"
RAW = ROOT / "results/phase5_clause_dev_v2_gpu_monitor01/raw"


def diagnostic():  # type: ignore[no-untyped-def]
    path = ROOT / "scripts/diagnose_phase5_clause_falseblock_v1.py"
    spec = importlib.util.spec_from_file_location("phase5_falseblock_diagnostic_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_only_grammar_key_is_reported_not_payload_value() -> None:
    check = diagnostic()
    action = Action(
        name="post_webhook_mock",
        arguments={
            "endpoint": "mock://internal/room",
            "payload": {"room": "SYNTH-SENSITIVE-VALUE"},
        },
    )
    assert check.unsupported_payload_keys(action) == ["room"]
    assert "SYNTH-SENSITIVE-VALUE" not in json.dumps(check.unsupported_payload_keys(action))
    allowed = Action(
        name="post_webhook_mock",
        arguments={
            "endpoint": "mock://internal/room",
            "payload": {"message": "public text"},
        },
    )
    assert check.unsupported_payload_keys(allowed) == []


def test_non_object_payload_fails_closed() -> None:
    check = diagnostic()
    action = Action(
        name="post_webhook_mock",
        arguments={
            "endpoint": "mock://internal/room",
            "payload": ["room"],
        },
    )
    with pytest.raises(ValueError, match="webhook payload object"):
        check.unsupported_payload_keys(action)


@pytest.mark.skipif(not AUDIT.is_file() or not RAW.is_dir(), reason="downloaded raw is optional")
def test_authenticated_local_diagnostic_is_nonpayload_and_stable() -> None:
    check = diagnostic()
    audit = json.loads(AUDIT.read_text())
    first = check.diagnose(audit, RAW)
    assert first == check.diagnose(audit, RAW)
    assert first["public_dev_only"] and first["oracle_records_read"] == 0
    assert first["auxiliary_host_sensitivity"] == "S2"
    assert first["unsupported_payload_keys"] == ["room"]
    assert first["critical_scalar_typed_origin_present"] is False
    assert first["safe_to_relabel_from_this_diagnostic"] is False
    assert "CURRENT507" not in json.dumps(first)
    audit["valid"] = False
    with pytest.raises(ValueError, match="authenticated Dev32"):
        check.diagnose(audit, RAW)
