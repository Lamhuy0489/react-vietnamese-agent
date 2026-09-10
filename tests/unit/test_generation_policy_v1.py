"""Policy hooks on fake native model; no real model/torch or Test inputs."""

import copy
import gc
import importlib
import json
from pathlib import Path
from typing import Any

import pytest
from test_context_stress_v1 import fake as fake

from react_agent.llm.base import GenerationConfig
from react_agent.llm.context_stress_v1 import REQUEST, ContextStressBackend
from react_agent.llm.generation_policy_v1 import (
    CONFIG_FIELDS,
    METHODS,
    PolicyStressBackend,
    PolicyStressFactory,
    config_snapshot,
)
from react_agent.llm.model_pair_v1 import ModelIdentity
from react_agent.validation.context_stress_audit_v1 import inventory, read_record
from react_agent.validation.generation_policy_audit_v1 import GLOBAL_DEFAULTS, audit_policy


class NativeConfig:
    def __init__(self, **values: Any) -> None:
        vars(self).update(dict.fromkeys(CONFIG_FIELDS))
        vars(self).update(values)

    @property
    def values(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dict(self) -> dict[str, Any]:
        return config_snapshot(self)

    def _get_default_generation_params(self) -> dict[str, Any]:
        return copy.deepcopy(GLOBAL_DEFAULTS)


class PrivateTensor:
    def __deepcopy__(self, memo: Any) -> Any:
        raise AssertionError("private tensor must not be copied")


@pytest.fixture(autouse=True)
def collect_owned_cycles(monkeypatch: pytest.MonkeyPatch) -> Any:
    yield
    monkeypatch.undo()
    gc.collect()


@pytest.fixture
def native(fake: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    model, state = fake
    model.transformers.GenerationConfig = NativeConfig
    model.model.generation_config = NativeConfig(
        eos_token_id=[151645, 151643],
        repetition_penalty=1.1,
        do_sample=True,
        temperature=0.7,
        top_p=0.8,
        top_k=20,
    )
    model.tokenizer.pad_token_id = 151643
    cls = type(model.model)
    original_generate = cls.generate
    state.policy_calls = []
    state.policy_failure = None

    def resolve(self: Any, generation_config: Any, **kwargs: Any) -> Any:
        state.policy_calls.append("resolve")
        result = copy.deepcopy(generation_config)
        for source in (self.generation_config.to_dict(), GLOBAL_DEFAULTS):
            for key, value in source.items():
                if getattr(result, key) is None:
                    setattr(result, key, copy.deepcopy(value))
        if state.policy_failure == "resolve":
            raise RuntimeError("PRIVATE_NATIVE_ERROR")
        return result, kwargs

    def length(
        self: Any,
        generation_config: Any,
        has_default_max_length: bool,
        has_default_min_length: bool,
        model_input_name: str,
        input_ids_length: int,
        inputs_tensor: Any,
    ) -> Any:
        state.policy_calls.append("length")
        generation_config.max_length = generation_config.max_new_tokens + input_ids_length
        generation_config.min_length = generation_config.min_new_tokens + input_ids_length
        if state.policy_failure == "length":
            raise KeyboardInterrupt("PRIVATE_INTERRUPT")
        return generation_config

    def generate(self: Any, **kwargs: Any) -> Any:
        submitted = kwargs.pop("generation_config")
        resolved, inputs = self._prepare_generation_config(submitted, **kwargs)
        # Actual Transformers adds private token tensors before length prep.
        resolved._eos_token_tensor = PrivateTensor()
        if state.policy_failure == "duplicate":
            self._prepare_generation_config(submitted, **kwargs)
        if state.policy_failure != "missing":
            self._prepare_generated_length(
                resolved, True, True, "input_ids", 4096, inputs["input_ids"]
            )
        if state.policy_failure == "publisher":
            self.generation_config.repetition_penalty = 1.2
        return original_generate(self, generation_config=resolved, **inputs)

    monkeypatch.setattr(cls, "_prepare_generation_config", resolve, raising=False)
    monkeypatch.setattr(cls, "_prepare_generated_length", length, raising=False)
    monkeypatch.setattr(cls, "generate", generate)
    return model, state


@pytest.mark.parametrize("role", ["agent", "guard"])
def test_actual_delegation_receipts_and_no_policy_change(
    native: Any, tmp_path: Path, role: Any
) -> None:
    model, state = native
    publisher = config_snapshot(model.model.generation_config)
    originals = {n: getattr(model.model, n) for n in METHODS}
    inner = ContextStressBackend(model, role, tmp_path / "stress")
    wrapped = PolicyStressBackend(inner, tmp_path / "policy")
    wrapped.generate(REQUEST, GenerationConfig(max_new_tokens=512 if role == "agent" else 128))
    assert state.policy_calls == ["resolve", "length"]
    assert len(state.generated) == len(state.forwards) == 1
    assert config_snapshot(model.model.generation_config) == publisher
    assert all(
        getattr(model.model, n) == originals[n] and n not in vars(model.model) for n in METHODS
    )
    submitted = read_record(inner.output / "prepared.json")["generation"]
    result = audit_policy(
        wrapped.output,
        role,
        ModelIdentity(model.model_id, model.model_revision),
        wrapped._owner,
        submitted,
        publisher,
    )
    assert result["resolved"]["repetition_penalty"] == 1.1
    assert result["resolved"]["do_sample"] is False and submitted["repetition_penalty"] is None
    assert result["resolved"]["temperature"] == 0.7
    assert result["length"]["min_length"] == (4608 if role == "agent" else 4224)
    assert not result["source_authenticated"] and not result["phase5_accepted"]
    assert result == audit_policy(
        wrapped.output,
        role,
        ModelIdentity(model.model_id, model.model_revision),
        wrapped._owner,
        submitted,
        publisher,
    )
    assert len(inventory(wrapped.output)) == 5
    # Differential control: same fake model and publisher, no policy hooks.
    control = ContextStressBackend(model, role, tmp_path / "unobserved")
    control.generate(REQUEST, GenerationConfig(max_new_tokens=512 if role == "agent" else 128))
    for name in ("generated", "completed"):
        observed_record = read_record(inner.output / f"{name}.json")
        control_record = read_record(control.output / f"{name}.json")
        assert observed_record["summary"] == control_record["summary"]
        assert observed_record["cache"] == control_record["cache"]
    with pytest.raises(RuntimeError, match="single-use"):
        wrapped.generate(REQUEST, GenerationConfig())


@pytest.mark.parametrize(
    "failure", ["resolve", "length", "duplicate", "missing", "publisher", "generate"]
)
def test_error_partials_restore_methods_and_retire(
    native: Any, tmp_path: Path, failure: str
) -> None:
    model, state = native
    state.policy_failure = failure
    if failure == "generate":
        state.failure = failure
    wrapped = PolicyStressBackend(
        ContextStressBackend(model, "agent", tmp_path / "stress"), tmp_path / "policy"
    )
    with pytest.raises((RuntimeError, ValueError, KeyboardInterrupt)):
        wrapped.generate(REQUEST, GenerationConfig())
    assert all(n not in vars(model.model) for n in METHODS)
    assert read_record(wrapped.output / "restored.json")["methods_restored"] is True
    assert not (wrapped.output / "completed.json").exists()
    assert all("PRIVATE_" not in p.read_text() for p in wrapped.output.iterdir())
    with pytest.raises(RuntimeError, match="single-use"):
        wrapped.generate(REQUEST, GenerationConfig())


@pytest.mark.parametrize("case", ["unknown", "nonfinite", "tensor", "missing"])
def test_invalid_config_not_serialized(case: str) -> None:
    config = NativeConfig()
    if case == "unknown":
        config.extra_field = "PRIVATE_SENTINEL"
    elif case == "nonfinite":
        config.temperature = float("nan")
    elif case == "tensor":
        config.temperature = PrivateTensor()
    else:
        del config.top_k
    with pytest.raises((ValueError, TypeError)):
        config_snapshot(config)


def test_factory_refuses_existing_policy_before_native_load(tmp_path: Path) -> None:
    def load() -> Any:
        raise AssertionError("no model loading allowed")

    with pytest.raises(ValueError, match="before model loading"):
        PolicyStressFactory(load, "agent", tmp_path / "stress", tmp_path)()


@pytest.mark.parametrize(
    "stage,keys,value",
    [
        ("entered", ("pid",), 0),
        ("entered", ("role",), "guard"),
        ("entered", ("publisher", "repetition_penalty"), 1.0),
        ("entered", ("global_defaults", "top_k"), 20),
        ("entered", ("policy_changed",), True),
        ("resolved", ("resolved", "do_sample"), True),
        ("resolved", ("resolved", "repetition_penalty"), 1.0),
        ("resolved", ("submitted", "top_k"), 20),
        ("resolved", ("model_kwargs_keys",), ["input_ids"]),
        ("length", ("before", "max_length"), 4608),
        ("length", ("after", "min_length"), 4607),
        ("length", ("after", "repetition_penalty"), 1.0),
        ("length", ("input_tokens",), 4095),
        ("restored", ("methods_restored",), 1),
        ("completed", ("hook_calls", METHODS[0]), 2),
        ("completed", ("resolved_sha256",), "0" * 64),
        ("completed", ("length_sha256",), "0" * 64),
        ("completed", ("model_generation_calls",), True),
    ],
)
def test_independent_audit_rejects_mutations(
    native: Any, tmp_path: Path, stage: str, keys: Any, value: Any
) -> None:
    model, _ = native
    publisher = config_snapshot(model.model.generation_config)
    inner = ContextStressBackend(model, "agent", tmp_path / "stress")
    wrapped = PolicyStressBackend(inner, tmp_path / "policy")
    wrapped.generate(REQUEST, GenerationConfig())
    submitted = read_record(inner.output / "prepared.json")["generation"]
    path = wrapped.output / f"{stage}.json"
    record = read_record(path)
    parent = record
    for key in keys[:-1]:
        parent = parent[key]
    parent[keys[-1]] = value
    path.write_text(json.dumps(record))
    before = inventory(wrapped.output)
    with pytest.raises(ValueError):
        audit_policy(
            wrapped.output,
            "agent",
            ModelIdentity(model.model_id, model.model_revision),
            wrapped._owner,
            submitted,
            publisher,
        )
    assert inventory(wrapped.output) == before


def test_owner_and_concurrency_before_instrumentation(
    native: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model, state = native
    wrapped = PolicyStressBackend(
        ContextStressBackend(model, "agent", tmp_path / "stress"), tmp_path / "policy"
    )
    monkeypatch.setattr(
        "react_agent.llm.generation_policy_v1.os.getpid", lambda: wrapped._owner + 1
    )
    with pytest.raises(RuntimeError, match="single policy owner"):
        wrapped.generate(REQUEST, GenerationConfig())
    monkeypatch.setattr("react_agent.llm.generation_policy_v1.os.getpid", lambda: wrapped._owner)
    with wrapped._lock:
        with pytest.raises(RuntimeError, match="single policy owner"):
            wrapped.generate(REQUEST, GenerationConfig())
    assert not wrapped.output.exists() and not state.policy_calls


def test_preexisting_instrumentation_is_not_overwritten(native: Any, tmp_path: Path) -> None:
    model, state = native
    original = model.model._prepare_generation_config
    model.model._prepare_generation_config = original
    wrapped = PolicyStressBackend(
        ContextStressBackend(model, "agent", tmp_path / "stress"), tmp_path / "policy"
    )
    with pytest.raises(ValueError, match="unmodified"):
        wrapped.generate(REQUEST, GenerationConfig())
    assert model.model._prepare_generation_config == original and not state.policy_calls


@pytest.mark.parametrize("case", ["commit", "nested", "existing"])
def test_entry_rejects_bad_identity_paths_before_cuda(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    entry = importlib.import_module("run_phase5_policy_stress_worker")

    def cuda() -> Any:
        raise AssertionError("CUDA must not be touched")

    monkeypatch.setattr(entry, "verify_gpu_environment", cuda)
    monkeypatch.setenv("PAIR_SOURCE_COMMIT", "wrong" if case == "commit" else "a" * 40)
    output = tmp_path / "probe"
    policy = output / "policy" if case == "nested" else tmp_path / "policy"
    if case == "existing":
        policy.mkdir()
    monkeypatch.setattr(
        "sys.argv",
        [
            "entry",
            "--output",
            str(output),
            "--policy-output",
            str(policy),
            "--guard-path",
            "unused",
            "--snapshot",
            "unused",
        ],
    )
    with pytest.raises(ValueError):
        entry.main()


@pytest.mark.parametrize("mutate", [False, True])
def test_source_checker_rejects_independent_default_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutate: bool
) -> None:
    import hashlib
    import zipfile

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    check = importlib.import_module("check_phase5_generation_policy")
    defaults = dict(GLOBAL_DEFAULTS)
    if mutate:
        defaults["repetition_penalty"] = 2.0
    source = (
        "class GenerationMixin:\n    def _prepare_generation_config(self):\n"
        "        generation_config.update(**self.generation_config.to_dict(), "
        "defaults_only=True, allow_custom_entries=True)\n"
        "        generation_config.update(**global_defaults, defaults_only=True)\n"
        "        generation_config.update(**kwargs)\n"
    )
    config = (
        "class GenerationConfig:\n    def _get_default_generation_params(self):\n"
        f"        return {defaults!r}\n"
    )
    wheel = tmp_path / "synthetic.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("transformers/generation/utils.py", source)
        archive.writestr("transformers/generation/configuration_utils.py", config)
    # Hash overrides apply only to this synthetic test, never production checks.
    monkeypatch.setattr(check, "WHEEL_SHA256", hashlib.sha256(wheel.read_bytes()).hexdigest())
    monkeypatch.setattr(check, "UTILS_SHA256", hashlib.sha256(source.encode()).hexdigest())
    if mutate:
        with pytest.raises(ValueError, match="independent global defaults"):
            check.check(wheel)
    else:
        result = check.check(wheel)
        assert result["valid"] and not result["gpu_readiness"] and not result["native_imported"]
