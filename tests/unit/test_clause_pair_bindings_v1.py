"""Lazy composition/admission checks without native imports or model loading."""

from pathlib import Path

import pytest

from react_agent.llm import clause_pair_probe_v1 as probe
from react_agent.llm import exit_pair_probe_v1 as previous
from react_agent.security_v1 import clause_pair_runtime_v1 as runtime


def test_identity_is_distinct_and_pins_all_new_components():
    old = previous.fixed_identity("stub", "valid")
    new = probe.fixed_identity("stub", "valid")
    assert new["protocol"] != old["protocol"]
    assert new["security_runtime_version"] != old["security_runtime_version"]
    for key in (
        "cases",
        "schedule",
        "pair_config",
        "generation",
        "runtime",
        "guard_prompt",
        "constrained_execution",
    ):
        assert new[key] == old[key]
    pins = probe.execution_sources()
    for path in (
        "security_v1/runtime_v12.py",
        "security_v1/value_origin_v3.py",
        "security_v1/authorization_anchors_v3.py",
        "validation/clause_pair_audit_v1.py",
    ):
        assert path in pins
    assert all(pins[k] == v for k, v in previous.execution_sources().items())


def test_native_binding_selects_candidate_not_cpu_fallback():
    assert probe.dependencies("hf")["run_pair_task"] is runtime.run_pair_task
    assert probe.dependencies("stub")["run_pair_task"] is probe.synthetic_runtime
    with pytest.raises(ValueError):
        probe.fixed_identity("hf", "backend_failure")


@pytest.mark.parametrize("synthetic", [False, True])
def test_wrong_pair_fails_before_any_output(tmp_path, synthetic):
    function = runtime.run_synthetic_pair_task if synthetic else runtime.run_pair_task
    with pytest.raises(TypeError):
        function(object(), pair=object(), output=tmp_path / "execution")
    assert not list(tmp_path.iterdir())


def test_bare_or_warm_role_cannot_bypass_constrained_admission(tmp_path):
    with pytest.raises(ValueError):
        runtime.SecurityRuntime._run_task(object(), object(), output=tmp_path, _worker=None)


def test_frozen_module_globals_not_modified():
    from react_agent.security_v1 import constrained_runtime_v1, exit_pair_runtime_v1, runtime_v12

    assert constrained_runtime_v1.RUNTIME_VERSION == "security_runtime_v8_constrained_v1"
    assert runtime_v12.RUNTIME_VERSION == "security_runtime_v12_clause_candidate"
    assert exit_pair_runtime_v1.baseline is constrained_runtime_v1
    assert Path(constrained_runtime_v1.__file__).is_file()
