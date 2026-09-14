"""Per-variant native evidence joins; no model loading and no quality scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v1 import Role
from react_agent.validation.context_policy_audit_v1 import publisher_policy
from react_agent.validation.context_stress_audit_v1 import audit_memory, equal
from react_agent.validation.efficient_requests_audit_v1 import _record
from react_agent.validation.grouped_dev_checkpoint_v2 import audit_checkpoint, audit_prefix
from react_agent.validation.guard_diagnostic_audit_v1 import audit as audit_guard
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.ordinary_native_audit_v1 import load, memory
from react_agent.validation.request_policy_audit_v1 import audit as audit_policy
from react_agent.validation.tokenizer_metadata_v1 import authenticate


def audit_native_task(
    root: Path,
    identity: dict[str, Any],
    task: dict[str, Any],
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
) -> dict[str, Any]:
    before = {
        name: inventory(path)
        for name, path in (("task", root), ("tokenizers", tokenizers), ("publishers", publishers))
    }
    require(identity["backend"] == "hf", "native backend required")
    equal(identity["native_pins"]["guard_snapshot_sha256"], pin.sha256, "snapshot identity")
    saved = audit_checkpoint(root, identity, task)
    receipt = _record((root / "execution/pair_runtime.json").read_text())
    level = task["level"]
    expected_roles = ["agent"] if level in {"A0", "A1"} else ["agent", "guard"]
    equal(sorted(receipt["snapshot"]["workers"]), expected_roles, "worker roles")
    names = {f"{role}_hf_metrics.jsonl" for role in expected_roles}
    sidecar = root / "native/guard_response_diagnostics.jsonl"
    if sidecar.exists() and "guard" in expected_roles:
        names.add(sidecar.name)
    equal(
        sorted(p.name for p in (root / "native").iterdir()),
        sorted(names),
        "exact native evidence files",
    )
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
                        tokens_per_generate_second=row["output_tokens"] / row["generate_seconds"],
                    )
                )
            policy_verified = joined["valid"]
        elif not requests:
            require(len(rows) == 1, "no hidden native generation")
            require(
                not (root / "policy" / role).exists() and not (root / "attention" / role).exists(),
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

    diagnostics = audit_guard(root / "execution", sidecar) if "guard" in expected_roles else None
    equal(
        {
            name: inventory(path)
            for name, path in (
                ("task", root),
                ("tokenizers", tokenizers),
                ("publishers", publishers),
            )
        },
        before,
        "native audit inputs unchanged",
    )
    return dict(
        key=task["key"],
        level=level,
        terminal=saved["terminal"],
        recovered=saved["recovered"],
        roles=roles,
        guard_diagnostics=diagnostics,
        startup_seconds=receipt["startup_seconds"],
        runtime_seconds_including_inner_cleanup=receipt["runtime_seconds_including_inner_cleanup"],
        outer_cleanup_seconds=receipt["outer_cleanup_seconds"],
        runtime_total_seconds=receipt["total_seconds"],
        task_timing=json.loads((root / "task_timing.json").read_text()),
        observed_graceful=all(
            w["lifecycle"] and all(e["method"] == "GRACEFUL" for e in w["lifecycle"])
            for w in receipt["snapshot"]["workers"].values()
        ),
        quality_scoring=False,
    )


def audit(
    output: Path,
    identity: dict[str, Any],
    shard: int,
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
) -> dict[str, Any]:
    before = inventory(output)
    checks = audit_prefix(output, identity, shard)
    tasks = [t for t in identity["tasks"] if t["shard"] == shard][: len(checks)]
    joined = [
        audit_native_task(
            output / "tasks" / task["key"], identity, task, tokenizers, publishers, pin
        )
        for task in tasks
    ]
    equal(inventory(output), before, "shard audit changed output")
    return dict(
        protocol="grouped_dev_native_audit_v2",
        artifact_integrity_valid=True,
        complete=len(checks) == 14,
        completed=len(checks),
        expected=14,
        shard=shard,
        tasks=joined,
        raw_sha256=before,
        source_authenticated=False,
        guard_quality_validated=False,
        phase5_accepted=False,
    )
