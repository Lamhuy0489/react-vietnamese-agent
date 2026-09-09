"""Synthetic evidence tests; never GPU measurements or held-out payloads."""

import copy
import importlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import MODEL
from react_agent.llm.agent_runtime_input_v1 import INVENTORY_SHA256
from react_agent.llm.base import GenerationConfig
from react_agent.llm.coexistence_placement_v1 import PlacementPlan
from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import REQUIRED, GuardSnapshot, SnapshotFile
from react_agent.llm.model_pair_hf_v1 import AGENT_CONTENT, AGENT_REVISION
from react_agent.llm.model_pair_probe_v1 import MIN_RESIDENT, TOLERANCE, SyntheticPairObserver
from react_agent.llm.model_pair_v1 import READY_COMMAND, ModelIdentity, PairConfig
from react_agent.llm.pair_cancellation_v1 import BUSY, PLAN, busy_role
from react_agent.validation.pair_cancellation_audit_v1 import audit_probe


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


@pytest.fixture
def sample(tmp_path: Path) -> tuple[Path, GuardSnapshot, str]:
    pin = GuardSnapshot(
        upstream_revision="a" * 40,
        files=tuple(SnapshotFile(name=n, size=1, sha256="b" * 64) for n in sorted(REQUIRED)),
    )
    config = PairConfig(
        ModelIdentity(MODEL, AGENT_REVISION), ModelIdentity(pin.model_id, pin.model_revision)
    )
    memory = SyntheticPairObserver()
    baseline = memory.sample("baseline")
    write(
        tmp_path / "manifest.json",
        {
            "protocol": "pair_cancellation_v1",
            "plan": list(PLAN),
            "identity": {
                "backend": "hf",
                "source_commit": "c" * 40,
                "snapshot_sha256": pin.sha256,
                "agent_adapter": "agent_hf_dual_gpu_v2_tf550",
                "environment": {"torch": "2.10.0+cu128", "cuda": "12.8", "transformers": "5.5.0"},
            },
            "actual_cuda": True,
            "initial_memory": baseline,
            "sample_interval_seconds": 1.0,
            "recovery_samples": 6,
            "tolerance_bytes": TOLERANCE,
            "min_resident_bytes": list(MIN_RESIDENT),
            "model_generation_calls": 0,
            "automatic_retry": False,
        },
    )
    rows = []
    for index, trial in enumerate(PLAN):
        root = tmp_path / trial
        workers = {}
        loads = {}
        for j, role in enumerate(("agent", "guard")):
            busy = role == busy_role(trial)
            pid = 100 + index * 2 + j
            identity = config.agent if role == "agent" else config.guard
            attempts = []
            for i in range(2 if busy else 1):
                execution = config.execution(role, cold=i == 0)
                attempts.append(
                    {
                        "pid": pid,
                        "sequence": i + 1,
                        "cold_start": i == 0,
                        "status": "OK" if i == 0 else "TIMEOUT",
                        "reaped": i != 0,
                        "worker_retained": i == 0,
                        "elapsed_seconds": 2 if i == 0 else execution.timeout_seconds + 0.5,
                        "load_seconds": 1 if i == 0 else 0,
                        "execution_config_sha256": execution.identity,
                        "request_sha256": text_hash(
                            canonical_json(
                                [{"role": "user", "content": READY_COMMAND if i == 0 else BUSY}]
                            )
                        ),
                        "generation_sha256": text_hash(
                            canonical_json(GenerationConfig().model_dump())
                        ),
                    }
                )
            method, code = (
                ("KILL", -9) if busy and trial == "guard_ignore_term" else ("TERMINATE", -15)
            )
            workers[role] = {
                "attempts": attempts,
                "closed": True,
                "handle_pending": False,
                "lifecycle": [
                    {
                        "pid": pid,
                        "sequence": 1,
                        "method": method,
                        "exitcode": code,
                        "reaped": True,
                        "elapsed_seconds": 0.7,
                    }
                ],
            }
            load = {
                "event": "load",
                "model_id": identity.model_id,
                "model_revision": identity.model_revision,
                "dtype": "float16",
                "quantization": None,
                "attention": "sdpa",
                "torch_version": "2.10.0+cu128",
                "transformers_version": "5.5.0",
                "cuda_version": "12.8",
                "load_seconds_including_hashes": 0.9,
            }
            if role == "agent":
                plan = PlacementPlan()
                load.update(
                    adapter_protocol="agent_hf_dual_gpu_v2_tf550",
                    placement_sha256=plan.sha256,
                    device_map=plan.device_map(),
                    agent_caps=list(plan.agent_caps),
                    runtime_admission={
                        "content_sha256": AGENT_CONTENT,
                        "inventory_sha256": INVENTORY_SHA256,
                        "full_inventory_match": False,
                        "documentation_mismatches": ["README.md"],
                        "runtime_files_match": True,
                        "runtime_files": 11,
                        "parameter_tensors": 339,
                        "serialized_parameter_bytes": 15231233024,
                    },
                    memory=[
                        {
                            "device": d,
                            "allocated_bytes": 1,
                            "reserved_bytes": 1,
                            "peak_allocated_bytes": 1,
                            "peak_reserved_bytes": 1,
                        }
                        for d in (0, 1)
                    ],
                )
            else:
                adapter = GuardHFConfig()
                load.update(
                    snapshot_sha256=pin.sha256,
                    adapter_config_sha256=adapter.sha256,
                    device=1,
                    device_map={"": 1},
                    allocator_limit_bytes=adapter.allocator_limit_bytes,
                    process_allocated_bytes=1,
                    process_reserved_bytes=1,
                    process_peak_allocated_bytes=1,
                    process_peak_reserved_bytes=1,
                )
            loads[role] = load
            write(root / f"{role}_hf_metrics.jsonl", load)
        write(
            root / "closed.json",
            {"state": "FAILED", "config_sha256": config.sha256, "workers": workers},
        )
        ready = copy.deepcopy(workers)
        for w in ready.values():
            w.update(attempts=w["attempts"][:1], lifecycle=[], closed=False, handle_pending=True)
        write(
            root / "ready.json",
            {
                "pair": {"state": "READY", "config_sha256": config.sha256, "workers": ready},
                "memory": memory.sample("resident"),
            },
        )
        write(root / "pair_config.json", {"sha256": config.sha256, "values": asdict(config)})
        write(root / "baseline.json", {"memory": baseline})
        role = busy_role(trial)
        write(
            root / "busy_entered.json",
            {
                "trial": trial,
                "role": role,
                "pid": workers[role]["attempts"][0]["pid"],
                "ignore_sigterm": trial == "guard_ignore_term",
                "actual_cuda_operation": True,
                "devices": [0, 1] if role == "agent" else [1],
                "model_generation_calls": 0,
            },
        )
        for i in range(6):
            write(root / f"recovery_{i}.json", {"memory": baseline, "elapsed_seconds": 200 + i})
        row = {
            "trial": trial,
            "valid": True,
            "status": "EXECUTION_COMPLETE",
            "timeout_observed": True,
            "reaped": True,
            "cleanup_error": False,
            "recovery_valid": True,
            "forced_method_valid": True,
        }
        rows.append(row)
        write(root / "trial.json", row)
    write(
        tmp_path / "summary.json",
        {
            "protocol": "pair_cancellation_v1",
            "rows": rows,
            "valid": True,
            "phase5_accepted": False,
            "model_generation_calls": 0,
            "error_class": None,
            "scope": "Cancellation with sibling resident; not model generation or context stress",
        },
    )
    return tmp_path, pin, "c" * 40


