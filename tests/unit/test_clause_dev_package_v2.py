"""V2 package and launcher select the corrected native route only."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(relative):
    spec = importlib.util.spec_from_file_location("candidate_v2", ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_builder_has_new_identity_and_both_routes(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    builder = load("scripts/prepare_phase5_clause_dev_package_v2.py")
    assert builder.TEMPLATE == "notebooks/kaggle/clause_dev32_kernel_v2.py"
    assert builder.BUILDER == "scripts/prepare_phase5_clause_dev_package_v2.py"
    assert "scripts/run_phase5_clause_dev_native_v2.py" in builder.ENTRYPOINTS
    assert "scripts/run_phase5_clause_dev_native_v1.py" in builder.ENTRYPOINTS
    assert "src/react_agent/llm/clause_dev_dispatch_v2.py" in builder.ENTRYPOINTS
    assert builder.BUNDLE_SHA == "b14976413b72898b6c0c1b8c46c1ebb0f62f63633f647ab2064fbc048262240f"


def test_v2_launcher_rejects_development_and_routes_native(tmp_path):
    worker = load("notebooks/kaggle/clause_dev32_kernel_v2.py")
    worker.SOURCE_MODE = "working_tree"
    worker.SOURCE_COMMIT = "a" * 40
    with pytest.raises(ValueError, match="committed release"):
        worker.main()
    worker.SOURCE_MODE = "committed"
    mount = tmp_path / "input/qwen2.5/transformers/7b-instruct/1"
    mount.mkdir(parents=True)
    (mount / "config.json").write_text("{}")
    output = tmp_path / "output"
    output.mkdir()
    calls = []
    worker.native_payload(
        SimpleNamespace(run=lambda *args: calls.append(args)),
        Path("python"),
        Path("project"),
        None,
        Path("guard"),
        Path("snapshot"),
        output,
        tmp_path / "input",
    )
    assert len(calls) == 17
    assert all(
        calls[1 + 2 * shard][4] == "scripts/run_phase5_clause_dev_native_v2.py"
        for shard in range(8)
    )
    assert all(
        calls[2 + 2 * shard][4] == "scripts/audit_phase5_clause_dev_native_v1.py"
        for shard in range(8)
    )
