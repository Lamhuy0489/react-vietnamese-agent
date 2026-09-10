"""Single-use diagnostic native generation; never a benchmark backend replacement."""

from __future__ import annotations

import copy
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.llm.agent_hf_v2 import AgentHFBackendV2
from react_agent.llm.agent_mount_v1 import MODEL, no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.context_geometry_v1 import (
    INPUT_TOKENS,
    Role,
    build_geometry,
    summarize_generation,
)
from react_agent.llm.guard_hf_v1 import GuardHFBackend, GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION, MODEL_ID
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION

REQUEST = [{"role": "user", "content": "context_stress_v1:fixed_synthetic_geometry"}]
ACK = "context_stress_v1:completed"


def cache_observation(native: Any, role: Role, cache: Any, length: int) -> dict[str, Any]:
    """Inspect all KV tensor shapes/dtypes/devices, never values or hidden states."""
    config = native.model.config
    layers = cache.layers
    if len(layers) != config.num_hidden_layers or cache.get_seq_length() != length:
        raise ValueError("complete native cache required")
    shape = (
        1,
        config.num_key_value_heads,
        length,
        config.hidden_size // config.num_attention_heads,
    )
    by_device: dict[int, int] = {}
    rows = []
    for index, layer in enumerate(layers):
        device = native.plan.device_map()[f"model.layers.{index}"] if role == "agent" else 1
        tensors = (layer.keys, layer.values)
        if any(
            tuple(t.shape) != shape
            or t.dtype != native.torch.float16
            or str(t.device) != f"cuda:{device}"
            for t in tensors
        ):
            raise ValueError("native KV shape/dtype/placement mismatch")
        size = sum(int(t.numel()) * int(t.element_size()) for t in tensors)
        by_device[device] = by_device.get(device, 0) + size
        rows.append({"layer": index, "device": device, "shape": list(shape), "bytes": size})
    return {"sequence_length": length, "layers": rows, "tensor_bytes_by_device": by_device}


