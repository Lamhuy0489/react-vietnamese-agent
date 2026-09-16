"""Synthetic CPU release receipts and negative controls; never loads native libraries."""

import copy
import hashlib
import json
import zipfile

import pytest

from react_agent.validation import constrained_generate_cpu_audit_v1 as impl


@pytest.fixture
def case(tmp_path):
    root, wheel = tmp_path / "cases", tmp_path / "wheel.zip"
    pins = {}
    with zipfile.ZipFile(wheel, "w") as archive:
        for name in (
            "generation/logits_process.py",
            "generation/utils.py",
            "models/qwen2/modeling_qwen2.py",
            "models/qwen2/configuration_qwen2.py",
        ):
            data = ("synthetic " + name).encode()
            archive.writestr("transformers/" + name, data)
            pins[name] = hashlib.sha256(data).hexdigest()
    summary = dict(
        protocol="constrained_generate_cpu_v1",
        valid=True,
        library_verified=True,
        source_commit="a" * 40,
        seed=42,
        language_identity=impl.LANGUAGE,
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
        source_sha256=pins,
        cases=[],
    )
    for name in impl.CASES:
        error = (
            "ValueError"
            if name == "forced_bos"
            else "KeyboardInterrupt"
            if name == "interrupt"
            else None
        )
        count = 0 if name == "forced_bos" else 1 if name == "interrupt" else 28
        counts = dict(
            generate=1,
            processors=0 if name == "forced_bos" else 1,
            callbacks=28 if error is None else 0,
        )
        summary["cases"].append(
            dict(
                case=name,
                error_class=error,
                forward_calls=count,
                methods_restored=True,
                seconds=0.1,
            )
        )
        records = dict(
            entered=dict(execution_identity=impl.IDENTITY),
            restored=dict(methods_restored=True, counts=counts),
        )
        if name != "forced_bos":
            records["admitted"] = dict(
                input_tokens=7,
                policy_sha256=impl.POLICY,
                language_sha256=impl.LANGUAGE,
                processor_types=[
                    "RepetitionPenaltyLogitsProcessor",
                    "PrefixConstrainedLogitsProcessor",
                ],
            )
        if error is None:
            records["completed"] = dict(
                counts=counts,
                output_tokens=count,
                output_token_sha256="b" * 64,
                response_sha256="c" * 64,
                execution_identity=impl.IDENTITY,
            )
        else:
            records["error"] = dict(error_class=error, counts=counts)
        (root / name).mkdir(parents=True)
        for stage, value in records.items():
            (root / name / f"{stage}.json").write_text(
                json.dumps(dict(case=name, stage=stage, **value))
            )
    return root, summary, wheel


def run(case):
    root, summary, wheel = case
    impl.validate_result(
        root, summary, "a" * 40, wheel, summary["source_sha256"]["generation/logits_process.py"]
    )


def test_synthetic_complete_consistent_and_read_only(case):
    before = copy.deepcopy(case[1])
    run(case)
    run(case)
    assert case[1] == before


@pytest.mark.parametrize(
    "fault",
    [
        "count_bool",
        "timing_bool",
        "timing_nan",
        "order",
        "missing_case",
        "quality",
        "gpu",
        "library",
        "source",
        "architecture",
        "unknown",
        "policy",
        "chain",
        "callbacks",
        "restoration",
        "missing_receipt",
        "extra_receipt",
        "hash",
        "early_forward",
        "interruption",
        "duplicate_key",
    ],
)
def test_tampering_refused(case, fault):
    root, summary, _ = case
    path = root / "success01/completed.json"
    if fault == "count_bool":
        summary["cases"][0]["forward_calls"] = True
    elif fault == "timing_bool":
        summary["cases"][0]["seconds"] = True
    elif fault == "timing_nan":
        summary["cases"][0]["seconds"] = float("nan")
    elif fault == "order":
        summary["cases"].reverse()
    elif fault == "missing_case":
        summary["cases"].pop()
    elif fault == "quality":
        summary["guard_quality_validated"] = True
    elif fault == "gpu":
        summary["gpu_used"] = True
    elif fault == "library":
        summary["library_verified"] = False
    elif fault == "source":
        summary["source_commit"] = "wrong"
    elif fault == "architecture":
        summary["architecture"]["num_hidden_layers"] = 28
    elif fault == "unknown":
        summary["extra"] = 1
    elif fault == "early_forward":
        summary["cases"][2]["forward_calls"] = 1
    elif fault == "interruption":
        summary["cases"][3]["error_class"] = None
    elif fault == "missing_receipt":
        path.unlink()
    elif fault == "extra_receipt":
        (root / "extra.json").write_text("{}")
    elif fault == "duplicate_key":
        path.write_text('{"stage":"completed","stage":"completed"}')
    else:
        if fault in {"policy", "chain"}:
            path = root / "success01/admitted.json"
        if fault == "restoration":
            path = root / "success01/restored.json"
        record = json.loads(path.read_text())
        if fault == "policy":
            record["policy_sha256"] = "f" * 64
        elif fault == "chain":
            record["processor_types"].reverse()
        elif fault == "callbacks":
            record["counts"]["callbacks"] = 27
        elif fault == "restoration":
            record["methods_restored"] = False
        else:
            record["response_sha256"] = "not a hash"
        path.write_text(json.dumps(record))
    with pytest.raises((ValueError, KeyError, FileNotFoundError)):
        run(case)
