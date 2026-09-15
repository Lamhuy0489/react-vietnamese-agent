"""Synthetic observer parity, fresh sinks, no leaked text and no fake responses."""

import json

import pytest
from test_guard_diagnostic_backend_v1 import Backend

from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticBackend, DiagnosticFactory
from react_agent.validation.guard_diagnostic_audit_v2 import Sidecar, _records


@pytest.mark.parametrize(
    "text",
    [
        Backend.text,
        "",
        "  ",
        '```json\n{"secret":"SYNTHETIC_PRIVATE"}\n```',
        '{"risk":"SAFE",}',
        '{"risk" "SAFE"}',
        '{"risk":"unterminated',
        "[]",
        "{}",
        "NaN",
        '{"x":1,"x":2}',
        "x" * 65537,
        "[" * 2000,
    ],
)
def test_output_and_input_parity(tmp_path, text):
    base = Backend(text=text)
    path = tmp_path / "audit"
    wrapped = DiagnosticBackend(base, path)
    messages = [{"role": "user", "content": "SYNTHETIC_PRIVATE_REQUEST"}]
    generation = GenerationConfig()
    for _ in range(2):
        assert wrapped.generate(messages, generation) is base.response
        assert base.messages is messages and base.config is generation
    records = _records(path.read_bytes(), Sidecar)
    assert [r.sequence for r in records] == [1, 2]
    assert "SYNTHETIC_PRIVATE" not in path.read_text()


def test_failure_has_no_fake_response(tmp_path):
    class Failure(Backend):
        def generate(self, messages, config):
            raise TimeoutError("synthetic timeout")

    path = tmp_path / "audit"
    wrapped = DiagnosticBackend(Failure(), path)
    with pytest.raises(TimeoutError):
        wrapped.generate([], GenerationConfig())
    assert not path.exists() and wrapped.sink.sequence == 0


def test_fresh_factory_and_process_owner(tmp_path):
    path = tmp_path / "audit"
    path.write_text("preserve")

    def forbidden():
        raise AssertionError("must not load")

    with pytest.raises(ValueError, match="fresh"):
        DiagnosticFactory(forbidden, path)()
    wrapped = DiagnosticBackend(Backend(), tmp_path / "new")
    wrapped.sink.owner_pid = -1
    with pytest.raises(RuntimeError, match="wrong process"):
        wrapped.generate([], GenerationConfig())
    assert path.read_text() == "preserve"


@pytest.mark.parametrize("mutation", ["truncate", "remove", "symlink"])
def test_sink_tampering_is_sticky_failure(tmp_path, mutation):
    path = tmp_path / "audit"
    wrapped = DiagnosticBackend(Backend(), path)
    wrapped.generate([], GenerationConfig())
    if mutation == "truncate":
        path.write_text("")
    else:
        path.unlink()
        if mutation == "symlink":
            target = tmp_path / "target"
            target.write_text("preserve")
            path.symlink_to(target)
    with pytest.raises(RuntimeError, match="guard diagnostic unavailable"):
        wrapped.generate([], GenerationConfig())
    assert wrapped.sink.sequence == 1
    with pytest.raises(RuntimeError, match="unavailable"):
        wrapped.generate([], GenerationConfig())
    if mutation == "symlink":
        assert target.read_text() == "preserve"


def test_response_identity_mismatch_not_masked(tmp_path):
    class Changed(Backend):
        def generate(self, messages, config):
            return ModelResponse(text=self.text, model_id="changed", model_revision="changed")

    path = tmp_path / "audit"
    wrapped = DiagnosticBackend(Changed(), path)
    assert wrapped.generate([], GenerationConfig()).model_id == "changed"
    assert not json.loads(path.read_text())["response_identity_matches"]
