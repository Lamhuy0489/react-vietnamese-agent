"""Synthetic release-metadata negatives; these tests never contact Kaggle."""

import importlib
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from react_agent.validation.guard_probe_audit_v2 import digest


@pytest.fixture
def release(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("audit_phase5_shutdown_runtime_gpu")


@pytest.fixture
def remote(tmp_path: Path, release: ModuleType) -> Path:
    root = tmp_path / "remote"
    root.mkdir()
    (root / "worker.py").write_text("# synthetic source, no inference\n")
    (root / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": release.KERNEL_ID,
                "code_file": "worker.py",
                "is_private": True,
                "enable_gpu": True,
                "enable_tpu": False,
                "enable_internet": False,
                "machine_shape": "NvidiaTeslaT4",
                "docker_image": release.IMAGE,
                "dataset_sources": [release.DATASET],
                "kernel_sources": [],
                "competition_sources": [],
                "model_sources": [release.AGENT_HANDLE],
            }
        )
    )
    return root


def test_remote_repeatable_and_readonly(release: ModuleType, remote: Path) -> None:
    before = release.inventory(remote)
    receipt = {"wrapper_sha256": digest(remote / "worker.py")}
    first = release.remote_identity(remote, receipt)
    assert release.remote_identity(remote, receipt) == first
    assert release.inventory(remote) == before


@pytest.mark.parametrize(
    "key,value",
    [
        ("id", "different/worker"),
        ("is_private", False),
        ("enable_internet", True),
        ("machine_shape", "Gpu"),
        ("docker_image", "latest"),
        ("dataset_sources", []),
        ("model_sources", []),
        ("code_file", "../worker.py"),
    ],
)
def test_metadata_mutations_rejected(
    release: ModuleType, remote: Path, key: str, value: object
) -> None:
    metadata = remote / "kernel-metadata.json"
    data = json.loads(metadata.read_text())
    data[key] = value
    metadata.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        release.remote_identity(remote, {"wrapper_sha256": digest(remote / "worker.py")})


@pytest.mark.parametrize("mutation", ["hash", "extra", "symlink"])
def test_source_mutations_rejected(release: ModuleType, remote: Path, mutation: str) -> None:
    receipt = {"wrapper_sha256": digest(remote / "worker.py")}
    if mutation == "hash":
        (remote / "worker.py").write_text("# altered source\n")
    elif mutation == "extra":
        (remote / "unexpected.json").write_text("{}")
    else:
        (remote / "linked.py").symlink_to(remote / "worker.py")
    with pytest.raises(ValueError):
        release.remote_identity(remote, receipt)


def test_cli_refuses_output_inside_raw_before_audit(
    release: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "audit",
            "--raw",
            str(raw),
            "--remote",
            str(tmp_path / "remote"),
            "--preflight",
            str(tmp_path / "preflight.json"),
            "--output",
            str(raw / "audit.json"),
        ],
    )
    with pytest.raises(ValueError, match="fresh independent"):
        release.main()
    assert list(raw.iterdir()) == []
