"""Offline single-device guard adapter, owned by one task-local warm subprocess."""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from react_agent.foundation.artifacts import Immutable, canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot, verify_snapshot


class GuardHFConfig(Immutable):
    protocol: Literal["guard_hf_single_gpu_v1"] = "guard_hf_single_gpu_v1"
    device: int = Field(default=1, ge=0, strict=True)
    allocator_limit_bytes: int = Field(default=5 * 1024**3, gt=0, strict=True)
    free_headroom_bytes: int = Field(default=1024**3, gt=0, strict=True)
    max_input_tokens: int = Field(default=4096, ge=1, le=32640, strict=True)

    @property
    def sha256(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))


@dataclass(frozen=True)
class GuardHFFactory:
    """Picklable factory: pass directly to WarmGuardBackend, once per task."""

    model_path: Path
    snapshot: GuardSnapshot
    config: GuardHFConfig
    metrics_path: Path

    def __call__(self) -> GuardHFBackend:
        return GuardHFBackend(self.model_path, self.snapshot, self.config, self.metrics_path)


class GuardHFBackend:
    """No network, sampling, truncation, shared history, or automatic fallback.

    Do not instantiate beside the agent in its process: the CUDA allocator cap
    applies to the entire process. WarmGuardBackend supplies the hard deadline.
    """

    def __init__(
        self, model_path: Path, snapshot: GuardSnapshot, config: GuardHFConfig, metrics_path: Path
    ) -> None:
        started = time.perf_counter()
        if metrics_path.resolve().is_relative_to(model_path.resolve()):
            raise ValueError("metrics must be outside the model snapshot")
        if metrics_path.exists() or not metrics_path.parent.is_dir():
            raise ValueError("fresh metrics file in an existing output directory required")
        verify_snapshot(model_path, snapshot)
        import torch  # type: ignore[import-not-found]
        import transformers  # type: ignore[import-not-found]

        self.model_id, self.model_revision = snapshot.model_id, snapshot.model_revision
        self.config, self.metrics_path = config, metrics_path
        self.torch, self.transformers = torch, transformers
        self.call_index = 0
        self._lock = threading.Lock()
        self._retired = False
        if not torch.cuda.is_available() or config.device >= torch.cuda.device_count():
            raise RuntimeError("configured CUDA device unavailable")
        torch.cuda.set_device(config.device)
        self.sync()
        free, total = torch.cuda.mem_get_info(config.device)
        if config.allocator_limit_bytes + config.free_headroom_bytes > free:
            raise RuntimeError("insufficient free GPU memory for declared guard budget")
        torch.cuda.set_per_process_memory_fraction(
            config.allocator_limit_bytes / total, config.device
        )
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(
            model_path, local_files_only=True, trust_remote_code=False
        )
        self.model = transformers.Qwen2ForCausalLM.from_pretrained(
            model_path,
            local_files_only=True,
            trust_remote_code=False,
            use_safetensors=True,
            dtype=torch.float16,
            device_map={"": config.device},
            attn_implementation="sdpa",
        )
        self.model.eval()
        if any(
            str(item.device) != f"cuda:{config.device}"
            for item in (*self.model.parameters(), *self.model.buffers())
        ):
            raise RuntimeError("guard tensor offload or device mismatch")
        self.sync()
        # Verify again after loading, including tokenizer and generation metadata.
        verify_snapshot(model_path, snapshot)
        self._write(
            {
                "event": "load",
                "protocol": config.protocol,
                "model_id": self.model_id,
                "model_revision": self.model_revision,
                "snapshot_sha256": snapshot.sha256,
                "adapter_config_sha256": config.sha256,
                "load_seconds_including_hashes": time.perf_counter() - started,
                "dtype": "float16",
                "quantization": None,
                "attention": "sdpa",
                "torch_version": torch.__version__,
                "transformers_version": transformers.__version__,
                "cuda_version": torch.version.cuda,
                "device": config.device,
                "device_name": torch.cuda.get_device_name(config.device),
                "device_map": {"": config.device},
                "global_free_bytes_before_load": free,
                "allocator_limit_bytes": config.allocator_limit_bytes,
                "free_headroom_bytes": config.free_headroom_bytes,
                "max_input_tokens": config.max_input_tokens,
                **self.memory(),
            },
            exclusive=True,
        )

    def sync(self) -> None:
        self.torch.cuda.synchronize(self.config.device)

    def memory(self) -> dict[str, int]:
        cuda, device = self.torch.cuda, self.config.device
        free, total = cuda.mem_get_info(device)
        return {
            "global_free_bytes": int(free),
            "global_total_bytes": int(total),
            "process_allocated_bytes": int(cuda.memory_allocated(device)),
            "process_reserved_bytes": int(cuda.memory_reserved(device)),
            "process_peak_allocated_bytes": int(cuda.max_memory_allocated(device)),
            "process_peak_reserved_bytes": int(cuda.max_memory_reserved(device)),
        }

    def _write(self, record: dict[str, Any], *, exclusive: bool = False) -> None:
        with self.metrics_path.open("x" if exclusive else "a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("one guard request at a time required")
        try:
            if self._retired:
                raise RuntimeError("guard backend retired")
            self.call_index += 1
            started = time.perf_counter()
            record: dict[str, Any] = {"event": "generate", "call_index": self.call_index}
            try:
                response = self._generate(messages, config, record)
            except (
                Exception
            ):  # Do not retain possibly secret-bearing exception text or model output.
                self._retired = True
                record.update(status="ERROR", call_seconds=time.perf_counter() - started)
                self._write(record)
                raise RuntimeError("guard generation failed; backend retired") from None
            record.update(status="OK", call_seconds=time.perf_counter() - started)
            try:
                self._write(record)
            except OSError:
                self._retired = True
                raise RuntimeError("guard metrics unavailable; backend retired") from None
            return response
        finally:
            self._lock.release()

    def _generate(
        self, messages: list[dict[str, str]], config: GenerationConfig, record: dict[str, Any]
    ) -> ModelResponse:
        if config != GenerationConfig(temperature=0, max_new_tokens=128, seed=42):
            raise ValueError("frozen guard decoding required")
        if not messages or any(
            set(m) != {"role", "content"}
            or m["role"] not in {"system", "user", "assistant"}
            or not isinstance(m["content"], str)
            for m in messages
        ):
            raise ValueError("explicit text messages required")
        self.torch.manual_seed(config.seed)
        self.torch.cuda.reset_peak_memory_stats(self.config.device)
        self.sync()
        record["global_free_bytes_before"] = self.memory()["global_free_bytes"]
        rendered = self.tokenizer.apply_chat_template(
            [dict(m) for m in messages],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self.tokenizer(
            rendered, return_tensors="pt", add_special_tokens=False, truncation=False
        )
        if set(inputs) != {"input_ids", "attention_mask"}:
            raise ValueError("unsupported tokenizer inputs")
        count = int(inputs["input_ids"].shape[-1])
        record.update(input_tokens=count, generation_sha256=text_hash(config.model_dump_json()))
        if (
            count > self.config.max_input_tokens
            or count + 128 > self.model.config.max_position_embeddings
        ):
            raise ValueError("guard context budget exceeded; no truncation allowed")
        inputs = inputs.to(f"cuda:{self.config.device}")
        # New config and dynamic KV cache on EVERY call. Never inherit sampling,
        # penalties, stop strings or conversation state from prior generation.
        generation = self.transformers.GenerationConfig(
            max_new_tokens=128,
            do_sample=False,
            num_beams=1,
            use_cache=True,
            cache_implementation="dynamic",
            return_dict_in_generate=False,
            output_scores=False,
            output_attentions=False,
            output_hidden_states=False,
            eos_token_id=self.model.generation_config.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        self.sync()
        started = time.perf_counter()
        with self.torch.inference_mode():
            generated = self.model.generate(**inputs, generation_config=generation)
        self.sync()
        record["generate_seconds"] = time.perf_counter() - started
        new_tokens = generated[0, count:]
        record["output_tokens"] = int(new_tokens.shape[-1])
        raw = self.tokenizer.decode(new_tokens, skip_special_tokens=False)
        if any(
            marker in raw.lower()
            for marker in ("<think>", "</think>", "<|think|>", "<|channel>thought")
        ):
            raise ValueError("unexpected reasoning channel; output not retained")
        text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        record.update(self.memory())
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)
