"""Identify bounded worker error envelopes from immutable local response hashes.

No API calls, model inference, raw-response recovery, journal mutation or retry.
An unmatched hash stays unknown. This does not diagnose why generation failed.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_phase5_acceptance_v2 import digest, read, verify

from react_agent.llm.request_reconciliation_v3 import IDENTITY
from react_agent.serving.structured_api_v1 import canonical, sha

ROOT = Path(__file__).resolve().parents[1]
WORKER = "21f66f981e6d9f075b07bc306b0ef802f09b221c5ae4539b06a26f5cf5e521c6"
CODES = ("OUTPUT_LIMIT", "OUTPUT_SCHEMA_FAILED")


def classify(started: dict[str, Any], finished: dict[str, Any]) -> str | None:
    """Match the exact v3 envelope; a HTTP status alone never implies a code."""
    if (started.get("state") != "started"
            or finished.get("state") != "response_received"
            or finished.get("http_status") != 422
            or set(started.get("identity", {})) != IDENTITY
            or any(started.get(k) != finished.get(k) for k in (
                "identity", "protocol", "request_id", "request_sha256", "task_id"))):
        raise ValueError("inconsistent request identity or nonterminal error record")
    matches = []
    for code in CODES:
        result = {"error": {"code": code}}
        status = {
            "instance_id": finished["identity"]["instance_id"],
            "request_id": finished["request_id"],
            "request_sha256": finished["request_sha256"],
            "state": "FAILED", "cancel_requested": False,
            "engine_returned": True, "engine_active": False,
            "gpu_quiescence_attested": True, "quiescence_basis": "device_synchronize",
            "durable": True, "instance_retired": False, "http_status": 422,
            "response_sha256": sha(canonical(result).encode()),
        }
        envelope = {"identity": finished["identity"], "result": result, "request": status}
        if sha(canonical(envelope).encode()) == finished.get("response_sha256"):
            matches.append(code)
    return matches[0] if len(matches) == 1 else None


def evaluate(run: Path, journal: Path) -> dict[str, Any]:
    manifest = read(run / "manifest.json")
    verify(ROOT, manifest["source_sha256"])
    verify(run / "source_snapshot", manifest["source_sha256"])
    identity = manifest["identities"]["agent"]
    if identity.get("worker_sha256") != WORKER:
        raise ValueError("unreviewed worker implementation")
    hashes = {str((run / "manifest.json").relative_to(ROOT)): digest(run / "manifest.json")}
    rows = []
    for path in sorted(journal.rglob("*.finished.json")):
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError("symlinked journal")
        finished = read(path)
        if finished.get("identity") != identity or finished.get("http_status") != 422:
            continue
        start = path.with_name(path.name.replace(".finished.", ".started."))
        if start.is_symlink():
            raise ValueError("symlinked journal")
        started = read(start)
        if path.name != finished["request_id"] + ".finished.json":
            raise ValueError("request filename mismatch")
        code = classify(started, finished)
        rows.append({"request_id": finished["request_id"], "task_id": finished["task_id"],
                     "request_sha256": finished["request_sha256"], "http_status": 422,
                     "response_sha256": finished["response_sha256"],
                     "worker_error_code": code, "known": code is not None})
        for p in (start, path):
            hashes[str(p.relative_to(ROOT))] = digest(p)
    ids = [row["request_id"] for row in rows]
    if not rows or len(set(ids)) != len(ids):
        raise ValueError("missing or duplicate failure evidence")
    for name in ("src/react_agent/serving/structured_api_v1.py",
                 "src/react_agent/serving/request_http_v3.py",
                 "src/react_agent/serving/request_lifecycle_v3.py",
                 "src/react_agent/llm/request_worker_journal_v1.py",
                 "scripts/audit_phase5_failure_codes_v1.py"):
        hashes[name] = digest(ROOT / name)
    return {"schema": "phase5_failure_code_audit_v1", "worker_identity": identity,
            "method": "exact SHA256 match of source-defined terminal error envelope",
            "rows": rows, "counts": dict(Counter(r["worker_error_code"] or "UNKNOWN"
                                                    for r in rows)),
            "input_sha256": hashes, "inference_requests": 0, "journal_mutations": 0,
            "semantic_retry_authorized": False,
            "limitation": "Error code identified; generated text and deeper cause unavailable"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.run.resolve(), args.journal.resolve())
    with args.output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(result["counts"]))


if __name__ == "__main__":
    main()
