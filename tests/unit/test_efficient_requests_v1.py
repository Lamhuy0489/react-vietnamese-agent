"""No-model request lifecycle and variable-geometry attention controls."""

import json
from pathlib import Path
from types import FunctionType
from types import SimpleNamespace as NS
from typing import Any

import pytest
from test_efficient_stress_v1 import Tensor, fake

from react_agent.llm import efficient_requests_v1 as impl
from react_agent.llm.base import GenerationConfig, ModelResponse


def libraries() -> tuple[Any, Any, Any]:
    torch, hf, calls = fake()
    hf.__name__ = "synthetic_hf"
    hf.use_gqa_in_sdpa.__module__ = hf.__name__
    hf.sdpa_attention_forward = FunctionType((lambda: None).__code__, vars(hf))
    torch._C = NS(
        _nn=NS(scaled_dot_product_attention=torch.nn.functional.scaled_dot_product_attention)
    )
    return torch, hf, calls


def tensors(role: str, input_tokens: int, index: int, masked: bool = False) -> tuple[Any, ...]:
    f, layer = divmod(index, 28)
    device = 0 if role == "agent" and layer < 20 else 1
    heads = 28 if role == "agent" else 12
    query, key = input_tokens if f == 0 else 1, input_tokens + f
    q, k, v = Tensor(heads, query, device), Tensor(heads, key, device), Tensor(heads, key, device)
    mask = None
    if masked:
        mask = Tensor(1, 1, device)
        mask.shape = (1, 1, query, key)
    return (
        q,
        k,
        v,
        dict(attn_mask=mask, dropout_p=0.0, scale=128**-0.5, is_causal=query > 1 and not masked),
    )


def generate(
    torch: Any, hf: Any, role: str, length: int, outputs: int, masked: bool = False
) -> ModelResponse:
    for i in range(28 * outputs):
        q, k, v, kw = tensors(role, length, i, masked)
        assert hf.use_gqa_in_sdpa(kw["attn_mask"], k) is False
        torch.nn.functional.scaled_dot_product_attention(q, k, v, **kw)
    return ModelResponse(text="synthetic", model_id="model", model_revision="revision")


@pytest.mark.parametrize(
    "role,length,outputs",
    [
        ("agent", 1, 1),
        ("guard", 1, 1),
        ("agent", 4096, 512),
        ("guard", 4096, 128),
        ("agent", 23, 3),
        ("guard", 99, 7),
    ],
)
@pytest.mark.parametrize("masked", [False, True])
def test_variable_sequence_and_scoped_restore(
    role: Any, length: int, outputs: int, masked: bool
) -> None:
    torch, hf, calls = libraries()
    old = hf.use_gqa_in_sdpa, torch.nn.functional.scaled_dot_product_attention, impl.flags(torch)
    records = {}
    result = impl.request_scope(
        torch,
        hf,
        role,
        lambda: generate(torch, hf, role, length, outputs, masked),
        lambda stage, **v: records.update({stage: v}),
    )
    assert result.text == "synthetic" and len(calls) == 28 * outputs
    assert records["completed"]["forward_groups"] == outputs
    assert records["completed"]["last_forward_key_tokens"] == length + outputs - 1
    assert records["completed"]["masked_calls"] == (28 * outputs if masked else 0)
    assert not records["completed"]["output_tokens_verified"]
    assert not records["completed"]["full_boundary_cache_verified"]
    assert (
        hf.use_gqa_in_sdpa,
        torch.nn.functional.scaled_dot_product_attention,
        impl.flags(torch),
    ) == old
    assert set(records) == {"entered", "restored", "completed"}


