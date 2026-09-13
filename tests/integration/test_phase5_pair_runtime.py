from __future__ import annotations

import json
import multiprocessing
import os
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.foundation.runtime_qa import action_response, final_response
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.pair_runtime_v1 import run_pair_task
from react_agent.security_v1.runtime_v7 import SecurityRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.tools.factory import build_smoke_registry
from react_agent.validation.pair_runtime_audit_v1 import audit_task

ROOT = Path(__file__).resolve().parents[2]
SAFE = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'
ACTION = action_response(Action(name="calculator", arguments={"expression": "1+1"}))
DEFAULT_RESPONSES = (ACTION, final_response("Public summary"))


@dataclass(frozen=True)
class Factory:
    role: str
    responses: tuple[str, ...]
    failure: str = ""

    def __call__(self):
        if self.failure == "load":
            raise RuntimeError("synthetic load error")
        return Backend(self.role, self.responses, self.failure)


class Backend:
    def __init__(self, role, responses, failure):
        self.model_id, self.model_revision = role, "synthetic_v1"
        self.responses, self.failure, self.calls = responses, failure, 0

    def generate(self, messages, config):
        if self.failure == "timeout":
            time.sleep(5)
        text = self.responses[self.calls]  # Exhaustion exercises process backend failure.
        self.calls += 1
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)


def registry():
    return build_smoke_registry(ROOT / "data/smoke")


def invoke(
    path,
    level="A6",
    responses=DEFAULT_RESPONSES,
    agent_failure="",
    guard_failure="",
    guard_responses=(SAFE,) * 16,
    max_steps=2,
    registry_factory=registry,
    instruction="Calculate one plus one",
    catalog=None,
):
    config = PairConfig(
        ModelIdentity("agent", "synthetic_v1"),
        ModelIdentity("guard", "synthetic_v1"),
        agent_start_seconds=10,
        guard_start_seconds=10,
        agent_call_seconds=0.2 if agent_failure == "timeout" else 5,
        guard_call_seconds=0.2 if guard_failure == "timeout" else 5,
    )
    agent = Factory("agent", responses, agent_failure)
    pair = (
        ModelPair(agent, Factory("guard", guard_responses, guard_failure), config)
        if int(level[1:]) >= 2
        else None
    )
    arguments = (
        {"pair": pair}
        if pair
        else {
            "agent_factory": agent,
            "agent_execution": WarmGuardConfig("agent", "synthetic_v1", 10),
        }
    )
    return run_pair_task(
        PublicWorkbenchTask(task_id="awb_pair", instruction=instruction),
        output=path,
        registry_factory=registry_factory,
        security=configuration(level),
        runtime_config=RuntimeConfig(max_steps=max_steps, max_format_retries_per_step=0),
        generation=GenerationConfig(),
        source_catalog=catalog or SourceCatalog(),
        **arguments,
    )


