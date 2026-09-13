"""Native-shaped sidecars only; checkpoint boundary explicitly mocked, no GPU."""

import json
from dataclasses import asdict

import pytest
import test_security_runtime_native_audit_v1 as legacy
from test_security_runtime_native_audit_v1 import inputs as old_inputs  # noqa: F401
from test_security_runtime_native_audit_v1 import native as native  # noqa: F401
from test_security_runtime_native_audit_v1 import sample as sample  # noqa: F401
from test_security_runtime_native_audit_v1 import template as template  # noqa: F401
from test_security_runtime_native_audit_v1 import tokenizers as tokenizers  # noqa: F401

from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.native_shutdown_v2 import agent_config, native_config
from react_agent.llm.security_runtime_probe_v2 import LEVELS, RUNTIME, TASK
from react_agent.validation import security_runtime_probe_audit_v2 as impl


@pytest.fixture(autouse=True)
def version(monkeypatch):
    monkeypatch.setattr(legacy, "impl", impl)


@pytest.fixture
def inputs(old_inputs):  # noqa: F811 — imported pytest fixture dependency
    path = old_inputs["probe"] / "identity.json"
    identity = json.loads(path.read_text())
    identity.update(
        protocol="security_runtime_probe_v2",
        levels=list(LEVELS),
        pair_config=asdict(native_config()),
        agent_only_execution=asdict(agent_config(native_config())),
        task=TASK.model_dump(mode="json"),
        runtime=RUNTIME.model_dump(),
        source_catalog=SourceCatalog().model_dump(mode="json"),
        automatic_retry=False,
        benchmark_tasks=0,
        test_tasks=0,
    )
    path.write_text(json.dumps(identity))
    return old_inputs


def test_join_and_forced_vs_recovered(inputs):
    legacy.test_join_is_repeatable_and_not_execution_claim(inputs)
    # Checkpoint is mocked: this changes synthetic classification inputs only.
    path = inputs["probe"] / "tasks/A0/execution/pair_runtime.json"
    receipt = json.loads(path.read_text())
    for event in receipt["snapshot"]["workers"]["agent"]["lifecycle"]:
        event["method"] = "TERMINATE"
        event["exitcode"] = -15
    path.write_text(json.dumps(receipt))
    result = impl.audit(**inputs)
    assert result["protocol"] == "security_runtime_native_join_v2"
    assert result["levels"][0]["recovered"] and not result["levels"][0]["observed_graceful"]


@pytest.mark.parametrize("fault", ["source", "tokenizer", "policy", "time", "guard_in_a0"])
def test_sidecar_mutations(inputs, fault):
    legacy.test_reject_mutated_sidecars(inputs, fault)


@pytest.mark.parametrize("field", ["protocol", "pair_config", "agent_only_execution", "generation"])
def test_new_identity_required(inputs, field):
    path = inputs["probe"] / "identity.json"
    value = json.loads(path.read_text())
    value[field] = {}
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="identity"):
        impl.audit(**inputs)
