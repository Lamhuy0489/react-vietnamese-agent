"""Read-only native sidecar join for the seven-level technical runtime probe."""

import json
from pathlib import Path
from typing import Any, cast

from react_agent.llm.document_runtime_probe_v1 import (
    LEVELS,
    checkpoint,
    inventory,
    validate_identity,
)
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v1 import Role
from react_agent.validation.context_policy_audit_v1 import publisher_policy
from react_agent.validation.context_stress_audit_v1 import audit_memory, equal
from react_agent.validation.efficient_requests_audit_v1 import _record
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.ordinary_native_audit_v1 import load, memory
from react_agent.validation.request_policy_audit_v1 import audit as audit_policy
from react_agent.validation.tokenizer_metadata_v1 import authenticate


def path_coverage(root: Path) -> dict[str, Any]:
    """Describe authenticated runtime traces; zero coverage remains a valid result.

    Callers must authenticate the checkpoint first. This is not an oracle score.
    """
    runtime = root / "execution/runtime"
    metadata = json.loads((runtime / "run_metadata.json").read_text())
    legacy = [
        json.loads(line) for line in (runtime / "trace_legacy.jsonl").read_text().splitlines()
    ]
    proposed = {r["call_id"]: r["data"] for r in legacy if r["event"] == "tool_call_proposed"}
    executed = {r["call_id"] for r in legacy if r["event"] == "tool_call_executed"}
    reads = [
        r
        for r in legacy
        if r["event"] == "tool_result"
        and r["call_id"] in executed
        and proposed[r["call_id"]]["name"] == "doc_read"
        and proposed[r["call_id"]]["arguments"] == {"doc_id": "CDOC_034"}
        and r["data"]["ok"] is True
        and r["data"]["content"].get("doc_id") == "CDOC_034"
    ]
    guard_path = runtime / "trace_guard.jsonl"
    guard = (
        [json.loads(line) for line in guard_path.read_text().splitlines()]
        if guard_path.exists()
        else []
    )
    stages = {
        stage: sum(
            1
            for r in guard
            if r["stage"] == stage
            and r["outcome"]["status"] == "OK"
            and not r["outcome"]["cache_hit"]
            and any(a["status"] == "OK" for a in r["execution_attempts"])
        )
        for stage in ("PRE", "POST", "FINAL")
    }
    return dict(
        successful_document_reads=len(reads),
        executed_tool_calls=len(executed),
        guard_successful_uncached_stages=stages,
        guard_execution_attempts=metadata.get("guard_execution_attempt_count", 0),
        path_covered=bool(reads)
        and (root.name in {"A0", "A1"} or bool(stages["PRE"] and stages["POST"])),
        final_answer=metadata["result"]["final_answer"],
        semantic_quality_scored=False,
    )


