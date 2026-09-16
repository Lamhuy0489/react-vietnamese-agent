"""Real GenerationMixin CPU control on a tiny random Qwen; never a quality experiment."""

from __future__ import annotations

import hashlib
import inspect
import json
import time
import zipfile
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import write_receipt
from react_agent.llm.base import ModelResponse
from react_agent.llm.constrained_guard_v1 import (
    LANGUAGE_SHA,
    METHODS,
    PROCESSOR_SHA,
    UTILS_SHA,
    constrained_scope,
)
from react_agent.llm.guard_language_native_v1 import NativeCodec, digest
from react_agent.llm.guard_token_language_v1 import compile_language

CASES = ("success01", "success02", "forced_bos", "interrupt")


def probe(
    bundle: Path, tokenizer_root: Path, admission: dict[str, Any], output: Path
) -> dict[str, Any]:
    import torch  # type: ignore[import-not-found]
    import transformers  # type: ignore[import-not-found]
    from transformers.generation.logits_process import (  # type: ignore[import-not-found]
        PrefixConstrainedLogitsProcessor,
        RepetitionPenaltyLogitsProcessor,
    )

    if (torch.__version__, transformers.__version__) != ("2.10.0+cu128", "5.5.0"):
        raise ValueError("pinned native CPU libraries required")
    wheel = bundle / "transformers-5.5.0-py3-none-any.whl"
    expected_wheel = json.loads((bundle / "guard_bundle.json").read_text())["wheel_sha256"][
        wheel.name
    ]
    if digest(wheel) != expected_wheel:
        raise ValueError("wheel pin mismatch")
    verified = {}
    with zipfile.ZipFile(wheel) as archive:
        for obj, name, pin in (
            (PrefixConstrainedLogitsProcessor, "generation/logits_process.py", PROCESSOR_SHA),
            (transformers.GenerationMixin.generate, "generation/utils.py", UTILS_SHA),
            (transformers.Qwen2ForCausalLM, "models/qwen2/modeling_qwen2.py", None),
            (transformers.Qwen2Config, "models/qwen2/configuration_qwen2.py", None),
        ):
            data = archive.read("transformers/" + name)
            expected = hashlib.sha256(data).hexdigest()
            path = inspect.getsourcefile(inspect.unwrap(obj))
            if path is None or digest(Path(path)) != expected or (pin and expected != pin):
                raise ValueError("installed native source mismatch")
            verified[name] = expected
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(tokenizer_root),
        local_files_only=True,
        trust_remote_code=False,
        use_fast=True,
    )
    language = compile_language(
        NativeCodec(tokenizer),
        tokenizer_sha256=text_hash(canonical_json(admission["tokenizer_sha256"])),
        vocabulary_size=admission["vocabulary_size"],
        eos=tuple(admission["eos"]),
    )
    if language.identity_sha256 != LANGUAGE_SHA:
        raise ValueError("admitted native tokenizer language required")
    architecture = dict(
        vocab_size=language.vocabulary_size,
        hidden_size=8,
        intermediate_size=16,
        num_hidden_layers=1,
        num_attention_heads=1,
        num_key_value_heads=1,
        max_position_embeddings=4096,
        bos_token_id=151643,
        eos_token_id=151645,
        pad_token_id=151643,
        tie_word_embeddings=True,
    )
    before_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    summaries = []
    try:
        for case in CASES:
            torch.manual_seed(42)
            model = transformers.Qwen2ForCausalLM(transformers.Qwen2Config(**architecture)).eval()
            model.generation_config = transformers.GenerationConfig.from_pretrained(
                str(tokenizer_root),
                local_files_only=True,
            )
            if case == "forced_bos":
                model.generation_config.forced_bos_token_id = 0
            inputs = tokenizer("Synthetic generation integration " + case, return_tensors="pt")
            generation = transformers.GenerationConfig(
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
            )
            target = output / case
            target.mkdir(parents=True, exist_ok=False)
            calls = 0

            def observe(*args: Any, mode: str = case) -> None:
                nonlocal calls
                calls += 1
                if mode == "interrupt":
                    raise KeyboardInterrupt()

            hook = model.register_forward_pre_hook(observe)

            def save(
                stage: str, destination: Path = target, mode: str = case, **values: Any
            ) -> None:
                write_receipt(destination / f"{stage}.json", dict(stage=stage, case=mode, **values))

            def invoke(
                model: Any = model, inputs: Any = inputs, generation: Any = generation
            ) -> ModelResponse:
                with torch.inference_mode():
                    generated = model.generate(**inputs, generation_config=generation)
                text = tokenizer.decode(
                    generated[0, inputs["input_ids"].shape[1] :],
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )
                return ModelResponse(
                    text=text, model_id="synthetic-tiny-qwen2", model_revision="random-seed42-v1"
                )

            started = time.perf_counter()
            error = None
            try:
                constrained_scope(
                    model,
                    language,
                    RepetitionPenaltyLogitsProcessor,
                    PrefixConstrainedLogitsProcessor,
                    invoke,
                    save,
                )
            except (ValueError, KeyboardInterrupt) as caught:
                error = type(caught).__name__
            finally:
                hook.remove()
            expected_error = (
                "ValueError"
                if case == "forced_bos"
                else "KeyboardInterrupt"
                if case == "interrupt"
                else None
            )
            if error != expected_error or any(name in vars(model) for name in METHODS):
                raise ValueError("native generation outcome/restoration mismatch")
            if (target / "completed.json").exists() != (expected_error is None):
                raise ValueError("native completion receipt mismatch")
            if case == "forced_bos" and calls != 0 or case == "interrupt" and calls != 1:
                raise ValueError("native negative-control forward count mismatch")
            if expected_error is None:
                done = json.loads((target / "completed.json").read_text())
                if calls != done["output_tokens"]:
                    raise ValueError("real forward/output-token count mismatch")
            summaries.append(
                dict(
                    case=case,
                    error_class=error,
                    forward_calls=calls,
                    seconds=time.perf_counter() - started,
                    methods_restored=True,
                )
            )
            del model
    finally:
        torch.set_num_threads(before_threads)
    for name, sha in admission["tokenizer_sha256"].items():
        if digest(tokenizer_root / name) != sha:
            raise ValueError("tokenizer input changed")
    return dict(
        protocol="constrained_generate_cpu_v1",
        valid=True,
        cases=summaries,
        library_verified=True,
        source_sha256=verified,
        architecture=architecture,
        seed=42,
        language_identity=language.identity_sha256,
        random_models_initialized=4,
        pretrained_weights_loaded=0,
        gpu_used=False,
        torch_threads_restored=torch.get_num_threads() == before_threads,
        native_generation_mixin_validated=True,
        production_guard_generation_validated=False,
        guard_quality_validated=False,
        phase5_accepted=False,
    )
