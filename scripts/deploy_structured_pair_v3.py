"""Submit one verified private pair and discover authenticated v3 connections."""

from __future__ import annotations

import argparse
import base64
import csv
import importlib
import io
import json
import os
import re
import shutil
import ssl
import subprocess
import tempfile
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from launch_structured_pair_v3 import (
    PROFILE,
    ROOT,
    _check_source_commit,
    _verify_package,
    canonical,
    digest,
    git,
    save,
)

from react_agent.llm.http_diagnostic_v1 import NoRedirect
from react_agent.llm.request_worker_transport_v1 import RequestWorkerHTTPS

CREDENTIALS = {"agent": "kaggle3.json", "guard": "kaggle1.json"}
ACCOUNTS = {"agent": "buiquocviet", "guard": "huylmhuhu"}


def kaggle(role: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="rvn-kaggle-v3-") as tmp:
        path = Path(tmp) / "kaggle.json"
        shutil.copy2(ROOT / "credential kaggle" / CREDENTIALS[role], path)
        path.chmod(0o600)
        account = json.loads(path.read_text()).get("username")
        if account != ACCOUNTS[role]:
            raise ValueError("credential account mismatch")
        cli_python = shutil.which("python3")
        if cli_python is None:
            raise ValueError("Python with Kaggle CLI required")
        return subprocess.run(  # noqa: S603 - fixed CLI, no shell; never print secrets
            [cli_python, "-m", "kaggle", *args],
            env={
                **{k: v for k, v in os.environ.items() if not k.startswith("KAGGLE_")},
                "KAGGLE_CONFIG_DIR": tmp,
            },
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )


def verify_model_access(role: str, model_source: str) -> None:
    """Require actual model-file access; public metadata alone is insufficient."""
    if not re.fullmatch(
        r"[a-z0-9_-]+/[a-z0-9_.-]+/transformers/[a-z0-9_.-]+/[1-9][0-9]*",
        model_source,
    ) or any(part in {".", ".."} for part in model_source.split("/")):
        raise ValueError("exact model version required")
    result = kaggle(role, ["models", "variations", "versions", "files", model_source,
                           "--page-size", "200", "--csv"])
    if result.returncode:
        raise ValueError(f"{role}: model file access unavailable; no submission made")
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    names = {row.get("name", "") for row in rows}
    if "config.json" not in names or not any(name.endswith(".safetensors") for name in names):
        raise ValueError(f"{role}: model file listing incomplete; no submission made")


def push(directory: Path) -> None:
    prepared = json.loads((directory / "prepared.json").read_text())
    commit = prepared["source_commit"]
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("immutable source commit required")
    _check_source_commit(commit)
    receipt = json.loads((directory / "preflight_v3/receipt.json").read_text())
    if (
        receipt.get("prepared_sha256") != digest(directory / "prepared.json")
        or receipt.get("launcher_sha256") != digest(ROOT / "scripts/launch_structured_pair_v3.py")
        or receipt.get("profile") != PROFILE
        or len(receipt.get("roles", [])) != 4
    ):
        raise ValueError("exact package preflight required")
    if not any(
        line.split()[0] == commit for line in git("ls-remote", "--heads", "origin").splitlines()
    ):
        raise ValueError("source freeze must be pushed before submission")
    for role, record in prepared["roles"].items():
        _verify_package(directory / role, record["files"])
        if not record["kernel"].startswith(ACCOUNTS[role] + "/"):
            raise ValueError("kernel account mismatch")
        metadata = json.loads((directory / role / "kernel-metadata.json").read_text())
        if metadata.get("is_private") is not True:
            raise ValueError("private notebook required")
        if (directory / f"{role}_submission_started.json").exists():
            raise ValueError("submission already attempted; inspect status, never auto-retry")
    for role, record in prepared["roles"].items():
        verify_model_access(role, record["cfg"]["model_source"])
    for role in prepared["roles"]:
        quota = kaggle(role, ["quota", "--csv"])
        if quota.returncode:
            raise ValueError("quota unavailable; no submission made")
        rows = list(csv.DictReader(io.StringIO(quota.stdout)))
        gpu = [row for row in rows if row.get("resource") == "GPU"]
        if len(gpu) != 1 or float(gpu[0]["remaining"].removesuffix("h")) <= 0:
            raise ValueError("GPU quota exhausted; no submission made")
    for role, record in prepared["roles"].items():
        save(
            directory / f"{role}_submission_started.json",
            {"kernel": record["kernel"], "source_commit": commit},
        )
        result = kaggle(
            role,
            [
                "kernels",
                "push",
                "-p",
                str(directory / role),
                "-t",
                "32400",
                "--accelerator",
                "NvidiaTeslaT4",
            ],
        )
        text = result.stdout + result.stderr
        match = re.search(r"Kernel version (\d+) successfully pushed", text)
        version = int(match.group(1)) if match else None
        save(
            directory / f"{role}_submission.json",
            {
                "kernel": record["kernel"],
                "returncode": result.returncode,
                "version": version,
                "source_commit": commit,
                "url": "https://www.kaggle.com/code/" + record["kernel"],
            },
        )
        if result.returncode or version is None:
            raise RuntimeError(
                "submission uncertain; inspect read-only before any further submission"
            )
        print(canonical({"role": role, "kernel": record["kernel"], "version": version}), flush=True)


