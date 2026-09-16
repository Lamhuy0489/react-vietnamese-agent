"""Read-only CPU receipt consistency; never execute downloaded source or model code."""

import hashlib
import math
import re
import zipfile
from pathlib import Path
from typing import Any

from react_agent.validation.context_stress_audit_v1 import equal, fields, inventory, read_record

LANGUAGE = "f8df0c2892984e8c6520a8e3bcf4e91dc793d8950165e99284c904a93f6bc3fb"
POLICY = "fbe63d97727be376a45d5b484ea70147e7724231dc625118515e5f2188c2d69f"
IDENTITY = "a3a5b0a2695dbf68426ccbec6785118ca3a30e320ccdfaea6f2d169679b5c425"
CASES = ("success01", "success02", "forced_bos", "interrupt")


def hash_value(value: Any) -> None:
    if type(value) is not str or re.fullmatch("[a-f0-9]{64}", value) is None:
        raise ValueError("SHA-256 value required")


def validate_result(
    root: Path, summary: dict[str, Any], commit: str, wheel: Path, processor_sha: str
) -> None:
    before = inventory(root)
    expected = dict(
        protocol="constrained_generate_cpu_v1",
        valid=True,
        library_verified=True,
        source_commit=commit,
        seed=42,
        language_identity=LANGUAGE,
        random_models_initialized=4,
        pretrained_weights_loaded=0,
        gpu_used=False,
        torch_threads_restored=True,
        native_generation_mixin_validated=True,
        production_guard_generation_validated=False,
        guard_quality_validated=False,
        phase5_accepted=False,
        test_payload_accessed=False,
        private_ground_truth_accessed=False,
        architecture=dict(
            vocab_size=151936,
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
        ),
    )
    fields(summary, set(expected) | {"cases", "source_sha256"}, "CPU summary")
    for key, value in expected.items():
        equal(summary[key], value, "CPU summary " + key)
    names = (
        "generation/logits_process.py",
        "generation/utils.py",
        "models/qwen2/modeling_qwen2.py",
        "models/qwen2/configuration_qwen2.py",
    )
    with zipfile.ZipFile(wheel) as archive:
        pins = {
            name: hashlib.sha256(archive.read("transformers/" + name)).hexdigest() for name in names
        }
    equal(summary["source_sha256"], pins, "actual native implementation pins")
    equal(pins[names[0]], processor_sha, "processor pin")
    rows = summary["cases"]
    if type(rows) is not list or len(rows) != 4:
        raise ValueError("four ordered CPU cases required")
    files = set()
    for case, row in zip(CASES, rows, strict=True):
        fields(row, {"case", "error_class", "forward_calls", "methods_restored", "seconds"}, "case")
        equal(row["case"], case, "case order")
        equal(row["methods_restored"], True, "case restored")
        error = (
            "ValueError"
            if case == "forced_bos"
            else "KeyboardInterrupt"
            if case == "interrupt"
            else None
        )
        equal(row["error_class"], error, "expected control outcome")
        seconds, count = row["seconds"], row["forward_calls"]
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError("finite CPU timing required")
        if type(count) is not int or not 0 <= count <= 128:
            raise ValueError("bounded integer forward count required")
        stages = {"entered", "restored", "completed" if error is None else "error"}
        if case != "forced_bos":
            stages.add("admitted")
        records = {}
        for stage in stages:
            name = f"{case}/{stage}.json"
            files.add(name)
            records[stage] = read_record(root / name)
            equal(records[stage].pop("case"), case, "receipt case")
            equal(records[stage].pop("stage"), stage, "receipt stage")
        equal(records["entered"], dict(execution_identity=IDENTITY), "execution identity")
        counts = dict(
            generate=1,
            processors=0 if case == "forced_bos" else 1,
            callbacks=count if error is None else 0,
        )
        equal(
            records["restored"],
            dict(methods_restored=True, counts=counts),
            "scope restoration/counts",
        )
        if "admitted" in records:
            admitted = records["admitted"]
            fields(
                admitted,
                {"input_tokens", "policy_sha256", "processor_types", "language_sha256"},
                "admission",
            )
            equal(admitted["policy_sha256"], POLICY, "policy identity")
            equal(admitted["language_sha256"], LANGUAGE, "language identity")
            equal(
                admitted["processor_types"],
                ["RepetitionPenaltyLogitsProcessor", "PrefixConstrainedLogitsProcessor"],
                "processor chain",
            )
            if (
                type(admitted["input_tokens"]) is not int
                or not 1 <= admitted["input_tokens"] <= 4096
            ):
                raise ValueError("bounded input count required")
        if error is None:
            if not 2 <= count <= 36:
                raise ValueError("native tokenizer response bound required")
            done = records["completed"]
            fields(
                done,
                {
                    "counts",
                    "output_tokens",
                    "output_token_sha256",
                    "response_sha256",
                    "execution_identity",
                },
                "completion",
            )
            equal(done["counts"], counts, "one callback per output/forward")
            equal(done["output_tokens"], count, "output count")
            equal(done["execution_identity"], IDENTITY, "completion identity")
            hash_value(done["response_sha256"])
            hash_value(done["output_token_sha256"])
        else:
            equal(count, 0 if case == "forced_bos" else 1, "negative forward count")
            equal(records["error"], dict(error_class=error, counts=counts), "error receipt")
    equal(sorted(before), sorted(files), "exact case files/no unreported attempts")
    equal(inventory(root), before, "CPU receipts unchanged")
