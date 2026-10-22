"""Prospective guard runner excludes labels and keeps errors and checkpoints."""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from react_agent.llm.base import ModelResponse
from react_agent.security_v1.guard import GuardInput
from react_agent.serving.structured_api_v1 import canonical


@pytest.fixture
def runner(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    module = importlib.import_module("run_phase5_guard_quality_v1")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "unresolved", lambda: False)
    return module


def fixture(runner, tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("synthetic frozen source")
    output = tmp_path / "run"
    output.mkdir()
    inputs = {k: GuardInput(user_instruction="Read the public schedule.", source_type="DOC",
                           candidate_content="Synthetic public content.").model_dump(mode="json")
              for k in ("first", "second")}
    labels = {"first": {"branch": "attack"}, "second": {"branch": "benign"}}
    (output / "inputs.json").write_text(canonical(inputs))
    (output / "labels.json").write_text(canonical(labels))
    manifest = {"schedule": list(inputs), "source_sha256": {source.name: runner.digest(source)},
                "dataset_sha256": {source.name: runner.digest(source)},
                "input_sha256": runner.digest(output / "inputs.json"),
                "labels_sha256": runner.digest(output / "labels.json"),
                "guard_identity": {"model_id": "synthetic", "model_revision": "revision"},
                "positive": ["SUSPICIOUS", "MALICIOUS"]}
    (output / "manifest.json").write_text(canonical(manifest))
    return output


class Backend:
    model_id = "synthetic"
    model_revision = "revision"

    def __init__(self, risk="SAFE", error=False):
        self.risk, self.error = risk, error
        self.messages = []

    def generate(self, messages, config):
        self.messages.append(messages)
        if self.error:
            raise ValueError("synthetic failure")
        value = {"risk": self.risk, "labels": [], "confidence": "HIGH"}
        return ModelResponse(text=canonical(value), model_id=self.model_id,
                             model_revision=self.model_revision)


def test_labels_are_unavailable_to_runner_and_resume_makes_no_calls(runner, tmp_path):
    output = fixture(runner, tmp_path)
    backend = Backend()
    labels = (output / "labels.json").read_bytes()
    (output / "labels.json").unlink()
    assert runner.run(output, lambda _: backend) == 2
    assert len(backend.messages) == 2
    for messages in backend.messages:
        content = json.loads(messages[1]["content"])
        assert set(content) == set(GuardInput.model_fields)
        assert not ({"branch", "family_id", "pair_id"} & set(content))
    assert runner.run(output, lambda _: pytest.fail("resume called backend")) == 0
    (output / "labels.json").write_bytes(labels)
    score = runner.score(output)
    assert score["counts"] == {"attack_attempted": 1, "FN": 1, "benign_attempted": 1, "TN": 1}


def test_error_is_retained_separately_from_classification(runner, tmp_path):
    output = fixture(runner, tmp_path)
    runner.run(output, lambda key: Backend("MALICIOUS", error=key == "second"))
    counts = runner.score(output)["counts"]
    assert counts["TP"] == 1 and counts["benign_error"] == 1
    assert "TN" not in counts and "FP" not in counts


def test_started_only_blocks_without_backend_call(runner, tmp_path):
    output = fixture(runner, tmp_path)
    (output / "tasks/first").mkdir(parents=True)
    with pytest.raises(ValueError, match="started-only"):
        runner.run(output, lambda _: pytest.fail("backend must not be called"))


@pytest.mark.parametrize("target", ["inputs.json", "labels.json", "tasks/first/completed.json"])
def test_tampered_artifacts_rejected(runner, tmp_path, target):
    output = fixture(runner, tmp_path)
    runner.run(output, lambda _: Backend())
    path = output / target
    value = json.loads(path.read_text())
    value["tampered"] = True
    path.write_text(canonical(value))
    with pytest.raises(ValueError, match="hash|changed"):
        runner.score(output)


def test_unresolved_delivery_blocks_before_inference(runner, tmp_path, monkeypatch):
    output = fixture(runner, tmp_path)
    monkeypatch.setattr(runner, "unresolved", lambda: True)
    with pytest.raises(ValueError, match="unresolved"):
        runner.run(output, lambda _: pytest.fail("backend must not be called"))
