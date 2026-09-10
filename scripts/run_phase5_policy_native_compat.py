#!/usr/bin/env python3
"""Native-library resolver harness, not model inference or a GPU stress run."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.context_stress_v1 import ACK, REQUEST, ContextStressBackend
from react_agent.llm.generation_policy_v1 import (
    CONFIG_FIELDS,
    METHODS,
    PolicyStressBackend,
    config_snapshot,
)
from react_agent.llm.model_pair_v1 import ModelIdentity, Role
from react_agent.validation.context_stress_audit_v1 import equal, read_record
from react_agent.validation.generation_policy_audit_v1 import GLOBAL_DEFAULTS, audit_policy

UTILS_SHA = "dde2df36821c0d724b5af47cb0ff71c3c4c1990c86d81b821911127ae4dc1254"
CONFIG_SHA = "0aaf06e21d844256eee23aac663672d0aa9d06ca1f7f59e9be655c761ccdb0a0"
CASES: tuple[tuple[Role, str], ...] = (
    ("agent", "none"),
    ("guard", "none"),
    ("guard", "error"),
    ("guard", "interrupt"),
)


class StubConfig:
    """Only for exact-package local rehearsal; never reported as native evidence."""

    def __init__(self, **kwargs: Any) -> None:
        vars(self).update(dict.fromkeys(CONFIG_FIELDS))
        vars(self).update(kwargs)

    def _get_default_generation_params(self) -> dict[str, Any]:
        return dict(GLOBAL_DEFAULTS)


class StubModel:
    def __init__(self) -> None:
        self.generation_config = StubConfig(
            do_sample=True, repetition_penalty=1.1, eos_token_id=[151645, 151643]
        )

    def _prepare_generation_config(self, generation_config: Any, **kwargs: Any) -> Any:
        values = config_snapshot(generation_config)
        for source in (config_snapshot(self.generation_config), GLOBAL_DEFAULTS):
            for key, value in source.items():
                if values[key] is None:
                    values[key] = value
        return StubConfig(**values), kwargs

    def _prepare_special_tokens(self, generation_config: Any, **kwargs: Any) -> None:
        generation_config._eos_token_tensor = object()

    def _prepare_generated_length(
        self,
        generation_config: Any,
        has_default_max_length: bool,
        has_default_min_length: bool,
        model_input_name: str,
        input_ids_length: int,
        inputs_tensor: Any,
    ) -> Any:
        generation_config.max_length = generation_config.max_new_tokens + input_ids_length
        generation_config.min_length = generation_config.min_new_tokens + input_ids_length
        return generation_config


def libraries(backend: str) -> tuple[Any, Any, dict[str, Any]]:
    if backend == "stub":
        return (
            SimpleNamespace(__version__="5.5.0", GenerationConfig=StubConfig),
            StubModel(),
            {
                "native_imported": False,
                "backend": "stub",
            },
        )
    import torch  # type: ignore[import-not-found]
    import transformers  # type: ignore[import-not-found]
    from transformers.generation.utils import GenerationMixin  # type: ignore[import-not-found]

    if transformers.__version__ != "5.5.0" or torch.__version__ != "2.10.0+cu128":
        raise ValueError("pinned Kaggle libraries required")
    hashes = {}
    for cls, expected in (
        (GenerationMixin, UTILS_SHA),
        (transformers.GenerationConfig, CONFIG_SHA),
    ):
        source = inspect.getsourcefile(cls)
        if source is None or hashlib.sha256(Path(source).read_bytes()).hexdigest() != expected:
            raise ValueError("installed native source differs from pinned wheel")
        hashes[cls.__name__] = expected

    class NativeModel(GenerationMixin):  # type: ignore[misc]
        def __init__(self) -> None:
            self.config = transformers.PretrainedConfig(is_encoder_decoder=False)
            self.generation_config = transformers.GenerationConfig(
                do_sample=True, repetition_penalty=1.1, eos_token_id=[151645, 151643]
            )
            self.device = torch.device("cpu")

        def generate(self, *args: Any, **kwargs: Any) -> Any:
            raise AssertionError("compatibility harness never calls model.generate")

    return (
        transformers,
        NativeModel(),
        {
            "backend": "native",
            "native_imported": True,
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "installed_source_sha256": hashes,
            "cuda_used": False,
        },
    )


class ResolverHarness(ContextStressBackend):
    """Protocol-shaped harness; deliberately does NOT execute the stress backend."""

    def __init__(self, native: Any, role: Role, output: Path, fault: str) -> None:
        self.native, self.role, self.output, self.fault = native, role, output, fault
        self.model_id, self.model_revision = f"synthetic-library-harness-{role}", "v1"
        self.submitted: dict[str, Any] = {}
        self.final_policy: dict[str, Any] = {}

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        equal(messages, REQUEST, "fixed harness marker")
        count = 512 if self.role == "agent" else 128
        equal(config.model_dump(), GenerationConfig(max_new_tokens=count).model_dump(), "config")
        submitted = self.native.transformers.GenerationConfig(
            min_new_tokens=count,
            max_new_tokens=count,
            do_sample=False,
            num_beams=1,
            use_cache=True,
            cache_implementation="dynamic",
            return_dict_in_generate=True,
            output_scores=False,
            output_logits=False,
            output_attentions=False,
            output_hidden_states=False,
            eos_token_id=[151645, 151643],
            pad_token_id=151643,
        )
        self.submitted = config_snapshot(submitted)
        if self.native.backend == "native":
            import torch

            ids = torch.ones((1, 4096), dtype=torch.long, device="cpu")
        else:
            ids = SimpleNamespace(shape=(1, 4096))
        model = self.native.model
        resolved, unused = model._prepare_generation_config(
            submitted, input_ids=ids, attention_mask=ids
        )
        equal(sorted(unused), ["attention_mask", "input_ids"], "model kwargs")
        model._prepare_special_tokens(resolved, kwargs_has_attention_mask=True, device="cpu")
        if self.fault == "error":
            raise RuntimeError("synthetic injected failure")
        if self.fault == "interrupt":
            raise KeyboardInterrupt("synthetic injected interruption")
        final = model._prepare_generated_length(resolved, True, True, "input_ids", 4096, ids)
        self.final_policy = config_snapshot(final)
        return ModelResponse(text=ACK, model_id=self.model_id, model_revision=self.model_revision)


def run(output: Path, backend: str, commit: str) -> dict[str, Any]:
    no_links(output)
    if output.exists() or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("fresh output and exact source identity required")
    output.mkdir(parents=True)
    rows = []
    for role, fault in CASES:
        tf, model, identity = libraries(backend)
        case = f"{role}_{fault}"
        inner = ResolverHarness(
            SimpleNamespace(transformers=tf, model=model, backend=backend),
            role,
            output / case / "unused_stress",
            fault,
        )
        publisher = config_snapshot(model.generation_config)
        wrapped = PolicyStressBackend(inner, output / case / "policy")
        caught = None
        try:
            wrapped.generate(
                REQUEST, GenerationConfig(max_new_tokens=512 if role == "agent" else 128)
            )
        except (RuntimeError, KeyboardInterrupt) as exc:
            caught = type(exc).__name__
        expected = {"none": None, "error": "RuntimeError", "interrupt": "KeyboardInterrupt"}[fault]
        equal(caught, expected, "expected harness outcome")
        equal(config_snapshot(model.generation_config), publisher, "publisher unchanged")
        if any(n in vars(model) for n in METHODS):
            raise ValueError("native method not restored")
        equal(read_record(wrapped.output / "restored.json")["methods_restored"], True, "restore")
        if fault == "none":
            audit = audit_policy(
                wrapped.output,
                role,
                ModelIdentity(inner.model_id, inner.model_revision),
                os.getpid(),
                inner.submitted,
                publisher,
            )
            control = ResolverHarness(inner.native, role, output / case / "unused_control", "none")
            control.generate(
                REQUEST, GenerationConfig(max_new_tokens=512 if role == "agent" else 128)
            )
            equal(control.final_policy, inner.final_policy, "native hook/nohook policy equality")
            write_receipt(output / case / "audit.json", audit)
        elif (wrapped.output / "completed.json").exists():
            raise ValueError("failed harness cannot have complete receipt")
        rows.append(
            {
                "case": case,
                "caught": caught,
                "methods_restored": True,
                "identity": identity,
                "model_generate_calls": 0,
                "policy_receipt_generation_count_is_synthetic": True,
            }
        )
    summary = {
        "protocol": "native_policy_library_compat_v1",
        "valid": True,
        "backend": backend,
        "source_commit": commit,
        "cases": rows,
        "model_generate_calls": 0,
        "weights_loaded": 0,
        "gpu_used": False,
        "phase5_accepted": False,
        "native_library_verified": backend == "native",
        "scope": "Native config/special-token/length functions with synthetic harness; "
        "not Qwen generation or GPU stress",
    }
    write_receipt(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("stub", "native"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output, args.backend, os.environ.get("PAIR_SOURCE_COMMIT", ""))
    print(f"POLICY_NATIVE_COMPAT_COMPLETE backend={args.backend} model_generate_calls=0")


if __name__ == "__main__":
    main()
