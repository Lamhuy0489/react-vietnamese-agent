"""Prepare, submit once, and discover two private inference-only Kaggle scripts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKER = "src/react_agent/serving/structured_api_v1.py"
TARGETS = {
    "agent": {"account": "buiquocviet", "credential": "kaggle3.json",
              "slug": "react-vn-qwen3-agent-api-v1", "model": "qwen3-8b",
              "model_source": "qwen-lm/qwen-3/transformers/8b/1"},
    "guard": {"account": "huylmhuhu", "credential": "kaggle1.json",
              "slug": "react-vn-llama3-guard-api-v1", "model": "llama-3.2-3b-instruct",
              "model_source": "metaresearch/llama-3.2/transformers/3b-instruct/1"},
}
TUNNEL = "https://github.com/cloudflare/cloudflared/releases/download/2026.9.3/"
TUNNEL_SHA = "77e26d8d900e0b8469f416239d14b5f296525fdf79fee6f511ef55609e3fbac2"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: Any, *, secret: bool = False) -> None:
    with path.open("x", encoding="utf-8") as stream:
        if secret:
            os.fchmod(stream.fileno(), 0o600)
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def git(*args: str) -> str:
    binary = shutil.which("git")
    if binary is None:
        raise ValueError("Git required")
    return subprocess.check_output(  # noqa: S603 - explicit Git command, no shell
        [binary, *args], cwd=ROOT, text=True).strip()


def prepare(directory: Path, source_commit: str) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    serialization = importlib.import_module("cryptography.hazmat.primitives.serialization")
    rsa = importlib.import_module("cryptography.hazmat.primitives.asymmetric.rsa")
    private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    key_path = directory / "discovery_private.pem"
    with key_path.open("xb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(private.private_bytes(serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    public = private.public_key().public_bytes(serialization.Encoding.PEM,
                                               serialization.PublicFormat.SubjectPublicKeyInfo)
    source = (ROOT / WORKER).read_text()
    if (source_commit != "development"
            and git("show", f"{source_commit}:{WORKER}") != source.strip()):
        raise ValueError("committed worker does not match working source")
    records = {}
    for role, target in TARGETS.items():
        folder = directory / role
        folder.mkdir()
        cfg = {"role": role, "model": target["model"], "model_source": target["model_source"],
            "source_commit": source_commit, "worker_sha256": digest(ROOT / WORKER),
            "session_id": uuid.uuid4().hex, "topic": "rvn-pair-" + uuid.uuid4().hex,
            "public_key_pem": public.decode(),
            "cloudflared_url": TUNNEL + "cloudflared-linux-amd64",
            "cloudflared_sha256": TUNNEL_SHA, "lifetime_seconds": 28800}
        name = target["slug"] + ".py"
        # Source is inline, not dynamically executed/decoded; CFG contains no credential.
        (folder / name).write_text(source + "\n\nLAUNCH_CONFIG = " + repr(cfg)
                                  + '\nif __name__ == "__main__":\n'
                                    '    install_and_serve(LAUNCH_CONFIG)\n')
        meta = {"id": target["account"] + "/" + target["slug"], "title": target["slug"],
            "code_file": name, "language": "python", "kernel_type": "script",
            "is_private": True, "enable_gpu": True, "enable_tpu": False,
            "enable_internet": True, "dataset_sources": [], "competition_sources": [],
            "kernel_sources": [], "model_sources": [target["model_source"]]}
        save(folder / "kernel-metadata.json", meta)
        records[role] = {"kernel": meta["id"], "cfg": cfg,
                        "files": {p.name: digest(p) for p in folder.iterdir()}}
    save(directory / "prepared.json", {"source_commit": source_commit, "roles": records})


def kaggle(role: str, args: list[str], *, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="rvn-kaggle-") as tmp:
        path = Path(tmp) / "kaggle.json"
        shutil.copy2(ROOT / "credential kaggle" / TARGETS[role]["credential"], path)
        path.chmod(0o600)
        python = shutil.which("python3")
        if python is None:
            raise ValueError("Python with Kaggle CLI required")
        return subprocess.run(  # noqa: S603 - exact CLI argv, credentials never printed
            [python, "-m", "kaggle", *args], env=dict(os.environ, KAGGLE_CONFIG_DIR=tmp),
            capture_output=True, text=True, timeout=timeout, check=False)


def push(directory: Path) -> None:
    prepared = json.loads((directory / "prepared.json").read_text())
    commit = prepared["source_commit"]
    if commit == "development" or not (directory / "preflight.json").is_file():
        raise ValueError("committed exact-worker preflight required")
    receipt = json.loads((directory / "preflight.json").read_text())
    if receipt.get("prepared_sha256") != digest(directory / "prepared.json"):
        raise ValueError("preflight not bound to this package")
    if git("ls-remote", "origin", "refs/heads/main").split()[0] != commit:
        raise ValueError("worker source commit must be GitHub main before submission")
    for role, record in prepared["roles"].items():
        folder = directory / role
        if any(digest(folder / name) != value for name, value in record["files"].items()):
            raise ValueError("packaged file changed")
        if (directory / f"{role}_submission_started.json").exists():
            raise ValueError("submission already attempted; inspect it instead of pushing twice")
        save(directory / f"{role}_submission_started.json", {"kernel": record["kernel"]})
        result = kaggle(role, ["kernels", "push", "-p", str(folder), "-t", "32400",
                               "--accelerator", "NvidiaTeslaT4"])
        output = result.stdout + result.stderr
        match = re.search(r"Kernel version (\d+) successfully pushed", output)
        save(directory / f"{role}_submission.json", {"kernel": record["kernel"],
            "returncode": result.returncode, "version": int(match.group(1)) if match else None,
            "source_commit": commit, "output": output})
        if result.returncode != 0 or match is None:
            raise RuntimeError("submission needs read-only inspection; do not auto-retry")
        print(role, "submitted", record["kernel"], "version", match.group(1), flush=True)


def discover(directory: Path) -> None:
    import ssl
    import urllib.request

    serialization = importlib.import_module("cryptography.hazmat.primitives.serialization")
    padding = importlib.import_module("cryptography.hazmat.primitives.asymmetric.padding")
    hashes = importlib.import_module("cryptography.hazmat.primitives.hashes")
    private = serialization.load_pem_private_key(
        (directory / "discovery_private.pem").read_bytes(), password=None)
    prepared = json.loads((directory / "prepared.json").read_text())
    context = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    records = []
    for role, record in prepared["roles"].items():
        cfg = record["cfg"]
        path = directory / f"{role}_connection.json"
        if path.exists():
            connection = json.loads(path.read_text())
        else:
            url = "https://ntfy.sh/" + cfg["topic"] + "/json?poll=1&since=all"
            with urllib.request.urlopen(url, context=context, timeout=15) as response:  # noqa: S310
                events = response.read(65536).decode().splitlines()
            connection = None
            for event in events:
                outer = json.loads(event)
                if outer.get("event") != "message":
                    continue
                packet = json.loads(outer["message"])
                if packet.get("session_id") != cfg["session_id"]:
                    continue
                raw = private.decrypt(base64.b64decode(packet["ciphertext"]), padding.OAEP(
                    mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
                connection = json.loads(raw)
                if connection["session_id"] != cfg["session_id"]:
                    raise ValueError("discovery identity mismatch")
            if connection is None:
                print(role, "waiting for warmup/tunnel", flush=True)
                continue
            save(path, connection, secret=True)
        request = urllib.request.Request(  # noqa: S310 - encrypted authenticated worker URL
            connection["endpoint"] + "/models", headers={
                "Authorization": "Bearer " + connection["api_key"]})
        with urllib.request.urlopen(request, context=context, timeout=15) as response:  # noqa: S310
            metadata = json.load(response)
        if any(metadata.get(k) != cfg[k] for k in ("session_id", "source_commit", "worker_sha256")):
            raise ValueError("live worker identity mismatch")
        metadata_path = directory / f"{role}_live_metadata.json"
        if not metadata_path.exists():
            save(metadata_path, metadata)
        elif json.loads(metadata_path.read_text()) != metadata:
            raise ValueError("live metadata changed")
        records.append({"id": cfg["model"], "role": role, "served_model_name": cfg["model"],
            "kernel_id": record["kernel"], **connection,
            "model_revision": metadata["model_revision"], "source_commit": cfg["source_commit"]})
        print(role, "READY", cfg["model"], flush=True)
    if len(records) == 2:
        target = directory / "pair_endpoints.json"
        value = {"profile": "react-vn-structured-api-v1", "models": records}
        if not target.exists():
            save(target, value, secret=True)
        elif json.loads(target.read_text()) != value:
            raise ValueError("connection config changed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "push", "discover", "status"])
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--source-commit", default="development")
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not directory.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("build/kaggle output required")
    if args.action == "prepare":
        prepare(directory, args.source_commit)
    elif args.action == "push":
        push(directory)
    elif args.action == "discover":
        discover(directory)
    else:
        prepared = json.loads((directory / "prepared.json").read_text())
        for role, record in prepared["roles"].items():
            result = kaggle(role, ["kernels", "status", record["kernel"]])
            print(role, result.stdout.strip() if result.returncode == 0 else "status unavailable")


if __name__ == "__main__":
    main()
