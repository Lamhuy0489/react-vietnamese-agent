"""Opt-in guard adapter with exact processor admission and request-local restoration."""

from __future__ import annotations

import hashlib
import inspect
import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.generation_policy_v1 import CONFIG_FIELDS, config_snapshot
from react_agent.llm.guard_hf_v1 import GuardHFBackend, GuardHFConfig
from react_agent.llm.guard_language_native_v1 import NativeCodec
from react_agent.llm.guard_token_language_v1 import TokenLanguage, compile_language, documents
from react_agent.security_v1.guard import parse_guard

PROFILE = "constrained_guard_adapter_v1"
LANGUAGE_SHA = "f8df0c2892984e8c6520a8e3bcf4e91dc793d8950165e99284c904a93f6bc3fb"
POLICY_SHA = "231f3e0b7e56f54043efa1002e6d1b37c132a28ca049294a32865d49c7b2efc6"
PROCESSOR_SHA = "c2cb748555325f429689a12cb4a9607dd3e2f9503b4eca6287702790c14fd780"
UTILS_SHA = "dde2df36821c0d724b5af47cb0ff71c3c4c1990c86d81b821911127ae4dc1254"
METHODS = ("generate", "_get_logits_processor")


def execution_identity(language: TokenLanguage) -> str:
    return text_hash(
        canonical_json(
            dict(
                profile=PROFILE,
                language=language.identity_sha256,
                effective_policy=POLICY_SHA,
                processors=["RepetitionPenalty:1.1", "PrefixConstrained"],
                processor_source=PROCESSOR_SHA,
                generation_source=UTILS_SHA,
            )
        )
    )


def admit_chain(
    chain: Any, callback: Any, repetition_type: type[Any], prefix_type: type[Any]
) -> None:
    if (
        len(chain) != 2
        or type(chain[0]) is not repetition_type
        or type(chain[1]) is not prefix_type
    ):
        raise ValueError("exact repetition-then-prefix processor chain required")
    if vars(chain[0]) != dict(
        penalty=1.1, prompt_ignore_length=None, logits_indices=None, cu_seq_lens_q=None
    ):
        raise ValueError("frozen repetition penalty required")
    if set(vars(chain[1])) != {"_prefix_allowed_tokens_fn", "_num_beams"} or (
        chain[1]._prefix_allowed_tokens_fn is not callback
        or type(chain[1]._num_beams) is not int
        or chain[1]._num_beams != 1
    ):
        raise ValueError("exact request callback required")


