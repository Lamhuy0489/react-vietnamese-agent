"""Observe actual native configuration resolution without changing decoding.

Opt-in, one owning worker/call. Hooks delegate to the original bound methods
exactly once; they never replay a resolver or serialize tensors/private state.
The frozen context backend remains unchanged and owns token/cache inspection.
"""

from __future__ import annotations

import inspect
import json
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.context_geometry_v1 import Role
from react_agent.llm.context_stress_v1 import ContextStressBackend, ContextStressFactory

VERSION = "5.5.0"
METHODS = ("_prepare_generation_config", "_prepare_generated_length")
CONFIG_FIELDS = frozenset(
    "max_length max_new_tokens min_length min_new_tokens early_stopping max_time stop_strings "
    "do_sample num_beams use_cache cache_implementation cache_config temperature top_k top_p "
    "min_p top_h typical_p epsilon_cutoff eta_cutoff repetition_penalty encoder_repetition_penalty "
    "length_penalty no_repeat_ngram_size bad_words_ids renormalize_logits forced_bos_token_id "
    "forced_eos_token_id remove_invalid_values exponential_decay_length_penalty suppress_tokens "
    "begin_suppress_tokens sequence_bias token_healing guidance_scale watermarking_config "
    "num_return_sequences output_attentions output_hidden_states output_scores output_logits "
    "return_dict_in_generate pad_token_id bos_token_id eos_token_id encoder_no_repeat_ngram_size "
    "decoder_start_token_id is_assistant num_assistant_tokens num_assistant_tokens_schedule "
    "assistant_confidence_threshold prompt_lookup_num_tokens max_matching_ngram_size "
    "assistant_early_exit assistant_lookbehind target_lookbehind compile_config disable_compile "
    "continuous_batching_config low_memory penalty_alpha dola_layers diversity_penalty "
    "num_beam_groups constraints force_words_ids prefill_chunk_size _from_model_config "
    "transformers_version".split()
)


def json_copy(value: Any) -> Any:
    """Reject non-JSON values before copying; never tensor.to_dict/deepcopy."""
    return json.loads(canonical_json(value))


def config_snapshot(config: Any, keys: frozenset[str] | None = None) -> dict[str, Any]:
    values = vars(config)
    if keys is None:
        keys = CONFIG_FIELDS
    if keys != CONFIG_FIELDS or set(values) - CONFIG_FIELDS - {
        "_commit_hash",
        "_original_object_hash",
        "_bos_token_tensor",
        "_eos_token_tensor",
        "_pad_token_tensor",
        "_decoder_start_token_tensor",
    }:
        raise ValueError("unsupported native config fields")
    if any(k not in values for k in keys):
        raise ValueError("configuration fields disappeared")
    # Explicitly whitelist observed public fields. Native special-token tensors
    # added later by generate() are private and must never be copied/serialized.
    result: dict[str, Any] = json_copy({k: values[k] for k in keys})
    result["transformers_version"] = VERSION
    return result


