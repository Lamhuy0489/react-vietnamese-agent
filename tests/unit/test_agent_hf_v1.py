"""CPU fakes only: adapter call semantics are not model/GPU execution evidence."""

from __future__ import annotations

import json
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from react_agent.llm import agent_hf_v1 as adapter
from react_agent.llm.agent_runtime_input_v1 import parameter_shapes
from react_agent.llm.base import GenerationConfig
from react_agent.llm.coexistence_placement_v1 import GIB, PlacementPlan


class Inputs(dict[str, Any]):
    def to(self, device: str) -> Inputs:
        self.device = device
        return self


class Tokens:
    def __init__(self, count: int) -> None:
        self.shape = (1, count)

    def __getitem__(self, key: object) -> Tokens:
        return self


@pytest.fixture
def fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    model_path = tmp_path / "model"
    model_path.mkdir()
    state = SimpleNamespace(
        available=True,
        devices=2,
        name="Tesla T4",
        free=16 * GIB,
        occupied=False,
        loaded=False,
        peak=1024,
        events=[],
        hash_calls=0,
        drift=False,
        input_count=20,
        batch=1,
        bad_mask=False,
        output_count=4,
        output="synthetic answer",
        fail=False,
        messages=[],
        calls=[],
        options=[],
        seeds=[],
        tokenizer_options=[],
        extras=False,
    )
    geometry = {
        "model_type": "qwen2",
        "architectures": ["Qwen2ForCausalLM"],
        "num_hidden_layers": 28,
        "hidden_size": 3584,
        "intermediate_size": 18944,
        "num_attention_heads": 28,
        "num_key_value_heads": 4,
        "vocab_size": 152064,
        "tie_word_embeddings": False,
        "max_position_embeddings": 32768,
        "use_sliding_window": False,
    }
    plan = PlacementPlan()
    parameters = []
    for name, shape in parameter_shapes().items():
        module = next(m for m in plan.device_map() if name.startswith(m + "."))
        parameters.append(
            (
                name,
                SimpleNamespace(
                    shape=shape, device=f"cuda:{plan.device_map()[module]}", dtype="float16"
                ),
            )
        )
    buffers = [
        (
            "model.rotary_emb.inv_freq",
            SimpleNamespace(shape=(64,), device="cuda:1", dtype="float32"),
        )
    ]

    def authenticate(root: Path, inventory: Path) -> dict[str, Any]:
        state.hash_calls += 1
        state.events.append("hash")
        if state.fail == "hash":
            raise ValueError("bad live bytes")
        return {
            "content_sha256": "b" * 64 if state.drift and state.hash_calls > 1 else "a" * 64,
            "full_inventory_match": False,
        }

    monkeypatch.setattr(adapter, "authenticate_runtime", authenticate)

    def template(messages: list[dict[str, str]], **kwargs: Any) -> str:
        assert kwargs == {
            "tokenize": False,
            "add_generation_prompt": True,
            "enable_thinking": False,
        }
        state.messages.append(messages)
        messages[0]["content"] += " changed only in copy"
        return "synthetic rendered prompt"

    def tokenize(rendered: str, **kwargs: Any) -> Inputs:
        state.tokenizer_options.append(kwargs)
        inputs = Inputs(
            input_ids=SimpleNamespace(shape=(state.batch, state.input_count)),
            attention_mask=SimpleNamespace(shape=(1, 1 if state.bad_mask else state.input_count)),
        )
        if state.extras:
            inputs["token_type_ids"] = object()
        return inputs

    class Tokenizer:
        pad_token_id = 0
        apply_chat_template = staticmethod(template)

        def __call__(self, rendered: str, **kwargs: Any) -> Inputs:
            return tokenize(rendered, **kwargs)

        def decode(self, tokens: Tokens, **kwargs: Any) -> str:
            return str(state.output)

    def generate(**kwargs: Any) -> Tokens:
        state.calls.append(kwargs)
        if state.fail:
            raise RuntimeError("synthetic sensitive exception")
        return Tokens(state.input_count + state.output_count)

    model = SimpleNamespace(
        config=SimpleNamespace(to_dict=lambda: geometry, max_position_embeddings=32768),
        generation_config=SimpleNamespace(eos_token_id=[1, 2], do_sample=True),
        eval=lambda: None,
        named_parameters=lambda **kw: parameters,
        named_buffers=lambda **kw: buffers,
        generate=generate,
    )

    def load_tokenizer(path: Path, **kwargs: Any) -> Tokenizer:
        state.events.append("tokenizer")
        state.options.append(kwargs)
        return Tokenizer()

    def load_model(path: Path, **kwargs: Any) -> SimpleNamespace:
        state.events.append("model")
        state.options.append(kwargs)
        state.loaded = True
        return model

    cuda = SimpleNamespace(
        is_available=lambda: state.available,
        device_count=lambda: state.devices,
        set_device=lambda device: state.events.append(("set_device", device)),
        synchronize=lambda device: None,
        mem_get_info=lambda device: (state.free, 16 * GIB),
        get_device_name=lambda device: state.name,
        set_per_process_memory_fraction=lambda fraction, device: state.events.append(
            ("cap", device, fraction)
        ),
        reset_peak_memory_stats=lambda device: state.events.append(("reset_peak", device)),
        memory_allocated=lambda device: 100 if state.loaded or state.occupied else 0,
        memory_reserved=lambda device: 200 if state.loaded or state.occupied else 0,
        max_memory_allocated=lambda device: state.peak,
        max_memory_reserved=lambda device: state.peak,
    )
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            cuda=cuda,
            float16="float16",
            float32="float32",
            manual_seed=state.seeds.append,
            inference_mode=nullcontext,
            __version__="FAKE",
            version=SimpleNamespace(cuda="FAKE"),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            AutoTokenizer=SimpleNamespace(from_pretrained=load_tokenizer),
            Qwen2ForCausalLM=SimpleNamespace(from_pretrained=load_model),
            GenerationConfig=lambda **kw: SimpleNamespace(**kw),
            __version__="FAKE",
        ),
    )
    return SimpleNamespace(
        state=state,
        model=model,
        parameters=parameters,
        buffers=buffers,
        root=model_path,
        inventory=tmp_path / "inventory.json",
        metrics=tmp_path / "metrics.jsonl",
        geometry=geometry,
    )