def test_valid_synthetic_evidence(sample: tuple[Path, GuardSnapshot, str]) -> None:
    result = audit_probe(*sample)
    assert result["valid"] and result["workers_reaped"] == 6 and not result["phase5_accepted"]
    assert all(r["signed_residual_bytes"] == [[0, 0]] * 6 for r in result["measurements"])


@pytest.mark.parametrize(
    "log,counts",
    [
        ("", []),
        (
            "resource_tracker: There appear to be 3 leaked semaphore objects "
            "to clean up at shutdown",
            [3],
        ),
        (
            "There appear to be 2 leaked semaphore objects\n"
            "There appear to be 1 leaked semaphore objects",
            [2, 1],
        ),
    ],
)
def test_ipc_warnings_never_claim_clean(
    monkeypatch: pytest.MonkeyPatch, log: str, counts: list[int]
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    tool = importlib.import_module("audit_phase5_pair_cancel_gpu")
    result = tool.shutdown_warnings(log)
    assert result["semaphore_warning_counts"] == counts
    assert result["ipc_cleanup_verified"] is False


@pytest.mark.parametrize(
    "case",
    [
        "pid",
        "deadline",
        "request",
        "generation",
        "pending",
        "kill",
        "load",
        "budget",
        "runtime",
        "cuda",
        "residual",
        "time",
        "total",
        "resident",
        "manifest",
        "summary",
        "extra",
        "missing",
        "ready",
        "load_count",
    ],
)
def test_reject_corruption(sample: tuple[Path, GuardSnapshot, str], case: str) -> None:
    root, _, _ = sample
    trial = root / "guard_ignore_term"
    name = {
        "load": "guard_hf_metrics.jsonl",
        "budget": "agent_hf_metrics.jsonl",
        "runtime": "agent_hf_metrics.jsonl",
        "cuda": "busy_entered.json",
        "residual": "recovery_5.json",
        "time": "recovery_5.json",
        "total": "recovery_0.json",
        "resident": "ready.json",
        "ready": "ready.json",
        "load_count": "guard_hf_metrics.jsonl",
    }.get(case, "closed.json")
    path = trial / name
    if case in ("manifest", "summary"):
        path = root / f"{case}.json"
    if case == "extra":
        write(trial / "extra.json", {})
    elif case == "missing":
        path.unlink()
    else:
        v = json.loads(path.read_text())
        if case == "pid":
            v["workers"]["guard"]["attempts"][1]["pid"] = -1
        elif case == "deadline":
            v["workers"]["guard"]["attempts"][1]["elapsed_seconds"] = 1
        elif case in ("request", "generation"):
            v["workers"]["guard"]["attempts"][1][case + "_sha256"] = "0" * 64
        elif case == "pending":
            v["workers"]["agent"]["handle_pending"] = True
        elif case == "kill":
            v["workers"]["guard"]["lifecycle"][0].update(method="TERMINATE", exitcode=-15)
        elif case == "load":
            v["model_revision"] = "other"
        elif case == "budget":
            v["memory"][1]["peak_reserved_bytes"] = 99 * 1024**3
        elif case == "runtime":
            v["runtime_admission"]["full_inventory_match"] = True
        elif case == "cuda":
            v["actual_cuda_operation"] = False
        elif case == "residual":
            v["memory"][1]["free_bytes"] -= 1024**3
        elif case == "time":
            v["elapsed_seconds"] = float("nan")
        elif case == "total":
            v["memory"][1]["total_bytes"] += 1
        elif case == "resident":
            v["memory"] = SyntheticPairObserver().sample("baseline")
        elif case == "manifest":
            v["automatic_retry"] = True
        elif case == "summary":
            v["valid"] = False
        elif case == "ready":
            v["pair"]["workers"]["guard"]["attempts"][0]["pid"] = -1
        write(path, v)
        if case == "load_count":
            path.write_text(path.read_text() * 2)
    with pytest.raises((ValueError, FileNotFoundError)):
        audit_probe(*sample)