class ContextStressBackend:
    """One request, no retries/cache reuse; existing supervisor owns hard timeout.

    Only compose with authenticated native loaders in a dedicated spawn worker.
    Raw model objects and token IDs never cross IPC. Durable stage files survive
    OOM/forced termination; their existence alone does not mean completion.
    """

    def __init__(self, native: Any, role: Role, output: Path) -> None:
        if role not in ("agent", "guard"):
            raise ValueError("fixed stress role required")
        no_links(output)
        output.mkdir(parents=True, exist_ok=False)
        self.native, self.role, self.output = native, role, output
        self.model_id, self.model_revision = native.model_id, native.model_revision
        self._owner = os.getpid()
        self._lock = threading.Lock()
        self._used = False

    def _save(self, stage: str, **values: Any) -> None:
        write_receipt(
            self.output / f"{stage}.json",
            {
                "protocol": "context_stress_v1",
                "stage": stage,
                "pid": self._owner,
                "role": self.role,
                "model_id": self.model_id,
                "model_revision": self.model_revision,
                **values,
            },
        )

    def _memory(self) -> list[dict[str, int]]:
        native = self.native
        rows = []
        for device in (0, 1) if self.role == "agent" else (1,):
            cuda = native.torch.cuda
            free, total = cuda.mem_get_info(device)
            row = {
                "device": device,
                "global_free_bytes": int(free),
                "global_total_bytes": int(total),
                "allocated_bytes": int(cuda.memory_allocated(device)),
                "reserved_bytes": int(cuda.memory_reserved(device)),
                "peak_allocated_bytes": int(cuda.max_memory_allocated(device)),
                "peak_reserved_bytes": int(cuda.max_memory_reserved(device)),
            }
            cap = (
                native.plan.agent_caps[device]
                if self.role == "agent"
                else native.config.allocator_limit_bytes
            )
            if any(
                row[k] < 0 or row[k] > cap
                for k in (
                    "allocated_bytes",
                    "reserved_bytes",
                    "peak_allocated_bytes",
                    "peak_reserved_bytes",
                )
            ):
                raise RuntimeError("stress allocator budget exceeded")
            rows.append(row)
        return rows

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if os.getpid() != self._owner or not self._lock.acquire(blocking=False):
            raise RuntimeError("single owning worker required")
        try:
            if self._used:
                raise RuntimeError("stress backend is single-use; retire worker")
            self._used = True
            started = time.perf_counter()
            self._save("entered")
            try:
                if messages != REQUEST or config != GenerationConfig(
                    max_new_tokens=512 if self.role == "agent" else 128
                ):
                    raise ValueError("diagnostic request/config only")
                self._run(started)
            except Exception as exc:
                # No exception text/locals/traceback/model outputs in evidence.
                self._save(
                    "error",
                    error_class=type(exc).__name__,
                    total_seconds=time.perf_counter() - started,
                )
                raise RuntimeError("context stress failed; retire worker") from None
            return ModelResponse(
                text=ACK, model_id=self.model_id, model_revision=self.model_revision
            )
        finally:
            self._lock.release()

    def _run(self, started: float) -> None:
        native, role = self.native, self.role
        if native.transformers.__version__ != "5.5.0":
            raise ValueError("pinned native Transformers required")
        native.sync()
        for device_index in (0, 1) if role == "agent" else (1,):
            native.torch.cuda.reset_peak_memory_stats(device_index)
        before = self._memory()
        token_started = time.perf_counter()
        geometry = build_geometry(native.tokenizer, role, self.model_revision)
        total_tokens = INPUT_TOKENS + geometry.output_tokens
        if total_tokens > native.model.config.max_position_embeddings:
            raise ValueError("native positional limit exceeded")
        device = "cuda:0" if role == "agent" else "cuda:1"
        ids = native.torch.tensor(
            [list(geometry.input_ids)], dtype=native.torch.long, device=device
        )
        mask = native.torch.ones_like(ids)
        generation = native.transformers.GenerationConfig(
            min_new_tokens=geometry.output_tokens,
            max_new_tokens=geometry.output_tokens,
            do_sample=False,
            num_beams=1,
            use_cache=True,
            cache_implementation="dynamic",
            return_dict_in_generate=True,
            output_scores=False,
            output_logits=False,
            output_attentions=False,
            output_hidden_states=False,
            eos_token_id=copy.deepcopy(native.model.generation_config.eos_token_id),
            pad_token_id=native.tokenizer.pad_token_id,
        )
        self._save(
            "prepared",
            geometry=geometry.receipt(),
            generation=generation.to_dict(),
            tokenize_seconds=time.perf_counter() - token_started,
            memory=before,
            seed=42,
            input_device=device,
            prefill_seconds=None,
            timing_scope="generation aggregate includes prefill; not separated",
        )
        native.torch.manual_seed(42)
        native.sync()
        generated = final = None
        try:
            generation_started = time.perf_counter()
            with native.torch.inference_mode():
                generated = native.model.generate(
                    input_ids=ids, attention_mask=mask, generation_config=generation
                )
            native.sync()
            generation_seconds = time.perf_counter() - generation_started
            if tuple(generated.sequences.shape) != (1, total_tokens):
                raise ValueError("exact forced-length output shape required")
            sequence_ids = generated.sequences[0].tolist()
            cache = generated.past_key_values
            observed = cache_observation(native, role, cache, total_tokens - 1)
            summary = summarize_generation(
                geometry, sequence_ids, cache_length_after_generation=observed["sequence_length"]
            )
            self._save(
                "generated",
                summary=summary,
                cache=observed,
                generation_seconds=generation_seconds,
                memory=self._memory(),
            )
            # Native generation leaves its last emitted token unforwarded. Feed
            # that token exactly once with the existing cache and complete mask.
            native.sync()
            forward_started = time.perf_counter()
            with native.torch.inference_mode():
                final = native.model(
                    input_ids=generated.sequences[:, -1:].to(device),
                    attention_mask=native.torch.ones(
                        (1, total_tokens), dtype=native.torch.long, device=device
                    ),
                    past_key_values=cache,
                    use_cache=True,
                    logits_to_keep=1,
                    return_dict=True,
                    output_attentions=False,
                    output_hidden_states=False,
                )
            native.sync()
            forward_seconds = time.perf_counter() - forward_started
            full = cache_observation(native, role, final.past_key_values, total_tokens)
            summary = summarize_generation(
                geometry,
                sequence_ids,
                cache_length_after_generation=total_tokens - 1,
                cache_length_after_final_forward=full["sequence_length"],
            )
            self._save(
                "completed",
                summary=summary,
                cache=full,
                memory=self._memory(),
                generation_seconds=generation_seconds,
                final_forward_seconds=forward_seconds,
                total_seconds=time.perf_counter() - started,
                model_generation_calls=1,
                separate_final_forwards=1,
                memory_scope="process allocator peaks; global endpoints, not global peak",
            )
        finally:
            # No manual CUDA/tracker cleanup or cache persisted into another call.
            del generated, final


@dataclass(frozen=True)
class ContextStressFactory:
    native_factory: Callable[[], LLMBackend]
    role: Role
    output: Path

    def __post_init__(self) -> None:
        if self.role not in ("agent", "guard"):
            raise ValueError("fixed stress role required")

    def __call__(self) -> LLMBackend:
        no_links(self.output)
        if self.output.exists():
            raise ValueError("fresh stress output required before loading")
        native = self.native_factory()
        expected = AgentHFBackendV2 if self.role == "agent" else GuardHFBackend
        if type(native) is not expected:
            raise ValueError("authenticated frozen native loader required")
        if self.role == "agent" and (
            native.model_revision != AGENT_REVISION or native.model_id != MODEL
        ):
            raise ValueError("pinned agent identity required")
        if isinstance(native, GuardHFBackend) and (
            native.model_id != MODEL_ID
            or native.model_revision
            != f"hf:{CANDIDATE_REVISION};snapshot-sha256:"
            "36b6d38e9e3cbc47427b1fabcf6f44fdd926a1d95a04a33bbfb19d7f1ffd5fbe"
            or native.config != GuardHFConfig()
        ):
            raise ValueError("pinned guard identity/config required")
        return ContextStressBackend(native, self.role, self.output)
