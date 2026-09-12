"""Join ordinary supervisor, publisher, policy, attention and native allocator records."""

from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.agent_runtime_input_v1 import INVENTORY_SHA256
from react_agent.llm.coexistence_placement_v1 import PlacementPlan
from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AGENT_CONTENT
from react_agent.llm.model_pair_v1 import Role
from react_agent.llm.ordinary_pair_probe_v1 import native_config
from react_agent.validation.context_policy_audit_v1 import publisher_policy
from react_agent.validation.context_stress_audit_v1 import audit_memory, equal, inventory
from react_agent.validation.efficient_requests_audit_v1 import _record, _seconds
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.ordinary_pair_audit_v1 import ROLES, hashed, read
from react_agent.validation.ordinary_pair_audit_v1 import audit as audit_supervisor
from react_agent.validation.request_policy_audit_v1 import audit as audit_policy


def memory(row: dict[str, Any], role: Role, totals: list[int]) -> None:
    if role == "agent":
        audit_memory(row["memory"], role, totals)
    else:
        audit_memory(
            [
                dict(
                    device=1,
                    global_free_bytes=row["global_free_bytes"],
                    global_total_bytes=row["global_total_bytes"],
                    **{
                        key: row["process_" + key]
                        for key in (
                            "allocated_bytes",
                            "reserved_bytes",
                            "peak_allocated_bytes",
                            "peak_reserved_bytes",
                        )
                    },
                )
            ],
            role,
            totals,
        )


def load(row: dict[str, Any], role: Role, pin: GuardSnapshot, totals: list[int]) -> None:
    """Add placement/content/budgets to inner native-metric identity/version checks."""
    value: Any
    if role == "agent":
        plan = PlacementPlan()
        for key, value in dict(
            placement_sha256=plan.sha256,
            device_map=plan.device_map(),
            agent_caps=list(plan.agent_caps),
        ).items():
            equal(row[key], value, "agent placement " + key)
        admission = row["runtime_admission"]
        for key, value in dict(
            content_sha256=AGENT_CONTENT,
            inventory_sha256=INVENTORY_SHA256,
            full_inventory_match=False,
            documentation_mismatches=["README.md"],
            runtime_files_match=True,
            runtime_files=11,
            parameter_tensors=339,
            serialized_parameter_bytes=15231233024,
        ).items():
            equal(admission[key], value, "agent runtime admission " + key)
        equal(
            hashed(
                dict(
                    protocol="agent_runtime_input_v1",
                    inventory=INVENTORY_SHA256,
                    files=admission["files"],
                )
            ),
            AGENT_CONTENT,
            "agent admitted file bytes",
        )
    else:
        config = GuardHFConfig()
        for key, value in dict(
            snapshot_sha256=pin.sha256,
            adapter_config_sha256=config.sha256,
            device=1,
            device_map={"": 1},
            allocator_limit_bytes=config.allocator_limit_bytes,
            free_headroom_bytes=config.free_headroom_bytes,
            max_input_tokens=config.max_input_tokens,
        ).items():
            equal(row[key], value, "guard placement " + key)
        require(row["device_name"] in ("T4", "Tesla T4", "NVIDIA T4"), "guard T4")
    memory(row, role, totals)


