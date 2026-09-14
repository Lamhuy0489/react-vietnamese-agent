"""Opt-in observer preserves responses, generation inputs and failures."""

import json
from dataclasses import dataclass

import pytest

from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.guard_diagnostic_backend_v1 import DiagnosticBackend, DiagnosticFactory


@dataclass
class Backend:
    text: str = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'
    model_id: str = "synthetic-guard"
    model_revision: str = "diagnostic_v1"

    def generate(self, messages, config):
        self.messages, self.config = messages, config
        self.response = ModelResponse(
            text=self.text, model_id=self.model_id, model_revision=self.model_revision
        )
        return self.response


def test_response_input_and_sequence_parity(tmp_path):
    base = Backend()
    output = tmp_path / "diagnostics.jsonl"
    backend = DiagnosticBackend(base, output)
    messages = [{"role": "user", "content": "SYNTHETIC_PRIVATE_REQUEST"}]
    generation = GenerationConfig(max_new_tokens=128)
    for _ in range(2):
        assert backend.generate(messages, generation) is base.response
        assert base.messages is messages and base.config is generation
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert [r["sequence"] for r in records] == [1, 2]
    assert all(r["diagnostic"]["category"] == "valid" for r in records)
    assert "SYNTHETIC_PRIVATE_REQUEST" not in output.read_text()
    assert all(r["response_identity_matches"] for r in records)


def test_invalid_output_is_returned_unchanged_and_sanitized(tmp_path):
    base = Backend(text='{"secret_key":"SYNTHETIC_PRIVATE_VALUE"}')
    backend = DiagnosticBackend(base, tmp_path / "audit")
    assert backend.generate([], GenerationConfig()).text == base.text
    saved = backend.output.read_text()
    assert "secret_key" not in saved and "SYNTHETIC_PRIVATE_VALUE" not in saved
    assert json.loads(saved)["diagnostic"]["category"] == "schema"


def test_transport_exception_propagates_without_fake_receipt(tmp_path):
    class Failure(Backend):
        def generate(self, messages, config):
            raise TimeoutError("synthetic error")

    output = tmp_path / "audit"
    backend = DiagnosticBackend(Failure(), output)
    with pytest.raises(TimeoutError):
        backend.generate([], GenerationConfig())
    assert not output.exists()


def test_fresh_output_before_model_load(tmp_path):
    output = tmp_path / "audit"
    output.write_text("preserve")

    def forbidden():
        raise AssertionError("must not load")

    with pytest.raises(ValueError, match="fresh"):
        DiagnosticFactory(forbidden, output)()
    assert output.read_text() == "preserve"


def test_sink_failure_is_sanitized_and_fail_closed(tmp_path):
    output = tmp_path / "audit"
    backend = DiagnosticBackend(Backend(), output)
    output.mkdir()
    with pytest.raises(RuntimeError, match="guard diagnostic unavailable"):
        backend.generate([], GenerationConfig())
    assert backend.sequence == 0


def test_identity_change_is_not_masked(tmp_path):
    base = Backend()
    wrapped = DiagnosticBackend(base, tmp_path / "audit")
    base.model_revision = "changed"
    assert wrapped.model_revision == "changed"


def test_symlink_rejected_and_owner_enforced(tmp_path):
    target = tmp_path / "target"
    target.write_text("untouched")
    output = tmp_path / "audit"
    output.symlink_to(target)
    with pytest.raises(ValueError):
        DiagnosticBackend(Backend(), output)
    backend = DiagnosticBackend(Backend(), tmp_path / "fresh")
    backend.owner_pid = -1
    with pytest.raises(RuntimeError, match="worker process"):
        backend.generate([], GenerationConfig())
