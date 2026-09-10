#!/usr/bin/env python3
"""Hash-bound static native-interface checks; no imports, installation or inference."""

from __future__ import annotations

import argparse
import ast
import hashlib
import zipfile
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.validation.context_stress_audit_v1 import NATIVE_NONE_FIELDS, equal
from react_agent.validation.guard_probe_audit_v2 import digest, require

WHEEL_SHA256 = "821a9ff0961abbb29eb1eb686d78df1c85929fdf213a3fe49dc6bd94f9efa944"
MEMBERS = (
    "transformers/generation/configuration_utils.py",
    "transformers/models/qwen2/modeling_qwen2.py",
    "transformers/cache_utils.py",
)


def method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)


def inspect_wheel(path: Path) -> dict[str, Any]:
    no_links(path)
    require(digest(path) == WHEEL_SHA256, "pinned Transformers wheel required")
    with zipfile.ZipFile(path) as wheel:
        sources = {name: wheel.read(name) for name in MEMBERS}
    config = ast.parse(sources[MEMBERS[0]])
    constructor = method(config, "GenerationConfig", "__init__")
    defaults: dict[str, None] = {}
    for node in constructor.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.targets[0], ast.Attribute):
            continue
        name, value = node.targets[0].attr, node.value
        if not isinstance(value, ast.Call):
            raise ValueError("generation default assignment")
        require(ast.unparse(value.func) == "kwargs.pop" and len(value.args) == 2, "kwargs default")
        equal(ast.literal_eval(value.args[0]), name, "default field identity")
        equal(ast.literal_eval(value.args[1]), None, "fresh config defaults must be None")
        defaults[name] = None
    explicit = {
        "min_new_tokens",
        "max_new_tokens",
        "do_sample",
        "num_beams",
        "use_cache",
        "cache_implementation",
        "return_dict_in_generate",
        "output_scores",
        "output_logits",
        "output_attentions",
        "output_hidden_states",
        "eos_token_id",
        "pad_token_id",
        "transformers_version",
        "_commit_hash",
    }
    equal(sorted(defaults), sorted(NATIVE_NONE_FIELDS | explicit), "complete native config fields")
    serialization = ast.unparse(method(config, "GenerationConfig", "to_dict"))
    require(
        "del output['_commit_hash']" in serialization
        and "output['transformers_version'] = __version__" in serialization,
        "config serialization contract",
    )
    qwen = ast.parse(sources[MEMBERS[1]])
    forward = method(qwen, "Qwen2ForCausalLM", "forward")
    args = {a.arg for a in forward.args.args + forward.args.kwonlyargs}
    required = {"input_ids", "attention_mask", "past_key_values", "use_cache", "logits_to_keep"}
    require(required <= args and forward.args.kwarg is not None, "Qwen final-forward interface")
    cache = ast.parse(sources[MEMBERS[2]])
    sequence = ast.unparse(method(cache, "DynamicLayer", "get_seq_length"))
    require("self.keys.shape[-2]" in sequence, "dynamic cache sequence dimension")
    update = ast.unparse(method(cache, "DynamicLayer", "update"))
    require("self.keys" in update and "self.values" in update, "dynamic KV storage")
    return {
        "protocol": "context_stress_static_compatibility_v1",
        "valid": True,
        "wheel_sha256": WHEEL_SHA256,
        "source_sha256": {n: hashlib.sha256(v).hexdigest() for n, v in sources.items()},
        "constructor_fields": len(defaults),
        "serialized_fields": len(defaults) - 1,
        "none_default_fields": sorted(NATIVE_NONE_FIELDS),
        "qwen_forward_required_arguments": sorted(required),
        "native_imported": False,
        "model_weights_loaded": False,
        "native_inference_verified": False,
        "scope": "Pinned source interface assertions only; exact bundle rehearsal "
        "and GPU execution still required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transformers-wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    if args.output.exists():
        raise ValueError("fresh compatibility output required")
    receipt = inspect_wheel(args.transformers_wheel)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, receipt)
    print("CONTEXT_STRESS_STATIC_COMPATIBILITY_COMPLETE native_inference_verified=False")


if __name__ == "__main__":
    main()