def load(fake: SimpleNamespace) -> adapter.AgentHFBackend:
    return adapter.AgentHFBackend(fake.root, fake.inventory, fake.metrics)


def test_caps_before_load_and_full_identity(fake: SimpleNamespace) -> None:
    backend = load(fake)
    events = fake.state.events
    for item in [("cap", 0, 12 / 16), ("cap", 1, 7 / 16)]:
        assert events.index(item) < events.index("tokenizer") < events.index("model")
    assert fake.state.hash_calls == 2 and events[0] == events[-1] == "hash"
    assert backend.model_revision.endswith("a" * 64)
    for options in fake.state.options:
        assert options["local_files_only"] and not options["trust_remote_code"]
    options = fake.state.options[-1]
    assert options["device_map"] == PlacementPlan().device_map()
    assert options["max_memory"] == {0: 12 * GIB, 1: 7 * GIB}
    assert options["dtype"] == "float16" and options["use_safetensors"]
    record = json.loads(fake.metrics.read_text())
    assert record["placement_sha256"] == PlacementPlan().sha256
    assert len(record["memory"]) == 2
    assert not record["runtime_admission"]["full_inventory_match"]


@pytest.mark.parametrize(
    "case",
    [
        "cuda",
        "count",
        "name",
        "memory",
        "occupied",
        "hash",
        "drift",
        "offload",
        "shape",
        "dtype",
        "missing",
        "duplicate",
        "buffer",
        "geometry",
        "peak",
    ],
)
def test_load_rejection(fake: SimpleNamespace, case: str) -> None:
    if case == "cuda":
        fake.state.available = False
    elif case == "count":
        fake.state.devices = 3
    elif case == "name":
        fake.state.name = "other GPU"
    elif case == "memory":
        fake.state.free = 13 * GIB - 1
    elif case == "occupied":
        fake.state.occupied = True
    elif case == "hash":
        fake.state.fail = "hash"
    elif case == "drift":
        fake.state.drift = True
    elif case == "offload":
        fake.parameters[0][1].device = "cpu"
    elif case in ("shape", "dtype"):
        setattr(fake.parameters[0][1], case, (2,) if case == "shape" else "bfloat16")
    elif case == "missing":
        fake.parameters.pop()
    elif case == "duplicate":
        fake.parameters.append(fake.parameters[0])
    elif case == "buffer":
        fake.buffers[0][1].shape = (128,)
    elif case == "geometry":
        fake.geometry["num_hidden_layers"] = 27
    elif case == "peak":
        fake.state.peak = 7 * GIB + 1
    with pytest.raises((ValueError, RuntimeError)):
        load(fake)
    assert not fake.metrics.exists()
    if case in {"cuda", "count", "name", "memory", "occupied", "hash"}:
        assert not fake.state.options


def test_fresh_generation_metrics_and_message_isolation(fake: SimpleNamespace) -> None:
    backend = load(fake)
    first = [{"role": "user", "content": "synthetic A"}]
    second = [{"role": "user", "content": "synthetic B"}]
    for messages in (first, second, first):
        assert backend.generate(messages, GenerationConfig()).text == "synthetic answer"
    assert first[0]["content"] == "synthetic A" and second[0]["content"] == "synthetic B"
    generations = [c["generation_config"] for c in fake.state.calls]
    assert len({id(g) for g in generations}) == 3
    for call in fake.state.calls:
        assert set(call) == {"input_ids", "attention_mask", "generation_config"}
        g = call["generation_config"]
        assert g.max_new_tokens == 512 and g.cache_implementation == "dynamic"
        assert g.num_beams == 1 and g.use_cache and not g.do_sample
        assert not g.output_hidden_states and not g.output_scores and not g.output_attentions
    assert fake.state.seeds == [42, 42, 42]
    assert all(not kw["truncation"] for kw in fake.state.tokenizer_options)
    raw = fake.metrics.read_text()
    assert "synthetic" not in raw and "prompt" not in raw
    records = [json.loads(line) for line in raw.splitlines()]
    assert len(records) == 4
    assert records[-1]["input_tokens"] == 20 and records[-1]["output_tokens"] == 4
    assert records[-1]["generate_seconds"] >= 0 and records[-1]["tokenize_seconds"] >= 0


