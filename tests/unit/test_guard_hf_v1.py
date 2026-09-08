"""CPU adapter contract tests; fake tensors are NOT real inference evidence."""

from __future__ import annotations

import json
import pickle
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from react_agent.llm.base import GenerationConfig
from react_agent.llm.guard_hf_v1 import GuardHFBackend, GuardHFConfig, GuardHFFactory
from react_agent.llm.guard_snapshot_v1 import (
    CANDIDATE_REVISION,
    REQUIRED,
    GuardSnapshot,
    describe_snapshot,
    verify_snapshot,
)

SAFE = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'
GENERATION = GenerationConfig(max_new_tokens=128)


@pytest.fixture
def snapshot(tmp_path: Path) -> tuple[Path, GuardSnapshot]:
    root = tmp_path / "snapshot"
    root.mkdir()
    for name in REQUIRED:
        (root / name).write_text("synthetic fixture", encoding="utf-8")
    (root / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen2",
                "architectures": ["Qwen2ForCausalLM"],
            }
        )
    )
    return root, describe_snapshot(root, CANDIDATE_REVISION)


class Inputs(dict[str, Any]):
    def to(self, device: str) -> Inputs:
        self.device = device
        return self


class Tokens:
    shape = (4,)

    def __getitem__(self, key: object) -> Tokens:
        return self


class FakeTokenizer:
    pad_token_id = 0
    output = SAFE
    input_count = 20

    def __init__(self) -> None:
        self.messages: list[list[dict[str, str]]] = []
        self.tokenizer_options: list[dict[str, Any]] = []

    def apply_chat_template(self, messages: list[dict[str, str]], **kw: Any) -> str:
        self.messages.append(messages)
        assert kw == {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False}
        # Deliberate mutation must not leak to the caller.
        messages[0]["content"] += "-fake-template"
        return "fake-rendered-prompt"

    def __call__(self, rendered: str, **kw: Any) -> Inputs:
        self.tokenizer_options.append(kw)
        return Inputs(
            input_ids=SimpleNamespace(shape=(1, self.input_count)), attention_mask=object()
        )

    def decode(self, tokens: Tokens, **kw: Any) -> str:
        return self.output


class FakeModel:
    config = SimpleNamespace(max_position_embeddings=32768)
    generation_config = SimpleNamespace(eos_token_id=[1, 2], do_sample=True)
    tensor_device = "cuda:1"
    fail = False

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def eval(self) -> None:
        pass

    def parameters(self) -> list[Any]:
        return [SimpleNamespace(device=self.tensor_device)]

    def buffers(self) -> list[Any]:
        return []

    def generate(self, **kw: Any) -> Tokens:
        self.calls.append(kw)
        if self.fail:
            raise RuntimeError("synthetic sensitive failure details")
        return Tokens()


@pytest.fixture
def fake_modules(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    tokenizer, model = FakeTokenizer(), FakeModel()
    state = SimpleNamespace(free=12 * 1024**3, available=True, allocations=[], seeds=[], loaders=[])
    cuda = SimpleNamespace(
        is_available=lambda: state.available,
        device_count=lambda: 2,
        set_device=lambda device: None,
        synchronize=lambda device: None,
        mem_get_info=lambda device: (state.free, 16 * 1024**3),
        set_per_process_memory_fraction=lambda fraction, device: state.allocations.append(
            (fraction, device)
        ),
        reset_peak_memory_stats=lambda device: None,
        memory_allocated=lambda device: 300,
        memory_reserved=lambda device: 400,
        max_memory_allocated=lambda device: 500,
        max_memory_reserved=lambda device: 600,
        get_device_name=lambda device: "FAKE T4",
    )

    def load_tokenizer(path: Path, **kw: Any) -> FakeTokenizer:
        state.loaders.append(("tokenizer", kw))
        return tokenizer

    def load_model(path: Path, **kw: Any) -> FakeModel:
        state.loaders.append(("model", kw))
        return model

    torch = SimpleNamespace(
        cuda=cuda,
        float16="float16",
        manual_seed=state.seeds.append,
        inference_mode=nullcontext,
        __version__="FAKE",
        version=SimpleNamespace(cuda="FAKE"),
    )
    transformers = SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=load_tokenizer),
        Qwen2ForCausalLM=SimpleNamespace(from_pretrained=load_model),
        GenerationConfig=lambda **kw: SimpleNamespace(**kw),
        __version__="FAKE",
    )
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    return SimpleNamespace(tokenizer=tokenizer, model=model, state=state)