@pytest.mark.parametrize(
    "fault",
    [
        "length_zero",
        "length_over",
        "cache_reused",
        "head",
        "device",
        "dtype",
        "scale",
        "causal",
        "gqa",
        "mask",
        "incomplete",
        "over_output",
        "no_calls",
        "no_helper",
        "double_helper",
    ],
)
def test_invalid_sequences_fail_and_restore(fault: str) -> None:
    torch, hf, _ = libraries()
    old = hf.use_gqa_in_sdpa
    records = {}

    def run() -> ModelResponse:
        if fault == "no_calls":
            return ModelResponse(text="", model_id="m", model_revision="r")
        q, k, v, kw = tensors("guard", 5, 0)
        if fault == "length_zero":
            q.shape = (1, 12, 0, 128)
        elif fault == "length_over":
            q.shape = (1, 12, 4097, 128)
        elif fault == "cache_reused":
            k.shape = (1, 12, 6, 128)
        elif fault == "head":
            k.shape = (1, 2, 5, 128)
        elif fault == "device":
            q.device = "cuda:0"
        elif fault == "dtype":
            q.dtype = "float32"
        elif fault == "scale":
            kw["scale"] = 1.0
        elif fault == "causal":
            kw["is_causal"] = False
        elif fault == "gqa":
            kw["enable_gqa"] = True
        elif fault == "mask":
            kw["attn_mask"] = Tensor(1, 5, 1)
        if fault == "over_output":
            return generate(torch, hf, "guard", 5, 129)
        if fault != "no_helper":
            hf.use_gqa_in_sdpa(None, k)
        if fault == "double_helper":
            hf.use_gqa_in_sdpa(None, k)
        torch.nn.functional.scaled_dot_product_attention(q, k, v, **kw)
        return ModelResponse(text="", model_id="m", model_revision="r")

    with pytest.raises(ValueError):
        impl.request_scope(torch, hf, "guard", run, lambda stage, **v: records.update({stage: v}))
    assert records["restored"]["state_restored"]
    assert hf.use_gqa_in_sdpa is old and not impl._LOCK.locked()
    assert "completed" not in records


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt])
def test_exception_and_writer_error_release_scope(failure: Any) -> None:
    torch, hf, _ = libraries()
    old = hf.use_gqa_in_sdpa

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise failure("not saved")

    with pytest.raises(failure):
        impl.request_scope(torch, hf, "agent", fail, lambda *a, **k: None)
    assert hf.use_gqa_in_sdpa is old and not impl._LOCK.locked()
    with pytest.raises(failure):
        impl.request_scope(torch, hf, "agent", lambda: generate(torch, hf, "agent", 2, 1), fail)
    assert hf.use_gqa_in_sdpa is old and not impl._LOCK.locked()


def test_existing_hook_refused_without_mutation() -> None:
    torch, hf, _ = libraries()
    old = hf.use_gqa_in_sdpa
    torch.nn.functional.scaled_dot_product_attention = lambda *a, **kw: None
    with pytest.raises(ValueError, match="unmodified"):
        impl.request_scope(torch, hf, "agent", lambda: None, lambda *a, **kw: None)  # type: ignore[arg-type,return-value]
    assert hf.use_gqa_in_sdpa is old and not impl._LOCK.locked()


def test_backend_multi_request_then_permanent_retirement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    torch, hf, _ = libraries()
    monkeypatch.setattr(impl, "libraries", lambda: (torch, hf))
    seen = []

    def native(messages: Any, config: Any) -> ModelResponse:
        seen.append(messages)
        return generate(torch, hf, "agent", int(messages[0]["content"]), 2)

    backend = impl.EfficientRequestBackend(
        NS(model_id="model", model_revision="revision", generate=native),
        "agent",
        tmp_path / "evidence",
    )
    for length in (5, 17, 5):
        assert (
            backend.generate([dict(role="user", content=str(length))], GenerationConfig()).text
            == "synthetic"
        )
    assert len(seen) == 3
    rows = [
        json.loads(p.read_text()) for p in sorted((tmp_path / "evidence").glob("*/completed.json"))
    ]
    assert [r["input_tokens"] for r in rows] == [5, 17, 5]
    assert [r["request_index"] for r in rows] == [1, 2, 3]
    with pytest.raises(ValueError):
        backend.generate([dict(role="user", content="4097")], GenerationConfig())
    with pytest.raises(RuntimeError, match="retired"):
        backend.generate([dict(role="user", content="5")], GenerationConfig())
    assert len(seen) == 4


@pytest.mark.parametrize("kind", ["identity", "response_identity", "config", "pid", "lock"])
def test_backend_admission_and_retirement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    torch, hf, _ = libraries()
    monkeypatch.setattr(impl, "libraries", lambda: (torch, hf))
    native = NS(
        model_id="model",
        model_revision="revision",
        generate=lambda *a: generate(torch, hf, "guard", 2, 1),
    )
    b = impl.EfficientRequestBackend(native, "guard", tmp_path / "e")
    if kind == "identity":
        native.model_revision = "changed"
    elif kind == "response_identity":
        native.generate = lambda *a: ModelResponse(
            text="", model_id="other", model_revision="revision"
        )
    elif kind == "pid":
        b._owner = -1
    elif kind == "lock":
        b._lock.acquire()
    with pytest.raises((ValueError, RuntimeError)):
        b.generate([], GenerationConfig(max_new_tokens=1 if kind == "config" else 128))
    if kind not in ("pid", "lock"):
        assert b._retired
    if kind == "lock":
        b._lock.release()


def test_factory_rejects_before_loading(tmp_path: Path) -> None:
    calls = []

    def factory() -> None:
        calls.append(1)

    with pytest.raises(ValueError):
        impl.EfficientRequestFactory(factory, "agent", tmp_path)()  # type: ignore[arg-type]
    assert not calls
    with pytest.raises(ValueError):
        impl.EfficientRequestFactory(factory, "bad", tmp_path / "e")()  # type: ignore[arg-type]
    assert not calls


