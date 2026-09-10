"""Fake tensor/model tests, no native dependencies or local model execution."""

from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from react_agent.llm import context_stress_v1 as mod
from react_agent.llm.base import GenerationConfig
from react_agent.llm.context_geometry_v1 import INPUT_TOKENS


class Tensor:
    def __init__(self, data: list[list[int]], device: str = "cuda:0") -> None:
        self.data, self.device = data, device
        self.shape = (len(data), len(data[0]))

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, tuple):
            return Tensor([self.data[0][key[1]]], self.device)
        return SimpleNamespace(tolist=lambda: self.data[key].copy())

    def to(self, device: str) -> Tensor:
        self.device = device
        return self


class Config:
    def __init__(self, **values: Any) -> None:
        self.values = values

    def to_dict(self) -> dict[str, Any]:
        return self.values.copy()


@pytest.fixture
def fake() -> Any:
    state = SimpleNamespace(
        generated=[],
        forwards=[],
        seeds=[],
        resets=[],
        peak=100,
        failure=None,
        caches=[],
        native_configs=[],
    )

    class Tokenizer:
        pad_token_id = 0
        all_special_ids = [0, 1]

        def __len__(self) -> int:
            return 100

        def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
            assert not add_special_tokens
            return [2, 3, 4]

        def decode(self, *args: Any, **kwargs: Any) -> str:
            raise AssertionError("never decode model output")

    def cache(length: int, device: str) -> Any:
        def tensor() -> Any:
            return SimpleNamespace(
                shape=(1, 2, length, 4),
                device=device,
                dtype="fp16",
                numel=lambda: 2 * length * 4,
                element_size=lambda: 2,
            )

        layers = [SimpleNamespace(keys=tensor(), values=tensor()) for _ in range(2)]
        return SimpleNamespace(layers=layers, get_seq_length=lambda: length)

    def generate(**kw: Any) -> Any:
        state.generated.append(kw)
        if state.failure == "generate":
            raise RuntimeError("PRIVATE ERROR TEXT")
        count = kw["generation_config"].values["max_new_tokens"]
        sequence = kw["input_ids"].data[0] + [9] * count
        if state.failure == "prefix":
            sequence[0] = 8
        if state.failure == "short":
            sequence.pop()
        c = cache(len(sequence) - 1, kw["input_ids"].device)
        state.caches.append(c)
        if state.failure == "cache_shape":
            c.layers[0].keys.shape = (1, 1, 1, 1)
        if state.failure == "cache_device":
            c.layers[0].values.device = "cpu"
        if state.failure == "cache_dtype":
            c.layers[0].values.dtype = "fp32"
        if state.failure == "cache_layers":
            c.layers.pop()
        return SimpleNamespace(
            sequences=Tensor([sequence], kw["input_ids"].device), past_key_values=c
        )

    class Model:
        config = SimpleNamespace(
            max_position_embeddings=32768,
            num_hidden_layers=2,
            num_key_value_heads=2,
            hidden_size=16,
            num_attention_heads=4,
        )
        generation_config = SimpleNamespace(eos_token_id=[1, 5])

        def generate(self, **kw: Any) -> Any:
            return generate(**kw)

        def __call__(self, **kw: Any) -> Any:
            state.forwards.append(kw)
            if state.failure == "forward":
                raise RuntimeError("PRIVATE FORWARD ERROR")
            length = kw["past_key_values"].get_seq_length() + 1
            if state.failure == "forward_length":
                length -= 1
            return SimpleNamespace(past_key_values=cache(length, kw["input_ids"].device))

    cuda = SimpleNamespace(
        reset_peak_memory_stats=state.resets.append,
        mem_get_info=lambda d: (10**9, 2 * 10**9),
        memory_allocated=lambda d: 100,
        memory_reserved=lambda d: 100,
        max_memory_allocated=lambda d: state.peak,
        max_memory_reserved=lambda d: state.peak,
    )
    torch = SimpleNamespace(
        cuda=cuda,
        long="long",
        float16="fp16",
        manual_seed=state.seeds.append,
        inference_mode=nullcontext,
        tensor=lambda data, **kw: Tensor(data, kw["device"]),
        ones_like=lambda t: Tensor([[1] * t.shape[1]], t.device),
        ones=lambda shape, **kw: Tensor([[1] * shape[1]], kw["device"]),
    )
    native = SimpleNamespace(
        torch=torch,
        transformers=SimpleNamespace(__version__="5.5.0", GenerationConfig=Config),
        model=Model(),
        tokenizer=Tokenizer(),
        sync=lambda: None,
        model_id="synthetic",
        model_revision="synthetic:v1",
        plan=SimpleNamespace(
            agent_caps={0: 10**8, 1: 10**8},
            device_map=lambda: {"model.layers.0": 0, "model.layers.1": 0},
        ),
        config=SimpleNamespace(allocator_limit_bytes=10**8),
    )
    return native, state


