"""Public runtime provenance schedule with offline synthetic proposals."""
import importlib
import json
import tempfile
from pathlib import Path

import pytest
from test_remote_api_runtime_v1 import REVISION, RunnerFactory

from react_agent.llm.base import ModelResponse

ROOT = Path(__file__).resolve().parents[2]


class Agent:
    model_id = "synthetic"
    model_revision = REVISION
    def __init__(self):
        self.attempts = 0
        self.calls = []
    def generate(self, messages, config):
        self.attempts += 1
        both = "rồi đọc" in messages[1]["content"]
        docs = ["DOC_APIPRIVATE", "DOC_APIPUBLIC"] if both else ["DOC_APIPUBLIC"]
        index = self.attempts - 1
        value = ({"action": {"name": "doc_read", "arguments": {"doc_id": docs[index]}}}
                 if index < len(docs) else
                 {"final_answer": {"answer": "Phòng tiếp nhận hồ sơ: F306."}})
        return ModelResponse(text=json.dumps(value), model_id=self.model_id,
                             model_revision=self.model_revision)


class Factory(RunnerFactory):
    def __call__(self):
        return Agent() if self.role == "agent" else super().__call__()


def test_twelve_cases_public_runtime_and_source_labels(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_remote_api_provenance_v1")
    with tempfile.TemporaryDirectory(dir=ROOT / "build", prefix="provenance_cpu_") as temp:
        root = Path(temp)
        (root / "data").symlink_to(ROOT / "data", target_is_directory=True)
        (root / "scripts").mkdir()
        source = root / "scripts/runner.py"
        source.write_text("synthetic identity")
        (root / "docs/evaluation").mkdir(parents=True)
        (root / "docs/evaluation/remote_api_provenance_v1_protocol.md").write_bytes(
            (ROOT / "docs/evaluation/remote_api_provenance_v1_protocol.md").read_bytes())
        monkeypatch.setattr(runner, "ROOT", root)
        monkeypatch.setattr(runner, "JOURNAL", root / "journal")
        monkeypatch.setattr(runner, "__file__", str(source))
        monkeypatch.setattr(runner, "StructuredSessionFactory", Factory)
        output = root / "build/evaluation/provenance"
        result = runner.run(root, output)
        assert result["completed_conditions"] == 12
        for row in result["conditions"]:
            saved = json.loads((output / f"{row['case']}__{row['level']}" /
                                "started.json").read_text())
            labels = {b["label"]["source_id"]: b["label"]["sensitivity"]
                      for b in saved["catalog"]["bindings"]}
            assert labels["DOC_APIPRIVATE"] == "S2"
            if row["case"] == "unknown_public":
                assert "DOC_APIPUBLIC" not in labels
            else:
                assert labels["DOC_APIPUBLIC"] == "S0"
            assert row["agent_attempts"] <= 4
            if row["level"] == "A0":
                assert row["guard_attempts"] == 0
        evaluator = importlib.import_module("evaluate_remote_api_provenance_v1")
        monkeypatch.setattr(evaluator, "ROOT", root)
        scored = evaluator.evaluate(output)
        assert len(scored["conditions"]) == 12 and not scored["missing"]
        a0 = [r for r in scored["conditions"] if r["level"] == "A0"]
        assert all(r["exact_public_utility"] for r in a0)
        assert all(r["required_read_order_covered"] for r in a0)
        assert not any(r["private_marker_leaked"] for r in scored["conditions"])
        checkpoint = output / "public_only__A0/completed.json"
        checkpoint.write_text("changed")
        with pytest.raises(ValueError, match="artifact mismatch"):
            evaluator.evaluate(output)
        with pytest.raises(ValueError, match="fresh"):
            runner.run(root, output)
