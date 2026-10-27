import copy
import json

import pytest

from react_agent.llm.request_reconciliation_v3 import save_resolution, verify_terminal_status

IDENTITY = {"instance_id": "boot1", "session_id": "session", "source_commit": "a" * 40,
            "worker_sha256": "b" * 64, "model_revision": "sha256:" + "c" * 64,
            "model_id": "synthetic", "role": "agent"}
STATUS = {"instance_id": "boot1", "request_id": "r1", "request_sha256": "d" * 64,
          "state": "CANCELLED", "engine_returned": True, "engine_active": False,
          "gpu_quiescence_attested": True, "quiescence_basis": "device_synchronize",
          "durable": True, "instance_retired": False, "http_status": 409,
          "cancel_requested": True, "response_sha256": "e" * 64}


def verify(response):
    return verify_terminal_status(identity=IDENTITY, request_id="r1", request_sha256="d" * 64,
                                  response=response)


@pytest.mark.parametrize("field,value", [
    ("instance_id", "oldboot"), ("request_id", "r2"), ("request_sha256", "f" * 64),
    ("state", "CANCEL_REQUESTED"), ("state", "QUIESCENCE_UNKNOWN"),
    ("engine_returned", False), ("engine_active", True), ("gpu_quiescence_attested", False),
    ("gpu_quiescence_attested", 1), ("quiescence_basis", "callback_returned"),
    ("durable", False), ("instance_retired", True), ("http_status", 200),
    ("cancel_requested", False), ("response_sha256", "wrong"),
])
def test_mismatch_and_unresolved_fail_closed(field, value):
    response = {"identity": dict(IDENTITY), "request": {**STATUS, field: value}}
    with pytest.raises(ValueError):
        verify(response)


@pytest.mark.parametrize("field", sorted(IDENTITY))
def test_every_identity_pin_must_match(field):
    response = {"identity": {**IDENTITY, field: "changed"}, "request": dict(STATUS)}
    with pytest.raises(ValueError, match="identity mismatch"):
        verify(response)


@pytest.mark.parametrize("state,code", [("SUCCEEDED", 200), ("FAILED", 422), ("CANCELLED", 409)])
def test_terminal_receipt_does_not_authorize_semantic_retry(tmp_path, state, code):
    response = {"identity": dict(IDENTITY), "request": {**STATUS, "state": state,
                         "http_status": code, "cancel_requested": state == "CANCELLED"}}
    prior = copy.deepcopy(response)
    path = tmp_path / "resolution.json"
    receipt = save_resolution(path, identity=IDENTITY, request_id="r1", request_sha256="d" * 64,
                               response=response)
    assert response == prior and json.loads(path.read_text()) == receipt
    assert receipt["execution_resolved"] and not receipt["semantic_retry_authorized"]
    with pytest.raises(FileExistsError):
        save_resolution(path, identity=IDENTITY, request_id="r1", request_sha256="d" * 64,
                        response=response)