@pytest.mark.parametrize(
    "case",
    [
        "empty",
        "context",
        "native_context",
        "batch",
        "mask",
        "extras",
        "oom",
        "reasoning",
        "decoding",
        "zero_output",
        "long_output",
        "placement_drift",
        "peak",
    ],
)
def test_generation_failure_retires(fake: SimpleNamespace, case: str) -> None:
    backend = load(fake)
    generation = GenerationConfig()
    if case in ("empty", "context"):
        fake.state.input_count = 0 if case == "empty" else 4097
    elif case == "native_context":
        fake.model.config.max_position_embeddings = 520
    elif case == "batch":
        fake.state.batch = 2
    elif case == "mask":
        fake.state.bad_mask = True
    elif case == "extras":
        fake.state.extras = True
    elif case == "oom":
        fake.state.fail = True
    elif case == "reasoning":
        fake.state.output = "<think>synthetic hidden reasoning</think>"
    elif case == "decoding":
        generation = GenerationConfig(seed=41)
    elif case in ("zero_output", "long_output"):
        fake.state.output_count = 0 if case == "zero_output" else 513
    elif case == "placement_drift":
        fake.parameters[0][1].device = "cpu"
    elif case == "peak":
        fake.state.peak = 7 * GIB + 1
    with pytest.raises(RuntimeError, match="retired"):
        backend.generate([{"role": "user", "content": "synthetic request"}], generation)
    calls = len(fake.state.calls)
    with pytest.raises(RuntimeError, match="retired"):
        backend.generate([{"role": "user", "content": "synthetic retry"}], GenerationConfig())
    assert len(fake.state.calls) == calls
    if case in {
        "empty",
        "context",
        "native_context",
        "batch",
        "mask",
        "extras",
        "decoding",
        "peak",
        "placement_drift",
    }:
        assert calls == 0
    assert "synthetic" not in fake.metrics.read_text()
    assert json.loads(fake.metrics.read_text().splitlines()[-1])["status"] == "ERROR"


@pytest.mark.parametrize("count", [1, 4096])
def test_context_boundaries(fake: SimpleNamespace, count: int) -> None:
    backend = load(fake)
    fake.state.input_count = count
    assert backend.generate([{"role": "user", "content": "fixture"}], GenerationConfig()).text


@pytest.mark.parametrize("case", ["existing", "inside", "linked"])
def test_metrics_path(fake: SimpleNamespace, case: str) -> None:
    if case == "existing":
        fake.metrics.write_text("keep")
    elif case == "inside":
        fake.metrics = fake.root / "metrics"
    else:
        fake.metrics.symlink_to(fake.root / "target")
    with pytest.raises(ValueError):
        load(fake)
    assert not fake.state.events


def test_metrics_failure_and_concurrency(
    fake: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = load(fake)
    backend._lock.acquire()
    try:
        with pytest.raises(RuntimeError, match="one agent request"):
            backend.generate([], GenerationConfig())
    finally:
        backend._lock.release()
    assert not fake.state.calls

    def fail_write(*args: Any, **kwargs: Any) -> None:
        raise OSError("synthetic secret storage error")

    monkeypatch.setattr(backend, "_write", fail_write)
    with pytest.raises(RuntimeError, match="metrics unavailable"):
        backend.generate([{"role": "user", "content": "fixture"}], GenerationConfig())
    with pytest.raises(RuntimeError, match="retired"):
        backend.generate([], GenerationConfig())


@pytest.mark.parametrize(
    "messages",
    [
        [],
        [{"role": "tool", "content": "fixture"}],
        [{"role": "user", "content": "fixture", "extra": "x"}],
    ],
)
def test_invalid_messages(fake: SimpleNamespace, messages: list[dict[str, str]]) -> None:
    backend = load(fake)
    with pytest.raises(RuntimeError, match="retired"):
        backend.generate(messages, GenerationConfig())
    assert not fake.state.calls


def test_native_inert_defaults(fake: SimpleNamespace) -> None:
    fake.geometry.update(
        rope_scaling=None,
        auto_map=None,
        quantization_config=None,
        layer_types=["full_attention"] * 28,
    )
    assert load(fake).generate([{"role": "user", "content": "fixture"}], GenerationConfig()).text


@pytest.mark.parametrize(
    "key,value",
    [
        ("rope_scaling", {}),
        ("auto_map", {}),
        ("quantization_config", {}),
        ("layer_types", ["sliding_attention"] * 28),
    ],
)
def test_native_active_overrides_rejected(fake: SimpleNamespace, key: str, value: Any) -> None:
    fake.geometry[key] = value
    with pytest.raises(ValueError):
        load(fake)
