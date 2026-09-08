"""Synthetic audit records only: these tests never load a model or CUDA."""

import json
from pathlib import Path
from typing import Any

import pytest

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_probe_v1 import GENERATION, PLAN, PROTOCOL, messages
from react_agent.llm.guard_snapshot_v1 import REQUIRED, GuardSnapshot, SnapshotFile
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.validation.guard_probe_audit_v1 import audit_completed_probe, digest


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def sample(tmp_path: Path) -> tuple[Path, Path, Path]:
    raw, bundle_path, receipt_path = tmp_path / "raw", tmp_path / "bundle", tmp_path / "receipt"
    pin = GuardSnapshot(
        upstream_revision="a" * 40,
        files=tuple(SnapshotFile(name=n, size=1, sha256="b" * 64) for n in sorted(REQUIRED)),
    )
    config = GuardHFConfig()
    execution = WarmGuardConfig(pin.model_id, pin.model_revision)
    bundle = {
        "source_commit": "c" * 40,
        "snapshot": pin.model_dump(mode="json"),
        "wheel_sha256": {"synthetic.whl": "d" * 64},
    }
    write(bundle_path, bundle)
    write(
        receipt_path,
        {
            "valid": True,
            "source_commit": bundle["source_commit"],
            "bundle_manifest_sha256": digest(bundle_path),
        },
    )
    write(
        raw / "guard_bundle_identity.json",
        {**bundle, "bundle_manifest_sha256": digest(bundle_path)},
    )
    write(
        raw / "guard_probe/probe_manifest.json",
        {
            "protocol": PROTOCOL,
            "identity": {
                "backend": "hf",
                "source_commit": bundle["source_commit"],
                "snapshot_sha256": pin.sha256,
                "adapter_config_sha256": config.sha256,
            },
            "worker_config_sha256": execution.identity,
            "model_id": pin.model_id,
            "model_revision": pin.model_revision,
            "generation": GENERATION.model_dump(),
            "inputs_sha256": text_hash(canonical_json({k: messages(k) for k in ("A", "B")})),
            "plan": PLAN,
            "classification_cache": "bypassed",
            "automatic_retry": False,
            "benchmark_dev_runs": 0,
            "test_payloads_parsed": 0,
        },
    )
    all_rows, lifecycles = [], []
    for trial, cases in PLAN:
        root = raw / "guard_probe" / trial
        events = [{"pid": 123, "reaped": True, "exitcode": 0, "method": "GRACEFUL"}]
        rows, attempts = [], []
        metrics = [
            {
                "event": "load",
                "model_id": pin.model_id,
                "model_revision": pin.model_revision,
                "snapshot_sha256": pin.sha256,
                "adapter_config_sha256": config.sha256,
                "device": 1,
                "device_map": {"": 1},
                "dtype": "float16",
                "quantization": None,
                "allocator_limit_bytes": config.allocator_limit_bytes,
                "device_name": "Synthetic T4",
                "load_seconds_including_hashes": 1.0,
            }
        ]
        for i, case in enumerate(cases):
            rows.append(
                {
                    "trial": trial,
                    "index": i,
                    "case": case,
                    "status": "OK",
                    "response_sha256": "e" * 64,
                    "parsed": {"risk": "SAFE", "labels": [], "confidence": "HIGH"},
                }
            )
            attempts.append(
                {
                    "pid": 123,
                    "sequence": i + 1,
                    "status": "OK",
                    "cold_start": i == 0,
                    "worker_retained": True,
                    "elapsed_seconds": 2.0,
                    "execution_config_sha256": execution.identity,
                    "request_sha256": text_hash(canonical_json(messages(case))),
                    "generation_sha256": text_hash(canonical_json(GENERATION.model_dump())),
                }
            )
            metrics.append(
                {
                    "event": "generate",
                    "status": "OK",
                    "call_index": i + 1,
                    "generation_sha256": text_hash(GENERATION.model_dump_json()),
                    "generate_seconds": 0.5,
                    "output_tokens": 20,
                    "input_tokens": 100,
                    "process_peak_allocated_bytes": 1024,
                }
            )
        write(
            root / "trial.json",
            {"records": rows, "attempts": attempts, "lifecycle": events, "closed": True},
        )
        write(
            root / "cuda_probe.json", {"valid": True, "device": 1, "actual_tensor_operation": True}
        )
        (root / "metrics.jsonl").write_text("\n".join(json.dumps(m) for m in metrics) + "\n")
        all_rows.extend(rows)
        lifecycles.append({"trial": trial, "closed": True, "events": events})
    write(
        raw / "guard_probe/summary.json",
        {
            "protocol": PROTOCOL,
            "valid": True,
            "phase5_accepted": False,
            "planned_calls": 4,
            "attempted_calls": 4,
            "structured_valid_calls": 4,
            "same_A_response_sha256": True,
            "rows": all_rows,
            "lifecycle": lifecycles,
        },
    )
    return raw, bundle_path, receipt_path


