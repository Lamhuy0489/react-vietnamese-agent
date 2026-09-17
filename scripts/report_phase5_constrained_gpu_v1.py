"""Derive constrained descriptive metrics only after a fresh, read-only release audit."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from audit_phase5_constrained_gpu_v1 import ROOT, audit
from report_phase5_observer_gpu_v2 import summarize as observer_summary

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.validation.context_stress_audit_v1 import equal


def summarize(verified: dict[str, Any], raw: Path) -> dict[str, Any]:
    equal(verified["protocol"], "constrained_gpu_release_audit_v1", "release protocol")
    equal(verified["native"]["protocol"], "constrained_native_audit_v1", "native protocol")
    # Adapt only the diagnostic nesting for the frozen descriptive summarizer.
    # The original authenticated receipt is never modified or saved as observer evidence.
    adapted = copy.deepcopy(verified)
    completed, incomplete = 0, 0
    for task in adapted["native"]["tasks"]:
        joined = task["guard_diagnostics"]
        equal(joined["protocol"], "constrained_runtime_join_v1", "constraint join protocol")
        completed += len(joined["completed"])
        incomplete += len(joined["incomplete"])
        task["guard_diagnostics"] = joined["observer"]
    result = observer_summary(adapted, raw)
    result["protocol"] = "constrained_native_descriptive_report_v1"
    result["constraint_completed_requests"] = completed
    result["constraint_incomplete_requests"] = incomplete
    result["limitations"].append(
        "Constrained syntax completion is not correctness of the guard classification."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "remote", "preflight", "submission", "observation", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    output = args.output.resolve()
    inputs = (args.raw, args.remote, args.preflight, args.submission, args.observation)
    if (
        output.exists()
        or output == ROOT / "results"
        or not output.is_relative_to(ROOT / "results")
        or any(
            output.is_relative_to(p.resolve()) or p.resolve().is_relative_to(output) for p in inputs
        )
    ):
        raise ValueError("fresh report output under results and outside inputs required")
    verified = audit(*inputs)
    summary = summarize(verified, args.raw)
    output.mkdir(parents=True)
    write_receipt(output / "release_audit.json", verified)
    write_receipt(output / "summary.json", summary)
    print("CONSTRAINED_NATIVE_REPORT_COMPLETE")


if __name__ == "__main__":
    main()
