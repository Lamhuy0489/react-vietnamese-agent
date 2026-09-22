"""Derive exit-boundary metrics after authenticating immutable native outputs."""

from __future__ import annotations

import copy
from collections import Counter
from pathlib import Path
from typing import Any

from audit_phase5_exit_gpu_v1 import audit
from report_phase5_constrained_gpu_v1 import main as original_main
from report_phase5_constrained_gpu_v1 import summarize as constrained_summary

from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.guard_probe_audit_v2 import require


def summarize(verified: dict[str, Any], raw: Path) -> dict[str, Any]:
    equal(verified["protocol"], "exit_pair_gpu_release_audit_v1", "release protocol")
    equal(verified["native"]["protocol"], "exit_constrained_native_audit_v1", "native protocol")
    adapted = copy.deepcopy(verified)
    adapted["protocol"] = "constrained_gpu_release_audit_v1"
    adapted["native"]["protocol"] = "constrained_native_audit_v1"
    result = constrained_summary(adapted, raw)
    rows = []
    workers = {(w["task"], w["role"]): w for w in result["workers"]}
    require(len(workers) == len(result["workers"]), "unique task-role lifecycle")
    for task in verified["native"]["tasks"]:
        joined = task["exit_milestones"]
        equal(joined["protocol"], "exit_pair_join_v1", "exit join protocol")
        equal(joined["valid"], True, "exit join accepted")
        equal(sorted(joined["roles"]), ["agent", "guard"], "exit role coverage")
        for role, observed in joined["roles"].items():
            lifecycle = workers.pop((task["key"], role))
            for key in ("pid", "method"):
                equal(observed[key], lifecycle[key], "exit/lifecycle " + key)
            rows.append(dict(task=task["key"], role=role, **observed))
    require(not workers, "all lifecycles have exit evidence")
    equal(inventory(raw), verified["raw_sha256"], "raw unchanged after summary")
    result.update(
        protocol="exit_pair_native_descriptive_report_v1",
        exit_workers=rows,
        exit_boundary_counts=dict(Counter(row["boundary"] for row in rows)),
        forced_exit_boundary_counts=dict(
            Counter(row["boundary"] for row in rows if row["method"] in {"TERMINATE", "KILL"})
        ),
        native_cause_identified=False,
        phase5_accepted=False,
    )
    result["limitations"].append(
        "Observed Python exit boundaries localize the symptom, not a native destructor or fix. "
        "All observed stages returned does not imply graceful process exit."
    )
    return result


def main() -> None:
    bind(original_main, audit=audit, summarize=summarize)()


if __name__ == "__main__":
    main()
