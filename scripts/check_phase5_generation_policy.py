#!/usr/bin/env python3
"""Check the policy observer's assumptions against a pinned wheel, without importing it."""

from __future__ import annotations

import argparse
import ast
import hashlib
import zipfile
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.generation_policy_v1 import CONFIG_FIELDS
from react_agent.validation.context_stress_audit_v1 import NATIVE_NONE_FIELDS, equal
from react_agent.validation.generation_policy_audit_v1 import GLOBAL_DEFAULTS
from react_agent.validation.guard_probe_audit_v2 import digest, require

WHEEL_SHA256 = "821a9ff0961abbb29eb1eb686d78df1c85929fdf213a3fe49dc6bd94f9efa944"
UTILS_SHA256 = "dde2df36821c0d724b5af47cb0ff71c3c4c1990c86d81b821911127ae4dc1254"


def check(path: Path) -> dict[str, Any]:
    no_links(path)
    require(digest(path) == WHEEL_SHA256, "pinned wheel required")
    with zipfile.ZipFile(path) as wheel:
        source = wheel.read("transformers/generation/utils.py")
        config = wheel.read("transformers/generation/configuration_utils.py")
    require(hashlib.sha256(source).hexdigest() == UTILS_SHA256, "pinned generation source")
    tree = ast.parse(config)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GenerationConfig")
    method = next(
        n
        for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "_get_default_generation_params"
    )
    value = next(n.value for n in method.body if isinstance(n, ast.Return))
    require(value is not None, "native global defaults")
    if value is None:
        raise ValueError("missing default dictionary")
    equal(ast.literal_eval(value), GLOBAL_DEFAULTS, "independent global defaults")
    equal(
        sorted(CONFIG_FIELDS - NATIVE_NONE_FIELDS),
        sorted(
            {
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
            }
        ),
        "observer serialized field coverage",
    )
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GenerationMixin")
    resolver = next(
        n
        for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "_prepare_generation_config"
    )
    updates = [
        ast.unparse(n)
        for n in ast.walk(resolver)
        if isinstance(n, ast.Call) and ast.unparse(n.func) == "generation_config.update"
    ]
    equal(
        updates,
        [
            "generation_config.update(**self.generation_config.to_dict(), "
            "defaults_only=True, allow_custom_entries=True)",
            "generation_config.update(**global_defaults, defaults_only=True)",
            "generation_config.update(**kwargs)",
        ],
        "native resolution precedence",
    )
    return {
        "protocol": "generation_policy_source_check_v1",
        "valid": True,
        "wheel_sha256": WHEEL_SHA256,
        "generation_utils_sha256": UTILS_SHA256,
        "configuration_utils_sha256": hashlib.sha256(config).hexdigest(),
        "serialized_fields": len(CONFIG_FIELDS),
        "global_defaults": GLOBAL_DEFAULTS,
        "resolution_updates": updates,
        "native_imported": False,
        "model_executions": 0,
        "phase5_accepted": False,
        "gpu_readiness": False,
        "scope": "Pinned source assumptions only; "
        "actual native hook execution still requires preflight",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    if args.output.exists():
        raise ValueError("fresh receipt path required")
    result = check(args.wheel)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("GENERATION_POLICY_SOURCE_CHECK_COMPLETE native_imported=False gpu_readiness=False")


if __name__ == "__main__":
    main()
