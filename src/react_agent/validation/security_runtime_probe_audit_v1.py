"""Read-only native sidecar join for the seven-level technical runtime probe."""

from pathlib import Path
from typing import Any, cast

from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v1 import Role
from react_agent.llm.security_runtime_probe_v1 import LEVELS, checkpoint, inventory
from react_agent.validation.context_policy_audit_v1 import publisher_policy
from react_agent.validation.context_stress_audit_v1 import audit_memory, equal
from react_agent.validation.efficient_requests_audit_v1 import _record
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.ordinary_native_audit_v1 import load, memory
from react_agent.validation.request_policy_audit_v1 import audit as audit_policy
from react_agent.validation.tokenizer_metadata_v1 import authenticate


def audit(
    probe: Path, tokenizers: Path, publishers: Path, pin: GuardSnapshot, commit: str
) -> dict[str, Any]:
    roots = {"probe": probe, "tokenizers": tokenizers, "publishers": publishers}
    before = {name: inventory(root) for name, root in roots.items()}
    identity = _record((probe / "identity.json").read_text())
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
                terminal=saved["terminal"],
                recovered=saved["recovered"],
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
        protocol="security_runtime_native_join_v1",
        artifact_integrity_valid=True,
        source_authenticated=False,
        phase5_accepted=False,
        guard_quality_validated=False,
        levels=results,
        raw_sha256=before,
        scope="Technical artifact join, not remote execution authentication or benchmark quality. "
        "Failed roles retain partial evidence.",
    )
