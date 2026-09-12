"""Ordinary policy/attention composition with fake tensors, never native inference."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import threading
import zipfile
from pathlib import Path
from types import SimpleNamespace as NS
from typing import Any

import pytest
from test_efficient_requests_v1 import generate as attention_generate
from test_efficient_requests_v1 import libraries
from test_generation_policy_v1 import NativeConfig, PrivateTensor

from react_agent.foundation.normalization import text_hash
from react_agent.llm import efficient_requests_v1 as attention
from react_agent.llm import request_policy_v1 as impl
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.generation_policy_v1 import METHODS, config_snapshot
from react_agent.validation import request_policy_audit_v1 as auditor
from react_agent.validation.generation_policy_audit_v1 import GLOBAL_DEFAULTS


class Model:
    def __init__(self) -> None:
        self.generation_config = NativeConfig(
            eos_token_id=[151645, 151643],
            do_sample=True,
            repetition_penalty=1.1,
            temperature=0.7,
            top_p=0.8,
            top_k=20,
        )
        self.fault = ""
        self.inputs = 1
        self.outputs = 1
        self.policies: list[dict[str, Any]] = []

    def _prepare_generation_config(self, generation_config: Any, **kwargs: Any) -> Any:
        if self.fault == "resolve_error":
            raise RuntimeError("PRIVATE_EXCEPTION")
        result = copy.deepcopy(generation_config)
        for source in (vars(self.generation_config), GLOBAL_DEFAULTS):
            for key, value in source.items():
                if getattr(result, key) is None:
                    setattr(result, key, copy.deepcopy(value))
        return result, kwargs

    def _prepare_generated_length(
        self,
        generation_config: Any,
        has_default_max_length: bool,
        has_default_min_length: bool,
        model_input_name: str,
        input_ids_length: int,
        inputs_tensor: Any,
    ) -> Any:
        if self.fault == "length_interrupt":
            raise KeyboardInterrupt("PRIVATE_INTERRUPT")
        generation_config.max_length = input_ids_length + generation_config.max_new_tokens
        if generation_config.min_new_tokens is not None:
            generation_config.min_length = input_ids_length + generation_config.min_new_tokens
        return generation_config


def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: Any = "agent") -> Any:
    torch, hf, _ = libraries()
    monkeypatch.setattr(attention, "libraries", lambda: (torch, hf))
    model = Model()
    model_id, revision = (
        (attention.MODEL, attention.AGENT_REVISION)
        if role == "agent"
        else (attention.MODEL_ID, attention.GUARD_REVISION)
    )
    native = NS(
        model=model,
        transformers=NS(__version__="5.5.0"),
        model_id=model_id,
        model_revision=revision,
    )
    metrics = tmp_path / "metrics.jsonl"
    rows = [
        dict(
            event="load",
            model_id=model_id,
            model_revision=revision,
            dtype="float16",
            attention="sdpa",
            quantization=None,
            torch_version="2.10.0+cu128",
            transformers_version="5.5.0",
            cuda_version="12.8",
            load_seconds_including_hashes=1.0,
            protocol="agent_hf_dual_gpu_v1" if role == "agent" else "guard_hf_single_gpu_v1",
            adapter_protocol="agent_hf_dual_gpu_v2_tf550" if role == "agent" else None,
        )
    ]

    def invoke(messages: Any, config: GenerationConfig) -> ModelResponse:
        assert messages == [dict(role="user", content="synthetic-public-input")]
        submitted = NativeConfig(
            max_new_tokens=config.max_new_tokens,
            do_sample=False,
            num_beams=1,
            use_cache=True,
            cache_implementation="dynamic",
            return_dict_in_generate=False,
            output_scores=False,
            output_attentions=False,
            output_hidden_states=False,
            eos_token_id=model.generation_config.eos_token_id,
            pad_token_id=151643,
        )
        ids = PrivateTensor()
        extra = dict(input_ids=ids, attention_mask=ids)
        if model.fault == "override":
            extra["top_k"] = 2
        resolved, unused = model._prepare_generation_config(submitted, **extra)
        assert unused["input_ids"] is ids and unused["attention_mask"] is ids
        resolved._eos_token_tensor = ids
        if model.fault == "duplicate":
            model._prepare_generation_config(submitted, **extra)
        if model.fault != "missing":
            model._prepare_generated_length(resolved, True, True, "input_ids", model.inputs, ids)
        if model.fault == "publisher":
            model.generation_config.repetition_penalty = 2.0
        if model.fault == "generate_error":
            raise RuntimeError("PRIVATE_NATIVE_ERROR")
        attention_generate(torch, hf, role, model.inputs, model.outputs)
        model.policies.append(config_snapshot(resolved))
        rows.append(
            dict(
                event="generate",
                status="OK",
                call_index=len(rows),
                input_tokens=model.inputs,
                output_tokens=model.outputs,
                generate_seconds=0.1,
                call_seconds=0.2,
                generation_sha256=text_hash(config.model_dump_json()),
            )
        )
        metrics.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return ModelResponse(text="synthetic-answer", model_id=model_id, model_revision=revision)

    native.generate = invoke
    inner = attention.EfficientRequestBackend(native, role, tmp_path / "attention")
    wrapped = impl.RequestPolicyBackend(inner, tmp_path / "policy")
    return NS(
        model=model,
        native=native,
        inner=inner,
        wrapped=wrapped,
        metrics=metrics,
        publisher=config_snapshot(model.generation_config),
        config=GenerationConfig(max_new_tokens=512 if role == "agent" else 128),
        messages=[dict(role="user", content="synthetic-public-input")],
    )


def run(value: Any, inputs: int = 1, outputs: int = 1) -> ModelResponse:
    value.model.inputs, value.model.outputs = inputs, outputs
    return value.wrapped.generate(value.messages, value.config)


def audit(value: Any, count: int) -> dict[str, Any]:
    return auditor.audit(
        value.wrapped.output,
        value.inner.output,
        value.metrics,
        role=value.inner.role,
        worker_pid=os.getpid(),
        expected_requests=count,
        publisher=value.publisher,
        pad_token_id=151643,
    )


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize("minimum", [None, 2])
def test_repeated_policy_join_and_unobserved_differential(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: Any, minimum: Any
) -> None:
    value = setup(tmp_path, monkeypatch, role)
    if minimum is not None:
        value.model.generation_config.min_new_tokens = minimum
        value.wrapped._publisher = config_snapshot(value.model.generation_config)
        value.publisher = value.wrapped._publisher
    for n, out in ((1, 1), (4096, 3), (1, 1)):
        assert run(value, n, out).text == "synthetic-answer"
        assert all(name not in vars(value.model) for name in METHODS)
    result = audit(value, 3)
    assert result == audit(value, 3)
    assert [r["input_tokens"] for r in result["policy_requests"]] == [1, 4096, 1]
    assert [r["min_length"] for r in result["policy_requests"]] == (
        [0, 0, 0] if minimum is None else [3, 4098, 3]
    )
    assert not result["source_authenticated"] and not result["publisher_metadata_authenticated"]
    assert value.model.policies[0] == value.model.policies[2]
    assert value.model.policies[0]["repetition_penalty"] == 1.1
    assert value.model.policies[0]["do_sample"] is False
    assert value.model.policies[0]["output_logits"] is None
    # Unobserved native path still gets attention for fake tensor compatibility.
    control = attention.EfficientRequestBackend(value.native, role, tmp_path / "control")
    control.generate(value.messages, value.config)
    assert value.model.policies[-1] == value.model.policies[0]


@pytest.mark.parametrize(
    "fault",
    [
        "resolve_error",
        "length_interrupt",
        "override",
        "duplicate",
        "missing",
        "publisher",
        "generate_error",
    ],
)
def test_failures_restore_retire_and_hide_exception_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    value = setup(tmp_path, monkeypatch)
    value.model.fault = fault
    with pytest.raises((RuntimeError, ValueError, KeyboardInterrupt)):
        run(value)
    assert value.wrapped._retired and not value.wrapped._lock.locked()
    assert all(n not in vars(value.model) for n in METHODS)
    target = value.wrapped.output / "request_000001"
    assert json.loads((target / "restored.json").read_text())["methods_restored"]
    assert not (target / "completed.json").exists()
    assert all("PRIVATE_" not in p.read_text() for p in target.iterdir())
    with pytest.raises(RuntimeError, match="retired"):
        run(value)


@pytest.mark.parametrize(
    "stage", ["entered", "resolved", "length", "restored", "completed", "error"]
)
def test_storage_failure_restoration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    value = setup(tmp_path, monkeypatch)
    writer = impl.write_receipt

    def save(path: Path, row: Any) -> None:
        if path.stem == stage:
            raise OSError("synthetic write failure")
        writer(path, row)

    monkeypatch.setattr(impl, "write_receipt", save)
    if stage == "error":
        value.model.fault = "generate_error"
    with pytest.raises(OSError):
        run(value)
    assert all(n not in vars(value.model) for n in METHODS)
    assert value.wrapped._retired and not value.wrapped._lock.locked()
    assert not (value.wrapped.output / "request_000001/completed.json").exists()


@pytest.mark.parametrize(
    "case", ["publisher", "model", "native", "identity", "version", "history", "role", "config"]
)
def test_pre_request_drift_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    value = setup(tmp_path, monkeypatch)
    run(value)
    if case == "publisher":
        value.model.generation_config.repetition_penalty = 2.0
    elif case == "model":
        value.native.model = Model()
    elif case == "native":
        value.inner.native = NS(
            model_id=value.inner.model_id, model_revision=value.inner.model_revision
        )
    elif case == "identity":
        value.native.model_id = "drift"
    elif case == "version":
        value.native.transformers.__version__ = "different"
    elif case == "history":
        value.inner._index += 1
    elif case == "role":
        value.inner.role = "guard"
    else:
        value.config = GenerationConfig(temperature=0.2)
    with pytest.raises(ValueError):
        run(value)
    assert value.wrapped._retired
    assert not (value.wrapped.output / "request_000002").exists()


def test_owner_lock_and_existing_hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value = setup(tmp_path, monkeypatch)
    with value.wrapped._lock, pytest.raises(RuntimeError, match="owner"):
        run(value)
    value.wrapped._owner += 1
    with pytest.raises(RuntimeError, match="owner"):
        run(value)
    value.wrapped._owner -= 1
    assert not value.wrapped._retired and value.wrapped._index == 0
    old = value.model._prepare_generation_config
    value.model._prepare_generation_config = old
    with pytest.raises(ValueError, match="class-bound"):
        run(value)
    assert value.model._prepare_generation_config is old


@pytest.mark.parametrize("count", [0, True, 4097, 1.0])
def test_input_bound(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, count: Any) -> None:
    value = setup(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="length"):
        run(value, count)
    assert all(n not in vars(value.model) for n in METHODS)


def test_foreign_hook_thread_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value = setup(tmp_path, monkeypatch)
    failures = []

    def foreign(*args: Any) -> Any:
        def call() -> None:
            try:
                value.model._prepare_generation_config(NativeConfig())
            except RuntimeError as exc:
                failures.append(type(exc).__name__)

        thread = threading.Thread(target=call)
        thread.start()
        thread.join()
        raise RuntimeError("synthetic")

    value.native.generate = foreign
    with pytest.raises(RuntimeError):
        run(value)
    assert failures == ["RuntimeError"]
    assert all(n not in vars(value.model) for n in METHODS)


@pytest.mark.parametrize("mode", ["existing", "nested", "used", "wrong_factory"])
def test_factory_admission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    value = setup(tmp_path, monkeypatch)
    policy = (
        tmp_path
        if mode == "existing"
        else value.inner.output / "nested"
        if mode == "nested"
        else tmp_path / "new"
    )
    loads = []

    def load(self: Any) -> Any:
        loads.append(True)
        return value.inner

    monkeypatch.setattr(attention.EfficientRequestFactory, "__call__", load)
    factory: Any = attention.EfficientRequestFactory(
        lambda: value.native, "agent", value.inner.output
    )
    if mode == "used":
        value.inner._index = 1
    if mode == "wrong_factory":
        factory = NS(output=value.inner.output)
    with pytest.raises(ValueError):
        impl.RequestPolicyFactory(factory, policy)()
    assert loads == ([True] if mode == "used" else [])


@pytest.mark.parametrize(
    "stage,key,new",
    [
        ("entered", "pid", True),
        ("entered", "publisher", {}),
        ("entered", "global_defaults", {}),
        ("entered", "request_index", 2),
        ("resolved", "model_kwargs_keys", ["input_ids"]),
        ("resolved", "submitted", {}),
        ("resolved", "resolved", {}),
        ("length", "input_tokens", 2),
        ("length", "before", {}),
        ("length", "after", {}),
        ("restored", "methods_restored", 1),
        ("completed", "model_generation_calls", 2),
        ("completed", "resolved_sha256", "0" * 64),
        ("completed", "length_sha256", "0" * 64),
    ],
)
def test_audit_corruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str, key: str, new: Any
) -> None:
    value = setup(tmp_path, monkeypatch)
    run(value)
    path = value.wrapped.output / "request_000001" / f"{stage}.json"
    row = json.loads(path.read_text())
    row[key] = new
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError):
        audit(value, 1)


@pytest.mark.parametrize(
    "fault", ["missing", "extra_directory", "error", "duplicate_key", "symlink", "native_join"]
)
def test_audit_inventory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str) -> None:
    value = setup(tmp_path, monkeypatch)
    run(value)
    path = value.wrapped.output / "request_000001/completed.json"
    if fault == "missing":
        path.unlink()
    elif fault == "extra_directory":
        (path.parent / "extra").mkdir()
    elif fault == "error":
        path.with_name("error.json").write_text("{}")
    elif fault == "duplicate_key":
        path.write_text(
            path.read_text().replace('"request_index": 1', '"request_index": 2, "request_index": 1')
        )
    elif fault == "symlink":
        other = tmp_path / "copy.json"
        path.rename(other)
        path.symlink_to(other)
    else:
        rows = value.metrics.read_text().splitlines()
        row = json.loads(rows[1])
        row["input_tokens"] = 2
        value.metrics.write_text(rows[0] + "\n" + json.dumps(row) + "\n")
    with pytest.raises(ValueError):
        audit(value, 1)


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize("minimum", [None, 2])
def test_pinned_native_policy_methods(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: Any, minimum: Any
) -> None:
    """Execute hash-authenticated resolve/length functions against fake config/tensors."""
    import ast
    import importlib.util

    wheel = Path(
        "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/transformers-5.5.0-py3-none-any.whl"
    )
    if not wheel.is_file():
        pytest.skip("cached pinned wheel unavailable; native method receipt required")
    assert (
        hashlib.sha256(wheel.read_bytes()).hexdigest()
        == "821a9ff0961abbb29eb1eb686d78df1c85929fdf213a3fe49dc6bd94f9efa944"
    )
    with zipfile.ZipFile(wheel) as archive:
        raw = archive.read("transformers/generation/utils.py")
    assert (
        hashlib.sha256(raw).hexdigest()
        == "dde2df36821c0d724b5af47cb0ff71c3c4c1990c86d81b821911127ae4dc1254"
    )
    tree = ast.parse(raw)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GenerationMixin")
    methods = [
        next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
        for name in METHODS
    ]
    source = tmp_path / "verified_length.py"
    source.write_text(
        "from __future__ import annotations\nimport copy\n"
        + "\n".join(ast.unparse(method) for method in methods)
        + "\n"
    )
    spec = importlib.util.spec_from_file_location("verified_native_length", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def update(
        config: Any, defaults_only: bool = False, allow_custom_entries: bool = False, **kwargs: Any
    ) -> dict[str, Any]:
        unused = {}
        for name, value in kwargs.items():
            if hasattr(config, name) or allow_custom_entries:
                if not defaults_only or getattr(config, name, None) is None:
                    setattr(config, name, copy.deepcopy(value))
            else:
                unused[name] = value
        return unused

    monkeypatch.setattr(NativeConfig, "update", update, raising=False)
    for name in METHODS:
        monkeypatch.setattr(Model, name, getattr(module, name))
    value = setup(tmp_path, monkeypatch, role)
    if minimum is not None:
        value.model.generation_config.min_new_tokens = minimum
        value.wrapped._publisher = config_snapshot(value.model.generation_config)
        value.publisher = value.wrapped._publisher
    for inputs in (1, 4096, 7):
        run(value, inputs, 1)
    result = audit(value, 3)
    limit = 512 if role == "agent" else 128
    assert [r["max_length"] for r in result["policy_requests"]] == [
        1 + limit,
        4096 + limit,
        7 + limit,
    ]
    assert [r["min_length"] for r in result["policy_requests"]] == (
        [0, 0, 0] if minimum is None else [3, 4098, 9]
    )


@pytest.mark.parametrize("target", ["policy", "attention", "metrics"])
def test_audit_detects_mutation_during_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    value = setup(tmp_path, monkeypatch)
    run(value)
    original = auditor._record

    def read(raw: str) -> Any:
        row = original(raw)
        if row["stage"] == "completed":
            path = (
                value.metrics
                if target == "metrics"
                else (value.wrapped.output if target == "policy" else value.inner.output)
                / "request_000001/entered.json"
            )
            path.write_text(path.read_text() + " ")
        return row

    monkeypatch.setattr(auditor, "_record", read)
    with pytest.raises(ValueError, match="mutated|changed"):
        audit(value, 1)


def test_exact_factory_positive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value = setup(tmp_path, monkeypatch)
    loads = []

    def load(self: Any) -> Any:
        loads.append(True)
        return value.inner

    monkeypatch.setattr(attention.EfficientRequestFactory, "__call__", load)
    factory = impl.RequestPolicyFactory(
        attention.EfficientRequestFactory(lambda: value.native, "agent", value.inner.output),
        tmp_path / "factory_policy",
    )
    assert not loads
    backend = factory()
    assert type(backend) is impl.RequestPolicyBackend
    assert backend.inner is value.inner and loads == [True]
    assert not backend.output.exists()
