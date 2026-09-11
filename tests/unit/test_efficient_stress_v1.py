"""Synthetic orchestration only: no Torch/model import or CUDA allocation."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace as NS
from typing import Any

import pytest

from react_agent.llm import efficient_stress_v1 as impl


class Tensor:
    def __init__(self, heads: int, tokens: int, device: int) -> None:
        self.shape = (1, heads, tokens, 128)
        self.dtype = "float16"
        self.device = f"cuda:{device}"

    def __getitem__(self, key: Any) -> Any:
        return self

    def expand(self, *shape: int) -> Any:
        return self

    def reshape(self, *shape: int) -> Any:
        result = Tensor(shape[1], shape[2], int(self.device[-1]))
        result.shape = shape
        return result

    def transpose(self, *args: Any) -> Any:
        return self

    def contiguous(self) -> Any:
        return self


def fake() -> tuple[Any, Any, list[Any]]:
    enabled = dict(flash=True, math=True, mem_efficient=True, cudnn=True)
    calls = []

    def sdpa(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs.copy()))
        return args[0]

    @contextmanager
    def kernel(backend: Any) -> Any:
        assert backend == "efficient"
        before = enabled.copy()
        enabled.update(flash=False, math=False, mem_efficient=True, cudnn=False)
        try:
            yield
        finally:
            enabled.update(before)

    @contextmanager
    def profile(**kwargs: Any) -> Any:
        assert kwargs == {"activities": ["cpu"]}
        yield NS(key_averages=lambda: [NS(key=impl.EFFICIENT_OPERATOR)])

    torch = NS(
        float16="float16",
        bool="bool",
        nn=NS(
            functional=NS(scaled_dot_product_attention=sdpa),
            attention=NS(sdpa_kernel=kernel, SDPBackend=NS(EFFICIENT_ATTENTION="efficient")),
        ),
        backends=NS(cuda=NS(**{n + "_sdp_enabled": (lambda n=n: enabled[n]) for n in enabled})),
        profiler=NS(profile=profile, ProfilerActivity=NS(CPU="cpu")),
    )
    return torch, NS(use_gqa_in_sdpa=lambda mask, key: mask is None), calls


def invoke(
    torch: Any, hf: Any, role: str, index: int, *, mask: bool = False, **changes: Any
) -> Any:
    spec = impl.expected(role, index)  # type: ignore[arg-type]
    q = Tensor(spec["heads"], spec["query_tokens"], spec["device"])
    k = Tensor(spec["heads"], spec["key_tokens"], spec["device"])
    v = Tensor(spec["heads"], spec["key_tokens"], spec["device"])
    explicit = None
    if mask:
        explicit = Tensor(1, 1, spec["device"])
        explicit.shape = (1, 1, spec["query_tokens"], spec["key_tokens"])
    assert hf.use_gqa_in_sdpa(explicit, k) is False
    kw = dict(
        attn_mask=explicit,
        dropout_p=0.0,
        scale=128**-0.5,
        is_causal=spec["query_tokens"] > 1 and explicit is None,
    )
    kw.update(changes)
    return torch.nn.functional.scaled_dot_product_attention(q, k, v, **kw)


@pytest.mark.parametrize("role,total", [("agent", 14364), ("guard", 3612)])
@pytest.mark.parametrize("mask", [False, True])
def test_full_sequence_mask_identity_and_restoration(role: Any, total: int, mask: bool) -> None:
    torch, hf, calls = fake()
    originals = (
        hf.use_gqa_in_sdpa,
        torch.nn.functional.scaled_dot_product_attention,
        impl.flags(torch),
    )
    records: dict[str, Any] = {}

    def save(stage: str, **values: Any) -> None:
        assert stage not in records
        records[stage] = values

    def run() -> str:
        for i in range(total):
            invoke(torch, hf, role, i, mask=mask)
        return "response"

    assert impl.scoped_call(torch, hf, role, run, save) == "response"
    assert len(calls) == total
    assert records["completed"]["completed_attention_calls"] == total
    assert records["completed"]["masks"] == {
        "none": 0 if mask else total,
        "explicit": total if mask else 0,
    }
    assert [s["index"] for s in records["completed"]["dispatch_samples"]] == [0, total - 28]
    assert (
        hf.use_gqa_in_sdpa,
        torch.nn.functional.scaled_dot_product_attention,
        impl.flags(torch),
    ) == originals
    assert set(records) == {"entered", "dispatch_1", "dispatch_2", "restored", "completed"}
    # Original builtin receives the exact mask, not a replacement or value copy.
    assert all(kw["attn_mask"] is not None for _, kw in calls) == mask


@pytest.mark.parametrize(
    "changes",
    [
        dict(enable_gqa=True),
        dict(scale=1.0),
        dict(dropout_p=0.1),
        dict(is_causal=False),
        dict(is_causal=1),
    ],
)
def test_refuse_changed_dispatch_and_restore(changes: dict[str, Any]) -> None:
    torch, hf, calls = fake()
    original = hf.use_gqa_in_sdpa
    records = []
    with pytest.raises(ValueError):
        impl.scoped_call(
            torch,
            hf,
            "agent",
            lambda: invoke(torch, hf, "agent", 0, **changes),
            lambda stage, **v: records.append((stage, v)),
        )
    assert not calls
    assert hf.use_gqa_in_sdpa is original
    assert records[-1][1]["state_restored"] is True
    assert not impl._SCOPE_LOCK.locked()


@pytest.mark.parametrize("error", [RuntimeError, KeyboardInterrupt, ValueError])
def test_native_failure_preserved_and_scope_reusable(error: Any) -> None:
    torch, hf, calls = fake()
    records = []

    def fail() -> None:
        invoke(torch, hf, "guard", 0)
        raise error("do not persist secret-like text")

    with pytest.raises(error):
        impl.scoped_call(torch, hf, "guard", fail, lambda s, **v: records.append((s, v)))
    assert records[-2][1]["error_class"] == error.__name__
    assert "secret-like" not in str(records)
    assert records[-1][1]["state_restored"]
    assert not impl._SCOPE_LOCK.locked()


def test_missing_calls_not_success() -> None:
    torch, hf, _ = fake()
    with pytest.raises(ValueError, match="complete all-layer"):
        impl.scoped_call(torch, hf, "agent", lambda: None, lambda *a, **kw: None)


def test_nested_scope_refused() -> None:
    torch, hf, _ = fake()
    with pytest.raises(RuntimeError, match="non-nested"):
        impl.scoped_call(
            torch,
            hf,
            "agent",
            lambda: impl.scoped_call(torch, hf, "guard", lambda: None, lambda *a, **kw: None),
            lambda *a, **kw: None,
        )
    assert not impl._SCOPE_LOCK.locked()


def test_foreign_thread_refused() -> None:
    torch, hf, _ = fake()
    failures = []

    def worker() -> None:
        try:
            hf.use_gqa_in_sdpa(None, None)
        except RuntimeError as exc:
            failures.append(str(exc))

    def run() -> None:
        t = threading.Thread(target=worker)
        t.start()
        t.join()

    with pytest.raises(ValueError, match="complete all-layer"):
        impl.scoped_call(torch, hf, "agent", run, lambda *a, **kw: None)
    assert failures == ["attention scope called from foreign owner"]


@pytest.mark.parametrize(
    "role,index", [("other", 0), ("agent", -1), ("agent", 14364), ("guard", 3612)]
)
def test_boundaries_rejected(role: Any, index: int) -> None:
    with pytest.raises(ValueError):
        impl.expected(role, index)


def test_factory_topology_validated_atomically(tmp_path: Path) -> None:
    from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig, ReadyFactory
    from react_agent.llm.worker_progress_v1 import ThreadProgressFactory

    pair = ModelPair(
        lambda: None, lambda: None, PairConfig(ModelIdentity("a", "1"), ModelIdentity("g", "1"))
    )  # type: ignore[arg-type,return-value]
    original = pair._workers["agent"].factory
    pair._workers["guard"].factory = lambda: None  # type: ignore[assignment,return-value]
    with pytest.raises(ValueError):
        impl.instrument_pair(pair, tmp_path / "o", tmp_path / "p", tmp_path / "a")
    assert pair._workers["agent"].factory is original
    pair._workers["guard"].factory = ReadyFactory(lambda: None)  # type: ignore[arg-type,return-value]
    impl.instrument_pair(pair, tmp_path / "o", tmp_path / "p", tmp_path / "a")
    for worker in pair._workers.values():
        assert type(worker.factory) is ReadyFactory
        assert type(worker.factory.factory) is ThreadProgressFactory
        assert type(worker.factory.factory.factory) is impl.EfficientStressFactory
    with pytest.raises(ValueError):
        impl.instrument_pair(pair, tmp_path / "o", tmp_path / "p", tmp_path / "a")


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize("masked", [False, True])
def test_verified_hf_source_composes_repeat_and_preserves_mask(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: Any, masked: bool
) -> None:
    import hashlib
    import importlib.util
    import sys
    import zipfile
    from types import ModuleType

    wheel = (
        Path(__file__).resolve().parents[2]
        / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/transformers-5.5.0-py3-none-any.whl"
    )
    if not wheel.exists():
        pytest.skip("Pinned wheel absent; no native composition claim")
    assert (
        hashlib.sha256(wheel.read_bytes()).hexdigest()
        == "821a9ff0961abbb29eb1eb686d78df1c85929fdf213a3fe49dc6bd94f9efa944"
    )
    with zipfile.ZipFile(wheel) as archive:
        source = archive.read("transformers/integrations/sdpa_attention.py")
    assert hashlib.sha256(source).hexdigest() == impl.SDPA_SHA
    path = tmp_path / "sdpa.py"
    path.write_bytes(source)
    torch, _, calls = fake()
    torch.Tensor, torch.nn.Module = Tensor, object
    torch.jit = NS(is_tracing=lambda: False)
    monkeypatch.setitem(sys.modules, "torch", torch)
    for name in (
        "_hf_fixture",
        "_hf_fixture.integrations",
        "_hf_fixture.utils",
        "_hf_fixture.utils.import_utils",
    ):
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    utils = sys.modules["_hf_fixture.utils"]
    utils.is_torch_npu_available = lambda: False
    utils.is_torch_xpu_available = lambda: False
    utils.logging = NS(get_logger=lambda _: NS(warning_once=lambda _: None))
    sys.modules["_hf_fixture.utils.import_utils"].is_torch_greater_or_equal = lambda *a, **kw: True
    spec = importlib.util.spec_from_file_location("_hf_fixture.integrations.sdpa", path)
    assert spec and spec.loader
    hf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hf)
    masks = []

    def run() -> None:
        total = 14364 if role == "agent" else 3612
        for index in range(total):
            geometry = impl.expected(role, index)
            heads, kv = (28, 4) if role == "agent" else (12, 2)
            q = Tensor(heads, geometry["query_tokens"], geometry["device"])
            k = Tensor(kv, geometry["key_tokens"], geometry["device"])
            v = Tensor(kv, geometry["key_tokens"], geometry["device"])
            mask = None
            if masked:
                mask = Tensor(1, 1, geometry["device"])
                mask.shape = (1, 1, geometry["query_tokens"], geometry["key_tokens"])
            masks.append(mask)
            hf.sdpa_attention_forward(
                NS(num_key_value_groups=heads // kv, is_causal=True),
                q,
                k,
                v,
                mask,
                scaling=128**-0.5,
            )

    impl.scoped_call(torch, hf, role, run, lambda *a, **kw: None)
    assert all(args[1].shape[1] == args[0].shape[1] for args, _ in calls)
    assert all(kw["attn_mask"] is mask for (_, kw), mask in zip(calls, masks, strict=True))