def check_cleanup(path, level):
    assert audit_task(path)["valid"]
    receipt = json.loads((path / "pair_runtime.json").read_text())
    workers = receipt["snapshot"]["workers"]
    assert set(workers) == ({"agent", "guard"} if int(level[1:]) >= 2 else {"agent"})
    live = {child.pid for child in multiprocessing.active_children()}
    for worker in workers.values():
        assert worker["closed"] and not worker["handle_pending"]
        assert all(row["reaped"] for row in worker["lifecycle"])
        assert all(row.get("pid") not in live for row in worker["attempts"])
    assert receipt["owner_pid"] == os.getpid()
    assert receipt["cleanup_error_class"] is None
    return receipt


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5", "A6"])
@pytest.mark.parametrize("terminal", ["completed", "parse_failure", "max_steps", "model_error"])
def test_real_spawn_pair_all_levels_terminals_and_cleanup(tmp_path, level, terminal):
    responses = (
        (ACTION, final_response("Public summary"))
        if terminal == "completed"
        else ((ACTION, "invalid") if terminal == "parse_failure" else (ACTION,))
    )
    result = invoke(
        tmp_path / "run", level, responses, max_steps=1 if terminal == "max_steps" else 2
    )
    assert result.result.status == terminal
    receipt = check_cleanup(tmp_path / "run", level)
    metadata = json.loads((tmp_path / "run/runtime/run_metadata.json").read_text())
    workers = receipt["snapshot"]["workers"]
    assert len(workers["agent"]["attempts"]) == 1 + result.control.model_turn_count
    if "guard" in workers:
        assert metadata["guard_execution_attempt_count"] == len(workers["guard"]["attempts"]) - 1
        pids = {row["pid"] for worker in workers.values() for row in worker["attempts"]}
        assert len(pids) == 2
        assert os.getpid() not in pids
    else:
        assert metadata["guard_execution_attempt_count"] == 0
        assert metadata["guard_execution"] is None


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5", "A6"])
def test_observable_parity_with_v7(tmp_path, level):
    responses = (ACTION, final_response("Public summary"))
    spawned = invoke(tmp_path / "spawned", level, responses)
    guard_kwargs = (
        {}
        if int(level[1:]) < 2
        else {
            "guard_factory": Factory("guard", (SAFE,) * 16),
            "guard_execution": WarmGuardConfig("guard", "synthetic_v1", 10),
        }
    )
    baseline = SecurityRuntime(
        Backend("agent", responses, ""),
        registry(),
        runtime_config=RuntimeConfig(max_steps=2, max_format_retries_per_step=0),
    ).run_instrumented(
        PublicWorkbenchTask(task_id="awb_pair", instruction="Calculate one plus one"),
        output=tmp_path / "baseline",
        security_config=configuration(level),
        **guard_kwargs,
    )
    assert spawned.result.model_dump(exclude={"run_id"}) == baseline.result.model_dump(
        exclude={"run_id"}
    )
    assert [b.model_messages() for b in spawned.contexts] == [
        b.model_messages() for b in baseline.contexts
    ]
    observations = []
    for path in [
        tmp_path / "spawned/runtime/trace_legacy.jsonl",
        tmp_path / "baseline/trace_legacy.jsonl",
    ]:
        observations.append(
            [
                {k: v for k, v in json.loads(line).items() if k not in {"timestamp", "run_id"}}
                for line in path.read_text().splitlines()
            ]
        )
    assert observations[0] == observations[1]


@pytest.mark.parametrize("failure", ["load", "timeout"])
@pytest.mark.parametrize("role", ["agent", "guard"])
def test_startup_and_inference_failures_keep_cleanup_evidence(tmp_path, failure, role):
    kwargs = {role + "_failure": failure}
    if failure == "load":
        with pytest.raises(RuntimeError):
            invoke(tmp_path / "run", **kwargs)
    else:
        result = invoke(tmp_path / "run", **kwargs)
        assert result.result.status == "model_error"
    check_cleanup(tmp_path / "run", "A6")


def test_cancellation_between_startup_and_runtime_reaps_both_workers(tmp_path):
    def cancel():
        raise KeyboardInterrupt("synthetic cancellation")

    with pytest.raises(KeyboardInterrupt):
        invoke(tmp_path / "run", registry_factory=cancel)
    receipt = check_cleanup(tmp_path / "run", "A6")
    assert receipt["error_class"] == "KeyboardInterrupt"


def test_invalid_guard_output_retires_pair_and_discards_cache(tmp_path):
    result = invoke(tmp_path / "run", guard_responses=("invalid",))
    assert result.result.status == "model_error"
    check_cleanup(tmp_path / "run", "A6")


def test_existing_output_rejected_before_worker_start(tmp_path):
    with pytest.raises(ValueError, match="fresh output"):
        invoke(tmp_path)
    assert not (tmp_path / "pair_runtime.json").exists()