@pytest.mark.parametrize("role,count,device", [("agent", 512, "cuda:0"), ("guard", 128, "cuda:1")])
def test_native_call_contract_and_no_decoded_output(
    fake: Any, tmp_path: Path, role: Any, count: int, device: str
) -> None:
    native, state = fake
    backend = mod.ContextStressBackend(native, role, tmp_path / "run")
    response = backend.generate(mod.REQUEST, GenerationConfig(max_new_tokens=count))
    assert response.text == mod.ACK and state.seeds == [42]
    assert len(state.generated) == len(state.forwards) == 1
    call = state.generated[0]
    options = call["generation_config"].values
    assert options["min_new_tokens"] == options["max_new_tokens"] == count
    assert options["eos_token_id"] == native.model.generation_config.eos_token_id
    assert options["eos_token_id"] is not native.model.generation_config.eos_token_id
    assert options["return_dict_in_generate"] and not options["output_hidden_states"]
    assert options["cache_implementation"] == "dynamic" and "past_key_values" not in call
    assert call["input_ids"].shape == (1, INPUT_TOKENS) and call["input_ids"].device == device
    final = state.forwards[0]
    assert final["input_ids"].data == [[9]] and final["attention_mask"].shape == (1, 4096 + count)
    assert final["past_key_values"] is state.caches[0] and final["logits_to_keep"] == 1
    generated = json.loads((backend.output / "generated.json").read_text())
    completed = json.loads((backend.output / "completed.json").read_text())
    assert not generated["summary"]["full_boundary_cache_observed"]
    assert completed["summary"]["full_boundary_cache_observed"]
    assert completed["cache"]["sequence_length"] == 4096 + count
    assert not completed["summary"]["generated_text_retained"]
    assert {p.name for p in backend.output.iterdir()} == {
        "entered.json",
        "prepared.json",
        "generated.json",
        "completed.json",
    }
    for path in backend.output.iterdir():
        data = path.read_text()
        assert "PRIVATE" not in data and 'sequence_ids"' not in data
    with pytest.raises(RuntimeError, match="single-use"):
        backend.generate(mod.REQUEST, GenerationConfig(max_new_tokens=count))
    assert len(state.generated) == 1


@pytest.mark.parametrize(
    "failure",
    [
        "generate",
        "forward",
        "prefix",
        "short",
        "cache_shape",
        "cache_device",
        "cache_dtype",
        "cache_layers",
        "forward_length",
        "version",
        "positions",
        "peak",
        "request",
        "config",
    ],
)
def test_errors_preserve_partials_retire_and_redact(
    fake: Any, tmp_path: Path, failure: str
) -> None:
    native, state = fake
    state.failure = failure
    messages = mod.REQUEST
    config = GenerationConfig()
    if failure == "version":
        native.transformers.__version__ = "other"
    if failure == "positions":
        native.model.config.max_position_embeddings = 4096
    if failure == "peak":
        state.peak = 10**9
    if failure == "request":
        messages = [{"role": "user", "content": "PRIVATE REQUEST"}]
    if failure == "config":
        config = GenerationConfig(max_new_tokens=1)
    backend = mod.ContextStressBackend(native, "agent", tmp_path / "run")
    with pytest.raises(RuntimeError, match="retire worker"):
        backend.generate(messages, config)
    assert (backend.output / "entered.json").exists() and (backend.output / "error.json").exists()
    assert not (backend.output / "completed.json").exists()
    assert all("PRIVATE" not in p.read_text() for p in backend.output.iterdir())
    with pytest.raises(RuntimeError, match="single-use"):
        backend.generate(mod.REQUEST, GenerationConfig())


def test_owner_and_concurrency_fail_before_work(
    fake: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    native, state = fake
    b = mod.ContextStressBackend(native, "agent", tmp_path / "run")
    monkeypatch.setattr(mod.os, "getpid", lambda: b._owner + 1)
    with pytest.raises(RuntimeError, match="owning"):
        b.generate(mod.REQUEST, GenerationConfig())
    monkeypatch.setattr(mod.os, "getpid", lambda: b._owner)
    with b._lock:
        with pytest.raises(RuntimeError, match="owning"):
            b.generate(mod.REQUEST, GenerationConfig())
    assert not state.generated and not list(b.output.iterdir())


def test_factory_is_lazy_and_rejects_unpinned_backend(fake: Any, tmp_path: Path) -> None:
    native, state = fake
    calls = []

    def load() -> Any:
        calls.append("load")
        return native

    factory = mod.ContextStressFactory(load, "agent", tmp_path / "run")
    assert not calls
    with pytest.raises(ValueError, match="authenticated"):
        factory()
    assert calls == ["load"] and not state.generated


def test_existing_output_refused_before_loading(tmp_path: Path) -> None:
    def load() -> Any:
        raise AssertionError("must not load")

    with pytest.raises(ValueError, match="fresh"):
        mod.ContextStressFactory(load, "agent", tmp_path)()