def backend(snapshot: tuple[Path, GuardSnapshot], tmp_path: Path, **kw: Any) -> GuardHFBackend:
    root, pin = snapshot
    return GuardHFFactory(root, pin, GuardHFConfig(**kw), tmp_path / "metrics.jsonl")()


def test_snapshot_identity_and_serialization(snapshot: tuple[Path, GuardSnapshot]) -> None:
    root, pin = snapshot
    assert pin == GuardSnapshot.model_validate_json(pin.model_dump_json())
    assert pin.model_revision.endswith(pin.sha256)
    verify_snapshot(root, pin)


@pytest.mark.parametrize("name", sorted(REQUIRED))
def test_every_snapshot_file_is_bound(snapshot: tuple[Path, GuardSnapshot], name: str) -> None:
    root, pin = snapshot
    (root / name).write_text("modified fixture")
    with pytest.raises(ValueError):
        verify_snapshot(root, pin)


@pytest.mark.parametrize("name", ["custom.py", "pytorch_model.bin", "extra.json", "subdir"])
def test_extra_snapshot_entries_rejected(snapshot: tuple[Path, GuardSnapshot], name: str) -> None:
    root, pin = snapshot
    (root / name).write_text("unexpected")
    with pytest.raises(ValueError):
        verify_snapshot(root, pin)


def test_missing_and_symlink_rejected(snapshot: tuple[Path, GuardSnapshot], tmp_path: Path) -> None:
    root, pin = snapshot
    original = root / "model.safetensors"
    destination = tmp_path / "weights"
    original.rename(destination)
    with pytest.raises(ValueError):
        verify_snapshot(root, pin)
    original.symlink_to(destination)
    with pytest.raises(ValueError):
        verify_snapshot(root, pin)


@pytest.mark.parametrize("revision", ["main", "v1", "989aa79", "a" * 39, "G" * 40])
def test_mutable_revision_rejected(snapshot: tuple[Path, GuardSnapshot], revision: str) -> None:
    root, _ = snapshot
    with pytest.raises(ValueError):
        describe_snapshot(root, revision)


@pytest.mark.parametrize(
    "change",
    [
        {"model_type": "other"},
        {"architectures": ["RemoteModel"]},
        {"auto_map": {}},
        {"quantization_config": {}},
    ],
)
def test_unsupported_model_config(
    snapshot: tuple[Path, GuardSnapshot], change: dict[str, Any]
) -> None:
    root, _ = snapshot
    path = root / "config.json"
    path.write_text(json.dumps(json.loads(path.read_text()) | change))
    with pytest.raises(ValueError):
        describe_snapshot(root, CANDIDATE_REVISION)


def test_duplicate_inventory_rejected(snapshot: tuple[Path, GuardSnapshot]) -> None:
    _, pin = snapshot
    with pytest.raises(ValueError):
        GuardSnapshot(upstream_revision=CANDIDATE_REVISION, files=pin.files + pin.files[:1])


def test_factory_is_picklable(snapshot: tuple[Path, GuardSnapshot], tmp_path: Path) -> None:
    root, pin = snapshot
    factory = GuardHFFactory(root, pin, GuardHFConfig(), tmp_path / "metrics.jsonl")
    assert pickle.loads(pickle.dumps(factory)) == factory  # noqa: S301 - local self-created fixture


def test_offline_load_budget_and_metrics(
    snapshot: tuple[Path, GuardSnapshot], tmp_path: Path, fake_modules: SimpleNamespace
) -> None:
    instance = backend(snapshot, tmp_path)
    assert instance.model_revision == snapshot[1].model_revision
    assert fake_modules.state.allocations == [(5 / 16, 1)]
    for _, options in fake_modules.state.loaders:
        assert options["local_files_only"] is True
        assert options["trust_remote_code"] is False
    options = fake_modules.state.loaders[-1][1]
    assert options["device_map"] == {"": 1}
    assert options["use_safetensors"] is True
    record = json.loads((tmp_path / "metrics.jsonl").read_text())
    assert record["snapshot_sha256"] == snapshot[1].sha256
    assert record["process_peak_allocated_bytes"] == 500
    assert record["global_free_bytes"] == fake_modules.state.free


