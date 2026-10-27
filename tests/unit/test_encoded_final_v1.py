import base64

import pytest

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.runtime_hooks import derive
from react_agent.security_v1.encoded_final_v1 import EncodedFinalGate
from react_agent.security_v1.final_entitlements_v2 import extract_final_entitlement
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex


def release(value, answer, *, sensitivity=Sensitivity.CONFIDENTIAL, user_text="Đọc hồ sơ nội bộ."):
    store = ArtifactStore("encoded_control")
    user = store.create(user_text, artifact_type=ArtifactType.USER_INPUT,
        source_type=SourceType.USER, source_id="synthetic_user", producer="host_context",
        created_step=0,
        sensitivity=Sensitivity.PUBLIC, trust=Trust.UNTRUSTED)
    source = store.create({"content": value}, artifact_type=ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.DOCUMENT, source_id="DOC_SYNTHETIC", producer="tool_source_snapshot",
        created_step=1, sensitivity=sensitivity, trust=Trust.UNTRUSTED)
    index = ValueOriginIndex(store)
    index.add_artifact(user.artifact_id, observed_step=0)
    index.add_artifact(source.artifact_id, observed_step=1)
    proposal = derive(store, answer, kind=ArtifactType.FINAL_RESPONSE,
        parents=(user.artifact_id, source.artifact_id), step=2)
    before = index.snapshot()
    gate = EncodedFinalGate()
    result = gate(index, proposal.artifact_id, user.artifact_id,
                  extract_final_entitlement(user_text))
    assert index.snapshot() == before
    return result, store.get(result.released_artifact_id).content(), gate.records


@pytest.mark.parametrize("value", ["SYNTH-FRESH-PRIVATE-9371", "Nội dung riêng giả lập こんにちは"])
@pytest.mark.parametrize("encoding", ["base64", "base64_unpadded", "url", "url_unpadded",
                                      "hex_lower", "hex_upper"])
def test_full_encoded_protected_values_denied(value, encoding):
    raw = value.encode()
    encoded = {"base64": base64.b64encode(raw).decode(),
        "base64_unpadded": base64.b64encode(raw).decode().rstrip("="),
        "url": base64.urlsafe_b64encode(raw).decode(),
        "url_unpadded": base64.urlsafe_b64encode(raw).decode().rstrip("="),
        "hex_lower": raw.hex(), "hex_upper": raw.hex().upper()}[encoding]
    result, answer, records = release(value, "prefix " + encoded + " suffix")
    assert result.effect.value == "DENY" and answer == ""
    assert records[0]["encoded_matches"]
    assert value not in str(records[0]["encoded_matches"])


def test_raw_redaction_and_unrelated_public_encoding_preserved():
    private = "SYNTH-SECOND-SECRET-8237"
    assert release(private, private)[0].effect.value == "REDACT"
    public = base64.b64encode("Thông báo công khai: H507.".encode()).decode()
    result, answer, records = release(private, public)
    assert result.effect.value == "ALLOW" and answer == public
    assert not records[0]["encoded_matches"]
    assert release(private, base64.b64encode(private.encode()).decode(),
                   sensitivity=Sensitivity.PUBLIC)[0].effect.value == "ALLOW"


def test_raw_occurrence_cannot_hide_encoded_duplicate():
    private = "SYNTH-DUPLICATE-PRIVATE-5816"
    answer = private + " " + base64.b64encode(private.encode()).decode()
    result, answer, _ = release(private, answer)
    assert result.effect.value == "DENY" and answer == ""


def test_raw_user_mention_does_not_authorize_encoded_disclosure():
    private = "SYNTH-GRANTED-PRIVATE-4283"
    result, answer, _ = release(private, base64.b64encode(private.encode()).decode(),
                                 user_text=f"Nhắc lại {private} trong câu trả lời.")
    assert result.effect.value == "DENY" and answer == ""


def test_screen_budget_failure_is_closed(monkeypatch):
    monkeypatch.setattr("react_agent.security_v1.encoded_final_v1.MAX_SCAN_WORK", 1)
    result, answer, records = release("SYNTH-BUDGET-PRIVATE-4739", "Public reply")
    assert result.effect.value == "DENY" and answer == ""
    assert records[0]["screen_errors"] == ["ENCODED_SCREEN_UNAVAILABLE"]
