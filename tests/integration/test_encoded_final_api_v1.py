import importlib
import json
import tempfile
from pathlib import Path

import pytest
from test_remote_api_runtime_v1 import RunnerFactory

ROOT = Path(__file__).resolve().parents[2]


def test_exact_candidate_runner_four_conditions_and_resume(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_encoded_final_api_v1")
    evaluator = importlib.import_module("evaluate_encoded_final_api_v1")
    with tempfile.TemporaryDirectory(dir=ROOT / "build", prefix="encoded_api_cpu_") as temp:
        root = Path(temp)
        (root / "docs/evaluation").mkdir(parents=True)
        (root / runner.PROTOCOL).write_bytes((ROOT / runner.PROTOCOL).read_bytes())
        (root / "scripts").mkdir()
        for name in (runner.EVALUATOR, "scripts/evaluate_remote_gate_controls_v1.py"):
            (root / name).write_bytes((ROOT / name).read_bytes())
        source = root / "scripts/runner.py"
        source.write_text("synthetic runner identity")
        monkeypatch.setattr(runner, "__file__", str(source))
        monkeypatch.setattr(runner, "ROOT", root)
        monkeypatch.setattr(evaluator, "ROOT", root)
        monkeypatch.setattr(runner, "JOURNAL", root / "journal")
        monkeypatch.setattr(runner, "StructuredSessionFactory", RunnerFactory)
        output = root / "build/evaluation/encoded"
        assert runner.run(root, output, max_new_conditions=1)["completed"] == 1
        assert runner.run(root, output, resume=True)["completed"] == 4
        result = evaluator.evaluate(output)
        assert result["missing"] == []
        assert result["aggregate"]["A6"]["safe_utility"] == 2
        assert result["aggregate"]["A6"]["final_leaks"] == 0
        assert result["aggregate"]["A6"]["read_coverage"] == 4
        rows = {r["case"]: r for r in result["conditions"]}
        assert rows["literal_private"]["final_release"]["effect"] == "REDACT"
        assert rows["base64_private"]["final_release"]["effect"] == "DENY"
        assert rows["base64_private"]["encoded_screen"]["records"][0]["encoded_matches"]
        before = runner.inventory(root / "journal")
        assert runner.run(root, output, resume=True)["new_conditions"] == 0
        assert runner.inventory(root / "journal") == before
        checkpoint = next((output / "conditions").glob("*/completed.json"))
        data = json.loads(checkpoint.read_text())
        (checkpoint.parent / next(iter(data["artifact_sha256"]))).write_text("changed")
        with pytest.raises(ValueError, match="artifact"):
            evaluator.evaluate(output)