def audit(
    probe: Path,
    policy: Path,
    attention: Path,
    publishers: Path,
    *,
    pin: GuardSnapshot,
    commit: str,
    pad_token_ids: dict[str, int],
) -> dict[str, Any]:
    """Pad IDs remain caller expectations until tokenizer metadata is independently checked."""
    roots = dict(probe=probe, policy=policy, attention=attention, publishers=publishers)
    for name, root in roots.items():
        no_links(root)
        require(
            all(
                not root.resolve().is_relative_to(other.resolve())
                and not other.resolve().is_relative_to(root.resolve())
                for key, other in roots.items()
                if key != name
            ),
            "disjoint audit inputs",
        )
    before = {name: inventory(root) for name, root in roots.items()}
    trees = {
        name: sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
        for name, root in roots.items()
    }
    config = native_config()
    equal(pin.model_id, config.guard.model_id, "guard snapshot model")
    equal(pin.model_revision, config.guard.model_revision, "content-bound guard snapshot")
    equal(sorted(pad_token_ids), sorted(ROLES), "both expected pad IDs")
    equal(
        sorted(before["publishers"]),
        ["agent_generation_config.json", "guard_generation_config.json"],
        "publisher files",
    )
    for root in (policy, attention):
        equal(sorted(p.name for p in root.iterdir()), sorted(ROLES), "sidecar role roots")
    supervisor = audit_supervisor(probe, commit=commit, backend="hf")
    totals = [row["total_bytes"] for row in read(probe / "baseline.json")["memory"]]
    joined, metadata, timings = {}, {}, []
    for role in ROLES:
        evidence = publisher_policy(publishers / f"{role}_generation_config.json", role)
        metrics_path = probe / f"{role}_hf_metrics.jsonl"
        rows = [_record(line) for line in metrics_path.read_text().splitlines()]
        joined[role] = audit_policy(
            policy / role,
            attention / role,
            metrics_path,
            role=role,
            worker_pid=supervisor["worker_pids"][role],
            expected_requests=3,
            publisher=evidence["observed_publisher_expected"],
            pad_token_id=pad_token_ids[role],
        )
        load(rows[0], role, pin, totals)
        entries = (
            rows[0]["runtime_admission"]["files"]
            if role == "agent"
            else [entry.model_dump() for entry in pin.files]
        )
        entries = [entry for entry in entries if entry["name"] == "generation_config.json"]
        require(len(entries) == 1, "admitted publisher metadata")
        for key in ("size", "sha256"):
            equal(entries[0][key], evidence["identity"][key], "admitted publisher " + key)
        attempts = supervisor["workers"][role]["attempts"]
        require(
            rows[0]["load_seconds_including_hashes"] <= attempts[0]["load_seconds"],
            "native load within worker startup",
        )
        metadata[role] = evidence
        for index, row in enumerate(rows[1:], 1):
            if role == "agent":
                audit_memory(row["memory_before"], role, totals)
                audit_memory(row["memory_after"], role, totals)
            else:
                memory(row, role, totals)
            require(
                row["call_seconds"] <= attempts[index]["generation_seconds"],
                "native call within worker timing",
            )
            host = next(
                call
                for call in supervisor["calls"]
                if call["role"] == role and call["request_index"] == index
            )
            timings.append(
                dict(
                    **host,
                    input_tokens=row["input_tokens"],
                    output_tokens=row["output_tokens"],
                    native_generate_seconds=row["generate_seconds"],
                    native_call_seconds=row["call_seconds"],
                    tokens_per_generate_second=_seconds(
                        row["output_tokens"] / row["generate_seconds"], "finite token throughput"
                    ),
                )
            )
    equal(
        {name: inventory(root) for name, root in roots.items()},
        before,
        "inputs changed during joined audit",
    )
    equal(
        {
            name: sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
            for name, root in roots.items()
        },
        trees,
        "input trees changed",
    )
    return dict(
        protocol="ordinary_native_joined_audit_v1",
        valid=True,
        phase5_accepted=False,
        native_validated=False,
        source_authenticated=False,
        tokenizer_metadata_authenticated=False,
        publisher_metadata_authenticated=True,
        supervisor_records_consistent=True,
        native_policy_attention_metrics_consistent=True,
        allocator_records_within_caps=True,
        source_commit=commit,
        supervisor=supervisor,
        policies=joined,
        publishers=metadata,
        calls=sorted(timings, key=lambda row: row["index"]),
        input_sha256=before,
        scope="Joined six-call artifact evidence. Native execution/source/package and tokenizer "
        "authentication remain release gates. Timings include instrumentation; no quality, "
        "speedup, full KV, IPC leak-free or A0-A6 adoption claim.",
    )
