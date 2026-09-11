"""Synthetic native metrics + actual request writer; no weights or native Torch."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace as NS
from typing import Any

import pytest
from test_efficient_requests_v1 import generate, libraries

from react_agent.foundation.normalization import text_hash
from react_agent.llm import efficient_requests_v1 as adapter
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.validation import efficient_requests_audit_v1 as impl


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, sort_keys=True))


def native_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def fixture(
    root: Path, monkeypatch: pytest.MonkeyPatch, role: Any = "agent"
) -> tuple[Path, Path, list[dict[str, Any]]]:
    attention, metrics = root / "attention", root / "native.jsonl"
    torch, hf, _ = libraries()
    monkeypatch.setattr(adapter, "libraries", lambda: (torch, hf))
    model, revision = (
        (adapter.MODEL, adapter.AGENT_REVISION)
        if role == "agent"
        else (adapter.MODEL_ID, adapter.GUARD_REVISION)
    )
    limit = 512 if role == "agent" else 128
    load = dict(
        event="load",
        model_id=model,
        model_revision=revision,
        dtype="float16",
        attention="sdpa",
        quantization=None,
        torch_version="2.10.0+cu128",
        transformers_version="5.5.0",
        cuda_version="12.8",
        protocol="agent_hf_dual_gpu_v1" if role == "agent" else "guard_hf_single_gpu_v1",
        load_seconds_including_hashes=42.5,
    )
    if role == "agent":
        load["adapter_protocol"] = "agent_hf_dual_gpu_v2_tf550"
    rows = [load]
    plan = [(1, 1), (4096, limit), (7, 3), (1, 1)]

    def invoke(messages: Any, config: GenerationConfig) -> ModelResponse:
        inputs, outputs = plan[len(rows) - 1]
        generate(torch, hf, role, inputs, outputs, masked=len(rows) % 2 == 0)
        rows.append(
            dict(
                event="generate",
                call_index=len(rows),
                status="OK",
                input_tokens=inputs,
                output_tokens=outputs,
                generate_seconds=0.25,
                call_seconds=0.5,
                generation_sha256=text_hash(config.model_dump_json()),
            )
        )
        return ModelResponse(text="synthetic result", model_id=model, model_revision=revision)

    backend = adapter.EfficientRequestBackend(
        NS(model_id=model, model_revision=revision, generate=invoke), role, attention
    )
    for _ in plan:
        backend.generate(
            [dict(role="user", content="synthetic")], GenerationConfig(max_new_tokens=limit)
        )
    native_rows(metrics, rows)
    return attention, metrics, rows


def audit(attention: Path, metrics: Path, role: Any = "agent", **kw: Any) -> dict[str, Any]:
    return impl.audit(
        attention,
        metrics,
        role=role,
        **(dict(worker_pid=os.getpid(), expected_requests=4) | kw),
    )


@pytest.mark.parametrize("role", ["agent", "guard"])
def test_actual_writer_join_repeatable_readonly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: Any
) -> None:
    attention, metrics, _ = fixture(tmp_path, monkeypatch, role)
    before = impl.inventory(attention), metrics.read_bytes()
    result = audit(attention, metrics, role)
    assert result == audit(attention, metrics, role)
    assert (impl.inventory(attention), metrics.read_bytes()) == before
    assert result["valid"] and result["request_count"] == 4
    assert len(result["input_sha256"]["attention"]) == 12
    assert result["requests"][1]["output_tokens"] == (512 if role == "agent" else 128)
    assert result["requests"][0]["last_forward_key_tokens"] == 1
    assert result["requests"][3]["last_forward_key_tokens"] == 1
    assert result["native_load_seconds"] == 42.5
    for key in (
        "phase5_accepted",
        "source_authenticated",
        "supervisor_pid_authenticated",
        "native_load_configuration_verified",
        "resolved_policy_verified",
        "full_boundary_cache_verified",
        "task_lifecycle_verified",
    ):
        assert result[key] is False


@pytest.mark.parametrize(
    "stage,key,value",
    [
        ("entered", "pid", 0),
        ("entered", "pid", True),
        ("entered", "request_index", 1.0),
        ("entered", "model_revision", "other"),
        ("entered", "role", "guard"),
        ("entered", "hf_sdpa_sha256", "0" * 64),
        ("entered", "flags_before", {"flash": True}),
        ("restored", "state_restored", 1),
        ("restored", "flags_after", dict(flash=False, math=False, mem_efficient=True, cudnn=False)),
        ("restored", "flags_after", dict(flash=1, math=True, mem_efficient=True, cudnn=True)),
        ("completed", "input_tokens", True),
        ("completed", "input_tokens", 2),
        ("completed", "forward_groups", 2),
        ("completed", "attention_calls", 27),
        ("completed", "helper_calls", 29),
        ("completed", "last_forward_key_tokens", 2),
        ("completed", "masked_calls", True),
        ("completed", "masked_calls", -1),
        ("completed", "masked_calls", 29),
        ("completed", "max_new_tokens", 128),
        ("completed", "output_tokens_verified", True),
        ("completed", "full_boundary_cache_verified", True),
        ("completed", "profiler_used", True),
        ("completed", "decoding_changed", True),
        ("completed", "scope", "full proof"),
        ("completed", "unexpected", "not allowed"),
    ],
)
def test_sidecar_corruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str, key: str, value: Any
) -> None:
    attention, metrics, _ = fixture(tmp_path, monkeypatch)
    path = attention / "request_000001" / f"{stage}.json"
    row = json.loads(path.read_text())
    row[key] = value
    write(path, row)
    with pytest.raises(ValueError):
        audit(attention, metrics)


@pytest.mark.parametrize(
    "row,key,value",
    [
        (0, "model_id", "different"),
        (0, "adapter_protocol", "v1"),
        (0, "torch_version", "other"),
        (0, "load_seconds_including_hashes", 0),
        (0, "load_seconds_including_hashes", True),
        (1, "event", "load"),
        (1, "status", "ERROR"),
        (1, "call_index", True),
        (1, "call_index", 2),
        (1, "generation_sha256", "0" * 64),
        (1, "input_tokens", 0),
        (1, "input_tokens", 4097),
        (1, "input_tokens", 1.0),
        (1, "output_tokens", True),
        (1, "output_tokens", 0),
        (1, "output_tokens", 513),
        (1, "generate_seconds", -1),
        (1, "generate_seconds", True),
        (1, "generate_seconds", float("nan")),
        (1, "generate_seconds", float("inf")),
        (1, "call_seconds", 0.1),
        (1, "call_seconds", 10**400),
    ],
)
def test_native_corruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, row: int, key: str, value: Any
) -> None:
    attention, metrics, rows = fixture(tmp_path, monkeypatch)
    rows[row][key] = value
    native_rows(metrics, rows)
    with pytest.raises(ValueError):
        audit(attention, metrics)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_stage",
        "error_stage",
        "empty_extra",
        "nested_empty",
        "gap",
        "duplicate_native",
        "missing_native",
        "reordered_native",
        "duplicate_key",
        "nonfinite_exp",
        "blank_line",
        "symlink_file",
        "symlink_directory",
        "nested_metrics",
        "non_object",
        "partial_json",
    ],
)
def test_inventory_and_json_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    attention, metrics, rows = fixture(tmp_path, monkeypatch)
    path = attention / "request_000001" / "completed.json"
    if fault == "missing_stage":
        path.unlink()
    elif fault == "error_stage":
        write(path.with_name("error.json"), {})
    elif fault == "empty_extra":
        (attention / "extra").mkdir()
    elif fault == "nested_empty":
        (path.parent / "extra").mkdir()
    elif fault == "gap":
        path.parent.rename(attention / "request_000005")
    elif fault == "duplicate_native":
        native_rows(metrics, rows + [rows[-1]])
    elif fault == "missing_native":
        native_rows(metrics, rows[:-1])
    elif fault == "reordered_native":
        native_rows(metrics, [rows[0], rows[2], rows[1], *rows[3:]])
    elif fault == "duplicate_key":
        path.write_text(
            path.read_text().replace('"input_tokens": 1', '"input_tokens": 2, "input_tokens": 1')
        )
    elif fault == "nonfinite_exp":
        metrics.write_text(
            metrics.read_text().replace('"call_seconds": 0.5', '"call_seconds": 1e999')
        )
    elif fault == "blank_line":
        metrics.write_text(metrics.read_text() + "\n")
    elif fault == "symlink_file":
        other = tmp_path / "copy.json"
        path.rename(other)
        path.symlink_to(other)
    elif fault == "symlink_directory":
        other = tmp_path / "copy"
        path.parent.rename(other)
        path.parent.symlink_to(other, target_is_directory=True)
    elif fault == "nested_metrics":
        metrics.rename(attention / "native.jsonl")
        metrics = attention / "native.jsonl"
    elif fault == "non_object":
        path.write_text("[]")
    elif fault == "partial_json":
        path.write_text('{"private_example":')
    with pytest.raises(ValueError):
        audit(attention, metrics)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"worker_pid": True},
        {"worker_pid": 0},
        {"worker_pid": os.getpid() + 1},
        {"expected_requests": True},
        {"expected_requests": 0},
        {"expected_requests": 3},
        {"role": "unknown"},
    ],
)
def test_external_expectations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kwargs: dict[str, Any]
) -> None:
    attention, metrics, _ = fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        audit(attention, metrics, **kwargs)


@pytest.mark.parametrize("target", ["metrics", "attention", "directory"])
def test_detect_mutation_during_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    attention, metrics, _ = fixture(tmp_path, monkeypatch)
    original = impl._request

    def mutate(*args: Any, **kw: Any) -> Any:
        result = original(*args, **kw)
        if result["request_index"] == 4:
            if target == "metrics":
                metrics.write_text(metrics.read_text() + " ")
            elif target == "directory":
                (attention / "extra").mkdir()
            else:
                path = attention / "request_000001" / "completed.json"
                path.write_text(path.read_text() + " ")
        return result

    monkeypatch.setattr(impl, "_request", mutate)
    with pytest.raises(ValueError, match="mutated"):
        audit(attention, metrics)


def test_metadata_not_copied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    attention, metrics, rows = fixture(tmp_path, monkeypatch)
    rows[1]["unassessed_metadata"] = "synthetic-private-marker"
    native_rows(metrics, rows)
    result = audit(attention, metrics)
    assert "synthetic-private-marker" not in json.dumps(result)


def test_cli_fresh_output_and_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    attention, metrics, _ = fixture(tmp_path, monkeypatch)
    output = tmp_path / "audit.json"
    command = [
        sys.executable,
        "scripts/audit_phase5_efficient_requests.py",
        "--attention",
        str(attention),
        "--metrics",
        str(metrics),
        "--role",
        "agent",
        "--worker-pid",
        str(os.getpid()),
        "--expected-requests",
        "4",
        "--output",
    ]
    result = subprocess.run(  # noqa: S603 — fixed local CLI, pytest-owned paths only
        command + [str(output)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text()) == audit(attention, metrics)
    prior = output.read_bytes()
    for forbidden in (output, metrics, attention / "new.json"):
        failed = subprocess.run(  # noqa: S603 — fixed local CLI, pytest-owned paths only
            command + [str(forbidden)], capture_output=True, check=False
        )
        assert failed.returncode != 0
    assert output.read_bytes() == prior
    assert not (attention / "new.json").exists()
    (attention / "request_000001" / "completed.json").unlink()
    failed_output = tmp_path / "failed.json"
    failed = subprocess.run(  # noqa: S603 — fixed local CLI, pytest-owned paths only
        command + [str(failed_output)], capture_output=True, check=False
    )
    assert failed.returncode != 0 and not failed_output.exists()
