"""Combined real wrapper bodies with synthetic tensors; no native-library claim."""

import json
import os
import pickle
import threading
from dataclasses import replace
from types import SimpleNamespace as NS

import pytest
from test_constrained_guard_v1 import (
    Matrix,
    Prefix,
    Repetition,
    submitted,
)
from test_constrained_guard_v1 import (
    Model as ConstraintModel,
)
from test_efficient_requests_v1 import generate as attention_generate
from test_efficient_requests_v1 import libraries
from test_generation_policy_v1 import NativeConfig
from test_guard_token_language_v1 import PairCodec
from test_native_guard_diagnostics_v1 import pin
from test_request_policy_v1 import Model as PolicyModel

from react_agent.llm import constrained_policy_v1 as impl
from react_agent.llm import efficient_requests_v1 as attention
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.constrained_guard_v1 import execution_identity
from react_agent.llm.generation_policy_v1 import config_snapshot
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticBackend
from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_token_language_v1 import compile_language, documents
from react_agent.llm.native_constrained_pair_v1 import native_pair
from react_agent.llm.native_guard_diagnostics_v2 import native_pair as previous_pair
from react_agent.llm.request_policy_v1 import RequestPolicyBackend
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory


class Model(PolicyModel):
    _get_logits_processor = ConstraintModel._get_logits_processor

    def generate(self, input_ids, attention_mask, generation_config, prefix_allowed_tokens_fn):
        resolved, _ = self._prepare_generation_config(
            generation_config,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        resolved = self._prepare_generated_length(resolved, True, True, "input_ids", 2, input_ids)
        self._get_logits_processor(resolved, prefix_allowed_tokens_fn)
        tokens = self.language.sequences[0] + (0,)
        for index in range(len(tokens)):
            prefix_allowed_tokens_fn(0, Matrix([40, 41, *tokens[:index]])[0])
        if self.fault == "native_error":
            raise RuntimeError("SECRET_synthetic")
        if self.fault == "native_interrupt":
            raise KeyboardInterrupt()
        attention_generate(self.torch, self.hf, "guard", 2, len(tokens))
        return Matrix([40, 41, *tokens])


@pytest.fixture
def backend(tmp_path, monkeypatch):
    torch, hf, _ = libraries()
    monkeypatch.setattr(attention, "libraries", lambda: (torch, hf))
    model = Model()
    model.generation_config.bos_token_id = 151643
    model.torch, model.hf = torch, hf
    model.language = compile_language(
        PairCodec(), tokenizer_sha256="a" * 64, vocabulary_size=16512, eos=(0, 1)
    )
    native = NS(
        model=model,
        tokenizer=object(),
        model_id=attention.MODEL_ID,
        model_revision=attention.GUARD_REVISION,
        transformers=NS(__version__="5.5.0"),
        config=GuardHFConfig(),
        _retired=False,
        call_index=0,
    )

    def generate(messages, config):
        native.call_index += 1
        model.generate(
            input_ids=Matrix([40, 41]),
            attention_mask=Matrix([1, 1]),
            generation_config=NativeConfig(**vars(submitted())),
        )
        return ModelResponse(
            text=documents()[0], model_id=native.model_id, model_revision=native.model_revision
        )

    native.generate = generate
    inner = attention.EfficientRequestBackend(native, "guard", tmp_path / "attention")
    policy = RequestPolicyBackend(inner, tmp_path / "policy")

    # Native loader admission is bypassed explicitly, not certified by this fixture.
    def admission(self, backend, language, output):
        self.native, self.language, self.output = backend, language, output
        self.model_id, self.model_revision = backend.model_id, backend.model_revision
        self._model, self._tokenizer = backend.model, backend.tokenizer
        self._publisher = config_snapshot(model.generation_config)
        self.constraint_identity = execution_identity(language)
        self._types = Repetition, Prefix
        self._owner, self._retired, self._index = os.getpid(), False, 0
        self._lock = threading.Lock()

    monkeypatch.setattr(impl.ConstrainedGuardBackend, "__init__", admission)
    return impl.ConstrainedPolicyBackend(policy, model.language, tmp_path / "constrained")


def run(backend):
    return backend.generate(
        [dict(role="user", content="synthetic public input")], GenerationConfig(max_new_tokens=128)
    )


def test_full_wrapper_composition_two_calls_and_sidecar(backend, tmp_path):
    observer = DiagnosticBackend(backend, tmp_path / "sidecar.jsonl")
    for index in (1, 2):
        response = observer.generate(
            [dict(role="user", content="synthetic public input")],
            GenerationConfig(max_new_tokens=128),
        )
        assert response.text == documents()[0]
        assert (
            backend._index
            == backend.policy._index
            == backend.attention._index
            == backend.native.call_index
            == index
        )
        for root in (backend.output, backend.policy.output, backend.attention.output):
            value = json.loads((root / f"request_{index:06d}/completed.json").read_text())
            assert value["request_index"] == index
        assert not {
            "generate",
            "_get_logits_processor",
            "_prepare_generation_config",
            "_prepare_generated_length",
        }.intersection(vars(backend._model))
    assert len((tmp_path / "sidecar.jsonl").read_text().splitlines()) == 2


@pytest.mark.parametrize(
    "fault",
    [
        "extra",
        "reverse",
        "penalty",
        "callback",
        "beam",
        "resolve_error",
        "length_interrupt",
        "native_error",
        "native_interrupt",
    ],
)
def test_nested_failure_restores_all_scopes_and_retires(backend, fault):
    backend._model.fault = fault
    with pytest.raises((ValueError, RuntimeError, KeyboardInterrupt)):
        run(backend)
    assert (
        backend.retired
        and backend.native._retired
        and backend.policy._retired
        and backend.attention._retired
    )
    for root in (backend.output, backend.policy.output, backend.attention.output):
        assert (root / "request_000001/restored.json").exists()
        assert not (root / "request_000001/completed.json").exists()
    assert not {
        "generate",
        "_get_logits_processor",
        "_prepare_generation_config",
        "_prepare_generated_length",
    }.intersection(vars(backend._model))
    with pytest.raises(RuntimeError, match="retired"):
        run(backend)
    assert backend._index == 1


@pytest.mark.parametrize("layer", ["policy", "attention", "native"])
def test_history_divergence_before_generation(backend, layer):
    target = getattr(backend, layer)
    setattr(target, "call_index" if layer == "native" else "_index", 3)
    with pytest.raises(ValueError, match="histories"):
        run(backend)
    assert backend.retired and not backend.output.exists()


def test_pair_topology_is_lazy_picklable_and_preserves_agent(tmp_path):
    args = [tmp_path / name for name in ("agent", "inventory", "guard")]
    args += [pin(), *[tmp_path / name for name in ("native", "attention", "policy")]]
    old = previous_pair(*args, witness=tmp_path / "old_witness")
    new = native_pair(*args, witness=tmp_path / "new_witness", constrained=tmp_path / "constraint")
    try:
        assert new.config == old.config and new.config.graceful_shutdown_seconds == 2
        assert new._workers["agent"].factory == old._workers["agent"].factory
        factory = new._workers["guard"].factory.factory.backend_factory
        assert type(factory) is impl.ConstrainedPolicyFactory
        assert factory.inner == old._workers["guard"].factory.factory.backend_factory
        assert pickle.loads(pickle.dumps(factory)) == factory  # noqa: S301
        assert new.state == "NEW" and not list(tmp_path.iterdir())
    finally:
        old.close()
        new.close()


@pytest.mark.parametrize(
    "target", ["agent", "inventory", "guard", "native", "attention", "policy", "witness"]
)
def test_constrained_root_overlap_rejected_before_transport(tmp_path, target):
    args = [tmp_path / name for name in ("agent", "inventory", "guard")]
    args += [pin(), *[tmp_path / name for name in ("native", "attention", "policy")]]
    with pytest.raises(ValueError):
        native_pair(*args, witness=tmp_path / "witness", constrained=tmp_path / target)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "fault",
    ["progress", "policy", "attention", "role", "loader", "snapshot", "stale", "source", "metrics"],
)
def test_factory_rejects_before_progress_or_native_load(tmp_path, monkeypatch, fault):
    args = [tmp_path / name for name in ("agent", "inventory", "guard")]
    args += [pin(), *[tmp_path / name for name in ("native", "attention", "policy")]]
    pair = native_pair(*args, witness=tmp_path / "witness", constrained=tmp_path / "constraint")
    try:
        factory = pair._workers["guard"].factory.factory.backend_factory
    finally:
        pair.close()

    def forbidden(self):
        raise AssertionError("must fail before progress configuration/model loading")

    monkeypatch.setattr(ThreadProgressFactory, "__call__", forbidden)
    policy = factory.inner.factory
    attention_factory = policy.attention
    if fault == "progress":
        factory = replace(factory, inner=None)
    elif fault == "policy":
        factory = replace(factory, inner=ThreadProgressFactory(None))
    elif fault in {"attention", "role", "loader"}:
        changed = (
            None
            if fault == "attention"
            else replace(
                attention_factory,
                **({"role": "agent"} if fault == "role" else {"native_factory": None}),
            )
        )
        factory = replace(factory, inner=ThreadProgressFactory(replace(policy, attention=changed)))
    elif fault == "snapshot":
        factory = replace(factory, snapshot=None)
    elif fault == "stale":
        factory.output.mkdir()
    elif fault == "source":
        factory = replace(factory, output=tmp_path / "guard")
    else:
        factory = replace(factory, output=attention_factory.native_factory.hf.metrics_path)
    with pytest.raises(ValueError):
        factory()
