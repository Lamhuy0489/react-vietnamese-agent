"""Experimental request-local attention adapter; not yet wired into benchmark runtime."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.llm.agent_hf_v2 import AgentHFBackendV2
from react_agent.llm.agent_mount_v1 import MODEL, no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.efficient_stress_v1 import flags
from react_agent.llm.guard_hf_v1 import GuardHFBackend, GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION, MODEL_ID
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.llm.model_pair_v1 import Role
from react_agent.llm.sdpa_probe_v1 import SDPA_SHA, libraries

_LOCK = threading.Lock()
GUARD_REVISION = f"hf:{CANDIDATE_REVISION};snapshot-sha256:" + (
    "36b6d38e9e3cbc47427b1fabcf6f44fdd926a1d95a04a33bbfb19d7f1ffd5fbe"
)


class RequestGeometry:
    """Validate ordinary cached generation, never force length or keep tensor values."""

    def __init__(self, role: Role) -> None:
        if role not in ("agent", "guard"):
            raise ValueError("known role required")
        self.role = role
        self.limit = 512 if role == "agent" else 128
        self.calls = 0
        self.input_tokens: int | None = None
        self.masked_calls = 0

    def check(self, torch: Any, q: Any, k: Any, v: Any, kw: dict[str, Any]) -> None:
        forward, layer = divmod(self.calls, 28)
        if forward >= self.limit or set(kw) != {"attn_mask", "dropout_p", "scale", "is_causal"}:
            raise ValueError("bounded ordinary HF generation required")
        shape = tuple(q.shape)
        if len(shape) != 4:
            raise ValueError("rank-four attention required")
        if self.input_tokens is None:
            if type(shape[2]) is not int or not 1 <= shape[2] <= 4096:
                raise ValueError("input length outside frozen cap")
            self.input_tokens = shape[2]
        query = self.input_tokens if forward == 0 else 1
        key = self.input_tokens + forward
        heads = 28 if self.role == "agent" else 12
        device = f"cuda:{0 if self.role == 'agent' and layer < 20 else 1}"
        for tensor, tokens in ((q, query), (k, key), (v, key)):
            if (
                tuple(tensor.shape) != (1, heads, tokens, 128)
                or tensor.dtype != torch.float16
                or str(tensor.device) != device
            ):
                raise ValueError("request-local KV/head/placement sequence mismatch")
        mask = kw["attn_mask"]
        if kw["dropout_p"] != 0.0 or kw["scale"] != 128**-0.5:
            raise ValueError("native inference scaling/dropout required")
        if type(kw["is_causal"]) is not bool or kw["is_causal"] != (query > 1 and mask is None):
            raise ValueError("native causal semantics required")
        if mask is not None and (
            tuple(mask.shape) != (1, 1, query, key)
            or mask.dtype not in (torch.float16, torch.bool)
            or str(mask.device) != device
        ):
            raise ValueError("bounded full mask required")

    def completed(self, masked: bool) -> None:
        self.calls += 1
        self.masked_calls += int(masked)

    def summary(self) -> dict[str, Any]:
        if not self.calls or self.calls % 28 or self.input_tokens is None:
            raise ValueError("complete layer groups required")
        return dict(
            input_tokens=self.input_tokens,
            attention_calls=self.calls,
            forward_groups=self.calls // 28,
            last_forward_key_tokens=self.input_tokens + self.calls // 28 - 1,
            masked_calls=self.masked_calls,
            max_new_tokens=self.limit,
            output_tokens_verified=False,
            full_boundary_cache_verified=False,
        )


def request_scope(
    torch: Any, hf: Any, role: Role, call: Callable[[], ModelResponse], save: Callable[..., None]
) -> ModelResponse:
    """No profiling/replay; original builtin is delegated exactly once per call."""
    geometry = RequestGeometry(role)
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError("one attention scope per process")
    installed = False
    owner = (os.getpid(), threading.get_ident())
    try:
        old_gqa = hf.use_gqa_in_sdpa
        old_sdpa = torch.nn.functional.scaled_dot_product_attention
        before = flags(torch)
        # Refuse existing instrumentation (including the frozen stress scope).
        if (
            old_gqa.__module__ != hf.__name__
            or old_sdpa is not torch._C._nn.scaled_dot_product_attention
        ):
            raise ValueError("unmodified pinned native bindings required")
        helpers = 0

        def owning() -> None:
            if owner != (os.getpid(), threading.get_ident()):
                raise RuntimeError("foreign attention owner")

        def no_gqa(mask: Any, key: Any) -> bool:
            nonlocal helpers
            owning()
            if helpers != geometry.calls:
                raise ValueError("ordered single HF helper call required")
            helpers += 1
            return False

        def observed(q: Any, k: Any, v: Any, **kw: Any) -> Any:
            owning()
            if helpers != geometry.calls + 1 or flags(torch) != dict(
                flash=False, math=False, mem_efficient=True, cudnn=False
            ):
                raise ValueError("efficient-only backend and HF helper required")
            geometry.check(torch, q, k, v, kw)
            result = old_sdpa(q, k, v, **kw)
            geometry.completed(kw["attn_mask"] is not None)
            return result

        save("entered", hf_sdpa_sha256=SDPA_SHA, flags_before=before)
        try:
            hf.use_gqa_in_sdpa = no_gqa
            torch.nn.functional.scaled_dot_product_attention = observed
            installed = True
            with torch.nn.attention.sdpa_kernel(torch.nn.attention.SDPBackend.EFFICIENT_ATTENTION):
                response = call()
            summary = geometry.summary()
            if helpers != geometry.calls:
                raise ValueError("unconsumed native helper call")
        except BaseException as exc:
            save("error", error_class=type(exc).__name__, attention_calls=geometry.calls)
            raise
        finally:
            if installed:
                hf.use_gqa_in_sdpa = old_gqa
                torch.nn.functional.scaled_dot_product_attention = old_sdpa
            restored = (
                hf.use_gqa_in_sdpa is old_gqa
                and torch.nn.functional.scaled_dot_product_attention is old_sdpa
                and flags(torch) == before
            )
            save("restored", state_restored=restored, flags_after=flags(torch))
        if not restored:
            raise RuntimeError("native state not restored; retire worker")
        save(
            "completed",
            **summary,
            state_restored=True,
            helper_calls=helpers,
            profiler_used=False,
            decoding_changed=False,
            scope="All-call geometry/efficient-only guards, not profiled dispatch, "
            "output count or full KV proof",
        )
        return response
    finally:
        _LOCK.release()


class EfficientRequestBackend:
    """Many successful requests in one task; any failure permanently retires it."""

    def __init__(self, native: LLMBackend, role: Role, output: Path) -> None:
        RequestGeometry(role)
        no_links(output)
        if output.exists():
            raise ValueError("fresh attention evidence root required")
        self.native, self.role, self.output = native, role, output
        self.model_id, self.model_revision = native.model_id, native.model_revision
        self._owner = os.getpid()
        self._lock = threading.Lock()
        self._retired = False
        self._index = 0

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if os.getpid() != self._owner or not self._lock.acquire(blocking=False):
            raise RuntimeError("one owning request worker required")
        try:
            if self._retired:
                raise RuntimeError("attention backend retired; no retries")
            self._index += 1
            try:
                if config != GenerationConfig(max_new_tokens=512 if self.role == "agent" else 128):
                    raise ValueError("frozen role generation config required")
                if (self.native.model_id, self.native.model_revision) != (
                    self.model_id,
                    self.model_revision,
                ):
                    raise ValueError("native identity drift")
                torch, hf = libraries()
                if hf.sdpa_attention_forward.__globals__ is not vars(hf):
                    raise ValueError("native helper globals mismatch")
                target = self.output / f"request_{self._index:06d}"
                no_links(target)
                target.mkdir(parents=True, exist_ok=False)

                def save(stage: str, **values: Any) -> None:
                    write_receipt(
                        target / f"{stage}.json",
                        dict(
                            protocol="efficient_requests_v1",
                            stage=stage,
                            role=self.role,
                            pid=self._owner,
                            request_index=self._index,
                            model_id=self.model_id,
                            model_revision=self.model_revision,
                            **values,
                        ),
                    )

                def invoke() -> ModelResponse:
                    response = self.native.generate(messages, config)
                    if (self.native.model_id, self.native.model_revision) != (
                        self.model_id,
                        self.model_revision,
                    ) or (response.model_id, response.model_revision) != (
                        self.model_id,
                        self.model_revision,
                    ):
                        raise ValueError("native response identity drift")
                    return response

                return request_scope(torch, hf, self.role, invoke, save)
            except BaseException:
                self._retired = True
                raise
        finally:
            self._lock.release()


@dataclass(frozen=True)
class EfficientRequestFactory:
    native_factory: Callable[[], LLMBackend]
    role: Role
    output: Path

    def __call__(self) -> LLMBackend:
        RequestGeometry(self.role)
        no_links(self.output)
        if self.output.exists():
            raise ValueError("fresh evidence required before model load")
        native = self.native_factory()
        expected = AgentHFBackendV2 if self.role == "agent" else GuardHFBackend
        identity = (MODEL, AGENT_REVISION) if self.role == "agent" else (MODEL_ID, GUARD_REVISION)
        if type(native) is not expected or (native.model_id, native.model_revision) != identity:
            raise ValueError("exact authenticated native loader/identity required")
        if isinstance(native, GuardHFBackend) and native.config != GuardHFConfig():
            raise ValueError("frozen guard limits required")
        return EfficientRequestBackend(native, self.role, self.output)
