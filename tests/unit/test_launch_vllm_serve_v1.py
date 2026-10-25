from __future__ import annotations

import base64
import importlib.util
import io
import json
import stat
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

ROOT = Path(__file__).resolve().parents[2]


def load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "launch_vllm_serve_v1", ROOT / "scripts/launch_vllm_serve_v1.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fake_root = tmp_path / "repo"
    source = fake_root / "notebooks/kaggle/vllm_serve_v1"
    source.mkdir(parents=True)
    for name in ("vllm_serve_v1.ipynb", "kernel-metadata.json"):
        (source / name).write_bytes((module.SOURCE / name).read_bytes())
    monkeypatch.setattr(module, "ROOT", fake_root)
    monkeypatch.setattr(module, "SOURCE", source)
    return module


def test_prepare_fills_config_and_keeps_key_private(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load(tmp_path, monkeypatch)
    folder = module.prepare("someone", "llama31_8b", "hf_test_token")
    config = json.loads((folder / "vllm_serve_v1.ipynb").read_text())["cells"][1]["source"]
    assert 'MODEL_KEY = "llama31_8b"' in config
    assert "HF_TOKEN_INLINE = 'hf_test_token'" in config
    assert stat.S_IMODE((folder / "vllm_serve_v1.ipynb").stat().st_mode) == 0o600
    assert "DISCOVERY = None" not in config and "PUBLIC KEY" in config
    assert "PRIVATE" not in config
    metadata = json.loads((folder / "kernel-metadata.json").read_text())
    assert metadata["id"] == "someone/react-vn-vllm-serve-v1-llama31-8b" and metadata["is_private"]
    mode = (folder / "discovery_private.pem").stat().st_mode
    assert stat.S_IMODE(mode) == 0o600


def test_discover_decrypts_sealed_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load(tmp_path, monkeypatch)
    folder = module.prepare("someone", "qwen3_8b")
    assert "HF_TOKEN_INLINE = None" in (folder / "vllm_serve_v1.ipynb").read_text()
    private = serialization.load_pem_private_key(
        (folder / "discovery_private.pem").read_bytes(), password=None
    )
    assert isinstance(private, rsa.RSAPrivateKey)
    plain = {"base_url": "https://x.trycloudflare.com/v1", "api_key": "k" * 40,
             "boot_id": "b1", "served_model_name": "Qwen/Qwen3-8B@abc"}
    sealed = private.public_key().encrypt(json.dumps(plain).encode(), padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    body = json.dumps({"boot_id": "b1", "ciphertext": base64.b64encode(sealed).decode()})
    line = json.dumps({"event": "message", "message": body})

    def fake_urlopen(url: str, **_: Any) -> io.BytesIO:
        assert url.startswith("https://ntfy.sh/react-vn-")
        return io.BytesIO(line.encode())

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    result = module.discover(folder, timeout_minutes=1)
    assert result["boot_id"] == "b1" and "api_key" not in result
    env = (folder / "endpoint.env").read_text()
    assert "VLLM_API_KEY=" + "k" * 40 in env
    assert stat.S_IMODE((folder / "endpoint.env").stat().st_mode) == 0o600
