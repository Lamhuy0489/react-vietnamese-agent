"""Release-level ordinary pair checks with synthetic records only."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from react_agent.llm.ordinary_pair_probe_v1 import native_config
from react_agent.validation.guard_probe_audit_v2 import digest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def audit_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("audit_phase5_ordinary_pair_gpu")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_remote_metadata_requires_explicit_two_t4_identity(
    audit_module: ModuleType, tmp_path: Path
) -> None:
    remote = tmp_path / "remote"
    remote.mkdir()
    code = remote / "ordinary_pair_t4x2-v1.py"
    code.write_text("# synthetic wrapper\n", encoding="utf-8")
    metadata = {
        "id": audit_module.KERNEL_ID,
        "code_file": code.name,
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "docker_image": audit_module.IMAGE,
        "dataset_sources": [audit_module.DATASET],
        "kernel_sources": [],
        "competition_sources": [],
        "model_sources": [audit_module.AGENT_HANDLE],
    }
    write_json(remote / "kernel-metadata.json", metadata)
    result = audit_module._check_remote_metadata(remote, {"wrapper_sha256": digest(code)})
    assert result["metadata"]["machine_shape"] == "NvidiaTeslaT4"
    assert result["sha256"][code.name] == digest(code)

    metadata["machine_shape"] = "Gpu"
    write_json(remote / "kernel-metadata.json", metadata)
    with pytest.raises(ValueError, match="remote metadata machine_shape"):
        audit_module._check_remote_metadata(remote, {"wrapper_sha256": digest(code)})


def test_native_metrics_summary_counts_only_successful_calls(
    audit_module: ModuleType, tmp_path: Path
) -> None:
    probe_root = tmp_path / "ordinary_probe"
    config = native_config()
    for role in ("agent", "guard"):
        model = getattr(config, role)
        load = {
            "event": "load",
            "model_id": model.model_id,
            "model_revision": model.model_revision,
            "dtype": "float16",
            "quantization": None,
            "attention": "sdpa",
            "torch_version": "2.10.0+cu128",
            "transformers_version": "5.5.0",
            "load_seconds_including_hashes": 1.0,
        }
        rows = [load]
        for index in range(1, 4):
            rows.append(
                {
                    "event": "generate",
                    "call_index": index,
                    "status": "OK",
                    "generate_seconds": 0.5,
                    "input_tokens": 2,
                    "output_tokens": 1,
                }
            )
        path = probe_root / f"{role}_hf_metrics.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    result = audit_module._native_metrics(
        tmp_path,
        {
            "summary": {
                "execution_valid": True,
                "calls_submitted": 6,
                "responses_returned": 6,
                "reaped": True,
                "recovery_valid": True,
                "repeated_a_equal": {"agent": True, "guard": True},
            },
            "inner": {
                "native_policy_attention_metrics_consistent": True,
                "supervisor": {"worker_pids": {"agent": 11, "guard": 12}},
            },
        },
    )
    assert result["native_model_loads"] == 2
    assert result["native_model_generation_calls"] == 6
    assert len(result["calls"]) == 6
    assert result["two_t4_memory_observed"] is True


def test_native_metrics_rejects_failed_generation(
    audit_module: ModuleType, tmp_path: Path
) -> None:
    # Keep the fixture intentionally small and use the real identity checks.
    config = native_config()
    for role in ("agent", "guard"):
        model = getattr(config, role)
        rows = [
            {
                "event": "load",
                "model_id": model.model_id,
                "model_revision": model.model_revision,
                "dtype": "float16",
                "quantization": None,
                "attention": "sdpa",
                "torch_version": "2.10.0+cu128",
                "transformers_version": "5.5.0",
                "load_seconds_including_hashes": 1.0,
            }
        ] + [
            {
                "event": "generate",
                "call_index": index,
                "status": "ERROR" if index == 2 else "OK",
                "generate_seconds": 0.5,
                "input_tokens": 2,
                "output_tokens": 1,
            }
            for index in range(1, 4)
        ]
        path = tmp_path / "ordinary_probe" / f"{role}_hf_metrics.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="generation status"):
        audit_module._native_metrics(
            tmp_path,
            {
                "summary": {
                    "execution_valid": True,
                    "calls_submitted": 6,
                    "responses_returned": 6,
                    "reaped": True,
                    "recovery_valid": True,
                    "repeated_a_equal": {"agent": True, "guard": True},
                },
                "inner": {
                    "native_policy_attention_metrics_consistent": True,
                    "supervisor": {"worker_pids": {"agent": 11, "guard": 12}},
                },
            },
        )