def constrained_scope(
    model: Any,
    language: TokenLanguage,
    repetition_type: type[Any],
    prefix_type: type[Any],
    invoke: Callable[[], ModelResponse],
    save: Callable[..., None],
) -> ModelResponse:
    """Caller owns lifecycle/lock; generic scope is tested with explicit CPU fakes."""
    if any(name in vars(model) for name in METHODS):
        raise ValueError("unmodified model methods required")
    originals = {n: getattr(model, n) for n in METHODS}
    if any(not inspect.ismethod(f) or f.__self__ is not model for f in originals.values()):
        raise ValueError("class-bound native methods required")
    owner = os.getpid(), threading.get_ident()
    publisher = config_snapshot(model.generation_config)
    counts = dict(generate=0, processors=0, callbacks=0)
    generated_tokens: tuple[int, ...] = ()
    installed: list[str] = []
    submitted: dict[str, Any] = dict.fromkeys(CONFIG_FIELDS)
    submitted.update(
        max_new_tokens=128,
        do_sample=False,
        num_beams=1,
        use_cache=True,
        cache_implementation="dynamic",
        return_dict_in_generate=False,
        output_scores=False,
        output_attentions=False,
        output_hidden_states=False,
        eos_token_id=[151645, 151643],
        pad_token_id=151643,
        transformers_version="5.5.0",
    )

    def owning() -> None:
        if owner != (os.getpid(), threading.get_ident()):
            raise RuntimeError("foreign constrained hook owner")

    def generate(*args: Any, **kwargs: Any) -> Any:
        nonlocal generated_tokens
        owning()
        counts["generate"] += 1
        if (
            args
            or counts["generate"] != 1
            or set(kwargs) != {"input_ids", "attention_mask", "generation_config"}
        ):
            raise ValueError("one exact native generate invocation required")
        if config_snapshot(kwargs["generation_config"]) != submitted:
            raise ValueError("submitted native generation changed")
        ids = kwargs["input_ids"]
        if len(ids.shape) != 2 or ids.shape[0] != 1 or not 1 <= ids.shape[1] <= 4096:
            raise ValueError("single bounded prompt required")
        prompt = tuple(ids[0].tolist())
        gate = language.request(prompt)

        def callback(batch_id: int, row: Any) -> list[int]:
            owning()
            if counts["processors"] != 1:
                raise ValueError("callback before chain admission")
            suffix = tuple(row.tolist())[len(prompt) :]
            if len(suffix) != counts["callbacks"]:
                raise ValueError("one ordered callback per generation step required")
            counts["callbacks"] += 1
            return gate(batch_id, row)

        def processors(*args: Any, **kwargs: Any) -> Any:
            owning()
            if counts["processors"]:
                raise ValueError("one processor construction required")
            bound = inspect.signature(originals["_get_logits_processor"]).bind(*args, **kwargs)
            effective = config_snapshot(bound.arguments["generation_config"])
            if effective["max_length"] != len(prompt) + 128:
                raise ValueError("resolved length mismatch")
            effective["max_length"] = 20
            if text_hash(canonical_json(effective)) != POLICY_SHA:
                raise ValueError("resolved decoding policy changed")
            if bound.arguments.get("prefix_allowed_tokens_fn") is not callback:
                raise ValueError("native callback changed")
            chain = originals["_get_logits_processor"](*args, **kwargs)
            admit_chain(chain, callback, repetition_type, prefix_type)
            counts["processors"] = 1
            save(
                "admitted",
                policy_sha256=POLICY_SHA,
                processor_types=[c.__class__.__name__ for c in chain],
                input_tokens=len(prompt),
                language_sha256=language.identity_sha256,
            )
            return chain

        model._get_logits_processor = processors
        installed.append("_get_logits_processor")
        output = originals["generate"](**kwargs, prefix_allowed_tokens_fn=callback)
        if (
            len(output.shape) != 2
            or output.shape[0] != 1
            or tuple(output[0].tolist()[: len(prompt)]) != prompt
        ):
            raise ValueError("generated sequence/prompt mismatch")
        generated_tokens = tuple(output[0].tolist()[len(prompt) :])
        language.verify_completion(generated_tokens)
        if counts["processors"] != 1 or counts["callbacks"] != len(generated_tokens):
            raise ValueError("generation bypassed constrained callbacks")
        return output

    save("entered", execution_identity=execution_identity(language))
    try:
        model.generate = generate
        installed.append("generate")
        response = invoke()
        if counts["generate"] != 1 or not generated_tokens:
            raise ValueError("missing native generation")
        parse_guard(response.text)
        if response.text != documents()[language.sequences.index(generated_tokens[:-1])]:
            raise ValueError("decoded response differs from constrained tokens")
        if config_snapshot(model.generation_config) != publisher:
            raise ValueError("publisher policy drift")
    except BaseException as error:
        save("error", error_class=type(error).__name__, counts=dict(counts))
        raise
    finally:
        for name in reversed(installed):
            delattr(model, name)
        restored = all(n not in vars(model) and getattr(model, n) == originals[n] for n in METHODS)
        save("restored", methods_restored=restored, counts=dict(counts))
    if not restored:
        raise RuntimeError("constrained methods not restored")
    save(
        "completed",
        counts=dict(counts),
        output_tokens=len(generated_tokens),
        output_token_sha256=text_hash(canonical_json(list(generated_tokens))),
        response_sha256=text_hash(response.text),
        execution_identity=execution_identity(language),
    )
    return response