def test_fresh_calls_no_shared_messages_or_generation_cache(
    snapshot: tuple[Path, GuardSnapshot], tmp_path: Path, fake_modules: SimpleNamespace
) -> None:
    instance = backend(snapshot, tmp_path)
    first = [{"role": "user", "content": "synthetic A"}]
    second = [{"role": "user", "content": "synthetic B"}]
    for messages in [first, second, first]:
        assert instance.generate(messages, GENERATION).text == SAFE
    assert first[0]["content"] == "synthetic A"
    assert second[0]["content"] == "synthetic B"
    assert [m[0]["content"] for m in fake_modules.tokenizer.messages] == [
        "synthetic A-fake-template",
        "synthetic B-fake-template",
        "synthetic A-fake-template",
    ]
    configs = [c["generation_config"] for c in fake_modules.model.calls]
    assert len({id(c) for c in configs}) == 3
    for call in fake_modules.model.calls:
        assert set(call) == {"input_ids", "attention_mask", "generation_config"}
        gen = call["generation_config"]
        assert not gen.do_sample and gen.cache_implementation == "dynamic"
        assert gen.use_cache and gen.num_beams == 1 and gen.max_new_tokens == 128
        assert not gen.output_attentions and not gen.output_hidden_states
    assert fake_modules.state.seeds == [42, 42, 42]
    assert all(not c["truncation"] for c in fake_modules.tokenizer.tokenizer_options)
    metrics = (tmp_path / "metrics.jsonl").read_text()
    assert "synthetic A" not in metrics and SAFE not in metrics and "fake-rendered" not in metrics
    assert len(metrics.splitlines()) == 4


@pytest.mark.parametrize(
    "option,value",
    [
        ("device", -1),
        ("device", True),
        ("allocator_limit_bytes", 0),
        ("free_headroom_bytes", 0),
        ("max_input_tokens", 0),
        ("max_input_tokens", 32641),
    ],
)
def test_invalid_budget(option: str, value: int) -> None:
    with pytest.raises(ValueError):
        GuardHFConfig(**{option: value})


@pytest.mark.parametrize("condition", ["missing_cuda", "device", "memory", "offload"])
def test_load_fail_closed(
    snapshot: tuple[Path, GuardSnapshot],
    tmp_path: Path,
    fake_modules: SimpleNamespace,
    condition: str,
) -> None:
    if condition == "missing_cuda":
        fake_modules.state.available = False
    if condition == "memory":
        fake_modules.state.free = 6 * 1024**3 - 1
    if condition == "offload":
        fake_modules.model.tensor_device = "cpu"
    with pytest.raises(RuntimeError):
        backend(snapshot, tmp_path, device=2 if condition == "device" else 1)
    assert not (tmp_path / "metrics.jsonl").exists()


@pytest.mark.parametrize("condition", ["context", "model_context", "oom", "reasoning", "decoding"])
def test_generation_failure_retires_without_sensitive_logs(
    snapshot: tuple[Path, GuardSnapshot],
    tmp_path: Path,
    fake_modules: SimpleNamespace,
    condition: str,
) -> None:
    instance = backend(snapshot, tmp_path)
    if condition == "context":
        fake_modules.tokenizer.input_count = 4097
    if condition == "model_context":
        fake_modules.model.config = SimpleNamespace(max_position_embeddings=140)
    if condition == "oom":
        fake_modules.model.fail = True
    if condition == "reasoning":
        fake_modules.tokenizer.output = "<think>synthetic sensitive content</think>"
    generation = (
        GenerationConfig(max_new_tokens=128, seed=41) if condition == "decoding" else GENERATION
    )
    with pytest.raises(RuntimeError, match="backend retired"):
        instance.generate([{"role": "user", "content": "synthetic request"}], generation)
    calls = len(fake_modules.model.calls)
    with pytest.raises(RuntimeError, match="retired"):
        instance.generate([{"role": "user", "content": "another request"}], GENERATION)
    assert len(fake_modules.model.calls) == calls
    if condition in {"context", "model_context", "decoding"}:
        assert calls == 0
    metrics = (tmp_path / "metrics.jsonl").read_text()
    assert "synthetic" not in metrics and "<think>" not in metrics
    assert json.loads(metrics.splitlines()[-1])["status"] == "ERROR"


