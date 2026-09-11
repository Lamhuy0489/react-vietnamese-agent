"""Opt-in, single-worker SDPA treatment for the frozen context diagnostic only."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.generation_policy_v1 import PolicyStressBackend, PolicyStressFactory
from react_agent.llm.model_pair_v1 import ModelPair, ReadyFactory, Role
from react_agent.llm.sdpa_probe_v1 import SDPA_SHA, libraries
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory

_SCOPE_LOCK = threading.Lock()
EFFICIENT_OPERATOR = "aten::_scaled_dot_product_efficient_attention"


def flags(torch: Any) -> dict[str, bool]:
    cuda = torch.backends.cuda
    return {
        n: bool(getattr(cuda, n + "_sdp_enabled")())
        for n in ("flash", "math", "mem_efficient", "cudnn")
    }


def expected(role: Role, index: int) -> dict[str, Any]:
    """One ordered call per layer per forward, including the last-token forward."""
    if role not in ("agent", "guard") or not 0 <= index < 28 * (513 if role == "agent" else 129):
        raise ValueError("fixed role and bounded attention count required")
    forward, layer = divmod(index, 28)
    return dict(
        query_tokens=4096 if forward == 0 else 1,
        key_tokens=4096 + forward,
        heads=28 if role == "agent" else 12,
        device=0 if role == "agent" and layer < 20 else 1,
    )


def scoped_call(
    torch: Any, hf: Any, role: Role, call: Callable[[], Any], save: Callable[..., None]
) -> Any:
    """Private-worker global scope; preserve all HF mask/scale/causality handling."""
    if not _SCOPE_LOCK.acquire(blocking=False):
        raise RuntimeError("one non-nested attention scope per process required")
    owner = (os.getpid(), threading.get_ident())
    original_gqa, original_sdpa = (
        hf.use_gqa_in_sdpa,
        torch.nn.functional.scaled_dot_product_attention,
    )
    try:
        before = flags(torch)
        expected(role, 0)
    except BaseException:
        _SCOPE_LOCK.release()
        raise
    count, helpers = 0, 0
    total = 28 * (513 if role == "agent" else 129)
    samples: list[dict[str, Any]] = []
    masks = {"none": 0, "explicit": 0}
    installed = False

    def owning() -> None:
        if (os.getpid(), threading.get_ident()) != owner:
            raise RuntimeError("attention scope called from foreign owner")

    def no_native_gqa(mask: Any, key: Any) -> bool:
        nonlocal helpers
        owning()
        helpers += 1
        if helpers != count + 1:
            raise ValueError("one HF eligibility call before each SDPA required")
        return False

    def observed(q: Any, k: Any, v: Any, **kw: Any) -> Any:
        nonlocal count
        owning()
        spec = expected(role, count)
        if helpers != count + 1 or flags(torch) != dict(
            flash=False, math=False, mem_efficient=True, cudnn=False
        ):
            raise ValueError("efficient-only dispatch and ordered HF helper required")
        if set(kw) != {"attn_mask", "dropout_p", "scale", "is_causal"}:
            raise ValueError("unchanged HF SDPA keywords required; no native GQA")
        for t, length in (
            (q, spec["query_tokens"]),
            (k, spec["key_tokens"]),
            (v, spec["key_tokens"]),
        ):
            if (
                tuple(t.shape) != (1, spec["heads"], length, 128)
                or t.dtype != torch.float16
                or str(t.device) != f"cuda:{spec['device']}"
            ):
                raise ValueError("exact repeated heads/FP16/context/device required")
        mask = kw["attn_mask"]
        if kw["dropout_p"] != 0.0 or kw["scale"] != 128**-0.5:
            raise ValueError("unchanged inference dropout and Qwen scaling required")
        if type(kw["is_causal"]) is not bool or kw["is_causal"] != (
            spec["query_tokens"] > 1 and mask is None
        ):
            raise ValueError("native causal behavior required")
        if mask is not None and (
            tuple(mask.shape) != (1, 1, spec["query_tokens"], spec["key_tokens"])
            or mask.dtype not in (torch.float16, torch.bool)
            or str(mask.device) != str(q.device)
        ):
            raise ValueError("bounded native mask shape/dtype/device required")
        masks["none" if mask is None else "explicit"] += 1
        index = count
        # Only two actual calls are profiled: first prefill and first layer of
        # final-forward boundary. No extra forward, warmup or replay is issued.
        if index in (0, total - 28):
            with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as prof:
                result = original_sdpa(q, k, v, **kw)
            operators = sorted(
                {e.key for e in prof.key_averages() if "scaled_dot_product" in e.key}
            )
            if EFFICIENT_OPERATOR not in operators or any(
                "math" in n or "flash" in n for n in operators
            ):
                raise ValueError("observed efficient dispatch required")
            samples.append(dict(index=index, **spec, operators=operators))
            save(f"dispatch_{len(samples)}", sample=samples[-1])
        else:
            result = original_sdpa(q, k, v, **kw)
        count += 1
        return result

    try:
        save(
            "entered",
            hf_sdpa_sha256=SDPA_SHA,
            flags_before=before,
            planned_attention_calls=total,
            numerical_treatment="HF repeat_kv + forced EFFICIENT_ATTENTION",
            decoding_changed=False,
        )
        hf.use_gqa_in_sdpa = no_native_gqa
        torch.nn.functional.scaled_dot_product_attention = observed
        installed = True
        with torch.nn.attention.sdpa_kernel(torch.nn.attention.SDPBackend.EFFICIENT_ATTENTION):
            result = call()
        if count != total or helpers != total or len(samples) != 2:
            raise ValueError("complete all-layer full-boundary attention coverage required")
    except BaseException as exc:
        save(
            "error",
            error_class=type(exc).__name__,
            completed_attention_calls=count,
            helper_calls=helpers,
        )
        raise
    finally:
        if installed:
            hf.use_gqa_in_sdpa = original_gqa
            torch.nn.functional.scaled_dot_product_attention = original_sdpa
        restored = (
            hf.use_gqa_in_sdpa is original_gqa
            and torch.nn.functional.scaled_dot_product_attention is original_sdpa
            and flags(torch) == before
        )
        try:
            save(
                "restored",
                state_restored=restored,
                flags_after=flags(torch),
                completed_attention_calls=count,
                helper_calls=helpers,
            )
        finally:
            _SCOPE_LOCK.release()
    if not restored:
        raise RuntimeError("attention state not restored; retire worker")
    save(
        "completed",
        completed_attention_calls=count,
        helper_calls=helpers,
        masks=masks,
        dispatch_samples=samples,
        state_restored=True,
        decoding_changed=False,
        timing_scope="Two attention calls have CPU profiler instrumentation; not benchmark latency",
    )
    return result


class EfficientStressBackend:
    def __init__(self, inner: PolicyStressBackend, output: Path) -> None:
        no_links(output)
        if output.exists():
            raise ValueError("fresh attention evidence required")
        self.inner, self.output = inner, output
        self.model_id, self.model_revision = inner.model_id, inner.model_revision
        self._owner, self._used = os.getpid(), False
        self._lock = threading.Lock()

    def _save(self, stage: str, **values: Any) -> None:
        write_receipt(
            self.output / f"{stage}.json",
            dict(
                protocol="efficient_stress_v1",
                stage=stage,
                pid=self._owner,
                role=self.inner.inner.role,
                model_id=self.model_id,
                model_revision=self.model_revision,
                **values,
            ),
        )

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if os.getpid() != self._owner or not self._lock.acquire(blocking=False):
            raise RuntimeError("single owning attention worker required")
        try:
            if self._used:
                raise RuntimeError("single-use attention backend required")
            self._used = True
            torch, hf = libraries()
            if (
                hf.sdpa_attention_forward.__globals__ is not vars(hf)
                or hf.use_gqa_in_sdpa.__module__ != hf.__name__
                or torch.nn.functional.scaled_dot_product_attention
                is not torch._C._nn.scaled_dot_product_attention
            ):
                raise ValueError("unmodified native attention bindings required")
            self.output.mkdir(parents=True, exist_ok=False)
            response: ModelResponse = scoped_call(
                torch,
                hf,
                self.inner.inner.role,
                lambda: self.inner.generate(messages, config),
                self._save,
            )
            return response
        finally:
            self._lock.release()


@dataclass(frozen=True)
class EfficientStressFactory:
    policy: PolicyStressFactory
    output: Path

    def __call__(self) -> LLMBackend:
        no_links(self.output)
        if self.output.exists():
            raise ValueError("fresh attention output required before model load")
        inner = self.policy()
        if type(inner) is not PolicyStressBackend:
            raise TypeError("exact policy backend required")
        return EfficientStressBackend(inner, self.output)


def instrument_pair(pair: ModelPair, output: Path, policy: Path, attention: Path) -> None:
    roots = (output, policy, attention)
    if pair.state != "NEW":
        raise ValueError("fresh unstarted pair required")
    for i, root in enumerate(roots):
        no_links(root)
        if root.exists() or any(
            root.resolve().is_relative_to(other.resolve())
            or other.resolve().is_relative_to(root.resolve())
            for other in roots[i + 1 :]
        ):
            raise ValueError("fresh separate diagnostic roots required")
    factories: dict[Role, ReadyFactory] = {}
    for role in ("agent", "guard"):
        ready = pair._workers[role].factory
        if type(ready) is not ReadyFactory or isinstance(
            ready.factory,
            (ReadyFactory, ThreadProgressFactory, PolicyStressFactory, EfficientStressFactory),
        ):
            raise ValueError("one unmodified ReadyFactory per role required")
        factories[role] = ready
    for role, ready in factories.items():
        pair._workers[role].factory = ReadyFactory(
            ThreadProgressFactory(
                EfficientStressFactory(
                    PolicyStressFactory(
                        ready.factory, role, output / f"{role}_stress", policy / role
                    ),
                    attention / role,
                )
            )
        )
