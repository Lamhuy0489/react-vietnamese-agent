"""Offline, instrumented batch-one generation for the scientific Dev pilot."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.pilot_profiles import PilotProfile, adapt_messages

PROTOCOL = "dev21_performance_v1"


class MeasuredHFBackend:
    """Record token counts/timing, never attention states or hidden reasoning."""

    def __init__(self, model_path: Path, profile: PilotProfile, output: Path) -> None:
        import torch  # type: ignore[import-not-found]
        import transformers  # type: ignore[import-not-found]

        self.model_id, self.model_revision = profile.model_id, profile.revision
        self.profile, self.output = profile, output
        self.task_id = "warmup"
        self.call_index = 0
        self.torch = torch
        self.devices = list(range(torch.cuda.device_count()))
        if len(self.devices) != 2 or any(
            "T4" not in torch.cuda.get_device_name(i) for i in self.devices
        ):
            raise RuntimeError("measured protocol requires exactly two NVIDIA T4 GPUs")
        torch.manual_seed(42)
        torch.cuda.manual_seed_all(42)
        self.sync()
        started = time.perf_counter()
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(
            model_path, local_files_only=True, trust_remote_code=False
        )
        model_class = (
            transformers.Gemma4ForConditionalGeneration
            if profile.model_id == "google/gemma-4"
            else transformers.AutoModelForCausalLM
        )
        self.model = model_class.from_pretrained(
            model_path,
            local_files_only=True,
            trust_remote_code=False,
            dtype=torch.float16,
            device_map="balanced",
            max_memory={i: "13GiB" for i in self.devices},
            attn_implementation="sdpa",
        )
        self.model.eval()
        device_map = {name: str(device) for name, device in self.model.hf_device_map.items()}
        if any(device in {"cpu", "disk"} for device in device_map.values()):
            raise RuntimeError("CPU/disk offload violates the measured GPU condition")
        self.sync()
        load_seconds = time.perf_counter() - started
        warmup_started = time.perf_counter()
        self.generate(
            [{"role": "user", "content": 'Trả lời bằng JSON: {"ok": true}'}],
            GenerationConfig(max_new_tokens=16),
        )
        self.sync()
        self.setup: dict[str, Any] = {
            "protocol": PROTOCOL,
            "load_seconds": load_seconds,
            "warmup_seconds": time.perf_counter() - warmup_started,
            "warmup_count": 1,
            "warmup_max_new_tokens": 16,
            "dtype": "float16",
            "quantization": None,
            "attention_implementation": "sdpa",
            "batch_size": 1,
            "device_map": device_map,
            "cuda_version": torch.version.cuda,
            "gpus": [
                {
                    "index": i,
                    "name": torch.cuda.get_device_name(i),
                    "total_memory_bytes": torch.cuda.get_device_properties(i).total_memory,
                }
                for i in self.devices
            ],
            "parameters_loaded": sum(p.numel() for p in self.model.parameters()),
            "thinking": False,
        }

    def sync(self) -> None:
        for device in self.devices:
            self.torch.cuda.synchronize(device)

    def begin_task(self, task_id: str) -> None:
        self.task_id, self.call_index = task_id, 0

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.call_index += 1
        for device in self.devices:
            self.torch.cuda.reset_peak_memory_stats(device)
        self.sync()
        started = time.perf_counter()
        rendered = self.tokenizer.apply_chat_template(
            adapt_messages(messages, self.profile.chat_adapter),
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        if "<|think|>" in rendered:
            raise RuntimeError("thinking trigger in a non-thinking condition")
        inputs = self.tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
        inputs = inputs.to(self.model.device)
        input_tokens = int(inputs["input_ids"].shape[-1])
        self.sync()
        inference_started = time.perf_counter()
        with self.torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=config.max_new_tokens,
                do_sample=False,
                use_cache=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        self.sync()
        inference_seconds = time.perf_counter() - inference_started
        new_tokens = generated[0, input_tokens:]
        # Decode transport markers first; fail without logging any reasoning content.
        raw = self.tokenizer.decode(new_tokens, skip_special_tokens=False)
        if "<|channel>thought" in raw or "<think>" in raw:
            raise RuntimeError("unexpected thinking channel; content not retained")
        text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        call_seconds = time.perf_counter() - started
        record = {
            "task_id": self.task_id,
            "call_index": self.call_index,
            "input_tokens": input_tokens,
            "output_tokens": int(new_tokens.shape[-1]),
            "call_seconds": call_seconds,
            "generate_seconds": inference_seconds,
            "peak_allocated_bytes": [self.torch.cuda.max_memory_allocated(i) for i in self.devices],
            "peak_reserved_bytes": [self.torch.cuda.max_memory_reserved(i) for i in self.devices],
        }
        if self.task_id != "warmup":
            with (self.output / "inference_metrics.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)
