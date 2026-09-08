"""CPU-only budget admission; no torch import, inference, or GPU-fit claim."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from react_agent.foundation.artifacts import Immutable, canonical_json
from react_agent.foundation.normalization import text_hash

GIB = 1024**3
LAYERS, HIDDEN, INTERMEDIATE, KV_WIDTH, VOCAB = 28, 3584, 18944, 512, 152064
LAYER_PARAMETERS = (
    2 * HIDDEN**2 + 2 * HIDDEN * KV_WIDTH + 3 * HIDDEN * INTERMEDIATE + 3 * HIDDEN + 2 * KV_WIDTH
)
PARAMETERS = 2 * VOCAB * HIDDEN + LAYERS * LAYER_PARAMETERS + HIDDEN


class PlacementPlan(Immutable):
    protocol: Literal["qwen7b_guard15_placement_v1"] = "qwen7b_guard15_placement_v1"
    agent_candidate: Literal["Qwen/Qwen2.5-7B-Instruct"] = "Qwen/Qwen2.5-7B-Instruct"
    guard_device: Literal[1] = 1
    first_device_layers: int = Field(default=20, ge=1, lt=28, strict=True)
    agent_caps: tuple[
        Annotated[int, Field(strict=True, gt=0)], Annotated[int, Field(strict=True, gt=0)]
    ] = (12 * GIB, 7 * GIB)
    guard_cap: Literal[5368709120] = 5368709120
    global_headroom: int = Field(default=GIB, ge=GIB, strict=True)
    workspace_per_device: int = Field(default=GIB, ge=GIB, strict=True)
    input_limit: Literal[4096] = 4096
    output_limit: Literal[512] = 512

    @model_validator(mode="before")
    @classmethod
    def strict_constants(cls, value: Any) -> Any:
        if isinstance(value, dict) and any(
            key in value and type(value[key]) is not int
            for key in ("guard_device", "guard_cap", "input_limit", "output_limit")
        ):
            raise ValueError("integer constants cannot be coerced")
        return value

    @model_validator(mode="after")
    def budgets(self) -> Self:
        if any(type(n) is not int or n <= 0 for n in self.agent_caps):
            raise ValueError("two positive integer agent caps required")
        if any(n > c for n, c in zip(self.estimated_bytes(), self.agent_caps, strict=True)):
            raise ValueError("analytical weight/KV/workspace estimate exceeds agent cap")
        return self

    def device_map(self) -> dict[str, int]:
        return {
            "model.embed_tokens": 0,
            **{f"model.layers.{i}": int(i >= self.first_device_layers) for i in range(LAYERS)},
            "model.norm": 1,
            "model.rotary_emb": 1,
            "lm_head": 1,
        }

    def weight_bytes(self) -> tuple[int, int]:
        first = VOCAB * HIDDEN + self.first_device_layers * LAYER_PARAMETERS
        return first * 2, (PARAMETERS - first) * 2

    def kv_bytes(self) -> tuple[int, int]:
        per_layer = 2 * KV_WIDTH * 2 * (self.input_limit + self.output_limit)
        return per_layer * self.first_device_layers, per_layer * (LAYERS - self.first_device_layers)

    def estimated_bytes(self) -> tuple[int, int]:
        weights, kv = self.weight_bytes(), self.kv_bytes()
        return (
            weights[0] + kv[0] + self.workspace_per_device,
            weights[1] + kv[1] + self.workspace_per_device,
        )

    def required_free_bytes(self) -> tuple[int, int]:
        return (
            self.agent_caps[0] + self.global_headroom,
            self.agent_caps[1] + self.guard_cap + self.global_headroom,
        )

    @property
    def sha256(self) -> str:
        return text_hash(
            canonical_json(
                {
                    "plan": self.model_dump(mode="json"),
                    "map": self.device_map(),
                    "parameters": PARAMETERS,
                    "weights": list(self.weight_bytes()),
                    "kv": list(self.kv_bytes()),
                    "estimate": list(self.estimated_bytes()),
                    "assumptions": "FP16/batch1/dynamicKV; workspace allowance is not peak bound",
                }
            )
        )


class DeviceMemory(Immutable):
    index: int = Field(ge=0, le=1, strict=True)
    name: str
    free_bytes: int = Field(ge=0, strict=True)
    total_bytes: int = Field(gt=0, strict=True)

    @model_validator(mode="after")
    def valid_memory(self) -> Self:
        if self.free_bytes > self.total_bytes or self.name not in {"Tesla T4", "NVIDIA T4", "T4"}:
            raise ValueError("valid T4 memory observation required")
        return self


def validate_agent_geometry(config: dict[str, Any]) -> None:
    """Reject a different model shape before trusting this fixed arithmetic.

    Unrelated publisher metadata is permitted. This does not authenticate the
    config, weights or implementation and never authorizes remote model code.
    """
    expected: dict[str, Any] = {
        "model_type": "qwen2",
        "architectures": ["Qwen2ForCausalLM"],
        "num_hidden_layers": LAYERS,
        "hidden_size": HIDDEN,
        "intermediate_size": INTERMEDIATE,
        "num_attention_heads": 28,
        "num_key_value_heads": 4,
        "vocab_size": VOCAB,
        "tie_word_embeddings": False,
        "max_position_embeddings": 32768,
        "use_sliding_window": False,
    }
    if any(type(config.get(k)) is not type(v) or config[k] != v for k, v in expected.items()):
        raise ValueError("unsupported agent geometry")
    if any(k in config for k in ("auto_map", "quantization_config", "rope_scaling")):
        raise ValueError("custom, quantized or extended-context configuration unsupported")
    for key, value in {"head_dim": 128, "attention_bias": True, "mlp_bias": False}.items():
        if key in config and (type(config[key]) is not type(value) or config[key] != value):
            raise ValueError("parameter geometry override")


def admit_devices(plan: PlacementPlan, observations: Iterable[DeviceMemory]) -> None:
    samples = list(observations)
    if len(samples) != 2 or {s.index for s in samples} != {0, 1}:
        raise ValueError("exactly two distinct device observations required")
    required = plan.required_free_bytes()
    if any(s.free_bytes < required[s.index] for s in samples):
        raise ValueError("insufficient combined process budgets plus global headroom")


def admit_context(plan: PlacementPlan, input_tokens: int, output_tokens: int) -> None:
    if (
        type(input_tokens) is not int
        or type(output_tokens) is not int
        or not 1 <= input_tokens <= plan.input_limit
        or output_tokens != plan.output_limit
    ):
        raise ValueError(
            "complete rendered context and fixed output budget required; no truncation"
        )


def validate_tensor_placement(plan: PlacementPlan, tensors: Iterable[tuple[str, str]]) -> None:
    """Inspect all named parameters/buffers; shape/hash authentication is separate."""
    mapping = plan.device_map()
    seen: set[str] = set()
    covered: set[str] = set()
    for name, device in tensors:
        if name in seen:
            raise ValueError("duplicate tensor name")
        seen.add(name)
        candidates = [m for m in mapping if name == m or name.startswith(m + ".")]
        if len(candidates) != 1 or device != f"cuda:{mapping[candidates[0]]}":
            raise ValueError("unknown, offloaded or incorrectly placed tensor")
        covered.add(candidates[0])
    if not (set(mapping) - {"model.rotary_emb"}).issubset(covered):
        raise ValueError("incomplete model module coverage")