class PolicyStressBackend:
    def __init__(self, inner: ContextStressBackend, output: Path) -> None:
        no_links(output)
        if (
            output.exists()
            or output.resolve().is_relative_to(inner.output.resolve())
            or inner.output.resolve().is_relative_to(output.resolve())
        ):
            raise ValueError("fresh policy output outside frozen stress artifacts required")
        self.inner, self.output = inner, output
        self.model_id, self.model_revision = inner.model_id, inner.model_revision
        self._owner, self._used = os.getpid(), False
        self._lock = threading.Lock()

    def _save(self, stage: str, **values: Any) -> None:
        write_receipt(
            self.output / f"{stage}.json",
            {
                "protocol": "generation_policy_observation_v1",
                "stage": stage,
                "pid": self._owner,
                "role": self.inner.role,
                "model_id": self.model_id,
                "model_revision": self.model_revision,
                **values,
            },
        )

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if os.getpid() != self._owner or not self._lock.acquire(blocking=False):
            raise RuntimeError("single policy owner required")
        try:
            if self._used:
                raise RuntimeError("policy backend is single-use")
            self._used = True
            self.output.mkdir(parents=True, exist_ok=False)
            return self._generate(messages, config)
        finally:
            self._lock.release()

    def _generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        native = self.inner.native
        model = native.model
        if native.transformers.__version__ != VERSION:
            raise ValueError("pinned native policy implementation required")
        # Do not overwrite another instrumentor or create a stack of wrappers.
        if any(name in vars(model) for name in METHODS):
            raise ValueError("unmodified class-bound native methods required")
        originals = {name: getattr(model, name) for name in METHODS}
        if any(not inspect.ismethod(m) or m.__self__ is not model for m in originals.values()):
            raise ValueError("native bound methods required")
        observed: dict[str, dict[str, Any]] = {}
        calls = {name: 0 for name in METHODS}
        keys: frozenset[str] = frozenset()
        publisher = config_snapshot(model.generation_config)
        defaults = json_copy(model.generation_config._get_default_generation_params())
        self._save(
            "entered",
            publisher=publisher,
            global_defaults=defaults,
            transformers_version=VERSION,
            model_generation_calls_planned=1,
            policy_changed=False,
        )

        def resolve(*args: Any, **kwargs: Any) -> Any:
            nonlocal keys
            calls[METHODS[0]] += 1
            if calls[METHODS[0]] != 1 or calls[METHODS[1]]:
                raise ValueError("one ordered native resolution required")
            bound = inspect.signature(originals[METHODS[0]]).bind(*args, **kwargs)
            submitted = config_snapshot(bound.arguments["generation_config"])
            keys = frozenset(submitted)
            # Only input tensors travel in kwargs; never record their values.
            extra = bound.arguments.get("kwargs", {})
            if set(extra) != {"input_ids", "attention_mask"}:
                raise ValueError("unexpected generation keyword override")
            result = originals[METHODS[0]](*args, **kwargs)
            effective, model_kwargs = result
            if set(model_kwargs) != {"input_ids", "attention_mask"}:
                raise ValueError("unexpected resolved model keyword")
            observed["resolved"] = config_snapshot(effective, keys)
            self._save(
                "resolved",
                submitted=submitted,
                resolved=observed["resolved"],
                model_kwargs_keys=sorted(model_kwargs),
            )
            return result

        def length(*args: Any, **kwargs: Any) -> Any:
            calls[METHODS[1]] += 1
            if calls[METHODS[0]] != 1 or calls[METHODS[1]] != 1:
                raise ValueError("one ordered native length preparation required")
            bound = inspect.signature(originals[METHODS[1]]).bind(*args, **kwargs)
            inputs = bound.arguments
            if inputs["model_input_name"] != "input_ids" or inputs["input_ids_length"] != 4096:
                raise ValueError("fixed native input geometry required")
            before = config_snapshot(inputs["generation_config"], keys)
            result = originals[METHODS[1]](*args, **kwargs)
            observed["length"] = config_snapshot(result, keys)
            self._save(
                "length",
                before=before,
                after=observed["length"],
                input_tokens=4096,
                model_input_name="input_ids",
            )
            return result

        installed = []
        restored = False
        try:
            for name, hook in zip(METHODS, (resolve, length), strict=True):
                setattr(model, name, hook)
                installed.append(name)
            response = self.inner.generate(messages, config)
            if any(n != 1 for n in calls.values()) or set(observed) != {"resolved", "length"}:
                raise ValueError("missing native policy observations")
            if config_snapshot(model.generation_config) != publisher:
                raise ValueError("publisher configuration mutated")
        except BaseException as exc:
            self._save("error", error_class=type(exc).__name__, hook_calls=calls)
            raise
        finally:
            for name in reversed(installed):
                delattr(model, name)
            restored = all(
                getattr(model, n) == originals[n] and n not in vars(model) for n in METHODS
            )
            self._save("restored", methods_restored=restored, hook_calls=calls)
        if not restored:
            raise RuntimeError("native methods not restored; retire worker")
        self._save(
            "completed",
            model_generation_calls=1,
            hook_calls=calls,
            resolved_sha256=text_hash(canonical_json(observed["resolved"])),
            length_sha256=text_hash(canonical_json(observed["length"])),
            methods_restored=True,
            policy_changed=False,
        )
        return response


@dataclass(frozen=True)
class PolicyStressFactory:
    native_factory: Callable[[], LLMBackend]
    role: Role
    stress_output: Path
    policy_output: Path

    def __call__(self) -> LLMBackend:
        no_links(self.policy_output)
        if (
            self.policy_output.exists()
            or self.policy_output.resolve().is_relative_to(self.stress_output.resolve())
            or self.stress_output.resolve().is_relative_to(self.policy_output.resolve())
        ):
            raise ValueError("fresh separate policy output required before model loading")
        backend = ContextStressFactory(self.native_factory, self.role, self.stress_output)()
        if not isinstance(backend, ContextStressBackend):
            raise TypeError("versioned context stress backend required")
        return PolicyStressBackend(backend, self.policy_output)
