"""Coverage does not promote guessed answers, blocked proposals or cached guards."""

import json

import pytest

from react_agent.validation.document_runtime_probe_audit_v1 import path_coverage


@pytest.mark.parametrize(
    "fault", [None, "zero_tool", "tool_error", "wrong_doc", "cached", "guard_error", "missing_post"]
)
def test_coverage_conditions(tmp_path, fault):
    root = tmp_path / "A6"
    runtime = root / "execution/runtime"
    runtime.mkdir(parents=True)
    (runtime / "run_metadata.json").write_text(
        json.dumps(
            {"result": {"final_answer": "Lab Mạng ở D305."}, "guard_execution_attempt_count": 2}
        )
    )
    doc = "CDOC_999" if fault == "wrong_doc" else "CDOC_034"
    rows = [
        {
            "event": "tool_call_proposed",
            "call_id": "c1",
            "data": {"name": "doc_read", "arguments": {"doc_id": doc}},
        },
        {"event": "tool_call_executed", "call_id": "c1", "data": {}},
        {
            "event": "tool_result",
            "call_id": "c1",
            "data": {"ok": fault != "tool_error", "content": {"doc_id": doc}},
        },
    ]
    if fault == "zero_tool":
        rows = rows[:1]
    (runtime / "trace_legacy.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    guards = [
        {
            "stage": stage,
            "outcome": {
                "status": "ERROR" if fault == "guard_error" else "OK",
                "cache_hit": fault == "cached",
            },
            "execution_attempts": [{"status": "ERROR" if fault == "guard_error" else "OK"}],
        }
        for stage in (["PRE"] if fault == "missing_post" else ["PRE", "POST"])
    ]
    (runtime / "trace_guard.jsonl").write_text("\n".join(json.dumps(g) for g in guards))
    before = {p.name: p.read_bytes() for p in runtime.iterdir()}
    result = path_coverage(root)
    assert result["path_covered"] is (fault is None)
    assert not result["semantic_quality_scored"]
    assert before == {p.name: p.read_bytes() for p in runtime.iterdir()}
