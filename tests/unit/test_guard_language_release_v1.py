"""Typed native-summary admission controls, explicitly synthetic records."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def case(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "language_audit", ROOT / "scripts/audit_phase5_guard_language_native_v1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    summary = dict(
        protocol="guard_language_native_cpu_v1",
        valid=True,
        library_verified=True,
        source_commit="a" * 40,
        torch="2.10.0+cu128",
        transformers="5.5.0",
        tokenizers="0.22.2",
        processor_source_sha256="b" * 64,
        documents=3069,
        case_indices=list(module.CASES),
        conflicting_processor_can_override=True,
        failures_propagated=["ValueError", "ValueError", "KeyboardInterrupt"],
        torch_threads_restored=True,
        model_generate_calls=0,
        model_weights_loaded=0,
        gpu_used=False,
        native_generation_validated=False,
        guard_quality_validated=False,
        phase5_accepted=False,
        test_payload_accessed=False,
        private_ground_truth_accessed=False,
        native_mask_checks=120,
        max_response_tokens_with_eos=60,
        compilation_seconds=1.0,
        mask_seconds=2.0,
        language_identity="c" * 64,
    )
    return module, summary


def test_synthetic_summary_passes_without_mutation(case):
    module, summary = case
    before = dict(summary)
    module.native_summary(summary, "a" * 40, "b" * 64)
    assert summary == before


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("valid", 1),
        ("library_verified", False),
        ("documents", 1),
        ("torch", "wrong"),
        ("source_commit", "b" * 40),
        ("processor_source_sha256", "c" * 64),
        ("native_mask_checks", 0),
        ("native_mask_checks", 2000),
        ("native_mask_checks", True),
        ("max_response_tokens_with_eos", 129),
        ("compilation_seconds", float("nan")),
        ("mask_seconds", -1),
        ("mask_seconds", True),
        ("language_identity", "wrong"),
        ("model_generate_calls", 1),
        ("guard_quality_validated", True),
        ("case_indices", []),
        ("failures_propagated", []),
        ("unknown", "extra"),
    ],
)
def test_summary_mutations_rejected(case, key, value):
    module, summary = case
    summary[key] = value
    with pytest.raises(ValueError):
        module.native_summary(summary, "a" * 40, "b" * 64)
