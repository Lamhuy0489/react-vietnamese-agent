"""Explicit anonymous acquisition of one pinned public Llama distribution.

Deployment only: imports perform no I/O. Every byte is checked before model load.
The Llama 3.2 license applies; public availability is not a license waiver.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

PROFILE = "public_unsloth_llama32_3b_v1"
REPO = "unsloth/Llama-3.2-3B-Instruct"
REVISION = "006f5dcd1393c3add266de40994ba96225e9689d"
FILES: dict[str, tuple[int, str]] = {
    'README.md': (5743,
        '99d1333b680f191e0e6a722d7d634e96c0540c287b9a89f735c208fd42ebb7ac'),
    'chat_template.jinja': (3827,
        '5816fce10444e03c2e9ee1ef8a4a1ea61ae7e69e438613f3b17b69d0426223a4'),
    'config.json': (890,
        'eadff796b79b82cefa0537004668d70a1dd099fd4986b91ef88398ed91b26311'),
    'generation_config.json': (234,
        '8bab06a398ca622f8b941eb0b5f425d71d007080436cfa4f37d6c03c23b756a9'),
    'model-00001-of-00002.safetensors': (4965799096,
        '13cbd6d16e927a0c5bad54102514e6e18b4a47b3a6eb911e39d678d328d19f55'),
    'model-00002-of-00002.safetensors': (1459729952,
        '7b770216613ac5c34d7c54bdff1fa616bc4e338a9d0b20af6303e48c295ee23c'),
    'model.safetensors.index.json': (20919,
        '0a57c30afc07c81610ae7fe013bea3b9d50365f9a8145ae98e8714220f3d7c7c'),
    'special_tokens_map.json': (454,
        '94e708c3f5e64acf85bbe5ad01467a1248faadb73e83b41793087ecced586e8f'),
    'tokenizer.json': (17209920,
        '6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b'),
    'tokenizer_config.json': (54669,
        '9ddd255c19fe319c8d4e891163540382e9fbda99f394674f2a929efc47d57458'),
}

def validate_configuration(cfg: dict[str, Any]) -> None:
    if (cfg.get("model_acquisition") != PROFILE or cfg.get("role") != "guard"
            or cfg.get("model") != "llama-3.2-3b-instruct"
            or cfg.get("model_source") != REPO + "@" + REVISION):
        raise ValueError("PUBLIC_MODEL_CONFIGURATION_MISMATCH")


def _verify(path: Path, expected: tuple[int, str]) -> None:
    size, digest = expected
    if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
        raise ValueError("PUBLIC_MODEL_FILE_INVALID")
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            hasher.update(chunk)
    if hasher.hexdigest() != digest:
        raise ValueError("PUBLIC_MODEL_HASH_MISMATCH")


def prepare_model(root: Path = Path("/kaggle/working/public-llama-" + REVISION)) -> Path:
    """Download exact declared files once; reject altered cache or incomplete files."""
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("PUBLIC_MODEL_DIRECTORY_LINK")
    root.mkdir(parents=True, exist_ok=True)
    if any(p.name not in FILES for p in root.iterdir()):
        raise ValueError("PUBLIC_MODEL_UNEXPECTED_FILE")
    for name, expected in FILES.items():
        target = root / name
        if target.exists() or target.is_symlink():
            _verify(target, expected)
            continue
        temporary = root / (name + ".partial")
        started = time.monotonic()
        count, reported = 0, 0
        request = urllib.request.Request(
            "https://huggingface.co/" + REPO + "/resolve/" + REVISION + "/" + name,
            headers={"User-Agent": "react-vn-public-model/1"},
        )
        print("MODEL_DOWNLOAD " + name, flush=True)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                if not response.geturl().startswith("https://"):
                    raise ValueError("PUBLIC_MODEL_REDIRECT_SCHEME")
                with temporary.open("xb") as stream:
                    while chunk := response.read(4 * 1024 * 1024):
                        count += len(chunk)
                        if count > expected[0] or time.monotonic() - started > 1200:
                            raise ValueError("PUBLIC_MODEL_DOWNLOAD_BOUND")
                        stream.write(chunk)
                        if count - reported >= 256 * 1024 * 1024:
                            print("MODEL_DOWNLOAD_BYTES " + name + " " + str(count), flush=True)
                            reported = count
            _verify(temporary, expected)
            temporary.rename(target)
        finally:
            if temporary.exists():
                temporary.unlink()
        print("MODEL_VERIFIED " + name, flush=True)
    # Reject accidental fine-tuned/quantized architecture substitutions before HF load.
    config = json.loads((root / "config.json").read_text())
    if (config.get("model_type") != "llama" or config.get("hidden_size") != 3072
            or config.get("num_hidden_layers") != 28 or "quantization_config" in config):
        raise ValueError("PUBLIC_MODEL_ARCHITECTURE_MISMATCH")
    return root