def test_existing_or_snapshot_metrics_rejected(
    snapshot: tuple[Path, GuardSnapshot], tmp_path: Path, fake_modules: SimpleNamespace
) -> None:
    backend(snapshot, tmp_path)
    with pytest.raises(ValueError):
        backend(snapshot, tmp_path)
    root, pin = snapshot
    with pytest.raises(ValueError):
        GuardHFFactory(root, pin, GuardHFConfig(), root / "metrics.jsonl")()


def test_concurrent_call_rejected(
    snapshot: tuple[Path, GuardSnapshot], tmp_path: Path, fake_modules: SimpleNamespace
) -> None:
    instance = backend(snapshot, tmp_path)
    instance._lock.acquire()
    try:
        with pytest.raises(RuntimeError, match="one guard request"):
            instance.generate([{"role": "user", "content": "fixture"}], GENERATION)
    finally:
        instance._lock.release()
    assert not fake_modules.model.calls


@pytest.mark.parametrize(
    "messages",
    [
        [],
        [{"role": "tool", "content": "fixture"}],
        [{"role": "user", "content": "fixture", "extra": "not allowed"}],
    ],
)
def test_invalid_messages_rejected(
    snapshot: tuple[Path, GuardSnapshot],
    tmp_path: Path,
    fake_modules: SimpleNamespace,
    messages: list[dict[str, str]],
) -> None:
    instance = backend(snapshot, tmp_path)
    with pytest.raises(RuntimeError):
        instance.generate(messages, GENERATION)
    assert not fake_modules.model.calls


def test_metrics_failure_does_not_return_success(
    snapshot: tuple[Path, GuardSnapshot],
    tmp_path: Path,
    fake_modules: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance = backend(snapshot, tmp_path)

    def unavailable(record: dict[str, Any], **kw: Any) -> None:
        raise OSError("synthetic sensitive disk error")

    monkeypatch.setattr(instance, "_write", unavailable)
    with pytest.raises(RuntimeError, match="metrics unavailable"):
        instance.generate([{"role": "user", "content": "fixture"}], GENERATION)
    with pytest.raises(RuntimeError, match="retired"):
        instance.generate([{"role": "user", "content": "fixture"}], GENERATION)
    assert len(fake_modules.model.calls) == 1


def test_tampering_during_load_is_rejected(
    snapshot: tuple[Path, GuardSnapshot],
    tmp_path: Path,
    fake_modules: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def changed() -> None:
        (snapshot[0] / "tokenizer_config.json").write_text("changed during fake load")

    monkeypatch.setattr(fake_modules.model, "eval", changed)
    with pytest.raises(ValueError, match="content mismatch"):
        backend(snapshot, tmp_path)
    assert not (tmp_path / "metrics.jsonl").exists()


def test_tampering_rejected_before_load(
    snapshot: tuple[Path, GuardSnapshot], tmp_path: Path, fake_modules: SimpleNamespace
) -> None:
    (snapshot[0] / "model.safetensors").write_text("wrong weights")
    with pytest.raises(ValueError):
        backend(snapshot, tmp_path)
    assert not fake_modules.state.loaders


def test_exact_context_limit_allowed(
    snapshot: tuple[Path, GuardSnapshot], tmp_path: Path, fake_modules: SimpleNamespace
) -> None:
    instance = backend(snapshot, tmp_path)
    fake_modules.tokenizer.input_count = 4096
    assert instance.generate([{"role": "user", "content": "fixture"}], GENERATION).text == SAFE


def test_identity_changes_with_inventory_and_budget(snapshot: tuple[Path, GuardSnapshot]) -> None:
    root, pin = snapshot
    (root / "tokenizer_config.json").write_text("new trusted synthetic tokenizer")
    new = describe_snapshot(root, CANDIDATE_REVISION)
    assert new.model_revision != pin.model_revision
    assert GuardHFConfig().sha256 != GuardHFConfig(max_input_tokens=2048).sha256