def audit(
    probe: Path, tokenizers: Path, publishers: Path, pin: GuardSnapshot, commit: str
) -> dict[str, Any]:
    roots = {"probe": probe, "tokenizers": tokenizers, "publishers": publishers}
    before = {name: inventory(root) for name, root in roots.items()}
    identity = _record((probe / "identity.json").read_text())
    validate_identity(identity)
    require(
        identity["backend"] == "hf" and identity["source_commit"] == commit,
        "native source identity",
    )
    equal(identity["snapshot_sha256"], pin.sha256, "native snapshot identity")
    equal(sorted(p.name for p in (probe / "tasks").iterdir()), list(LEVELS), "seven levels")
    results = []
    for level in LEVELS:
        root = probe / "tasks" / level
        saved = checkpoint(root)
        receipt = _record((root / "execution/pair_runtime.json").read_text())
        expected_roles = ["agent"] if level in {"A0", "A1"} else ["agent", "guard"]
        equal(sorted(receipt["snapshot"]["workers"]), expected_roles, "worker roles")
        equal(
            sorted(p.name for p in (root / "native").iterdir()),
            [f"{role}_hf_metrics.jsonl" for role in expected_roles],
            "native role files",
        )
        equal(receipt["security"], identity["security"][level], "level security identity")
        equal(receipt["task_sha256"], identity["task_sha256"], "probe task identity")
        equal(receipt["generation"], identity["generation"], "probe decoding identity")
        totals = [r["total_bytes"] for r in _record((root / "baseline.json").read_text())["memory"]]
        roles = {}
        for name, worker in receipt["snapshot"]["workers"].items():
            role = cast(Role, name)
            tokenizer = authenticate(tokenizers / f"{role}_tokenizer_config.json", role)
            publisher = publisher_policy(publishers / f"{role}_generation_config.json", role)
            metrics = root / "native" / f"{role}_hf_metrics.jsonl"
            rows = [_record(line) for line in metrics.read_text().splitlines()]
            load(rows[0], role, pin, totals)
            attempts = worker["attempts"]
            require(
                rows[0]["load_seconds_including_hashes"] <= attempts[0]["load_seconds"],
                "startup contains native load",
            )
            expected_model = identity["pair_config"][role]
            equal(rows[0]["model_id"], expected_model["model_id"], "loaded model")
            equal(rows[0]["model_revision"], expected_model["model_revision"], "loaded revision")
            files = (
                rows[0]["runtime_admission"]["files"]
                if role == "agent"
                else [f.model_dump() for f in pin.files]
            )
            for filename, evidence in (
                ("tokenizer_config.json", tokenizer),
                ("generation_config.json", publisher),
            ):
                entries = [f for f in files if f["name"] == filename]
                require(len(entries) == 1, "one admitted metadata file")
                for key in ("size", "sha256"):
                    equal(entries[0][key], evidence["identity"][key], "metadata admission")
            require(
                tokenizer["eos_token_id"] in publisher["publisher_json"]["eos_token_id"],
                "tokenizer EOS in publisher",
            )
            requests = attempts[1:]
            successful = bool(requests) and all(r["status"] == "OK" for r in requests)
            calls = []
            if successful:
                joined = audit_policy(
                    root / "policy" / role,
                    root / "attention" / role,
                    metrics,
                    role=role,
                    worker_pid=attempts[0]["pid"],
                    expected_requests=len(requests),
                    publisher=publisher["observed_publisher_expected"],
                    pad_token_id=tokenizer["pad_token_id"],
                )
                for index, (row, attempt) in enumerate(zip(rows[1:], requests, strict=True), 1):
                    require(
                        row["call_seconds"] <= attempt["generation_seconds"],
                        "native within worker call",
                    )
                    if role == "guard":
                        memory(row, role, totals)
                    else:
                        audit_memory(row["memory_before"], role, totals)
                        audit_memory(row["memory_after"], role, totals)
                    calls.append(
                        dict(
                            index=index,
                            input_tokens=row["input_tokens"],
                            output_tokens=row["output_tokens"],
                            generate_seconds=row["generate_seconds"],
                            call_seconds=row["call_seconds"],
                            tokens_per_generate_second=row["output_tokens"]
                            / row["generate_seconds"],
                        )
                    )
                policy_verified = joined["valid"]
            elif not requests:
                require(len(rows) == 1, "no hidden native generation")
                require(
                    not (root / "policy" / role).exists()
                    and not (root / "attention" / role).exists(),
                    "no hidden request sidecars",
                )
                policy_verified = False
            else:
                # Preserve partial native evidence; never represent it as a fully joined success.
                policy_verified = False
            roles[role] = dict(
                worker_attempts=len(requests),
                policy_attention_verified=policy_verified,
                load_verified=True,
                calls=calls,
                failed_or_partial=bool(requests) and not successful,
            )
        results.append(
            dict(
                level=level,
                path_coverage=path_coverage(root),
                terminal=saved["terminal"],
                recovered=saved["recovered"],
                observed_graceful=all(
                    w["lifecycle"] and all(e["method"] == "GRACEFUL" for e in w["lifecycle"])
                    for w in receipt["snapshot"]["workers"].values()
                ),
                roles=roles,
                cleanup_methods=[
                    e["method"]
                    for w in receipt["snapshot"]["workers"].values()
                    for e in w["lifecycle"]
                ],
            )
        )
    equal({name: inventory(root) for name, root in roots.items()}, before, "audit inputs unchanged")
    return dict(
        protocol="document_runtime_native_join_v1",
        artifact_integrity_valid=True,
        source_authenticated=False,
        phase5_accepted=False,
        guard_quality_validated=False,
        levels=results,
        raw_sha256=before,
        scope="Technical artifact join, not remote execution authentication or benchmark quality. "
        "Failed roles retain partial evidence.",
    )