class ConstrainedGuardBackend:
    """Wrap a fresh exact guard loader; not yet an admitted paired-runtime factory."""

    def __init__(self, native: GuardHFBackend, language: TokenLanguage, output: Path) -> None:
        no_links(output)
        if type(native) is not GuardHFBackend or native.call_index or native._retired:
            raise ValueError("fresh exact guard backend required")
        if native.config != GuardHFConfig() or language.identity_sha256 != LANGUAGE_SHA:
            raise ValueError("frozen guard limits and admitted Qwen language required")
        if (
            output.exists()
            or output.resolve().is_relative_to(native.metrics_path.resolve())
            or native.metrics_path.resolve().is_relative_to(output.resolve())
        ):
            raise ValueError("fresh separate adapter evidence required")
        from transformers.generation.logits_process import (  # type: ignore[import-not-found]
            PrefixConstrainedLogitsProcessor,
            RepetitionPenaltyLogitsProcessor,
        )

        if native.transformers.__version__ != "5.5.0" or native.torch.__version__ != "2.10.0+cu128":
            raise ValueError("pinned native libraries required")
        self.native, self.language, self.output = native, language, output
        self._types = RepetitionPenaltyLogitsProcessor, PrefixConstrainedLogitsProcessor
        bound_generate = native.model.generate
        if (
            not inspect.ismethod(bound_generate)
            or id(bound_generate.__self__) != id(native.model)
            or bound_generate.__func__ is not native.transformers.GenerationMixin.generate
        ):
            raise ValueError("original native GenerationMixin method required")
        for obj, expected in (
            (self._types[0], PROCESSOR_SHA),
            (self._types[1], PROCESSOR_SHA),
            (native.model.generate, UTILS_SHA),
            (native.model._get_logits_processor, UTILS_SHA),
        ):
            # torch.no_grad wraps generate in torch/utils/_contextlib.py.
            # Authenticate the exact SDK method above, then hash its unwrapped body.
            path = inspect.getsourcefile(inspect.unwrap(obj))
            if path is None or hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
                raise ValueError("native implementation pin mismatch")
        self.model_id, self.model_revision = native.model_id, native.model_revision
        self.constraint_identity = execution_identity(language)
        self._model, self._tokenizer = native.model, native.tokenizer
        self._publisher = config_snapshot(native.model.generation_config)
        self._owner, self._retired, self._index = os.getpid(), False, 0
        self._lock = threading.Lock()

    @property
    def retired(self) -> bool:
        return self._retired or self.native._retired

    def retire(self) -> None:
        self._retired = True
        self.native._retired = True

    def verify_identity(self) -> None:
        """Validate live decoding state even when a classifier would serve a cache hit."""
        if (self.native.model_id, self.native.model_revision) != (
            self.model_id,
            self.model_revision,
        ) or (
            self.native.model is not self._model
            or self.native.tokenizer is not self._tokenizer
            or self.native.config != GuardHFConfig()
            or self.constraint_identity != execution_identity(self.language)
            or config_snapshot(self._model.generation_config) != self._publisher
        ):
            raise ValueError("adapter identity changed")
        if self.retired:
            raise RuntimeError("adapter retired; no retry")

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if os.getpid() != self._owner or not self._lock.acquire(blocking=False):
            raise RuntimeError("single adapter owner required")
        try:
            if self.retired:
                raise RuntimeError("adapter retired; no retry")
            try:
                if config != GenerationConfig(max_new_tokens=128):
                    raise ValueError("guard generation limits changed")
                self.verify_identity()
                self._index += 1
                target = self.output / f"request_{self._index:06d}"
                no_links(target)
                target.mkdir(parents=True, exist_ok=False)

                def save(stage: str, **values: Any) -> None:
                    write_receipt(
                        target / f"{stage}.json",
                        dict(
                            protocol=PROFILE,
                            stage=stage,
                            model_id=self.model_id,
                            model_revision=self.model_revision,
                            request_index=self._index,
                            **values,
                        ),
                    )

                def invoke() -> ModelResponse:
                    response = self.native.generate(messages, config)
                    self.verify_identity()
                    if (response.model_id, response.model_revision) != (
                        self.model_id,
                        self.model_revision,
                    ):
                        raise ValueError("response identity changed")
                    return response

                return constrained_scope(
                    self._model,
                    self.language,
                    *self._types,
                    invoke,
                    save,
                )
            except BaseException:
                self.retire()
                raise
        finally:
            self._lock.release()


def language_for_guard(native: GuardHFBackend, tokenizer_hashes: dict[str, str]) -> TokenLanguage:
    """Caller authenticates the six metadata hashes before loading the native guard."""
    language = compile_language(
        NativeCodec(native.tokenizer),
        tokenizer_sha256=text_hash(canonical_json(tokenizer_hashes)),
        vocabulary_size=native.model.config.vocab_size,
        eos=tuple(sorted(native.model.generation_config.eos_token_id)),
    )
    if language.identity_sha256 != LANGUAGE_SHA:
        raise ValueError("native tokenizer language differs from admitted CPU result")
    return language
