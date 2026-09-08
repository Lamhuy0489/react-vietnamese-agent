#!/usr/bin/env python3
"""Audit one downloaded guard kernel and produce a reproducible technical report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from react_agent.agent.state import RunResult
from react_agent.config import load_generation_config
from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.guard_probe_v1 import write_json
from react_agent.schemas.trace import TraceEvent
from react_agent.validation.guard_probe_audit_v1 import audit_completed_probe as strict_audit
from react_agent.validation.guard_probe_audit_v2 import (
    audit_completed_probe,
    digest,
    read_json,
    require,
)

ROOT = Path(__file__).resolve().parents[1]


def audit_dummy(raw: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    clean = "data/clean/v1_1/"
    files = {
        "agent": "configs/agent/A0.yaml",
        "generation": "configs/runtime/default.yaml",
        "dev": clean + "splits/dev.jsonl",
        "selection": clean + "dev_pilot/task_ids.json",
        "faults": clean + "dev_pilot/fault_plans.json",
        "environment_manifest": clean + "manifests/environment_manifest.json",
    }
    for path in files.values():
        require(digest(ROOT / path) == bundle["source_sha256"][path], "local public input changed")
    ids = read_json(ROOT / files["selection"])["task_ids"]
    root = raw / "dummy"
    identity = read_json(root / "identity.json")
    require(
        identity
        == {
            "backend": "dummy",
            "benchmark": "clean_v1.1",
            "chat_adapter": "native",
            "evaluator_version": "clean_v1_1_typed_v1",
            "git_commit": bundle["source_commit"],
            "model_id": "dummy",
            "model_revision": "phase1_v1",
            "model_profile": "qwen",
            "measurement_protocol": None,
            "generation": load_generation_config(ROOT / files["generation"]).model_dump(),
            "task_ids": ids,
            "file_sha256": {name: bundle["source_sha256"][path] for name, path in files.items()},
        },
        "Dummy identity",
    )
    require(
        len(ids) == len(set(ids)) == 21
        and set(ids) == {p.name for p in (root / "tasks").iterdir()},
        "Dummy task coverage",
    )
    results, run_ids, count = [], set(), 0
    for task_id in ids:
        task = root / "tasks" / task_id
        checkpoint = read_json(task / "result.json")
        require(digest(task / "trace.jsonl") == checkpoint["trace_sha256"], "trace hash")
        result = RunResult.model_validate(checkpoint["result"])
        require(
            result.task_id == task_id
            and result.run_id not in run_ids
            and result.status == "completed",
            "Dummy result",
        )
        run_ids.add(result.run_id)
        trace = [
            TraceEvent.model_validate_json(line)
            for line in (task / "trace.jsonl").read_text().splitlines()
        ]
        require(
            [e.event for e in trace] == ["run_start", "model_output", "final_answer", "run_end"]
            and all(e.task_id == task_id and e.run_id == result.run_id for e in trace),
            "Dummy event order",
        )
        require(
            [e.timestamp for e in trace] == sorted(e.timestamp for e in trace), "trace time order"
        )
        count += len(trace)
        results.append(result.model_dump(mode="json"))
    require(read_json(root / "results.json") == results, "aggregate/checkpoints mismatch")
    summary = read_json(root / "summary.json")
    for key, value in {
        "tasks": 21,
        "terminal_runs": 21,
        "statuses": {"completed": 21},
        "model_errors": 0,
        "test_tasks_loaded": 0,
        "private_ground_truth_loaded": 0,
    }.items():
        require(summary[key] == value, "Dummy summary")
    return {
        "valid": True,
        "tasks": 21,
        "events": count,
        "unique_run_ids": len(run_ids),
        "scope": "Dummy transport/checkpoints only, not semantic task success",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--remote-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        not args.output.exists()
        and args.output.resolve().is_relative_to(ROOT / "results")
        and not args.output.resolve().is_relative_to(args.raw.resolve()),
        "fresh audit directory",
    )
    base = ROOT / "experiments/manifests/phase5_guard_bundle_v1_preflight03.json"
    bootstrap_path = ROOT / "experiments/manifests/phase5_guard_mount_v2_preflight01.json"
    bundle_path = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
    bootstrap, bundle = read_json(bootstrap_path), read_json(bundle_path)
    result = audit_completed_probe(args.raw, bundle_path, base)
    try:
        strict_audit(args.raw, bundle_path, base)
    except ValueError as exc:
        require(str(exc) == "worker cleanup", "unexpected strict audit failure")
        result["v1_strict_audit"] = "REJECTED: worker cleanup (not graceful)"
    else:
        result["v1_strict_audit"] = "PASS"
    require(
        read_json(args.raw / "guard_bootstrap_identity.json")
        == {
            "protocol": "guard_pax_bootstrap_v2",
            "bootstrap_commit": bootstrap["bootstrap_commit"],
            "bundle_manifest_sha256": bootstrap["bundle_manifest_sha256"],
        },
        "bootstrap identity",
    )
    metadata = read_json(args.remote_source / "kernel-metadata.json")
    require(metadata["code_file"] == Path(metadata["code_file"]).name, "remote code filename")
    require(
        digest(args.remote_source / metadata["code_file"]) == bootstrap["wrapper_sha256"],
        "remote wrapper differs from submitted bytes",
    )
    for key, value in {
        "id": "huylmhuhu/react-vn-guard15-probe-run-v1",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [bundle["dataset"]],
    }.items():
        require(metadata[key] == value, "remote kernel metadata")
    result["dummy"] = audit_dummy(args.raw, bundle)
    expected_files = {
        "react-vn-guard15-probe-run-v1.log",
        "guard_bootstrap_identity.json",
        "guard_bundle_identity.json",
        "guard_probe/probe_manifest.json",
        "guard_probe/summary.json",
        "dummy/identity.json",
        "dummy/results.json",
        "dummy/summary.json",
    }
    for trial in ("warm", "fresh"):
        expected_files.update(
            f"guard_probe/{trial}/{n}" for n in ("trial.json", "cuda_probe.json", "metrics.jsonl")
        )
    for task in read_json(args.raw / "dummy/identity.json")["task_ids"]:
        expected_files.update(f"dummy/tasks/{task}/{n}" for n in ("result.json", "trace.jsonl"))
    require(set(result["raw_sha256"]) == expected_files, "selected output inventory")
    require(prerequisites(ROOT) == read_json(base)["prerequisites"], "sealed input changed")
    result.update(
        bootstrap_commit=bootstrap["bootstrap_commit"],
        bootstrap_preflight_sha256=digest(bootstrap_path),
        remote_metadata=metadata,
        remote_source_sha256={
            p.name: digest(p) for p in args.remote_source.iterdir() if p.is_file()
        },
        test_access="hash-only prerequisites; no Test payload parsing",
        source_sha256={
            str(p.relative_to(ROOT)): digest(p)
            for p in (Path(__file__), ROOT / "src/react_agent/validation/guard_probe_audit_v2.py")
        },
    )
    lines = [
        "# Guard-only Qwen 1.5B technical probe",
        "",
        "Four synthetic calls; two T4 allocated, two guard workers sequential on device 1. "
        "Not ASR or model selection.",
        "",
        f"Probe repeatability: {result['probe_valid']}; all workers reaped: True; "
        f"graceful cleanup: {result['graceful_cleanup_pass']}.",
        "",
        "| Trial/call | Request s (cold includes load) | Generate s | Tokens | "
        "Token/s | Peak allocated GiB |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["calls"]:
        lines.append(
            f"| {row['trial']}/{row['index'] + 1}:{row['case']} | "
            f"{row['request_seconds']:.3f} | {row['generate_seconds']:.3f} | "
            f"{row['output_tokens']} | {row['tokens_per_generate_second']:.2f} | "
            f"{row['process_peak_allocated_bytes'] / 1024**3:.3f} |"
        )
    lines.extend(["", "## Observed classifications (not accuracy estimates)", ""])
    for row in result["rows"]:
        lines.append(
            f"- {row['trial']}/{row['index'] + 1}:{row['case']}: "
            + json.dumps(row["parsed"], ensure_ascii=False)
        )
    lines.extend(
        [
            "",
            "## Limits and next gates",
            "",
            "- Override/exfiltration input B classified SAFE: "
            + str(any(r["case"] == "B" and r["parsed"]["risk"] == "SAFE" for r in result["rows"]))
            + ". SAFE here is a diagnostic miss, not a passing security result.",
            "- All four B/A hashes match: "
            + str(len({r["response_sha256"] for r in result["rows"]}) == 1)
            + ". Repeatability does not prove discrimination or general statelessness.",
            "- Graceful cleanup: "
            + str(result["graceful_cleanup_pass"])
            + ". V1 strict audit result retained; reap does not measure GPU memory recovery.",
            "- Cold timings include process setup/hash scans/load; "
            "warm sample n=2 is not a general speed benchmark.",
            "- No agent resident, no concurrency/context stress, "
            "no benchmark Test, no semantic retries.",
            "- Next: GPU cleanup/cancellation, agent placement/coexistence, "
            "then declared grouped Dev validation. Phase 5 remains open.",
        ]
    )
    args.output.mkdir(parents=True)
    write_json(args.output / "audit.json", result)
    with (args.output / "report.md").open("x") as stream:
        stream.write("\n".join(lines) + "\n")
    print("PASS integrity; see separate graceful-cleanup and model-quality limitations")


if __name__ == "__main__":
    main()
