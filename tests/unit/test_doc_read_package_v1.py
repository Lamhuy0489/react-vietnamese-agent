"""Exact public closure; host experiment controls must never reach the worker."""

import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def builder(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("prepare_phase5_doc_read_package_v1")


def test_native_worker_closure(builder):
    bundle = json.loads((builder.DATASET / "guard_bundle.json").read_text())
    files = builder.worker_files(bundle["source_sha256"])
    assert builder.SEEDS <= files.keys()
    assert "src/react_agent/validation/doc_read_final_runtime_audit_v1.py" in files
    assert "src/react_agent/security_v1/value_origin_v4.py" in files
    assert not any("doc_read_final_controls" in n or "authoring/" in n for n in files)
    assert not any(n.startswith("data/") and n not in bundle["source_sha256"] for n in files)


@pytest.mark.parametrize("injected", [
    "src/react_agent/authoring/benchmark.py",
    "src/react_agent/validation/doc_read_final_controls_v1.py",
    "data/dev/unapproved.json", "data/prospective/unapproved.json", "../escape",
])
def test_rejects_host_data(builder, monkeypatch, injected):
    monkeypatch.setattr(builder, "dependency_closure", lambda *_: {injected})
    monkeypatch.setattr(builder, "PUBLIC", set())
    monkeypatch.setattr(builder, "SEEDS", set())
    with pytest.raises(ValueError):
        builder.worker_files({})
