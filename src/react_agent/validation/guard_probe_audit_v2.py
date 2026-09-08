"""Versioned audit reporting forced cleanup separately; never launches inference."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_probe_v1 import GENERATION, PLAN, PROTOCOL, messages
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1.guard import GuardResult
from react_agent.security_v1.warm_guard import WarmGuardConfig


def require(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def audit_completed_probe(raw: Path, bundle_path: Path, receipt_path: Path) -> dict[str, Any]:
    """Accept complete transport evidence, separately report response repeatability.

    Failed/partial transports require a separate failure investigation, not repair or
    semantic retry. A hash mismatch between A responses is a valid measured failure.
    This checks the probe, not Dummy scoring, remote privacy or global VRAM cleanup.
    Unlike v1, recognized signal termination is recorded without claiming graceful close.
    """
    receipt, bundle = read_json(receipt_path), read_json(bundle_path)
    require(receipt["valid"] is True, "unaccepted bundle")
    require(digest(bundle_path) == receipt["bundle_manifest_sha256"], "bundle hash")
    require(bundle["source_commit"] == receipt["source_commit"], "source commit")
    files = sorted(p for p in raw.rglob("*") if p.is_file())
    require(not raw.is_symlink(), "linked root")
    require(not any(p.is_symlink() for p in raw.rglob("*")), "linked artifact")
    before = {p.relative_to(raw).as_posix(): digest(p) for p in files}
    identity = read_json(raw / "guard_bundle_identity.json")
    require(
        identity
        == {
            "source_commit": bundle["source_commit"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
            "snapshot": bundle["snapshot"],
            "wheel_sha256": bundle["wheel_sha256"],
        },
        "worker bundle identity",
    )
    pin = GuardSnapshot.model_validate(bundle["snapshot"])
    config = GuardHFConfig()
    execution = WarmGuardConfig(pin.model_id, pin.model_revision)
    probe = raw / "guard_probe"
    manifest, summary = read_json(probe / "probe_manifest.json"), read_json(probe / "summary.json")
    require(
        manifest
        == {
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
            "plan": [[trial, list(cases)] for trial, cases in PLAN],
            "classification_cache": "bypassed",
            "automatic_retry": False,
            "benchmark_dev_runs": 0,
            "test_payloads_parsed": 0,
        },
        "probe manifest",
    )
    rows: list[dict[str, Any]] = []
    timings: list[dict[str, Any]] = []
    lifecycles: list[dict[str, Any]] = []
    loads: list[dict[str, Any]] = []
    for trial, cases in PLAN:
        record = read_json(probe / trial / "trial.json")
        require(record["closed"] is True, "unclosed worker")
        events = record["lifecycle"]
        require(
            len(events) == 1
            and events[0]["reaped"] is True
            and (events[0]["method"], events[0]["exitcode"])
            in {("GRACEFUL", 0), ("TERMINATE", -15), ("KILL", -9)},
            "worker cleanup",
        )
        lifecycles.append({"trial": trial, "closed": True, "events": events})
        attempts = record["attempts"]
        require(len(record["records"]) == len(attempts) == len(cases), "call coverage")
        require(
            len({a["pid"] for a in attempts}) == 1 and attempts[0]["pid"] == events[0]["pid"],
            "worker identity",
        )
        require(
            read_json(probe / trial / "cuda_probe.json")
            == {
                "valid": True,
                "device": config.device,
                "actual_tensor_operation": True,
            },
            "actual CUDA probe",
        )
        metrics = [
            json.loads(line) for line in (probe / trial / "metrics.jsonl").read_text().splitlines()
        ]
        require(len(metrics) == len(cases) + 1, "metrics coverage")
        load = metrics[0]
        for key, expected in {
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
        }.items():
            require(load[key] == expected, f"load identity: {key}")
        require("T4" in load["device_name"], "GPU model")
        require(positive(load["load_seconds_including_hashes"]), "load timing")
        loads.append({"trial": trial, **load})
        for index, (case, row, attempt, metric) in enumerate(
            zip(cases, record["records"], attempts, metrics[1:], strict=True)
        ):
            require(
                row["trial"] == trial
                and row["index"] == index
                and row["case"] == case
                and row["status"] == "OK",
                "completed transport",
            )
            GuardResult.model_validate(row["parsed"])
            require(
                len(row["response_sha256"]) == 64
                and all(c in "0123456789abcdef" for c in row["response_sha256"]),
                "response digest",
            )
            require(
                attempt["status"] == "OK"
                and attempt["sequence"] == index + 1
                and attempt["cold_start"] is (index == 0)
                and attempt["worker_retained"] is True,
                "attempt lifecycle",
            )
            require(
                attempt["request_sha256"] == text_hash(canonical_json(messages(case)))
                and attempt["generation_sha256"]
                == text_hash(canonical_json(GENERATION.model_dump()))
                and attempt["execution_config_sha256"] == execution.identity,
                "request identity",
            )
            require(
                metric["event"] == "generate"
                and metric["status"] == "OK"
                and metric["call_index"] == index + 1
                and metric["generation_sha256"] == text_hash(GENERATION.model_dump_json()),
                "generation identity",
            )
            require(
                positive(attempt["elapsed_seconds"])
                and positive(metric["generate_seconds"])
                and 0 < metric["output_tokens"] <= 128
                and 0 < metric["input_tokens"] <= config.max_input_tokens,
                "timing/token bounds",
            )
            require(
                0 < metric["process_peak_allocated_bytes"] <= config.allocator_limit_bytes,
                "allocator budget",
            )
            rows.append(row)
            timings.append(
                {
                    "trial": trial,
                    "case": case,
                    "index": index,
                    "request_seconds": attempt["elapsed_seconds"],
                    "tokens_per_generate_second": metric["output_tokens"]
                    / metric["generate_seconds"],
                    **metric,
                }
            )
    same = len({r["response_sha256"] for r in rows if r["case"] == "A"}) == 1
    for key, expected in {
        "protocol": PROTOCOL,
        "valid": same,
        "phase5_accepted": False,
        "planned_calls": 4,
        "attempted_calls": 4,
        "structured_valid_calls": 4,
        "same_A_response_sha256": same,
        "rows": rows,
        "lifecycle": lifecycles,
    }.items():
        require(summary[key] == expected, f"summary mismatch: {key}")
    require(
        before == {p.relative_to(raw).as_posix(): digest(p) for p in raw.rglob("*") if p.is_file()},
        "raw changed during audit",
    )
    return {
        "protocol": "guard_completed_probe_audit_v2",
        "audit_module_sha256": digest(Path(__file__)),
        "integrity_valid": True,
        "probe_valid": same,
        "graceful_cleanup_pass": all(x["events"][0]["method"] == "GRACEFUL" for x in lifecycles),
        "cleanup": lifecycles,
        "all_workers_reaped": True,
        "phase5_accepted": False,
        "source_commit": bundle["source_commit"],
        "model_revision": pin.model_revision,
        "bundle_manifest_sha256": digest(bundle_path),
        "preflight_receipt_sha256": digest(receipt_path),
        "raw_sha256": before,
        "calls": timings,
        "loads": loads,
        "rows": rows,
        "limits": "Four synthetic calls; no ASR, agent coexistence or post-reap VRAM measurement.",
    }
