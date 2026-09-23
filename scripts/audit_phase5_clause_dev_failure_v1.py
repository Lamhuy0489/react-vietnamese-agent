"""Authenticate v1 pre-start infrastructure failure without accepting a native run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_phase5_clause_dev_gpu_v1 as release

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.clause_dev_dispatch_v1 import release_identity
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_probe_v1 import validate_memory
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.exit_pair_audit_v1 import checked_runtime
from react_agent.validation.tokenizer_metadata_v1 import authenticate

ERROR = "got multiple values for keyword argument 'constrained'"


def failure_evidence(
    probe: Path,
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
    commit: str,
    model_inventory: Path,
    environment: Path,
) -> dict[str, Any]:
    raw = probe.parent
    before = inventory(raw)
    saved = read_record(probe / "shard0/identity.json")
    source = read_record(raw / "source_manifest.json")
    manifest, _ = release_identity(
        release.ROOT / "data/adversarial/release_v2",
        environment,
        commit,
        "hf",
        model_inventory,
        pin,
        release=source,
    )
    manifest["exit_observer"]["runtime"] = checked_runtime(saved["run"]["exit_observer"]["runtime"])
    equal(saved, {"run": manifest, "shard": 0}, "failed run identity")
    task = manifest["tasks"][0]
    root = probe / "shard0/tasks" / task["key"]
    prefix = root.relative_to(raw).as_posix() + "/"
    expected = {
        "observer_bootstrap.json",
        "source_manifest.json",
        "dev32/shard0/identity.json",
        "react-vn-clause-dev32-v1.log",
        "tokenizers/agent_tokenizer_config.json",
        "tokenizers/guard_tokenizer_config.json",
        *{
            prefix + name
            for name in (
                "baseline.json",
                "recovery.json",
                "environment/cached_pages/pages.json",
                "environment/documents/documents.json",
                "environment/database/seed.json",
                "environment/database/university.db",
            )
        },
    }
    equal(sorted(before), sorted(expected), "exact pre-start evidence; no execution/checkpoints")
    baseline = read_record(root / "baseline.json")["memory"]
    samples = read_record(root / "recovery.json")["memory"]
    validate_memory(baseline)
    equal(len(samples), manifest["recovery"]["samples"], "recovery sample count")
    for sample in samples:
        validate_memory(sample)
    recovered = all(
        sample[i]["total_bytes"] == baseline[i]["total_bytes"]
        and abs(sample[i]["free_bytes"] - baseline[i]["free_bytes"])
        <= manifest["recovery"]["tolerance_bytes"]
        for sample in samples[-manifest["recovery"]["stable_tail"] :]
        for i in (0, 1)
    )
    for role in ("agent", "guard"):
        authenticate(tokenizers / f"{role}_tokenizer_config.json", role)
    log = json.loads((raw / "react-vn-clause-dev32-v1.log").read_text())
    transcript = "".join(row["data"] for row in log)
    if not all(
        fragment in transcript
        for fragment in (
            "TypeError: react_agent.security_v1.constrained_runtime_v1._run() " + ERROR,
            "clause_dev_dispatch_v1.py",
            "in native_runtime",
            "constrained_runtime_v1.py",
            "TOKENIZER_METADATA_COLLECTED roles=2 native_tokenizer_executed=False",
        )
    ):
        raise ValueError("known pre-start traceback required")
    equal(inventory(raw), before, "failure audit read-only")
    return dict(
        protocol="clause_dev32_prestart_failure_v1",
        failure_class="infrastructure_wiring",
        error_class="TypeError",
        failed_task=task["key"],
        completed_tasks=0,
        planned_tasks=32,
        inference_result_available=False,
        model_generation_evidence_count=0,
        pre_worker_start_from_source_and_log=True,
        memory_recovered=recovered,
        quality_scored=False,
    )


def failed_equal(actual: Any, expected: Any, label: str) -> None:
    if label == "terminal COMPLETE required":
        equal(actual, "ERROR", "terminal ERROR required for failure-only audit")
    elif label == "native protocol":
        equal(actual, "clause_dev32_prestart_failure_v1", "failure evidence protocol")
    else:
        equal(actual, expected, label)


def audit(*args: Path) -> dict[str, Any]:
    result: dict[str, Any] = bind(release.audit, equal=failed_equal, native_audit=failure_evidence)(
        *args
    )
    return {
        **result,
        "protocol": "clause_dev32_failed_release_audit_v1",
        "native_run_accepted": False,
        "terminal_status": "ERROR",
        "retry_scope": "all32 unexecuted tasks under a corrected new source identity",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "remote", "preflight", "submission", "observation", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    protected = (args.raw, args.remote, args.preflight, args.submission, args.observation)
    for path in (args.output, *protected):
        no_links(path)
    if (
        args.output.exists()
        or not args.output.resolve().is_relative_to(release.ROOT / "results")
        or any(
            args.output.resolve().is_relative_to(p.resolve())
            or p.resolve().is_relative_to(args.output.resolve())
            for p in protected
        )
    ):
        raise ValueError("fresh results destination outside inputs required")
    result = audit(*protected)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("FAILED_RELEASE_AUTHENTICATED; no native quality result")


if __name__ == "__main__":
    main()
