"""Exact paired runner checkpoint controls; CPU synthetic transport only."""
import importlib
import json
import tempfile
from pathlib import Path

import pytest
from test_remote_api_runtime_v1 import RunnerFactory

ROOT = Path(__file__).resolve().parents[2]


def test_public_pair_selection_and_checkpoint_resume(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_remote_api_paired_dev_v1")
    rows = runner.selected()
    assert len(rows) == 4 and {r.split for r in rows} == {"dev"}
    assert len({r.group_id for r in rows}) == 2
    with tempfile.TemporaryDirectory(dir=ROOT / "build", prefix="paired_cpu_") as temp:
        root = Path(temp)
        output = root / "build/evaluation/paired"
        monkeypatch.setattr(runner, "ROOT", root)
        monkeypatch.setattr(runner, "JOURNAL", root / "journal")
        source = root / "runner.py"
        source.write_text("synthetic runner identity")
        (root / "docs/evaluation").mkdir(parents=True)
        (root / "docs/evaluation/remote_api_paired_dev_v1_protocol.md").write_bytes(
            (ROOT / "docs/evaluation/remote_api_paired_dev_v1_protocol.md").read_bytes())
        (root / "scripts").mkdir()
        source = root / "scripts/runner.py"
        source.write_text("synthetic runner identity")
        (root / "scripts/evaluate_remote_api_paired_dev_v1.py").write_bytes(
            (ROOT / "scripts/evaluate_remote_api_paired_dev_v1.py").read_bytes())
        monkeypatch.setattr(runner, "__file__", str(source))
        monkeypatch.setattr(runner, "StructuredSessionFactory", RunnerFactory)
        first = runner.run(root, output, max_new_conditions=2)
        assert first["completed"] == 2 and first["remaining"] == 26
        with pytest.raises(ValueError, match="resume"):
            runner.run(root, output)
        rest = runner.run(root, output, resume=True)
        assert rest["completed"] == 28 and rest["remaining"] == 0
        before = {str(p): p.read_bytes() for p in (root / "journal").rglob("*.json")}
        done = runner.run(root, output, resume=True)
        assert done["new_conditions"] == 0
        assert before == {str(p): p.read_bytes() for p in (root / "journal").rglob("*.json")}
        checkpoint = next((output / "conditions").glob("*/completed.json"))
        saved = json.loads(checkpoint.read_text())
        target = checkpoint.parent / next(iter(saved["artifact_sha256"]))
        target.write_text("changed")
        with pytest.raises(ValueError, match="artifact changed"):
            runner.run(root, output, resume=True)


def test_uncertain_started_condition_never_retried(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_remote_api_paired_dev_v1")
    with tempfile.TemporaryDirectory(dir=ROOT / "build", prefix="paired_uncertain_") as temp:
        root = Path(temp)
        monkeypatch.setattr(runner, "ROOT", root)
        monkeypatch.setattr(runner, "JOURNAL", root / "journal")
        source = root / "runner.py"
        source.write_text("synthetic")
        (root / "docs/evaluation").mkdir(parents=True)
        (root / "docs/evaluation/remote_api_paired_dev_v1_protocol.md").write_bytes(
            (ROOT / "docs/evaluation/remote_api_paired_dev_v1_protocol.md").read_bytes())
        (root / "scripts").mkdir()
        source = root / "scripts/runner.py"
        source.write_text("synthetic runner identity")
        (root / "scripts/evaluate_remote_api_paired_dev_v1.py").write_bytes(
            (ROOT / "scripts/evaluate_remote_api_paired_dev_v1.py").read_bytes())
        monkeypatch.setattr(runner, "__file__", str(source))
        monkeypatch.setattr(runner, "StructuredSessionFactory", RunnerFactory)
        output = root / "build/evaluation/paired"
        runner.run(root, output, max_new_conditions=0)
        manifest = json.loads((output / "manifest.json").read_text())
        condition = output / "conditions" / manifest["schedule"][0]["key"]
        condition.mkdir()
        (condition / "started.json").write_text("{}")
        with pytest.raises(ValueError, match="uncertain"):
            runner.run(root, output, resume=True)
        assert not (root / "journal").exists()
