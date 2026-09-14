"""New package check on actual synthetic runtime output; no native models."""

import importlib
import json
from pathlib import Path

import pytest

from react_agent.llm.document_runtime_probe_v1 import inventory, run
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver

ROOT = Path(__file__).resolve().parents[2]


def test_checkpoint_check_is_readonly_and_rejects_identity(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    check = importlib.import_module("check_phase5_document_package")
    probe = tmp_path / "probe"
    run(
        probe,
        ROOT / "data/clean/v1_1/environment",
        backend="stub",
        commit="a" * 40,
        observer_factory=SyntheticPairObserver,
    )
    before = inventory(probe)
    first = check.audit(probe)
    assert first == check.audit(probe)
    assert first["levels"] == 7 and first["native_model_loads"] == 0
    assert first["native_factory_lazy_verified"] and not first["phase5_accepted"]
    assert all(c["path_covered"] for c in first["path_coverage"].values())
    assert all(c["successful_document_reads"] == 1 for c in first["path_coverage"].values())
    original = Path.read_text
    identity_path = probe / "identity.json"
    value = json.loads(identity_path.read_text())

    def read(path, *args, **kwargs):
        return json.dumps(value) if path == identity_path else original(path, *args, **kwargs)

    for key, bad in [
        ("protocol", "security_runtime_probe_v1"),
        ("security_runtime_version", "security_runtime_v7"),
        ("source_catalog", {"bindings": []}),
    ]:
        value = json.loads(identity_path.read_text())
        value[key] = bad
        with monkeypatch.context() as patch:
            patch.setattr(Path, "read_text", read)
            with pytest.raises(ValueError, match="identity"):
                check.audit(probe)
    run(
        probe,
        ROOT / "data/clean/v1_1/environment",
        backend="stub",
        commit="a" * 40,
        observer_factory=SyntheticPairObserver,
        resume=True,
    )
    assert inventory(probe) == before
