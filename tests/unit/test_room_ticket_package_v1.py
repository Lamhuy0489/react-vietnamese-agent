"""Keep the prospective room-ticket CPU worker's source closure public."""

import hashlib
import importlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def builder(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("prepare_phase5_room_ticket_package_v1")


def test_worker_closure_contains_adapter_but_no_authoring(builder):
    bundle = json.loads((builder.DATASET / "guard_bundle.json").read_text(encoding="utf-8"))
    files = builder.worker_files(bundle["source_sha256"])
    assert builder.SEEDS <= files.keys()
    assert "src/react_agent/validation/host_inventory_schema_v1.py" in files
    assert "src/react_agent/security_v1/public_field_ticket_policy_v2.py" in files
    assert "src/react_agent/llm/room_ticket_native_dispatch_v1.py" in files
    assert "src/react_agent/validation/room_ticket_native_release_v1.py" in files
    assert "src/react_agent/validation/room_ticket_run_manifest_v1.py" in files
    assert "scripts/run_phase5_room_ticket_native_v1.py" in files
    assert "scripts/run_phase5_room_prospective_native_v2.py" in files
    assert "src/react_agent/llm/room_control_native_dispatch_v1.py" in files
    assert "src/react_agent/security_v1/room_control_pair_runtime_v1.py" in files
    assert "src/react_agent/validation/room_control_native_release_v1.py" in files
    assert "src/react_agent/validation/room_control_pair_audit_v1.py" in files
    assert "src/react_agent/validation/room_prospective_run_manifest_v2.py" in files
    assert not any(name.startswith("src/react_agent/authoring/") for name in files)
    assert not any(
        name.startswith("data/") and name not in bundle["source_sha256"] for name in files
    )


@pytest.mark.parametrize(
    "injected",
    ["src/react_agent/authoring/benchmark.py", "data/unapproved/document.json", "../escape"],
)
def test_worker_closure_rejects_forbidden_paths(builder, monkeypatch: pytest.MonkeyPatch, injected):
    monkeypatch.setattr(builder, "dependency_closure", lambda *_: {injected})
    monkeypatch.setattr(builder, "PUBLIC", set())
    monkeypatch.setattr(builder, "SEEDS", set())
    with pytest.raises(ValueError):
        builder.worker_files({})


def test_committed_source_check_requires_exact_git_blob(builder, monkeypatch: pytest.MonkeyPatch):
    expected = hashlib.sha256(b"frozen").hexdigest()
    monkeypatch.setattr(builder.subprocess, "check_output", lambda *args, **kwargs: b"frozen")
    builder.committed_sources({"pyproject.toml": expected}, "a" * 40)
    monkeypatch.setattr(builder.subprocess, "check_output", lambda *args, **kwargs: b"dirty")
    with pytest.raises(ValueError, match="differs from committed source"):
        builder.committed_sources({"pyproject.toml": expected}, "a" * 40)

    def missing(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "git show")

    monkeypatch.setattr(builder.subprocess, "check_output", missing)
    with pytest.raises(ValueError, match="absent from committed source"):
        builder.committed_sources({"pyproject.toml": expected}, "a" * 40)
