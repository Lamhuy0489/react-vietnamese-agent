"""Prepare and CPU-preflight the versioned request-worker v3 pair package.

This launcher deliberately has no Kaggle submission, status, or discovery
action.  ``prepare`` only creates an auditable private package and
``preflight`` exercises that package with synthetic callbacks in isolated
stdlib Python.  Native model loading, tunnel startup, credentials, and
network I/O belong to a separately reviewed deployment step.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "react-vn-request-lifecycle-v3-candidate"
DISCOVERY_PROFILE = PROFILE
WORKER_FILES = (
    "react_agent/__init__.py",
    "react_agent/serving/__init__.py",
    "react_agent/serving/structured_api_v1.py",
    "react_agent/serving/quiescent_engine_v3.py",
    "react_agent/serving/request_storage_v3.py",
    "react_agent/serving/request_lifecycle_v3.py",
    "react_agent/serving/request_http_v3.py",
    "react_agent/serving/request_worker_v3.py",
    "react_agent/serving/request_worker_entrypoint_v3.py",
)
TARGETS = {
    "agent": {
        "account": "buiquocviet",
        "slug": "react-vn-qwen3-agent-api-v3-candidate",
        "model": "qwen3-8b",
        "model_source": "qwen-lm/qwen-3/transformers/8b/1",
    },
    "guard": {
        "account": "huylmhuhu",
        "slug": "react-vn-llama3-guard-api-v3-candidate",
        "model": "llama-3.2-3b-instruct",
        "model_source": "metaresearch/llama-3.2/transformers/3b-instruct/1",
    },
}
TUNNEL = "https://github.com/cloudflare/cloudflared/releases/download/2026.9.3/"
TUNNEL_SHA = "77e26d8d900e0b8469f416239d14b5f296525fdf79fee6f511ef55609e3fbac2"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def save(path: Path, value: Any, *, secret: bool = False) -> None:
    with path.open("x", encoding="utf-8") as stream:
        if secret:
            os.fchmod(stream.fileno(), 0o600)
        stream.write(canonical(value) + "\n")


def git(*args: str) -> str:
    binary = shutil.which("git")
    if binary is None:
        raise ValueError("Git required")
    return subprocess.check_output(  # noqa: S603 - fixed Git executable and argv
        [binary, *args], cwd=ROOT, text=True
    ).strip()


def _check_source_commit(source_commit: str) -> None:
    if source_commit == "development":
        return
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("full immutable Git commit required")
    binary = shutil.which("git")
    if binary is None:
        raise ValueError("Git required")
    for relative in WORKER_FILES:
        committed = subprocess.check_output(  # noqa: S603 - exact Git blob bytes
            [binary, "show", f"{source_commit}:src/{relative}"], cwd=ROOT)
        current = (ROOT / "src" / relative).read_bytes()
        if committed != current:
            raise ValueError(f"committed source does not match working tree: {relative}")


def _wrapper(sources: dict[str, str], cfg: dict[str, Any]) -> str:
    # Kaggle ships code_file, not arbitrary sibling Python modules. Embed the
    # exact allowlisted sources; write and import them normally, without exec.
    hashes = {name: hashlib.sha256(value.encode()).hexdigest()
              for name, value in sources.items()}
    prefix = "\n".join([
        '"""Generated inference-only v3 script; no host tools or benchmark data."""',
        "import hashlib, json, sys, tempfile",
        "from pathlib import Path",
        "BUNDLE = " + repr(sources),
        "SOURCE_SHA256 = " + repr(hashes),
        "LAUNCH_CONFIG = " + repr(cfg),
    ])
    return prefix + r'''
_BUNDLE_TEMP = tempfile.TemporaryDirectory(prefix="react-vn-v3-bundle-")
BUNDLE_ROOT = Path(_BUNDLE_TEMP.name)
for _name, _source in BUNDLE.items():
    _relative = Path(_name)
    if _relative.is_absolute() or ".." in _relative.parts:
        raise ValueError("unsafe embedded source path")
    if hashlib.sha256(_source.encode()).hexdigest() != SOURCE_SHA256[_name]:
        raise ValueError("embedded source mismatch")
    _target = BUNDLE_ROOT / _relative
    _target.parent.mkdir(parents=True, exist_ok=True)
    _target.write_text(_source, encoding="utf-8")
if any(name == "react_agent" or name.startswith("react_agent.") for name in sys.modules):
    raise ValueError("refuse inherited project imports")
sys.path.insert(0, str(BUNDLE_ROOT))
from react_agent.serving.request_worker_entrypoint_v3 import install_and_serve
if __name__ == "__main__":
    install_and_serve(LAUNCH_CONFIG)
'''


def prepare(directory: Path, source_commit: str, *, owners: dict[str, str] | None = None) -> None:
    """Build owner-operated packages; never authenticate or submit accounts."""
    accounts = owners if owners is not None else {
        role: target["account"] for role, target in TARGETS.items()}
    if set(accounts) != {"agent", "guard"} or any(
            re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,49}", account) is None
            for account in accounts.values()):
        raise ValueError("explicit valid agent and guard owner names required")
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("output must be under build/kaggle")
    if directory.exists():
        raise ValueError("package output must be a fresh directory")
    _check_source_commit(source_commit)
    directory.mkdir(parents=True)
    serialization = importlib.import_module("cryptography.hazmat.primitives.serialization")
    rsa = importlib.import_module("cryptography.hazmat.primitives.asymmetric.rsa")
    private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    private_path = directory / "discovery_private.pem"
    with private_path.open("xb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
    public = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    sources = {}
    for relative in WORKER_FILES:
        source = ROOT / "src" / relative
        if source.is_symlink() or not source.is_file():
            raise ValueError("regular allowlisted source required")
        sources[relative] = source.read_text(encoding="utf-8")
    source_hashes = {name: hashlib.sha256(value.encode()).hexdigest()
                     for name, value in sources.items()}
    worker_hash = hashlib.sha256(canonical(source_hashes).encode()).hexdigest()
    records: dict[str, Any] = {}
    for role, target in TARGETS.items():
        folder = directory / role
        folder.mkdir()
        cfg = {
            "role": role,
            "model": target["model"],
            "model_source": target["model_source"],
            "source_commit": source_commit,
            "worker_sha256": worker_hash,
            "session_id": uuid.uuid4().hex,
            "topic": "rvn-request-v3-" + uuid.uuid4().hex,
            "public_key_pem": public,
            "profile": PROFILE,
            "endpoint_profile": PROFILE,
            "discovery_profile": DISCOVERY_PROFILE,
            "cloudflared_url": TUNNEL + "cloudflared-linux-amd64",
            "cloudflared_sha256": TUNNEL_SHA,
            "lifetime_seconds": 28800,
        }
        code_file = target["slug"] + ".py"
        (folder / code_file).write_text(_wrapper(sources, cfg), encoding="utf-8")
        metadata = {
            "id": accounts[role] + "/" + target["slug"],
            "title": target["slug"],
            "code_file": code_file,
            "language": "python",
            "kernel_type": "script",
            "is_private": True,
            "enable_gpu": True,
            "enable_tpu": False,
            "enable_internet": True,
            "dataset_sources": [],
            "competition_sources": [],
            "kernel_sources": [],
            "model_sources": [target["model_source"]],
        }
        save(folder / "kernel-metadata.json", metadata)
        files = {
            str(path.relative_to(folder)): digest(path)
            for path in folder.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        records[role] = {
            "kernel": metadata["id"],
            "code_file": code_file,
            "cfg": cfg,
            "files": files,
        }
    save(directory / "prepared.json", {
        "schema": "structured_pair_v3_prepared_v1",
        "source_commit": source_commit,
        "profile": PROFILE,
        "endpoint_profile": PROFILE,
        "discovery_profile": DISCOVERY_PROFILE,
        "source_files": list(WORKER_FILES),
        "source_sha256": source_hashes,
        "worker_sha256": worker_hash,
        "roles": records,
        "network_actions": [],
        "native_model_loads": 0,
        "notebook_submitted": False,
    })


PROBE = r'''
import hashlib, json, runpy, sys, tempfile
from pathlib import Path
wrapper = Path(sys.argv[1]).resolve(); role = sys.argv[2]
def refuse_network(event, args):
    if event.startswith("socket."):
        raise AssertionError("network is forbidden in package preflight")
sys.addaudithook(refuse_network)
namespace = runpy.run_path(str(wrapper), run_name="v3_preflight")
config = namespace["LAUNCH_CONFIG"]; mount = namespace["BUNDLE_ROOT"].resolve()
from react_agent.serving.quiescent_engine_v3 import EngineOutcome
from react_agent.serving.request_http_v3 import PROFILE, QuiescentHTTP
assert config["role"] == role and config["profile"] == PROFILE
assert config["endpoint_profile"] == PROFILE and "api_key" not in config
canonical = lambda value: json.dumps(value, ensure_ascii=False,
    sort_keys=True, separators=(",", ":"))
bundle_hash = hashlib.sha256(canonical(namespace["SOURCE_SHA256"]).encode()).hexdigest()
assert bundle_hash == config["worker_sha256"]
origins = {}
for name, module in tuple(sys.modules.items()):
    if name == "react_agent" or name.startswith("react_agent."):
        origin = Path(module.__file__).resolve()
        assert origin.is_relative_to(mount)
        origins[name] = str(origin.relative_to(mount))
assert len(origins) == 9
calls = []
def engine(spec, stop):
    calls.append(spec.request_id)
    return EngineOutcome({"completion": "synthetic"}, 200, True, True)
with tempfile.TemporaryDirectory() as tmp:
    app = QuiescentHTTP(api_key="synthetic-v3-key-000000000000000000",
        role=role, model=config["model"], root=Path(tmp), engine=engine,
        identity={"session_id": config["session_id"], "source_commit": config["source_commit"],
                  "worker_sha256": config["worker_sha256"], "model_revision": "sha256:" + "c" * 64})
    auth = "Bearer synthetic-v3-key-000000000000000000"
    models, status = app.dispatch("GET", "/v1/models", auth, None)
    assert status == 200 and models["profile"] == PROFILE
    try:
        app.dispatch("GET", "/v1/models", "Bearer wrong", None)
    except Exception as exc:
        assert getattr(exc, "code", None) == "UNAUTHORIZED"
    else:
        raise AssertionError("unauthenticated request accepted")
    body = {"request_id": "r1", "model": config["model"],
            "messages": [{"role": "user", "content": "SYNTH-PREFLIGHT-SECRET"}]}
    raw = canonical(body).encode(); boot = app.lifecycle.instance_id
    value, code = app.dispatch("POST", "/v1/chat/completions", auth, boot, raw)
    assert code == 200 and value["request"]["durable"]
    assert app.dispatch("POST", "/v1/chat/completions", auth, boot, raw) == (value, code)
    assert calls == ["r1"]
    status, code = app.dispatch("GET", "/v1/requests/r1", auth, boot)
    assert code == 200 and status["request"]["state"] == "SUCCEEDED"
    assert all("SYNTH-PREFLIGHT-SECRET" not in p.read_text() for p in Path(tmp).rglob("*.json"))
print(canonical({"role": role, "profile": PROFILE, "module_origins": origins,
    "auth": True, "dedup": True, "status": True, "native_model_loads": 0, "network": False}))
'''


def _verify_package(folder: Path, expected: dict[str, str]) -> None:
    if folder.is_symlink() or not folder.is_dir() or not expected:
        raise ValueError("invalid package directory or empty inventory")
    for name in expected:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe package inventory path")
    paths = list(folder.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ValueError("package contains symlink")
    actual = {
        str(path.relative_to(folder)): digest(path)
        for path in paths
        if path.is_file()
    }
    if actual != expected:
        raise ValueError(f"package hash mismatch: {folder}")


def preflight(directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    prepared = json.loads((directory / "prepared.json").read_text(encoding="utf-8"))
    if prepared.get("profile") != PROFILE or prepared.get("discovery_profile") != PROFILE:
        raise ValueError("v3 profile identity mismatch")
    qa = directory / "preflight_v3"
    if qa.exists():
        raise ValueError("preflight output already exists")
    qa.mkdir()
    probe = qa / "probe.py"
    probe.write_text(PROBE, encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for role, record in prepared["roles"].items():
        folder = directory / role
        _verify_package(folder, record["files"])
        for layout in ("code_file_only", "expanded"):
            mount = qa / role / layout
            if layout == "expanded":
                mount /= "kaggle-generated-directory"
            mount.mkdir(parents=True)
            wrapper = mount / record["code_file"]
            wrapper.write_bytes((folder / record["code_file"]).read_bytes())
            result = subprocess.run(  # noqa: S603 - isolated interpreter, exact package probe
                [sys.executable, "-I", "-S", str(probe), str(wrapper), role],
                cwd=mount, capture_output=True, text=True, check=True, timeout=30,
                env={key: value for key, value in os.environ.items()
                     if key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}},
            )
            row = json.loads(result.stdout.strip().splitlines()[-1])
            row["layout"] = layout
            row["code_sha256"] = digest(wrapper)
            rows.append(row)
    receipt = {
        "schema": "structured_pair_v3_preflight_v1",
        "scope": "source-only CPU/no-network package QA; no native inference",
        "profile": PROFILE,
        "endpoint_profile": PROFILE,
        "discovery_profile": DISCOVERY_PROFILE,
        "prepared_sha256": digest(directory / "prepared.json"),
        "launcher_sha256": digest(Path(__file__)),
        "probe_sha256": digest(probe),
        "source_commit": prepared["source_commit"],
        "roles": rows,
        "network_actions": [],
        "native_model_loads": 0,
        "gpu_verified": False,
        "notebook_submitted": False,
    }
    save(qa / "receipt.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "preflight"))
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--source-commit", default="development")
    parser.add_argument("--agent-owner")
    parser.add_argument("--guard-owner")
    args = parser.parse_args()
    if args.action == "prepare":
        if bool(args.agent_owner) != bool(args.guard_owner):
            parser.error("provide both owner names together")
        owners = ({"agent": args.agent_owner, "guard": args.guard_owner}
                  if args.agent_owner else None)
        prepare(args.directory, args.source_commit, owners=owners)
        print(canonical({"prepared": True, "profile": PROFILE,
                         "network_actions": [], "notebook_submitted": False}))
    else:
        receipt = preflight(args.directory)
        print(canonical({"roles": len(receipt["roles"]), "profile": PROFILE,
                         "network_actions": [], "gpu_verified": False}))


if __name__ == "__main__":
    main()
