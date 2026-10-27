"""The host factory must consume the actual v3 envelope and freeze its boot."""
import json

import pytest

import react_agent.llm.request_worker_runtime_v1 as runtime
from react_agent.llm.http_diagnostic_v1 import APIError


def connection(tmp_path):
    identity = {"model_id": "qwen3-8b", "role": "agent", "session_id": "session1",
                "source_commit": "a" * 40, "worker_sha256": "b" * 64,
                "model_revision": "sha256:" + "c" * 64, "instance_id": "boot1"}
    row = {key: value for key, value in identity.items() if key not in {"model_id", "instance_id"}}
    row.update(id=identity["model_id"], endpoint="https://synthetic.invalid/v1",
               api_key="synthetic-test-key")
    metadata = {"profile": runtime.PROFILE, "identity": identity, "status": "READY",
                "gpu_quiescence_attested": False}
    (tmp_path / "pair_endpoints.json").write_text(json.dumps(
        {"profile": runtime.PROFILE, "models": [row]}))
    (tmp_path / "agent_live_metadata.json").write_text(json.dumps(metadata))
    return metadata


def test_reads_nested_v3_metadata_and_pins_boot(tmp_path):
    connection(tmp_path)
    factory = runtime.RequestWorkerSessionFactory.from_directory(
        tmp_path, tmp_path / "journal", "task", "agent")
    assert factory.instance_id == "boot1"
    assert factory.public_identity()["instance_id"] == "boot1"
    assert "api_key" not in repr(factory)


def test_changed_boot_stops_before_journal_or_generation(tmp_path, monkeypatch):
    metadata = connection(tmp_path)
    factory = runtime.RequestWorkerSessionFactory.from_directory(
        tmp_path, tmp_path / "journal", "task", "agent")
    metadata["identity"]["instance_id"] = "boot2"

    class Transport:
        def __init__(self, *args, **kwargs):
            self.identity = metadata["identity"]

        def probe(self):
            return metadata

    monkeypatch.setattr(runtime, "RequestWorkerHTTPS", Transport)
    with pytest.raises(APIError, match="WORKER_BOOT_CHANGED"):
        factory()
    assert not (tmp_path / "journal").exists()


def test_rejects_flat_v1_metadata(tmp_path):
    metadata = connection(tmp_path)
    (tmp_path / "agent_live_metadata.json").write_text(json.dumps(metadata["identity"]))
    with pytest.raises(ValueError, match="v3 worker identity"):
        runtime.RequestWorkerSessionFactory.from_directory(
            tmp_path, tmp_path / "journal", "task", "agent")