@pytest.mark.parametrize("entitled", [True, False])
def test_pair_retains_final_entitlement_on_actual_database_rows(tmp_path, entitled):
    action = Action(name="db_query", arguments={"query": "SELECT student_id FROM scholarships"})
    catalog = SourceCatalog(
        bindings=(
            SourceBinding(
                tool="db_query",
                arguments_json=canonical_json(action.arguments),
                label=SourceLabel(
                    source_type=SourceType.DATABASE,
                    source_id="scholarships",
                    sensitivity=Sensitivity.CONFIDENTIAL,
                    trust=Trust.TRUSTED,
                ),
            ),
        )
    )
    instruction = "Read table scholarships column student_id"
    if entitled:
        instruction += "; Show student ID from table scholarships"
    result = invoke(
        tmp_path / "run",
        responses=(action_response(action), final_response("SV_SYN_001")),
        instruction=instruction,
        catalog=catalog,
    )
    assert result.result.final_answer == ("SV_SYN_001" if entitled else "[REDACTED]")
    assert result.control.tool_call_count == 1
    check_cleanup(tmp_path / "run", "A6")


@pytest.mark.parametrize("level", ["A4", "A5", "A6"])
def test_pair_retains_scope_denial_before_broker(tmp_path, level):
    action = Action(name="doc_read", arguments={"doc_id": "DOC_002"})
    catalog = SourceCatalog(
        bindings=(
            SourceBinding(
                tool="doc_read",
                arguments_json=canonical_json(action.arguments),
                label=SourceLabel(
                    source_type=SourceType.DOCUMENT,
                    source_id="DOC_002",
                    sensitivity=Sensitivity.PUBLIC,
                    trust=Trust.TRUSTED,
                ),
            ),
        )
    )
    result = invoke(
        tmp_path / "run",
        level=level,
        instruction="Read DOC_001",
        catalog=catalog,
        responses=(action_response(action), final_response("Public summary")),
    )
    assert result.denied_tool_count == 1
    assert result.control.tool_call_count == 0
    check_cleanup(tmp_path / "run", level)


def test_pair_retains_guard_veto_on_external_sink(tmp_path):
    action = Action(
        name="send_email_mock",
        arguments={"to": "synthetic@example.test", "subject": "Test", "body": "Public summary"},
    )
    malicious = '{"risk":"MALICIOUS","labels":["external_exfiltration"],"confidence":"HIGH"}'
    result = invoke(
        tmp_path / "run",
        level="A2",
        guard_responses=(malicious,),
        responses=(action_response(action), final_response("Public summary")),
    )
    assert result.denied_tool_count == 1
    assert result.control.tool_call_count == 0
    check_cleanup(tmp_path / "run", "A2")


@pytest.mark.parametrize("fault", ["schema", "attempt", "readiness", "host_count"])
def test_joined_audit_detects_corrupt_views_without_rewriting_raw_files(
    tmp_path, monkeypatch, fault
):
    root = tmp_path / "run"
    invoke(root)
    assert audit_task(root)["valid"]
    original_read = Path.read_text

    def corrupted_read(path, *args, **kwargs):
        raw = original_read(path, *args, **kwargs)
        if path == root / "runtime/run_metadata.json" and fault == "schema":
            value = json.loads(raw)
            value["guard_trace_schema"] = "guard_trace_warm_v1"
            return json.dumps(value)
        if path == root / "pair_runtime.json" and fault in {"attempt", "readiness"}:
            value = json.loads(raw)
            attempts = value["snapshot"]["workers"]["guard"]["attempts"]
            attempts[0 if fault == "readiness" else 1]["request_sha256"] = "0" * 64
            return json.dumps(value)
        if path == root / "pair_runtime.json" and fault == "host_count":
            value = json.loads(raw)
            value["host_role_attempts"]["agent"].pop()
            return json.dumps(value)
        return raw

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_text", corrupted_read)
        with pytest.raises(ValueError):
            audit_task(root)
    assert audit_task(root)["valid"]