def test_audit_and_immutable_reproduction(sample: tuple[Path, Path, Path]) -> None:
    first = audit_completed_probe(*sample)
    assert first == audit_completed_probe(*sample)
    assert first["integrity_valid"] and first["probe_valid"]
    assert not first["phase5_accepted"]
    assert len(first["calls"]) == 4 and len(first["loads"]) == 2
    assert first["calls"][0]["tokens_per_generate_second"] == 40


@pytest.mark.parametrize(
    "change",
    [
        "identity",
        "plan",
        "retry",
        "cleanup",
        "request",
        "coverage",
        "cuda",
        "summary",
        "bundle",
        "symlink",
        "metrics",
    ],
)
def test_reject_corruption(sample: tuple[Path, Path, Path], change: str) -> None:
    raw, bundle, _ = sample
    path = raw / "guard_probe/warm/trial.json"
    if change == "bundle":
        bundle.write_text(bundle.read_text() + " ")
    elif change == "symlink":
        (raw / "linked").symlink_to(bundle)
    elif change == "metrics":
        path = raw / "guard_probe/warm/metrics.jsonl"
        values = [json.loads(line) for line in path.read_text().splitlines()]
        values[1]["generate_seconds"] = -1
        path.write_text("\n".join(json.dumps(v) for v in values))
    else:
        if change == "identity":
            path = raw / "guard_bundle_identity.json"
        elif change in {"plan", "retry"}:
            path = raw / "guard_probe/probe_manifest.json"
        elif change == "cuda":
            path = raw / "guard_probe/warm/cuda_probe.json"
        elif change == "summary":
            path = raw / "guard_probe/summary.json"
        value = json.loads(path.read_text())
        if change == "identity":
            value["source_commit"] = "f" * 40
        elif change == "plan":
            value["plan"].reverse()
        elif change == "retry":
            value["automatic_retry"] = True
        elif change == "cleanup":
            value["lifecycle"][0]["reaped"] = False
        elif change == "request":
            value["attempts"][0]["request_sha256"] = "f" * 64
        elif change == "coverage":
            value["records"].pop()
        elif change == "cuda":
            value["actual_tensor_operation"] = False
        elif change == "summary":
            value["phase5_accepted"] = True
        write(path, value)
    with pytest.raises(ValueError):
        audit_completed_probe(*sample)


def test_measured_mismatch_is_not_corruption(sample: tuple[Path, Path, Path]) -> None:
    raw, _, _ = sample
    trial_path = raw / "guard_probe/fresh/trial.json"
    trial = json.loads(trial_path.read_text())
    trial["records"][0]["response_sha256"] = "f" * 64
    write(trial_path, trial)
    summary_path = raw / "guard_probe/summary.json"
    summary = json.loads(summary_path.read_text())
    summary["rows"][-1] = trial["records"][0]
    summary.update(valid=False, same_A_response_sha256=False)
    write(summary_path, summary)
    result = audit_completed_probe(*sample)
    assert result["integrity_valid"] and not result["probe_valid"]
