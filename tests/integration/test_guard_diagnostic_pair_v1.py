"""Real-spawn causal controls: invalid guard output retires pair, no semantic retry."""

import json
from pathlib import Path

import pytest
from test_phase5_pair_runtime import Factory

from react_agent.agent.state import RuntimeConfig
from react_agent.llm.base import GenerationConfig
from react_agent.llm.document_runtime_probe_v1 import CATALOG, TASK
from react_agent.llm.guard_diagnostic_backend_v1 import DiagnosticFactory
from react_agent.llm.model_pair_v1 import ModelIdentity
from react_agent.llm.model_pair_v2 import ShutdownPair, ShutdownPairConfig
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.document_pair_runtime_v1 import run_pair_task
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.pair_runtime_audit_v3 import audit_task

ROOT = Path(__file__).resolve().parents[2]
SAFE = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'
RESPONSES = (
    '{"action":{"name":"doc_read","arguments":{"doc_id":"CDOC_034"}}}',
    '{"final_answer":{"answer":"Lab Mạng ở D305."}}',
)


def invoke(path, level, response, diagnostic):
    config = ShutdownPairConfig(
        ModelIdentity("agent", "synthetic_v1"),
        ModelIdentity("guard", "synthetic_v1"),
        agent_start_seconds=10,
        guard_start_seconds=10,
        agent_call_seconds=5,
        guard_call_seconds=5,
    )
    factory = Factory("guard", (response,) * 4, "")
    guard = (
        DiagnosticFactory(factory, path.parent / (path.name + "_diagnostics.jsonl"))
        if diagnostic
        else factory
    )
    pair = ShutdownPair(Factory("agent", RESPONSES, ""), guard, config)
    run = run_pair_task(
        TASK,
        output=path,
        registry_factory=lambda: build_clean_registry(ROOT / "data/clean/v1_1/environment"),
        security=configuration(level),
        runtime_config=RuntimeConfig(max_steps=3, max_format_retries_per_step=0),
        generation=GenerationConfig(),
        source_catalog=CATALOG,
        pair=pair,
    )
    assert audit_task(path)["valid"]
    return run, json.loads((path / "pair_runtime.json").read_text())


@pytest.mark.parametrize("level", ["A2", "A3", "A4", "A5", "A6"])
@pytest.mark.parametrize(
    "response,category",
    [
        (SAFE, "valid"),
        ("not-json", "json_syntax"),
        ('{"risk":"SAFE","labels":[],"confidence":0.9}', "schema"),
        ('{"risk":"SAFE","risk":"SAFE","labels":[],"confidence":"HIGH"}', "duplicate_key"),
    ],
)
def test_observer_parity_and_failure_chain(tmp_path, level, response, category):
    baseline, old = invoke(tmp_path / "baseline", level, response, False)
    observed, new = invoke(tmp_path / "observed", level, response, True)
    assert (
        baseline.result.status
        == observed.result.status
        == ("completed" if category == "valid" else "model_error")
    )
    assert baseline.result.final_answer == observed.result.final_answer
    assert baseline.result.tool_sequence == observed.result.tool_sequence == ["doc_read"]
    sidecars = [
        json.loads(line)
        for line in (tmp_path / "observed_diagnostics.jsonl").read_text().splitlines()
    ]
    assert len(sidecars) == (2 if category == "valid" else 1)
    assert all(r["diagnostic"]["category"] == category for r in sidecars)
    for receipt in (old, new):
        workers = receipt["snapshot"]["workers"]
        assert all(w["closed"] and not w["handle_pending"] for w in workers.values())
        assert all(e["reaped"] for w in workers.values() for e in w["lifecycle"])
        if category != "valid":
            assert len(workers["guard"]["attempts"]) == 2  # readiness + one generation
            assert len(workers["agent"]["attempts"]) == 2
            for role in ("agent", "guard"):
                hosts = receipt["host_role_attempts"][role]
                assert [h["status"] for h in hosts] == ["OK", "ERROR"]
                assert hosts[1]["worker_attempts_before"] == hosts[1]["worker_attempts_after"]
    guards = [
        json.loads(line)
        for line in (tmp_path / "observed/runtime/trace_guard.jsonl").read_text().splitlines()
    ]
    if category != "valid":
        assert [g["outcome"]["error_code"] for g in guards] == ["INVALID_OUTPUT", "BACKEND_FAILURE"]
        assert [len(g["execution_attempts"]) for g in guards] == [1, 0]
    for sidecar, trace in zip(sidecars, guards, strict=category == "valid"):
        attempt = trace["execution_attempts"][0]
        assert sidecar["worker_pid"] == attempt["pid"]
        assert sidecar["request_sha256"] == attempt["request_sha256"]
        assert sidecar["generation_sha256"] == attempt["generation_sha256"]
