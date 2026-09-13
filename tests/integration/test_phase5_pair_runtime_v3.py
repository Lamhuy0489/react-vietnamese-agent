"""Real-spawn observed-shutdown runtime QA, reusing frozen synthetic trajectories."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import test_phase5_pair_runtime as legacy
import test_phase5_pair_runtime_v2 as failure_v2
from test_phase5_worker_shutdown_v2 import Factory as TeardownFactory

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.base import GenerationConfig
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig
from react_agent.llm.model_pair_v2 import AgentWorkerConfig, ShutdownPair, ShutdownPairConfig
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.pair_runtime_v3 import run_pair_task
from react_agent.security_v1.worker_shutdown_v2 import ShutdownBackend
from react_agent.validation.pair_runtime_audit_v3 import audit_task


def invoke(
    path,
    level="A6",
    responses=legacy.DEFAULT_RESPONSES,
    agent_failure="",
    guard_failure="",
    guard_responses=(legacy.SAFE,) * 16,
    max_steps=2,
    registry_factory=legacy.registry,
    instruction="Calculate one plus one",
    catalog=None,
):
    config = ShutdownPairConfig(
        ModelIdentity("agent", "synthetic_v1"),
        ModelIdentity("guard", "synthetic_v1"),
        agent_start_seconds=10,
        guard_start_seconds=10,
        agent_call_seconds=0.2 if agent_failure == "timeout" else 5,
        guard_call_seconds=0.2 if guard_failure == "timeout" else 5,
    )
    agent = legacy.Factory("agent", responses, agent_failure)
    args = (
        {
            "pair": ShutdownPair(
                agent, legacy.Factory("guard", guard_responses, guard_failure), config
            )
        }
        if int(level[1:]) >= 2
        else {
            "agent_factory": agent,
            "agent_execution": AgentWorkerConfig(
                "agent", "synthetic_v1", start_seconds=10, call_seconds=config.agent_call_seconds
            ),
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
        **args,
    )


@pytest.fixture(autouse=True)
def entry(monkeypatch):
    monkeypatch.setattr(legacy, "invoke", invoke)
    monkeypatch.setattr(legacy, "audit_task", audit_task)


@pytest.mark.parametrize("level", [f"A{i}" for i in range(7)])
@pytest.mark.parametrize("terminal", ["completed", "parse_failure", "max_steps", "model_error"])
def test_all_levels_terminals_and_shutdown(tmp_path, level, terminal):
    legacy.test_real_spawn_pair_all_levels_terminals_and_cleanup(tmp_path, level, terminal)


@pytest.mark.parametrize("level", [f"A{i}" for i in range(7)])
def test_v7_observable_parity(tmp_path, level):
    legacy.test_observable_parity_with_v7(tmp_path, level)
    assert audit_task(tmp_path / "spawned")["valid"]


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize("failure", ["load", "timeout"])
def test_startup_and_generation_failures(tmp_path, role, failure):
    legacy.test_startup_and_inference_failures_keep_cleanup_evidence(tmp_path, failure, role)


@pytest.mark.parametrize("level", ["A0", "A1"])
@pytest.mark.parametrize("failure", ["load", "timeout"])
def test_agent_only_separate_deadline_and_failure(tmp_path, level, failure):
    if failure == "load":
        with pytest.raises(RuntimeError):
            invoke(tmp_path / "run", level, agent_failure=failure)
    else:
        assert invoke(tmp_path / "run", level, agent_failure=failure).result.status == "model_error"
    value = legacy.check_cleanup(tmp_path / "run", level)
    attempts = value["snapshot"]["workers"]["agent"]["attempts"]
    if failure == "timeout":
        assert attempts[0]["status"] == "OK" and attempts[1]["status"] == "TIMEOUT"
        assert attempts[0]["execution_config_sha256"] != attempts[1]["execution_config_sha256"]


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize("victim", ["agent", "guard"])
def test_post_response_worker_death_preserved(tmp_path, monkeypatch, role, victim):
    failure_v2.test_real_worker_death_after_response(tmp_path, monkeypatch, role, victim)


def test_invalid_guard_retirement(tmp_path):
    legacy.test_invalid_guard_output_retires_pair_and_discards_cache(tmp_path)


def test_interruption_during_startup(tmp_path, monkeypatch):
    original = ShutdownBackend.generate

    def interrupted(worker, messages, config):
        if worker.model_id == "guard":
            raise KeyboardInterrupt("synthetic interruption")
        return original(worker, messages, config)

    monkeypatch.setattr(ShutdownBackend, "generate", interrupted)
    with pytest.raises(KeyboardInterrupt):
        invoke(tmp_path / "run")
    receipt = legacy.check_cleanup(tmp_path / "run", "A6")
    assert not receipt["startup_completed"]


@pytest.mark.parametrize(
    "mutation", ["pid", "owner", "cold_hash", "warm_hash", "grace", "ack", "protocol", "missing"]
)
def test_receipt_mutations_rejected(tmp_path, mutation):
    invoke(tmp_path / "run")
    path = tmp_path / "run/pair_runtime.json"
    original = path.read_text()
    receipt = json.loads(path.read_text())
    assert audit_task(path.parent)["valid"]
    worker = receipt["snapshot"]["workers"]["agent"]
    if mutation == "pid":
        worker["lifecycle"][0]["pid"] += 10000
    elif mutation == "owner":
        receipt["owner_pid"] += 10000
    elif mutation == "cold_hash":
        worker["attempts"][0]["execution_config_sha256"] = "0" * 64
    elif mutation == "warm_hash":
        worker["attempts"][1]["execution_config_sha256"] = "0" * 64
    elif mutation == "grace":
        worker["lifecycle"][0]["graceful_shutdown_seconds"] += 1
    elif mutation == "ack":
        worker["lifecycle"][0]["stop_received"] = False
    elif mutation == "protocol":
        receipt["snapshot"]["protocol"] = "model_pair_v1"
    else:
        worker["lifecycle"] = []
    # Corrupt the in-memory read view; preserve immutable runtime output bytes.
    from unittest.mock import patch

    read_text = Path.read_text

    def changed(selected, *args, **kwargs):
        return json.dumps(receipt) if selected == path else read_text(selected, *args, **kwargs)

    with patch.object(Path, "read_text", changed), pytest.raises(ValueError):
        audit_task(path.parent)
    assert path.read_text() == original


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize("mode,method", [("slow", "GRACEFUL"), ("hang", "TERMINATE")])
def test_pair_role_teardown_observations(tmp_path, role, mode, method):
    # Identical synthetic identities are allowed, but role PIDs must be distinct.
    identity = ModelIdentity("synthetic-shutdown", "v2")
    pair = ShutdownPair(
        TeardownFactory(mode if role == "agent" else "fast"),
        TeardownFactory(mode if role == "guard" else "fast"),
        ShutdownPairConfig(
            identity,
            identity,
            agent_start_seconds=10,
            guard_start_seconds=10,
            graceful_shutdown_seconds=0.7,
        ),
    )
    with pair:
        assert pair.generate("agent", [], GenerationConfig()).text == "public"
        assert pair.generate("guard", [], GenerationConfig()).text == "public"
    snapshot = pair.snapshot()
    event = snapshot["workers"][role]["lifecycle"][0]
    assert event["method"] == method and event["stop_received"]
    assert event["serve_returned"] is (mode == "slow")
    assert all(w["closed"] and not w["handle_pending"] for w in snapshot["workers"].values())
    (tmp_path / "pair_shutdown.json").write_text(json.dumps(snapshot, indent=2) + "\n")


def test_pair_methods_keep_frozen_ownership_semantics():
    for name in ("start", "generate", "close", "_cleanup", "_alive", "_identity"):
        assert getattr(ShutdownPair, name) is getattr(ModelPair, name)
    with pytest.raises(TypeError):
        ShutdownPair(
            TeardownFactory(),
            TeardownFactory(),
            PairConfig(ModelIdentity("a", "v1"), ModelIdentity("g", "v1")),
        )


def test_agent_only_grace_and_deadline_match_paired_agent():
    p = ShutdownPairConfig(ModelIdentity("agent", "v1"), ModelIdentity("guard", "v1"))
    a = AgentWorkerConfig("agent", "v1")
    for cold in (True, False):
        assert a.execution(cold=cold) == p.execution("agent", cold=cold)


@pytest.mark.parametrize("entitled", [True, False])
def test_final_entitlement_preserved(tmp_path, entitled):
    legacy.test_pair_retains_final_entitlement_on_actual_database_rows(tmp_path, entitled)


@pytest.mark.parametrize("level", ["A4", "A5", "A6"])
def test_scope_preserved(tmp_path, level):
    legacy.test_pair_retains_scope_denial_before_broker(tmp_path, level)


def test_guard_external_sink_veto_preserved(tmp_path):
    legacy.test_pair_retains_guard_veto_on_external_sink(tmp_path)


@pytest.mark.parametrize("value", [True, 0, -1, float("nan"), float("inf")])
def test_agent_deadline_validation(value):
    with pytest.raises(ValueError):
        AgentWorkerConfig("agent", "v1", call_seconds=value)