@pytest.mark.parametrize("stage", ["entered", "restored", "completed", "error"])
def test_receipt_write_failure_restores_and_unlocks(stage: str) -> None:
    torch, hf, _ = libraries()
    old = hf.use_gqa_in_sdpa, torch.nn.functional.scaled_dot_product_attention, impl.flags(torch)

    def save(name: str, **values: Any) -> None:
        if name == stage:
            raise OSError("synthetic storage failure")

    def run() -> ModelResponse:
        if stage == "error":
            raise RuntimeError("synthetic native failure")
        return generate(torch, hf, "agent", 3, 1)

    with pytest.raises(OSError):
        impl.request_scope(torch, hf, "agent", run, save)
    assert (
        hf.use_gqa_in_sdpa,
        torch.nn.functional.scaled_dot_product_attention,
        impl.flags(torch),
    ) == old
    assert not impl._LOCK.locked()


def test_nested_scope_fails_without_overwriting_outer_hook() -> None:
    torch, hf, _ = libraries()
    with pytest.raises(RuntimeError, match="one attention scope"):
        impl.request_scope(
            torch,
            hf,
            "agent",
            lambda: impl.request_scope(
                torch, hf, "guard", lambda: generate(torch, hf, "guard", 3, 1), lambda *a, **k: None
            ),
            lambda *a, **k: None,
        )
    assert not impl._LOCK.locked()


@pytest.mark.parametrize("role", ["agent", "guard"])
def test_factory_exact_native_shape(role: Any, tmp_path: Path) -> None:
    cls = impl.AgentHFBackendV2 if role == "agent" else impl.GuardHFBackend
    value = object.__new__(cls)
    value.model_id = impl.MODEL if role == "agent" else impl.MODEL_ID
    value.model_revision = impl.AGENT_REVISION if role == "agent" else impl.GUARD_REVISION
    if role == "guard":
        value.config = impl.GuardHFConfig()
    backend = impl.EfficientRequestFactory(lambda: value, role, tmp_path / "e")()
    assert isinstance(backend, impl.EfficientRequestBackend)
    assert backend.native is value
    assert not (tmp_path / "e").exists()


@pytest.mark.parametrize("masked", [False, True])
def test_pinned_hf_composition_across_variable_requests(
    masked: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
        pytest.skip("pinned source wheel absent; no native claim")
    assert (
        hashlib.sha256(wheel.read_bytes()).hexdigest()
        == "821a9ff0961abbb29eb1eb686d78df1c85929fdf213a3fe49dc6bd94f9efa944"
    )
    with zipfile.ZipFile(wheel) as z:
        source = z.read("transformers/integrations/sdpa_attention.py")
    assert hashlib.sha256(source).hexdigest() == impl.SDPA_SHA
    path = tmp_path / "native_sdpa.py"
    path.write_bytes(source)
    torch, _, calls = libraries()
    torch.Tensor, torch.nn.Module = Tensor, object
    torch.jit = NS(is_tracing=lambda: False)
    monkeypatch.setitem(sys.modules, "torch", torch)
    for name in (
        "_request_hf",
        "_request_hf.integrations",
        "_request_hf.utils",
        "_request_hf.utils.import_utils",
    ):
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    u = sys.modules["_request_hf.utils"]
    u.is_torch_npu_available = lambda: False
    u.is_torch_xpu_available = lambda: False
    u.logging = NS(get_logger=lambda _: NS(warning_once=lambda _: None))
    sys.modules["_request_hf.utils.import_utils"].is_torch_greater_or_equal = lambda *a, **k: True
    spec = importlib.util.spec_from_file_location("_request_hf.integrations.sdpa", path)
    assert spec and spec.loader
    hf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hf)
    for role in ("agent", "guard"):
        for length, outputs in ((1, 1), (4096, 3), (7, 2)):

            def run(
                role: str = role, length: int = length, outputs: int = outputs
            ) -> ModelResponse:
                for index in range(28 * outputs):
                    q, k, v, kw = tensors(role, length, index, masked)
                    kvheads, groups = (4, 7) if role == "agent" else (2, 6)
                    k.shape = (1, kvheads, k.shape[2], 128)
                    v.shape = k.shape
                    hf.sdpa_attention_forward(
                        NS(num_key_value_groups=groups, is_causal=True),
                        q,
                        k,
                        v,
                        kw["attn_mask"],
                        scaling=kw["scale"],
                    )
                return ModelResponse(text="synthetic", model_id="m", model_revision="r")

            impl.request_scope(torch, hf, role, run, lambda *a, **k: None)
    assert len(calls) == 28 * (1 + 3 + 2) * 2
