"""Pinned, no-weights tensor experiment; never installed into model attention."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

CAP = 2 * 1024**3
ATOL, RTOL = 0.005, 0.01
SDPA_SHA = "87f933d1a2d8508df572da5c0748c6b24c22ff2b625796949957dcd86cc57564"


def cases() -> list[dict[str, Any]]:
    rows = []
    for role, heads, kv, device, boundary in (("agent", 28, 4, 0, 4608), ("guard", 12, 2, 1, 4224)):
        for label, qlen, klen, mode in (
            ("short_prefill", 128, 128, "parity"),
            ("short_decode", 1, 257, "parity"),
            ("long_native", 4096, 4096, "native"),
            ("long_repeat", 4096, 4096, "repeat"),
            ("boundary_decode", 1, boundary, "repeat"),
        ):
            rows.append(
                dict(
                    name=f"{role}_{label}",
                    role=role,
                    heads=heads,
                    kv_heads=kv,
                    device=device,
                    query_tokens=qlen,
                    key_tokens=klen,
                    mode=mode,
                    head_dim=128,
                    seed=42,
                )
            )
    return rows


def libraries() -> tuple[Any, Any]:
    import torch  # type: ignore[import-not-found]
    import torch.nn.attention  # type: ignore[import-not-found]
    import transformers  # type: ignore[import-not-found]
    from transformers.integrations import sdpa_attention  # type: ignore[import-not-found]

    if (str(torch.__version__), str(torch.version.cuda), transformers.__version__) != (
        "2.10.0+cu128",
        "12.8",
        "5.5.0",
    ):
        raise ValueError("pinned GPU image libraries required")
    if hashlib.sha256(Path(sdpa_attention.__file__).read_bytes()).hexdigest() != SDPA_SHA:
        raise ValueError("installed HF SDPA source differs")
    if torch.cuda.device_count() != 2:
        raise ValueError("two pinned T4 devices required")
    return torch, sdpa_attention


def attention(torch: Any, hf: Any, q: Any, k: Any, v: Any, mode: str) -> Any:
    """Identical logical heads/scale/causality; repeat path refuses math fallback."""
    groups = q.shape[1] // k.shape[1]
    if mode == "native":
        module = SimpleNamespace(num_key_value_groups=groups, is_causal=True)
        return hf.sdpa_attention_forward(module, q, k, v, None, dropout=0.0)[0]
    if mode != "repeat":
        raise ValueError("known attention treatment required")
    k, v = hf.repeat_kv(k, groups), hf.repeat_kv(v, groups)
    with torch.nn.attention.sdpa_kernel(torch.nn.attention.SDPBackend.EFFICIENT_ATTENTION):
        out = torch.nn.functional.scaled_dot_product_attention(
            q,
            k,
            v,
            attn_mask=None,
            dropout_p=0.0,
            is_causal=q.shape[2] > 1,
            enable_gqa=False,
        )
    return out.transpose(1, 2).contiguous()


def memory(torch: Any, device: int) -> dict[str, int]:
    cuda = torch.cuda
    free, total = cuda.mem_get_info(device)
    return dict(
        allocated=int(cuda.memory_allocated(device)),
        reserved=int(cuda.memory_reserved(device)),
        peak_allocated=int(cuda.max_memory_allocated(device)),
        peak_reserved=int(cuda.max_memory_reserved(device)),
        global_free=int(free),
        global_total=int(total),
    )


def run_case(case: dict[str, Any], backend: str) -> dict[str, Any]:
    if case not in cases() or backend not in ("stub", "native"):
        raise ValueError("predeclared case/backend required")
    record: dict[str, Any] = dict(
        protocol="sdpa_tensor_case_v1",
        case=case,
        backend=backend,
        pid=os.getpid(),
        model_loads=0,
        model_generate_calls=0,
        tensor_values_retained=False,
    )
    if backend == "stub":
        return {**record, "native_verified": False, "status": "SIMULATED"}
    torch, hf = libraries()
    device = case["device"]
    torch.cuda.set_device(device)
    capability = list(torch.cuda.get_device_capability(device))
    name = torch.cuda.get_device_name(device)
    if capability != [7, 5] or name != "Tesla T4":
        raise ValueError("pinned T4 capability required")
    total = int(torch.cuda.get_device_properties(device).total_memory)
    torch.cuda.set_per_process_memory_fraction(CAP / total, device)
    torch.manual_seed(case["seed"])
    q = torch.randn(
        (1, case["heads"], case["query_tokens"], 128), dtype=torch.float16, device=device
    )
    k = torch.randn(
        (1, case["kv_heads"], case["key_tokens"], 128), dtype=torch.float16, device=device
    )
    v = torch.randn_like(k)
    torch.cuda.synchronize(device)
    fingerprints = [hashlib.sha256(t.cpu().numpy().tobytes()).hexdigest() for t in (q, k, v)]
    cuda = torch.backends.cuda
    gqa = bool(hf.use_gqa_in_sdpa(None, k))
    params = cuda.SDPAParams(q, k, v, None, 0.0, case["query_tokens"] > 1, gqa)
    eligibility = dict(
        flash=bool(cuda.can_use_flash_attention(params)),
        efficient=bool(cuda.can_use_efficient_attention(params)),
        cudnn=bool(cuda.can_use_cudnn_attention(params)),
    )
    del params
    record.update(
        native_verified=True,
        status="OBSERVED",
        input_sha256=fingerprints,
        hf_use_gqa=gqa,
        native_eligibility=eligibility,
        environment=dict(
            torch=str(torch.__version__),
            cuda=str(torch.version.cuda),
            transformers="5.5.0",
            hf_sdpa_sha256=SDPA_SHA,
            device_name=name,
            capability=capability,
        ),
        allocator_cap_bytes=CAP,
        modes=[],
        parity=None,
    )
    results = []
    for mode in ("native", "repeat") if case["mode"] == "parity" else (case["mode"],):
        torch.cuda.reset_peak_memory_stats(device)
        before = memory(torch, device)
        started = time.perf_counter()
        result = None
        status, error = "OK", None
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
            try:
                with torch.inference_mode():
                    result = attention(torch, hf, q, k, v, mode)
                torch.cuda.synchronize(device)
            except torch.OutOfMemoryError:
                status, error = "OOM", "OutOfMemoryError"
            except RuntimeError:
                # Unsupported dispatch is measured failure, never a fallback.
                status, error = "ERROR", "RuntimeError"
        elapsed = time.perf_counter() - started
        after = memory(torch, device)
        operators = sorted({e.key for e in prof.key_averages() if "scaled_dot_product" in e.key})
        item = dict(
            mode=mode,
            status=status,
            error_class=error,
            instrumented_seconds=elapsed,
            before=before,
            after=after,
            operators=operators,
            output_shape=None,
            output_finite=None,
        )
        if result is not None:
            item.update(
                output_shape=list(result.shape),
                output_finite=bool(torch.isfinite(result).all().item()),
            )
            results.append(result)
        record["modes"].append(item)
    if case["mode"] == "parity" and len(results) == 2:
        a, b = (t.float() for t in results)
        diff = (a - b).abs()
        record["parity"] = dict(
            atol=ATOL,
            rtol=RTOL,
            max_abs_error=float(diff.max().item()),
            max_tolerance_excess=float((diff - (ATOL + RTOL * a.abs())).max().item()),
            passed=bool(torch.all(diff <= ATOL + RTOL * a.abs()).item()),
        )
    return record
