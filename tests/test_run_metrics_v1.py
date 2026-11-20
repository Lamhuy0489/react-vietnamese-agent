import json
from pathlib import Path
from typing import Any

from react_agent.evaluation import run_metrics_v1 as m
from react_agent.security_v3.prompt_baselines import PromptBaselineBackend


class Fake:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate(self, messages: Any, config: Any) -> Any:
        self.calls.append({"usage": {"prompt_tokens": 10, "completion_tokens": 3},
                           "seconds": 0.5, "finish_reason": "stop"})


class TwoModel:
    """Wrapper with an auxiliary backend (like the sanitizer)."""

    def __init__(self, inner: Any, aux: Any) -> None:
        self._inner, self._sanitizer = inner, aux

    def generate(self, messages: Any, config: Any) -> Any:
        self._sanitizer.generate(messages, config)
        return self._inner.generate(messages, config)


def test_wrapper_forwarding_counts_calls_once() -> None:
    inner = Fake()
    wrapped = PromptBaselineBackend(inner, sandwich=True)  # forwards .calls via __getattr__
    assert [r for r, _ in m.recorded_backends(wrapped)] == ["agent"]


def test_call_window_roles_and_slice() -> None:
    agent, aux = Fake(), Fake()
    stack = TwoModel(agent, aux)
    stack.generate([], None)
    window = m.CallWindow(stack)
    window.open()
    stack.generate([], None)
    calls = window.close()
    assert {k: len(v) for k, v in calls.items()} == {"agent": 1, "sanitizer": 1}


def _event(step: int, event: str, ts: str, call: str | None = None, **data: Any) -> str:
    return json.dumps({"run_id": "r", "task_id": "t", "step": step, "event": event,
                       "timestamp": f"2026-11-15T10:00:{ts}Z", "call_id": call, "data": data})


def _sec(seq: int, event: str, **data: Any) -> str:
    return json.dumps({"schema_version": "security_trace_v1", "run_id": "r", "task_id": "t",
                       "step": 1, "sequence": seq, "event": event, "data_json": json.dumps(data)})


def test_execution_metrics_counts_denials_and_tokens(tmp_path: Path) -> None:
    ex = tmp_path / "execution"
    ex.mkdir()
    (ex / "trace_legacy.jsonl").write_text("\n".join([
        _event(0, "run_start", "00.000"),
        _event(1, "model_output", "01.000"),
        _event(1, "tool_call_proposed", "01.000", "c1", name="doc_search", arguments={}),
        _event(1, "tool_call_executed", "01.100", "c1"),
        _event(1, "tool_result", "01.300", "c1", ok=True),
        _event(2, "model_output", "02.000"),
        _event(3, "model_output", "03.000"),
        _event(3, "final_answer", "03.000", answer="x"),
        _event(3, "run_end", "03.000", status="completed")]) + "\n")
    (ex / "trace_security.jsonl").write_text("\n".join([
        _sec(1, "proposal", proposal_id="p1", action={"name": "doc_search"}),
        _sec(2, "decision", component="A1", stage="PRE", effect="ALLOW",
             proposal_id="p1", reasons=["PASS_THROUGH"]),
        _sec(3, "proposal", proposal_id="p2", action={"name": "send_email_mock"}),
        _sec(4, "decision", component="A1", stage="PRE", effect="DENY",
             proposal_id="p2", reasons=["CONFIRMATION_REQUIRED"]),
        _sec(5, "decision", component="A1", stage="FINAL", effect="REDACT",
             proposal_id=None, reasons=["FINAL_LEAK"])]) + "\n")
    calls = {"agent": [{"usage": {"prompt_tokens": 100, "completion_tokens": 20},
                        "seconds": 0.8, "finish_reason": "stop"}] * 4}
    out = m.execution_metrics(ex, calls, wall_seconds=3.5)
    assert out["agent_turns"] == 3 and out["defense_extra_llm_calls"] == 1
    assert out["llm_total"]["prompt_tokens"] == 400
    assert out["llm_total"]["completion_tokens"] == 80
    assert out["tool_calls"]["proposed_to_gate"] == 2
    assert out["tool_calls"]["sink_denied"] == 1
    assert out["gate"]["confirmation_required"] == 1 and out["gate"]["final_redacted"]
    assert out["seconds_split"]["tool"] == 0.2
    agg = m.aggregate([out, out])
    assert agg["total_tokens"]["mean"] == 480 and agg["executions_with_denial"] == 2
