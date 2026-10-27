"""Exercise checkpoint/resume and saved scoring with synthetic transport only."""
import importlib
import json
import tempfile
from pathlib import Path

import pytest
from test_remote_api_runtime_v1 import RunnerFactory

ROOT = Path(__file__).resolve().parents[2]


def test_mainline_runner_resume_and_saved_scoring(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_phase5_mainline")
    evaluator = importlib.import_module("evaluate_phase5_mainline")
    with tempfile.TemporaryDirectory(dir=ROOT / "build/evaluation", prefix="mainline_cpu_") as temp:
        root = Path(temp)
        monkeypatch.setattr(runner, "StructuredSessionFactory", RunnerFactory)
        monkeypatch.setattr(runner, "JOURNAL", root / "journal")
        monkeypatch.setattr(runner, "unresolved", lambda: False)
        output = root / "run"
        assert runner.run(root, output, max_new_conditions=0)["remaining"] == 14
        assert not (root / "journal").exists()
        assert runner.run(root, output, resume=True, max_new_conditions=1)["completed"] == 1
        assert runner.run(root, output, resume=True)["completed"] == 14
        before = runner.inventory(root / "journal")
        assert runner.run(root, output, resume=True)["new_conditions"] == 0
        assert runner.inventory(root / "journal") == before
        first = evaluator.evaluate(output)
        assert first == evaluator.evaluate(output)
        assert first["missing"] == []
        assert len(first["conditions"]) == 14
        assert all(r["agent_api_attempts"] == 2 for r in first["conditions"])
        # Synthetic calculator outputs cannot pass these document/email tasks.
        assert all(r["safe_utility"] == 0 for r in first["aggregate"].values())
        checkpoint = next((output / "conditions").glob("*/completed.json"))
        original = checkpoint.read_bytes()
        saved = json.loads(original)
        checkpoint.write_text(json.dumps({**saved, "final_answer": "tampered"}))
        with pytest.raises(ValueError, match="checkpoint"):
            evaluator.evaluate(output)
        with pytest.raises(ValueError, match="checkpoint"):
            runner.run(root, output, resume=True)
        checkpoint.write_bytes(original)
        trace = checkpoint.parent / "execution/trace_legacy.jsonl"
        trace.write_text("changed")
        with pytest.raises(ValueError, match="artifact"):
            evaluator.evaluate(output)
