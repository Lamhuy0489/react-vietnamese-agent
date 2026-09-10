"""Bind worker-local progress receipts to the unchanged IPC/lifecycle audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from react_agent.llm.pair_cancellation_v1 import PLAN
from react_agent.llm.worker_progress_v1 import STD_SHA256, VERSION
from react_agent.validation.guard_probe_audit_v2 import read_json, require


def audit_progress(root: Path, tracker: dict[str, Any], commit: str) -> dict[str, Any]:
    """No raw rewrites; report nonzero registrations as a prevention miss."""
    owner_pid = tracker["observations"]["owner.jsonl"]["pid"]
    require(
        read_json(root / "progress_identity.json")
        == {"protocol": "pair_progress_v1", "source_commit": commit, "owner_pid": owner_pid},
        "progress run identity",
    )
    expected = {f"{trial}_{role}.json" for trial in PLAN for role in ("agent", "guard")}
    policies = root / "progress_policy"
    require({p.name for p in policies.iterdir()} == expected, "exact progress policy inventory")
    observed = []
    for name in sorted(expected):
        trace_name = Path(name).stem + ".jsonl"
        trace = tracker["observations"][trace_name]
        value = read_json(policies / name)
        require(
            value
            == {
                "pid": trace["pid"],
                "role": trace["role"],
                "policy": {
                    "protocol": "worker_thread_progress_v1",
                    "tqdm_version": VERSION,
                    "tqdm_std_sha256": STD_SHA256,
                    "lock": "threading.RLock",
                    "scope": "one daemon spawn worker; no descendant processes",
                },
            },
            "worker progress receipt",
        )
        records = [
            json.loads(line) for line in (root / "tracker" / trace_name).read_text().splitlines()
        ]
        ready = next(r for r in records if r["action"] == "FACTORY_READY")
        modules = ready["modules"]
        require(modules.get("tqdm", {}).get("version") == VERSION, "loaded tqdm version")
        require(
            modules.get("tqdm.std", {}).get("source_sha256") == STD_SHA256,
            "loaded tqdm implementation",
        )
        observed.append(trace["register_calls"])
    for trial in PLAN:
        ready_pair = read_json(root / "pair_cancellation" / trial / "ready.json")["pair"]
        require(ready_pair["owner_pid"] == owner_pid, "trace/lifecycle owner PID binding")
    owner = tracker["observations"]["owner.jsonl"]
    return {
        "protocol": "pair_progress_prevention_audit_v1",
        "worker_register_calls": observed,
        "prevention_observed": all(n == 0 for n in observed),
        "owner_balanced": owner["register_calls"] == owner["unregister_calls"] == 90,
        "policy_receipts_verified": len(expected),
        "ipc_cleanup_verified": False,
        "scope": "Observed creation-path prevention, not exhaustive IPC or graceful exit proof",
    }
