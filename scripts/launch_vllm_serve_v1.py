"""Prepare a batch-mode vLLM serve notebook and receive its encrypted endpoint.

``prepare`` writes a fresh folder under ``build/kaggle/`` holding a private RSA
key (0600, Git ignored), the notebook with ``DISCOVERY`` filled in, and
``kernel-metadata.json`` for ``kaggle kernels push``. ``discover`` blocks until
the notebook posts its sealed URL/key to ntfy, then writes ``endpoint.env``
(0600) in the same folder. Neither action calls the Kaggle API.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import ssl
import time
import urllib.request
from pathlib import Path
from typing import Any

import certifi
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notebooks/kaggle/vllm_serve_v1"
MODEL_KEYS = ("qwen3_8b", "llama31_8b", "gemma4_12b")


def prepare(owner: str, model_key: str) -> Path:
    """Build a push-ready folder with a fresh discovery key pair."""
    if model_key not in MODEL_KEYS:
        raise ValueError(f"unknown model key {model_key}")
    folder = ROOT / "build/kaggle" / f"vllm_serve_v1_{model_key}_{time.strftime('%Y%m%d_%H%M%S')}"
    folder.mkdir(parents=True)
    private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    with (folder / "discovery_private.pem").open("xb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(private.private_bytes(serialization.Encoding.PEM,
                                           serialization.PrivateFormat.PKCS8,
                                           serialization.NoEncryption()))
    public = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    discovery = {"topic": "react-vn-" + secrets.token_hex(16), "public_key_pem": public}
    notebook = json.loads((SOURCE / "vllm_serve_v1.ipynb").read_text(encoding="utf-8"))
    config = notebook["cells"][1]
    text = "".join(config["source"])
    replacements = {
        'MODEL_KEY = "qwen3_8b"': f'MODEL_KEY = "{model_key}"',
        "DISCOVERY = None": f"DISCOVERY = {discovery!r}",
    }
    for old, new in replacements.items():
        if text.count(old) != 1:
            raise ValueError(f"config cell must contain {old!r} exactly once")
        text = text.replace(old, new)
    config["source"] = text
    (folder / "vllm_serve_v1.ipynb").write_text(json.dumps(notebook, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    metadata = json.loads((SOURCE / "kernel-metadata.json").read_text(encoding="utf-8"))
    metadata["id"] = f"{owner}/react-vn-vllm-serve-v1"
    (folder / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n",
                                                 encoding="utf-8")
    (folder / "discovery.json").write_text(json.dumps({"topic": discovery["topic"],
                                                       "owner": owner, "model_key": model_key}))
    return folder


def discover(folder: Path, timeout_minutes: float) -> dict[str, Any]:
    """Wait for the sealed endpoint message and write ``endpoint.env``."""
    topic = json.loads((folder / "discovery.json").read_text())["topic"]
    private = serialization.load_pem_private_key((folder / "discovery_private.pem").read_bytes(),
                                                 password=None)
    if not isinstance(private, rsa.RSAPrivateKey):
        raise TypeError("discovery key must be RSA")
    context = ssl.create_default_context(cafile=certifi.where())
    deadline = time.time() + timeout_minutes * 60
    while time.time() < deadline:
        url = f"https://ntfy.sh/{topic}/json?poll=1&since=all"
        try:
            with urllib.request.urlopen(url, timeout=30, context=context) as response:  # noqa: S310
                lines = [line for line in response.read().decode().splitlines() if line.strip()]
        except OSError as exc:  # local network drops are retried until the deadline
            print("ntfy poll failed, retrying:", type(exc).__name__, flush=True)
            time.sleep(30)
            continue
        messages = [json.loads(line) for line in lines]
        bodies = [m["message"] for m in messages if m.get("event") == "message"]
        if bodies:
            sealed = base64.b64decode(json.loads(bodies[-1])["ciphertext"])
            oaep = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                algorithm=hashes.SHA256(), label=None)
            plain = json.loads(private.decrypt(sealed, oaep))
            env = folder / "endpoint.env"
            with env.open("w") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(f"export VLLM_BASE_URL={plain['base_url']}\n"
                             f"export VLLM_API_KEY={plain['api_key']}\n")
            return {"boot_id": plain["boot_id"], "served_model_name": plain["served_model_name"],
                    "base_url": plain["base_url"], "env_file": str(env)}
        time.sleep(30)
    raise TimeoutError("no discovery message before timeout")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--owner", required=True)
    p.add_argument("--model-key", default="qwen3_8b", choices=MODEL_KEYS)
    d = sub.add_parser("discover")
    d.add_argument("--folder", type=Path, required=True)
    d.add_argument("--timeout-minutes", type=float, default=45)
    args = parser.parse_args()
    if args.action == "prepare":
        print(prepare(args.owner, args.model_key))
    else:
        print(json.dumps(discover(args.folder, args.timeout_minutes), indent=2))


if __name__ == "__main__":
    main()