def _fetch(url: str, headers: dict[str, str] | None = None) -> bytes:
    context = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
    request = urllib.request.Request(url, headers=headers or {})  # noqa: S310 - fixed discovery or validated tunnel
    with opener.open(request, timeout=20) as response:
        raw = response.read(262145)
    if len(raw) > 262144:
        raise ValueError("discovery response too large")
    return bytes(raw)


def validate_connection(connection: dict[str, Any], cfg: dict[str, Any]) -> None:
    if (
        set(connection) != {"endpoint", "api_key", "session_id", "profile"}
        or connection.get("session_id") != cfg["session_id"]
        or connection.get("profile") != PROFILE
        or not re.fullmatch(r"https://[a-z0-9-]+\.trycloudflare\.com/v1", connection["endpoint"])
        or not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", connection["api_key"])
    ):
        raise ValueError("discovery identity or endpoint mismatch")


def discover(directory: Path) -> bool:
    prepared = json.loads((directory / "prepared.json").read_text())
    serialization = importlib.import_module("cryptography.hazmat.primitives.serialization")
    padding = importlib.import_module("cryptography.hazmat.primitives.asymmetric.padding")
    hashes = importlib.import_module("cryptography.hazmat.primitives.hashes")
    private = serialization.load_pem_private_key(
        (directory / "discovery_private.pem").read_bytes(), None
    )
    rows = []
    for role, record in prepared["roles"].items():
        cfg = record["cfg"]
        path = directory / f"{role}_connection.json"
        if path.exists():
            connection = json.loads(path.read_text())
        else:
            connection = None
            raw = _fetch("https://ntfy.sh/" + cfg["topic"] + "/json?poll=1&since=all")
            for line in raw.decode().splitlines():
                event = json.loads(line)
                if event.get("event") != "message":
                    continue
                packet = json.loads(event["message"])
                if (
                    packet.get("session_id") != cfg["session_id"]
                    or packet.get("profile") != PROFILE
                ):
                    continue
                decoded = private.decrypt(
                    base64.b64decode(packet["ciphertext"], validate=True),
                    padding.OAEP(
                        mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None
                    ),
                )
                value = json.loads(decoded)
                validate_connection(value, cfg)
                if connection is not None and connection != value:
                    raise ValueError("multiple connection identities for one session")
                connection = value
            if connection is None:
                print(canonical({"role": role, "status": "waiting_discovery"}), flush=True)
                continue
            save(path, connection, secret=True)
        validate_connection(connection, cfg)
        metadata = json.loads(
            _fetch(
                connection["endpoint"] + "/models",
                {"Authorization": "Bearer " + connection["api_key"]},
            )
        )
        identity = metadata.get("identity", {})
        expected = {
            "role": role,
            "model_id": cfg["model"],
            "session_id": cfg["session_id"],
            "source_commit": cfg["source_commit"],
            "worker_sha256": cfg["worker_sha256"],
        }
        revision = identity.get("model_revision", "")
        if any(identity.get(k) != v for k, v in expected.items()) or not re.fullmatch(
            r"sha256:[a-f0-9]{64}", revision
        ):
            raise ValueError("live source/model identity mismatch")
        transport = RequestWorkerHTTPS(
            connection["endpoint"],
            connection["api_key"],
            {**expected, "model_revision": revision},
            timeout=20,
        )
        verified = transport.probe()
        if verified != metadata:
            raise ValueError("worker changed during discovery")
        target = directory / f"{role}_live_metadata.json"
        if target.exists():
            if json.loads(target.read_text()) != metadata:
                raise ValueError("recorded worker boot changed")
        else:
            save(target, metadata)
        rows.append(
            {
                "id": cfg["model"],
                "role": role,
                **connection,
                "model_revision": revision,
                "source_commit": cfg["source_commit"],
                "worker_sha256": cfg["worker_sha256"],
                "kernel_id": record["kernel"],
            }
        )
        print(canonical({"role": role, "status": "READY", "identity": identity}), flush=True)
    if len(rows) != 2:
        return False
    target = directory / "pair_endpoints.json"
    value = {"profile": PROFILE, "models": rows}
    if target.exists():
        if json.loads(target.read_text()) != value:
            raise ValueError("connection configuration changed")
    else:
        save(target, value, secret=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("push", "discover", "status", "quota"))
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="new read-only status/quota audit JSON")
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not directory.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("build/kaggle directory required")
    if args.action == "push":
        push(directory)
    elif args.action == "discover":
        discover(directory)
    else:
        prepared = json.loads((directory / "prepared.json").read_text())
        records = []
        for role, record in prepared["roles"].items():
            result = kaggle(
                role,
                ["quota", "--csv"]
                if args.action == "quota"
                else ["kernels", "status", record["kernel"]],
            )
            # Do not expose arbitrary CLI failures; credentials may occur in exception text.
            row = {
                "role": role,
                "kernel": record["kernel"],
                "returncode": result.returncode,
                "output": result.stdout.strip() if result.returncode == 0 else "unavailable",
            }
            records.append(row)
            print(canonical(row))
        if args.output:
            save(
                args.output,
                {
                    "action": args.action,
                    "utc": datetime.now(UTC).isoformat(),
                    "records": records,
                    "inference_requests": 0,
                },
            )
        if any(row["returncode"] != 0 for row in records):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
