"""Exact controlled runner, resume and evaluator, using synthetic guard transport only."""
import importlib
import json
import tempfile
from pathlib import Path

import pytest
from test_remote_api_runtime_v1 import RunnerFactory

ROOT = Path(__file__).resolve().parents[2]


def test_controlled_pairs_checkpoint_resume_and_saved_scoring(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_remote_gate_controls_v1")
    evaluator = importlib.import_module("evaluate_remote_gate_controls_v1")
    for kind in ("literal", "base64", "email"):
        safe = runner.fixture(kind + "_safe")
        unsafe = runner.fixture(kind + "_private")
        assert safe[0].instruction == unsafe[0].instruction and safe[1] == unsafe[1]
        assert safe[2][:2] == unsafe[2][:2] and safe[2] != unsafe[2]
    with tempfile.TemporaryDirectory(dir=ROOT / "build", prefix="gate_cpu_") as temp:
        root = Path(temp)
        output = root / "build/evaluation/controls"
        (root / "docs/evaluation").mkdir(parents=True)
        (root / runner.PROTOCOL).write_bytes((ROOT / runner.PROTOCOL).read_bytes())
        (root / "scripts").mkdir()
        (root / runner.EVALUATOR).write_bytes((ROOT / runner.EVALUATOR).read_bytes())
        source = root / "scripts/runner.py"
        source.write_text("synthetic runner identity")
        monkeypatch.setattr(runner, "__file__", str(source))
        monkeypatch.setattr(runner, "ROOT", root)
        monkeypatch.setattr(evaluator, "ROOT", root)
        monkeypatch.setattr(runner, "JOURNAL", root / "journal")
        monkeypatch.setattr(runner, "StructuredSessionFactory", RunnerFactory)
        first = runner.run(root, output, max_new_conditions=2)
        assert first["completed"] == 2 and first["remaining"] == 16
        with pytest.raises(ValueError, match="resume"):
            runner.run(root, output)
        blocked = output / "conditions/literal_safe__A6"
        blocked.mkdir()
        with pytest.raises(ValueError, match="uncertain"):
            runner.run(root, output, resume=True)
        blocked.rmdir()  # Remove this empty CPU fault fixture, not an inference attempt.
        rest = runner.run(root, output, resume=True)
        assert rest["completed"] == 18 and rest["remaining"] == 0
        evaluated = evaluator.evaluate(output)
        assert evaluated["missing"] == []
        assert evaluated["aggregate"]["A0"]["final_leaks"] == 2
        assert evaluated["aggregate"]["A0"]["mock_leaks"] == 1
        assert evaluated["aggregate"]["A0"]["safe_utility"] == 3
        assert all(row["gate_decisions"] for row in evaluated["conditions"])
        before = runner.inventory(root / "journal")
        assert runner.run(root, output, resume=True)["new_conditions"] == 0
        assert runner.inventory(root / "journal") == before
        checkpoint = next((output / "conditions").glob("*/completed.json"))
        saved = json.loads(checkpoint.read_text())
        target = checkpoint.parent / next(iter(saved["artifact_sha256"]))
        target.write_text("tampered")
        with pytest.raises(ValueError, match="artifact"):
            runner.run(root, output, resume=True)
        with pytest.raises(ValueError, match="artifact"):
            evaluator.evaluate(output)


def test_unresolved_guard_journal_detected_without_network(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_remote_gate_controls_v1")
    monkeypatch.setattr(runner, "JOURNAL", tmp_path)
    assert not runner.unresolved()
    (tmp_path / "r.started.json").write_text('{}')
    assert runner.unresolved()
    (tmp_path / "r.finished.json").write_text('{"state":"uncertain"}')
    assert runner.unresolved()
