"""Native-capable adapter exercised through explicit synthetic CPU transport."""

import json
import shutil
from pathlib import Path

import pytest

from react_agent.security_v1.doc_read_pair_runtime_v1 import run_synthetic_pair_task
from react_agent.validation.doc_read_final_controls_v1 import approval, specimen
from react_agent.validation.doc_read_pair_audit_v1 import audit_join

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module", params=["s2_collision", "private_final", "duplicate_public"])
def source(request, tmp_path_factory):
    approved = approval()
    root = tmp_path_factory.mktemp("doc_pair") / request.param
    task, kwargs = specimen(ROOT, root, request.param)
    result = run_synthetic_pair_task(task, approval=approved,
                                     expected_approval_sha256=approved.identity, **kwargs)
    assert result.result.status == "completed"
    return root


def joined(root):
    return audit_join(root / "execution", root / "native/guard_response_diagnostics.jsonl",
                      root / "witness.jsonl", approval=approval(),
                      expected_approval_sha256=approval().identity)


def test_full_pair_final_and_broker_join(source):
    result = joined(source)
    assert result["valid"] is True
    assert joined(source) == result


@pytest.mark.parametrize("fault", ["result_content", "executed", "call_id", "order", "step"])
def test_broker_corruption_rejected(source, tmp_path, fault):
    root = tmp_path / "copy"
    shutil.copytree(source, root)
    path = root / "execution/runtime/trace_legacy.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    result = next(row for row in rows if row["event"] == "tool_result")
    if fault == "result_content":
        result["data"]["content"]["content"] = "tampered"
    elif fault == "call_id":
        result["call_id"] = "call_fake"
    elif fault == "step":
        next(row for row in rows if row["event"] == "tool_call_executed")["step"] += 1
    elif fault == "order":
        i = next(i for i, row in enumerate(rows) if row["event"] == "tool_call_executed")
        j = rows.index(result)
        rows[i], rows[j] = rows[j], rows[i]
    else:
        rows = [row for row in rows if row["event"] != "tool_call_executed"]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError):
        joined(root)
