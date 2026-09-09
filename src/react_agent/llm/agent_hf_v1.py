"""Budget-enforcing Qwen7B backend for a dedicated agent process on two T4s."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import MODEL, REVISION, no_links
from react_agent.llm.agent_runtime_input_v1 import authenticate_runtime, parameter_shapes
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.coexistence_placement_v1 import (
    DeviceMemory,
    PlacementPlan,
    admit_context,
    admit_devices,
    validate_agent_geometry,
    validate_tensor_placement,
)


class AgentHFBackend:
    """Synchronous adapter, not a process supervisor or a hard deadline owner.

    Own the process exclusively; load before the separate guard. On failure the
    caller must retire/reap this process, not retry loading beside partial state.
    """

    def __init__(self, model_path: Path, inventory_path: Path, metrics_path: Path) -> None:
        started = time.perf_counter()
        no_links(metrics_path)
        if metrics_path.resolve().is_relative_to(model_path.resolve()):
            raise ValueError("metrics must be outside model mount")
        if metrics_path.exists() or not metrics_path.parent.is_dir():
            raise ValueError("fresh metrics path with existing parent required")
        admission = authenticate_runtime(model_path, inventory_path)
        import torch  # type: ignore[import-not-found]
        import transformers  # type: ignore[import-not-found]

        self.torch, self.transformers = torch, transformers
        self.plan = PlacementPlan()
        self.model_id = MODEL
        self.model_revision = REVISION + ":runtime-sha256:" + admission["content_sha256"]
        self.metrics_path = metrics_path
        self._lock = threading.Lock()
        self._retired = False
        self.call_index = 0
        if not torch.cuda.is_available() or torch.cuda.device_count() != 2:
            raise RuntimeError("exactly two CUDA devices required")
        torch.cuda.set_device(0)
        self.sync()
        observations = []
        for device in (0, 1):
            free, total = torch.cuda.mem_get_info(device)
            observations.append(
                DeviceMemory(
                    index=device,
                    name=torch.cuda.get_device_name(device),
                    free_bytes=free,
                    total_bytes=total,
                )
            )
            if torch.cuda.memory_allocated(device) or torch.cuda.memory_reserved(device):
                raise RuntimeError("dedicated empty agent allocator required")
        admit_devices(self.plan, observations)
        for device in (0, 1):
            torch.cuda.set_per_process_memory_fraction(
                self.plan.agent_caps[device] / observations[device].total_bytes, device
            )
            torch.cuda.reset_peak_memory_stats(device)
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(
            model_path, local_files_only=True, trust_remote_code=False
        )
        self.model = transformers.Qwen2ForCausalLM.from_pretrained(
            model_path,
            local_files_only=True,
            trust_remote_code=False,
            use_safetensors=True,
            dtype=torch.float16,
            device_map=self.plan.device_map(),
            max_memory=dict(enumerate(self.plan.agent_caps)),
            attn_implementation="sdpa",
        )
        self.model.eval()
        self.validate_loaded_geometry()
        self.validate_loaded_tensors()
        self.sync()
        self.check_memory()
        if authenticate_runtime(model_path, inventory_path) != admission:
            raise ValueError("model mount changed during loading")
        self._write(
            {
                "event": "load",
                "protocol": "agent_hf_dual_gpu_v1",
                "model_id": self.model_id,
                "model_revision": self.model_revision,
                "runtime_admission": admission,
                "placement_sha256": self.plan.sha256,
                "device_map": self.plan.device_map(),
                "agent_caps": self.plan.agent_caps,
                "global_before": [s.model_dump() for s in observations],
                "load_seconds_including_hashes": time.perf_counter() - started,
                "dtype": "float16",
                "attention": "sdpa",
                "quantization": None,
                "torch_version": torch.__version__,
                "transformers_version": transformers.__version__,
                "cuda_version": torch.version.cuda,
                "memory": self.memory(),
            },
            exclusive=True,
        )

    def sync(self) -> None:
        for device in (0, 1):
            self.torch.cuda.synchronize(device)

    def memory(self) -> list[dict[str, int]]:
        cuda = self.torch.cuda
        records = []
        for device in (0, 1):
            free, total = cuda.mem_get_info(device)
            records.append(
                {
                    "device": device,
                    "global_free_bytes": int(free),
                    "global_total_bytes": int(total),
                    "allocated_bytes": int(cuda.memory_allocated(device)),
                    "reserved_bytes": int(cuda.memory_reserved(device)),
                    "peak_allocated_bytes": int(cuda.max_memory_allocated(device)),
                    "peak_reserved_bytes": int(cuda.max_memory_reserved(device)),
                }
            )
        return records

    def check_memory(self) -> None:
        for row in self.memory():
            if any(
                row[key] > self.plan.agent_caps[row["device"]]
                for key in (
                    "allocated_bytes",
                    "reserved_bytes",
                    "peak_allocated_bytes",
                    "peak_reserved_bytes",
                )
            ):
                raise RuntimeError("agent allocator budget exceeded")

    def validate_loaded_tensors(self) -> None:
        parameters = list(self.model.named_parameters(remove_duplicate=False))
        buffers = list(self.model.named_buffers(remove_duplicate=False))
        shapes = parameter_shapes()
        if len(parameters) != len(shapes) or {n for n, _ in parameters} != set(shapes):
            raise ValueError("loaded parameter inventory mismatch")
        if any(tuple(t.shape) != shapes[n] or t.dtype != self.torch.float16 for n, t in parameters):
            raise ValueError("loaded parameter shape/dtype mismatch")
        for name, tensor in buffers:
            if (
                name != "model.rotary_emb.inv_freq"
                or tuple(tensor.shape) != (64,)
                or tensor.dtype not in (self.torch.float16, self.torch.float32)
            ):
                raise ValueError("unexpected model buffer")
        validate_tensor_placement(self.plan, [(n, str(t.device)) for n, t in parameters + buffers])

    def validate_loaded_geometry(self) -> None:
        # Native Qwen2Config materializes rope_scaling=None even when absent in
        # publisher JSON. Only inert None defaults are normalized here; the raw
        # authenticated config still uses the strict frozen validator.
        config = dict(self.model.config.to_dict())
        for key in ("auto_map", "quantization_config", "rope_scaling"):
            if key in config and config[key] is None:
                del config[key]
        validate_agent_geometry(config)
        if "layer_types" in config and config["layer_types"] != ["full_attention"] * 28:
            raise ValueError("unexpected native attention layout")

    def _write(self, record: dict[str, Any], *, exclusive: bool = False) -> None:
        with self.metrics_path.open("x" if exclusive else "a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("one agent request at a time required")
        try:
            if self._retired:
                raise RuntimeError("agent backend retired")
            self.call_index += 1
            started = time.perf_counter()
            record: dict[str, Any] = {"event": "generate", "call_index": self.call_index}
            try:
                response = self._generate(messages, config, record)
                record.update(status="OK", call_seconds=time.perf_counter() - started)
                self._write(record)
            except Exception:  # Retire/rethrow; never retain secret-bearing error text.
                self._retired = True
                record.update(status="ERROR", call_seconds=time.perf_counter() - started)
                try:
                    self._write(record)
                except OSError:
                    raise RuntimeError("agent metrics unavailable; backend retired") from None
                raise RuntimeError("agent generation failed; backend retired") from None
            return response
        finally:
            self._lock.release()

    def _generate(
        self, messages: list[dict[str, str]], config: GenerationConfig, record: dict[str, Any]
    ) -> ModelResponse:
        if config != GenerationConfig():
            raise ValueError("fixed greedy512/seed42 decoding required")
        if not messages or any(
            set(m) != {"role", "content"}
            or m["role"] not in {"system", "user", "assistant"}
            or not isinstance(m["content"], str)
            for m in messages
        ):
            raise ValueError("explicit text messages required")
        self.validate_loaded_geometry()
        self.validate_loaded_tensors()
        self.torch.manual_seed(config.seed)
        self.sync()
        for device in (0, 1):
            self.torch.cuda.reset_peak_memory_stats(device)
        record["memory_before"] = self.memory()
        started = time.perf_counter()
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
        shape = tuple(inputs["input_ids"].shape)
        if len(shape) != 2 or shape[0] != 1 or tuple(inputs["attention_mask"].shape) != shape:
            raise ValueError("batch one matching mask required")
        count = int(shape[1])
        record.update(
            input_tokens=count,
            tokenize_seconds=time.perf_counter() - started,
            generation_sha256=text_hash(config.model_dump_json()),
        )
        admit_context(self.plan, count, config.max_new_tokens)
        if count + config.max_new_tokens > self.model.config.max_position_embeddings:
            raise ValueError("native context exceeded")
        inputs = inputs.to("cuda:0")
        generation = self.transformers.GenerationConfig(
            max_new_tokens=512,
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
        self.check_memory()
        self.sync()
        started = time.perf_counter()
        with self.torch.inference_mode():
            generated = self.model.generate(**inputs, generation_config=generation)
        self.sync()
        record["generate_seconds"] = time.perf_counter() - started
        if len(generated.shape) != 2 or generated.shape[0] != 1:
            raise ValueError("invalid generated batch")
        output_tokens = int(generated.shape[1]) - count
        if not 1 <= output_tokens <= 512:
            raise ValueError("invalid output token count")
        new_tokens = generated[0, count:]
        raw = self.tokenizer.decode(new_tokens, skip_special_tokens=False)
        if any(
            marker in raw.lower()
            for marker in ("<think>", "</think>", "<|think|>", "<|channel>thought")
        ):
            raise ValueError("unexpected reasoning channel; output not retained")
        text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        self.validate_loaded_tensors()
        self.check_memory()
        record.update(output_tokens=output_tokens, memory_after=self.memory())
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)
