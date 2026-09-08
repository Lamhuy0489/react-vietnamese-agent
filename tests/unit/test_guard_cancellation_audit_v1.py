"""Synthetic GPU-shaped records, not real GPU evidence or benchmark fixtures."""

import json
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import REQUIRED, GuardSnapshot, SnapshotFile
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.validation.guard_cancellation_audit_v1 import audit_probe, memory


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


@pytest.fixture
def sample(tmp_path: Path) -> tuple[Path, GuardSnapshot, str]:
    root = Path(__file__).resolve().parents[2]
    receipt = json.loads(
        (root / "experiments/manifests/phase5_guard_cancellation_v1_preflight01.json").read_text()
    )
    summary = receipt["checks"][0]["probe"]
    pin = GuardSnapshot(
        upstream_revision="a" * 40,
        files=tuple(SnapshotFile(name=n, size=1, sha256="b" * 64) for n in sorted(REQUIRED)),
    )
    config, adapter = WarmGuardConfig(pin.model_id, pin.model_revision), GuardHFConfig()
    initial = summary["rows"][0]["before"]
    write(
        tmp_path / "manifest.json",
        {
            "protocol": "guard_cancellation_v1",
            "plan": [r["trial"] for r in summary["rows"]],
            "identity": {"backend": "hf", "source_commit": "c" * 40, "snapshot_sha256": pin.sha256},
            "execution_config_sha256": config.identity,
            "timeout_seconds": 120,
            "terminate_grace_seconds": 0.5,
            "kill_grace_seconds": 1,
            "generation": {"max_new_tokens": 128, "temperature": 0.0, "seed": 42},
            "model_generation_calls": 0,
            "recovery_samples": 6,
            "sample_interval_seconds": 1,
            "memory_tolerance_bytes": 256 * 1024**2,
            "min_residency_bytes": 2 * 1024**3,
            "initial_memory": initial,
            "automatic_retry": False,
        },
    )
    for row in summary["rows"]:
        name, pid = row["trial"], row["attempts"][0]["pid"]
        for a in row["attempts"]:
            a["execution_config_sha256"] = config.identity
            if a["status"] == "TIMEOUT":
                a["elapsed_seconds"] = 120.6
        write(tmp_path / name / "trial.json", row)
        write(tmp_path / name / "before.json", row["before"])
        write(tmp_path / name / "resident_memory.json", row["resident"])
        write(
            tmp_path / name / "resident_ready.json",
            {
                "pid": pid,
                "model_id": pin.model_id,
                "model_revision": pin.model_revision,
                "actual_cuda_operation": True,
                "model_generation_calls": 0,
            },
        )
        if name != "resident_close":
            write(
                tmp_path / name / "busy_entered.json",
                {
                    "pid": pid,
                    "ignore_sigterm": name == "ignore_term_timeout",
                    "actual_cuda_operation": True,
                    "model_generation_calls": 0,
                },
            )
        write(
            tmp_path / name / "hf_metrics.jsonl",
            {
                "event": "load",
                "model_id": pin.model_id,
                "model_revision": pin.model_revision,
                "snapshot_sha256": pin.sha256,
                "adapter_config_sha256": adapter.sha256,
                "device": 1,
                "device_map": {"": 1},
                "dtype": "float16",
                "quantization": None,
                "allocator_limit_bytes": adapter.allocator_limit_bytes,
                "device_name": "Fake T4",
                "load_seconds_including_hashes": 0.001,
                "process_peak_allocated_bytes": 3 * 1024**3,
            },
        )
    write(tmp_path / "summary.json", summary)
    return tmp_path, pin, "c" * 40


def test_valid(sample: tuple[Path, GuardSnapshot, str]) -> None:
    result = audit_probe(*sample)
    assert result["resource_recovery_pass"] and result["normal_close_graceful"]
    assert not result["phase5_accepted"]
    assert all(r["residual_bytes"] == [0] * 6 for r in result["measurements"])


@pytest.mark.parametrize(
    "change",
    [
        "pid",
        "timeout",
        "extra_attempt",
        "unreaped",
        "late_memory",
        "samples",
        "baseline",
        "resident",
        "kill",
        "summary",
        "generation",
        "cuda",
        "extra_file",
        "snapshot",
        "negative_memory",
    ],
)
def test_reject(sample: tuple[Path, GuardSnapshot, str], change: str) -> None:
    root, _, _ = sample
    path = root / "ignore_term_timeout/trial.json"
    value = json.loads(path.read_text())
    if change == "pid":
        value["attempts"][1]["pid"] += 1
    elif change == "timeout":
        value["attempts"][1]["elapsed_seconds"] = 2
    elif change == "extra_attempt":
        value["attempts"].append(value["attempts"][1])
    elif change == "unreaped":
        value["lifecycle"][0]["reaped"] = False
    elif change == "late_memory":
        value["after_samples"][-1]["free_bytes"] -= 1024**3
    elif change == "samples":
        value["after_samples"].pop()
    elif change == "baseline":
        value["before"]["free_bytes"] -= 1024**3
    elif change == "resident":
        value["resident"] = value["before"]
    elif change == "kill":
        value["lifecycle"][0].update(method="TERMINATE", exitcode=-15)
    elif change == "negative_memory":
        value["after_samples"][0]["free_bytes"] = -1
    else:
        path = (
            root
            / {
                "summary": "summary.json",
                "generation": "manifest.json",
                "snapshot": "manifest.json",
                "cuda": "ignore_term_timeout/busy_entered.json",
                "extra_file": "extra.json",
            }[change]
        )
        value = json.loads(path.read_text()) if path.exists() else {}
        if change == "summary":
            value["valid"] = False
        elif change == "generation":
            value["model_generation_calls"] = 1
        elif change == "snapshot":
            value["identity"]["snapshot_sha256"] = "d" * 64
        elif change == "cuda":
            value["actual_cuda_operation"] = False
    write(path, value)
    with pytest.raises(ValueError):
        audit_probe(*sample)


@pytest.mark.parametrize(
    "value", [None, {}, {"free_bytes": True, "total_bytes": 2}, {"free_bytes": 3, "total_bytes": 2}]
)
def test_memory_reject(value: Any) -> None:
    with pytest.raises(ValueError):
        memory(value)
