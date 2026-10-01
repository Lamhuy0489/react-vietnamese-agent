"""Pinned model acquisition rejects corrupt cache/downloads before native load."""
import hashlib
import io
import json

import pytest

from react_agent.serving import public_llama_source_v1 as source
from react_agent.serving.structured_api_v1 import fingerprint


class Response(io.BytesIO):
    def geturl(self):
        return "https://cdn.huggingface.co/synthetic"


@pytest.fixture
def network(monkeypatch):
    files = {"config.json": json.dumps({"model_type": "llama", "hidden_size": 3072,
                                       "num_hidden_layers": 28}).encode(),
             "model.safetensors": b"synthetic-weights", "chat_template.jinja": b"synthetic"}
    monkeypatch.setattr(source, "FILES", {
        name: (len(raw), hashlib.sha256(raw).hexdigest()) for name, raw in files.items()})
    calls = []
    def fetch(request, timeout):
        assert source.REVISION in request.full_url and timeout == 60
        assert "authorization" not in {k.lower() for k in request.headers}
        calls.append(request.full_url)
        return Response(files[request.full_url.rsplit("/", 1)[1]])
    monkeypatch.setattr(source.urllib.request, "urlopen", fetch)
    return files, calls


def test_download_verified_cache_and_chat_template_fingerprint(tmp_path, network):
    files, calls = network
    root = source.prepare_model(tmp_path / "model")
    assert len(calls) == len(files)
    assert fingerprint(root)["files"]["chat_template.jinja"]["sha256"] == hashlib.sha256(
        files["chat_template.jinja"]).hexdigest()
    source.prepare_model(root)
    assert len(calls) == len(files)


def test_corrupt_cache_is_not_silently_replaced(tmp_path, network):
    _, calls = network
    root = source.prepare_model(tmp_path / "model")
    (root / "model.safetensors").write_bytes(b"X" * len(b"synthetic-weights"))
    before = len(calls)
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        source.prepare_model(root)
    assert len(calls) == before


@pytest.mark.parametrize("payload,error", [(b"bad", "FILE_INVALID"),
    (b"X" * 500, "DOWNLOAD_BOUND")])
def test_invalid_download_never_promoted(tmp_path, network, monkeypatch, payload, error):
    monkeypatch.setattr(source.urllib.request, "urlopen", lambda *a, **k: Response(payload))
    root = tmp_path / "model"
    with pytest.raises(ValueError, match=error):
        source.prepare_model(root)
    assert not list(root.iterdir())


def test_network_failure_preserves_verified_files(tmp_path, network, monkeypatch):
    files, _ = network
    root = tmp_path / "model"
    root.mkdir()
    (root / "config.json").write_bytes(files["config.json"])
    def fail(*args, **kwargs):
        raise OSError("synthetic unavailable")
    monkeypatch.setattr(source.urllib.request, "urlopen", fail)
    with pytest.raises(OSError):
        source.prepare_model(root)
    assert [p.name for p in root.iterdir()] == ["config.json"]


def test_unknown_file_and_linked_cache_rejected(tmp_path, network):
    root = tmp_path / "model"
    root.mkdir()
    (root / "unexpected.py").write_text("not a model")
    with pytest.raises(ValueError, match="UNEXPECTED_FILE"):
        source.prepare_model(root)
    link = tmp_path / "link"
    link.symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError, match="DIRECTORY_LINK"):
        source.prepare_model(link)


@pytest.mark.parametrize("change", [{"role": "agent"}, {"model": "other"},
                                    {"model_source": source.REPO + "@main"}])
def test_public_source_cannot_change_role_or_revision(change):
    cfg = {"role": "guard", "model": "llama-3.2-3b-instruct",
           "model_acquisition": source.PROFILE, "model_source": source.REPO + "@" + source.REVISION}
    source.validate_configuration(cfg)
    with pytest.raises(ValueError, match="CONFIGURATION_MISMATCH"):
        source.validate_configuration({**cfg, **change})
