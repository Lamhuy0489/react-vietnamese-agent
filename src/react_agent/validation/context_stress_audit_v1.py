"""Read-only context-stress receipt audit; never imports torch or launches workers.

An internally consistent receipt is not independent proof of native execution.
The GPU release wrapper must additionally authenticate source, packaging and raw
hashes. Token hashes cannot reconstruct the tokenizer or certify semantic quality.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import MODEL, no_links
from react_agent.llm.base import GenerationConfig
from react_agent.llm.coexistence_placement_v1 import PlacementPlan
from react_agent.llm.context_geometry_v1 import SEED_TEXT
from react_agent.llm.context_stress_v1 import ACK, REQUEST
from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.llm.model_pair_probe_v1 import MIN_RESIDENT, TOLERANCE, validate_memory
from react_agent.llm.model_pair_v1 import READY_COMMAND, ModelIdentity, PairConfig, Role
from react_agent.validation.guard_probe_audit_v2 import digest, positive, require
from react_agent.validation.pair_cancellation_audit_v1 import audit_load

STAGES = ("entered", "prepared", "generated", "completed")
ROLES: tuple[Role, Role] = ("agent", "guard")
# Fresh Transformers 5.5.0 GenerationConfig.to_dict(), before generate() merges
# runtime defaults. Verified against the pinned wheel by the compatibility CLI.
NATIVE_NONE_FIELDS = frozenset(
    "max_length min_length early_stopping max_time stop_strings cache_config "
    "temperature top_k top_p min_p top_h typical_p epsilon_cutoff eta_cutoff "
    "repetition_penalty encoder_repetition_penalty length_penalty no_repeat_ngram_size "
    "bad_words_ids renormalize_logits forced_bos_token_id forced_eos_token_id "
    "remove_invalid_values exponential_decay_length_penalty suppress_tokens "
    "begin_suppress_tokens sequence_bias token_healing guidance_scale watermarking_config "
    "num_return_sequences bos_token_id encoder_no_repeat_ngram_size decoder_start_token_id "
    "is_assistant num_assistant_tokens num_assistant_tokens_schedule "
    "assistant_confidence_threshold "
    "prompt_lookup_num_tokens max_matching_ngram_size assistant_early_exit assistant_lookbehind "
    "target_lookbehind compile_config disable_compile continuous_batching_config low_memory "
    "penalty_alpha dola_layers diversity_penalty num_beam_groups constraints force_words_ids "
    "prefill_chunk_size _from_model_config".split()
)


def equal(actual: Any, expected: Any, label: str) -> None:
    """JSON equality without Python's True==1 or 1.0==1 coercion."""
    require(canonical_json(actual) == canonical_json(expected), label)


def read_record(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def invalid(value: str) -> Any:
        raise ValueError("nonfinite JSON number")

    result = json.loads(path.read_text(), object_pairs_hook=pairs, parse_constant=invalid)
    require(type(result) is dict, "JSON object required")
    return dict(result)


def inventory(root: Path) -> dict[str, str]:
    no_links(root)
    require(root.is_dir(), "artifact directory required")
    paths = sorted(root.rglob("*"))
    require(
        all(not p.is_symlink() and (p.is_dir() or p.is_file()) for p in paths), "linked artifact"
    )
    return {p.relative_to(root).as_posix(): digest(p) for p in paths if p.is_file()}


def fields(record: dict[str, Any], keys: set[str], label: str) -> None:
    require(set(record) == keys, label + " fields")


def sha(value: Any) -> None:
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "SHA256")


def audit_cache(value: dict[str, Any], role: Role, length: int) -> dict[str, int]:
    """Recompute all 28 layer shapes and FP16 K+V bytes, not just the sum."""
    heads = 4 if role == "agent" else 2
    by_device: dict[str, int] = {}
    layers = []
    for index in range(28):
        device = int(index >= 20) if role == "agent" else 1
        size = 2 * heads * length * 128 * 2
        layers.append(
            {"layer": index, "device": device, "shape": [1, heads, length, 128], "bytes": size}
        )
        key = str(device)
        by_device[key] = by_device.get(key, 0) + size
    equal(
        value,
        {"sequence_length": length, "layers": layers, "tensor_bytes_by_device": by_device},
        "KV geometry/bytes",
    )
    return by_device


def audit_memory(rows: Any, role: Role, totals: list[int]) -> None:
    devices = [0, 1] if role == "agent" else [1]
    require(type(rows) is list and len(rows) == len(devices), "allocator device coverage")
    for row, device in zip(rows, devices, strict=True):
        fields(
            row,
            {
                "device",
                "global_free_bytes",
                "global_total_bytes",
                "allocated_bytes",
                "reserved_bytes",
                "peak_allocated_bytes",
                "peak_reserved_bytes",
            },
            "allocator",
        )
        require(all(type(v) is int for v in row.values()), "integer byte observations")
        cap = (
            PlacementPlan().agent_caps[device]
            if role == "agent"
            else GuardHFConfig().allocator_limit_bytes
        )
        require(
            row["device"] == device
            and row["global_total_bytes"] == totals[device]
            and 0 <= row["global_free_bytes"] <= totals[device],
            "global allocator endpoint",
        )
        allocated, reserved = row["allocated_bytes"], row["reserved_bytes"]
        peak, peak_reserved = row["peak_allocated_bytes"], row["peak_reserved_bytes"]
        require(
            0 < allocated <= reserved <= peak_reserved <= cap
            and allocated <= peak <= peak_reserved,
            "allocator budget/order",
        )
        require(
            reserved <= totals[device] - row["global_free_bytes"],
            "process reservation exceeds global used",
        )


def audit_stages(
    root: Path, role: Role, identity: ModelIdentity, pid: int, totals: list[int]
) -> dict[str, Any]:
    before = inventory(root)
    equal(sorted(before), sorted(s + ".json" for s in STAGES), "exact stress stage inventory")
    require(type(pid) is int and pid > 0, "worker PID")
    count = 512 if role == "agent" else 128
    records = {s: read_record(root / (s + ".json")) for s in STAGES}
    extra = {
        "entered": set(),
        "prepared": {
            "geometry",
            "generation",
            "tokenize_seconds",
            "memory",
            "seed",
            "input_device",
            "prefill_seconds",
            "timing_scope",
        },
        "generated": {"summary", "cache", "generation_seconds", "memory"},
        "completed": {
            "summary",
            "cache",
            "memory",
            "generation_seconds",
            "final_forward_seconds",
            "total_seconds",
            "model_generation_calls",
            "separate_final_forwards",
            "memory_scope",
        },
    }
    base = {
        "protocol": "context_stress_v1",
        "role": role,
        "pid": pid,
        "model_id": identity.model_id,
        "model_revision": identity.model_revision,
    }
    for stage, row in records.items():
        fields(row, set(base) | {"stage"} | extra[stage], stage)
        equal({k: row[k] for k in base}, base, "stress identity")
        equal(row["stage"], stage, "stage name")
    prepared, generated, completed = (records[s] for s in STAGES[1:])
    geometry = prepared["geometry"]
    fixed = {
        "protocol": "context_geometry_v1",
        "construction": "encode_no_specials_repeat_then_seed_prefix_v1",
        "role": role,
        "tokenizer_identity": identity.model_revision,
        "seed_text_sha256": text_hash(SEED_TEXT),
        "input_tokens": 4096,
        "required_new_tokens": count,
        "scope": "Synthetic token geometry, not natural chat-context utility",
    }
    variable = {
        "vocab_size",
        "seed_token_count",
        "seed_ids_sha256",
        "special_ids_sha256",
        "input_ids_sha256",
    }
    fields(geometry, set(fixed) | variable, "geometry")
    equal({k: geometry[k] for k in fixed}, fixed, "geometry identity")
    require(
        type(geometry["vocab_size"]) is int
        and geometry["vocab_size"] > 151645
        and type(geometry["seed_token_count"]) is int
        and 1 <= geometry["seed_token_count"] <= 4096,
        "tokenizer counts",
    )
    for key in variable - {"vocab_size", "seed_token_count"}:
        sha(geometry[key])
    options = prepared["generation"]
    # Reject overrides even when outside the forced-length critical subset.
    critical = {
        "min_new_tokens": count,
        "max_new_tokens": count,
        "do_sample": False,
        "num_beams": 1,
        "use_cache": True,
        "cache_implementation": "dynamic",
        "return_dict_in_generate": True,
        "output_scores": False,
        "output_logits": False,
        "output_attentions": False,
        "output_hidden_states": False,
        "eos_token_id": [151645, 151643],
        "pad_token_id": 151643,
    }
    equal(
        options,
        {**dict.fromkeys(NATIVE_NONE_FIELDS), **critical, "transformers_version": "5.5.0"},
        "native generation settings",
    )
    for key, expected in {
        "seed": 42,
        "input_device": "cuda:0" if role == "agent" else "cuda:1",
        "prefill_seconds": None,
        "timing_scope": "generation aggregate includes prefill; not separated",
    }.items():
        equal(prepared[key], expected, "prepared " + key)
    for observation in (generated, completed):
        summary = observation["summary"]
        final = observation is completed
        expected_summary = {
            "protocol": "context_generation_geometry_v1",
            "role": role,
            "input_tokens": 4096,
            "new_tokens": count,
            "sequence_tokens": 4096 + count,
            "sequence_ids_sha256": summary["sequence_ids_sha256"],
            "output_ids_sha256": summary["output_ids_sha256"],
            "cache_length_after_generation": 4095 + count,
            "cache_length_after_final_forward": 4096 + count if final else None,
            "full_boundary_cache_observed": final,
            "generated_text_retained": False,
            "scope": "Caller-supplied token/cache observations, not GPU allocation certification",
        }
        equal(summary, expected_summary, "generation summary")
        for key in ("sequence_ids_sha256", "output_ids_sha256"):
            sha(summary[key])
            equal(summary[key], generated["summary"][key], "sequence continuity")
        audit_cache(observation["cache"], role, 4096 + count if final else 4095 + count)
    for row in (prepared, generated, completed):
        audit_memory(row["memory"], role, totals)
    for earlier, later in ((prepared, generated), (generated, completed)):
        for a, b in zip(earlier["memory"], later["memory"], strict=True):
            require(
                all(b[k] >= a[k] for k in ("peak_allocated_bytes", "peak_reserved_bytes")),
                "peak counters decreased",
            )
    for row in (generated, completed):
        for memory in row["memory"]:
            require(
                memory["allocated_bytes"]
                >= row["cache"]["tensor_bytes_by_device"][str(memory["device"])],
                "live KV exceeds allocation",
            )
    duration = completed["generation_seconds"]
    tokenize, forward, total = (
        prepared["tokenize_seconds"],
        completed["final_forward_seconds"],
        completed["total_seconds"],
    )
    require(
        all(positive(v) for v in (duration, tokenize, forward, total)),
        "finite positive stage timings",
    )
    equal(duration, generated["generation_seconds"], "generation timing continuity")
    require(total >= tokenize + duration + forward, "backend timing containment")
    equal(completed["model_generation_calls"], 1, "one native generation")
    equal(completed["separate_final_forwards"], 1, "one final forward")
    equal(
        completed["memory_scope"],
        "process allocator peaks; global endpoints, not global peak",
        "memory scope",
    )
    equal(inventory(root), before, "stress records changed during audit")
    return {
        "pid": pid,
        "input_tokens": 4096,
        "new_tokens": count,
        "full_cache_tokens": 4096 + count,
        "full_kv_bytes_by_device": completed["cache"]["tensor_bytes_by_device"],
        "tokenize_seconds": tokenize,
        "generation_seconds_including_prefill": duration,
        "aggregate_output_tokens_per_second": count / duration,
        "prefill_seconds": None,
        "final_forward_seconds": forward,
        "backend_total_seconds": total,
        "memory": {s: records[s]["memory"] for s in STAGES[1:]},
    }


def audit_worker(worker: dict[str, Any], role: Role, config: PairConfig) -> int:
    fields(worker, {"attempts", "lifecycle", "closed", "handle_pending"}, "worker")
    require(worker["closed"] is True and worker["handle_pending"] is False, "worker not closed")
    attempts, lifecycle = worker["attempts"], worker["lifecycle"]
    require(len(attempts) == 2 and len(lifecycle) == 1, "exact worker attempts/cleanup")
    event = lifecycle[0]
    pid = event["pid"]
    require(type(pid) is int and pid > 0 and positive(event["elapsed_seconds"]), "cleanup PID/time")
    equal(
        {k: event[k] for k in ("sequence", "reaped")}, {"sequence": 1, "reaped": True}, "reap event"
    )
    require(
        (event["method"], event["exitcode"]) in {("GRACEFUL", 0), ("TERMINATE", -15), ("KILL", -9)}
        and type(event["exitcode"]) is int,
        "recognized cleanup method",
    )
    fields(event, {"pid", "sequence", "reaped", "method", "exitcode", "elapsed_seconds"}, "cleanup")
    for i, row in enumerate(attempts):
        cold = i == 0
        execution = config.execution(role, cold=cold)
        generation = GenerationConfig(max_new_tokens=512 if cold or role == "agent" else 128)
        fixed = {
            "pid": pid,
            "sequence": i + 1,
            "cold_start": cold,
            "status": "OK",
            "reaped": False,
            "worker_retained": True,
            "execution_config_sha256": execution.identity,
            "request_sha256": text_hash(
                canonical_json([{"role": "user", "content": READY_COMMAND}] if cold else REQUEST)
            ),
            "generation_sha256": text_hash(canonical_json(generation.model_dump())),
        }
        fields(
            row, set(fixed) | {"elapsed_seconds", "load_seconds", "generation_seconds"}, "attempt"
        )
        equal({k: row[k] for k in fixed}, fixed, "attempt identity")
        elapsed, load, duration = (
            row["elapsed_seconds"],
            row["load_seconds"],
            row["generation_seconds"],
        )
        require(
            positive(elapsed) and positive(duration) and elapsed < execution.timeout_seconds,
            "attempt time/deadline",
        )
        require(
            positive(load)
            if cold
            else type(load) in (int, float) and math.isfinite(load) and load == 0,
            "load once",
        )
        require(elapsed >= load + duration, "attempt timing containment")
    return int(pid)


def audit_probe(root: Path, pin: GuardSnapshot, commit: str) -> dict[str, Any]:
    """Validate only complete evidence; partial/error runs are retained and rejected."""
    before = inventory(root)
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "source commit")
    config = PairConfig(
        ModelIdentity(MODEL, AGENT_REVISION), ModelIdentity(pin.model_id, pin.model_revision)
    )
    expected = {
        "manifest.json",
        "baseline.json",
        "ready.json",
        "agent_call.json",
        "guard_call.json",
        "closed.json",
        "summary.json",
    }
    expected.update(f"recovery_{i}.json" for i in range(6))
    for role in ROLES:
        expected.add(f"{role}_hf_metrics.jsonl")
        expected.update(f"{role}_stress/{s}.json" for s in STAGES)
    equal(sorted(before), sorted(expected), "exact probe inventory")
    equal(
        read_record(root / "manifest.json"),
        {
            "protocol": "context_stress_pair_probe_v1",
            "identity": {
                "backend": "hf",
                "source_commit": commit,
                "snapshot_sha256": pin.sha256,
                "environment": {"torch": "2.10.0+cu128", "cuda": "12.8", "transformers": "5.5.0"},
                "progress_policy": "worker_thread_progress_v1",
            },
            "pair_config_sha256": config.sha256,
            "inputs_sha256": text_hash(canonical_json({"agent": REQUEST, "guard": REQUEST})),
            "generation": {
                "agent": GenerationConfig().model_dump(),
                "guard": GenerationConfig(max_new_tokens=128).model_dump(),
            },
            "order": [
                "baseline",
                "ready_agent_then_guard",
                "agent_call",
                "guard_call",
                "close",
                "recovery",
            ],
            "min_resident_bytes": list(MIN_RESIDENT),
            "recovery_tolerance_bytes": TOLERANCE,
            "sample_interval_seconds": 1.0,
            "recovery_samples": 6,
            "automatic_retry": False,
            "benchmark_tasks": 0,
            "test_payloads_parsed": 0,
        },
        "probe manifest",
    )
    baseline_record = read_record(root / "baseline.json")
    fields(baseline_record, {"memory"}, "baseline")
    baseline = baseline_record["memory"]
    validate_memory(baseline)
    totals = [m["total_bytes"] for m in baseline]
    closed = read_record(root / "closed.json")
    workers = closed["workers"]
    equal(sorted(workers), ["agent", "guard"], "pair worker coverage")
    pids = {role: audit_worker(workers[role], role, config) for role in ROLES}
    owner = closed["owner_pid"]
    require(
        type(owner) is int and owner > 0 and len({owner, *pids.values()}) == 3,
        "distinct owner/worker PIDs",
    )
    events: list[dict[str, Any]] = []
    for role in ROLES:
        events.extend(
            [
                {
                    "sequence": len(events) + 1,
                    "stage": "ready",
                    "role": role,
                    "pid": pids[role],
                    "cold_execution_sha256": config.execution(role, cold=True).identity,
                },
                {
                    "sequence": len(events) + 2,
                    "stage": "warm_deadline",
                    "role": role,
                    "execution_sha256": config.execution(role, cold=False).identity,
                },
            ]
        )
    for role in ROLES:
        events.append(
            {"sequence": len(events) + 1, "stage": "generate", "role": role, "status": "OK"}
        )
    for role in reversed(ROLES):
        events.append(
            {"sequence": len(events) + 1, "stage": "cleanup", "role": role, "reaped": True}
        )
    base = {
        "protocol": "model_pair_v1",
        "state": "CLOSED",
        "config_sha256": config.sha256,
        "owner_pid": owner,
        "events": events,
        "workers": workers,
        "phase5_accepted": False,
    }
    equal(closed, base, "closed snapshot")
    measurements = {}
    ready_memory = []
    for index, name in enumerate(("ready", "agent_call", "guard_call")):
        record = read_record(root / (name + ".json"))
        fields(
            record,
            {"pair", "memory"} | ({"role", "response_sha256", "call_seconds"} if index else set()),
            name,
        )
        live_workers = {}
        for role in ROLES:
            count = 2 if index == 2 or (index == 1 and role == "agent") else 1
            live_workers[role] = {
                "attempts": workers[role]["attempts"][:count],
                "lifecycle": [],
                "closed": False,
                "handle_pending": True,
            }
        equal(
            record["pair"],
            {**base, "state": "READY", "events": events[: 4 + index], "workers": live_workers},
            "live snapshot continuity",
        )
        memory = record["memory"]
        validate_memory(memory)
        require([m["total_bytes"] for m in memory] == totals, "global totals changed")
        require(
            all(
                baseline[d]["free_bytes"] - memory[d]["free_bytes"] >= MIN_RESIDENT[d]
                for d in (0, 1)
            ),
            "combined residency",
        )
        if not index:
            ready_memory = memory
            continue
        role = "agent" if index == 1 else "guard"
        equal(record["role"], role, "call role")
        equal(record["response_sha256"], text_hash(ACK), "call ACK")
        require(positive(record["call_seconds"]), "host call duration")
        identity = config.agent if role == "agent" else config.guard
        measurements[role] = audit_stages(
            root / f"{role}_stress", role, identity, pids[role], totals
        )
        # Strict JSON decode additionally guards duplicate keys in the reused load auditor.
        read_record(root / f"{role}_hf_metrics.jsonl")
        load = audit_load(root / f"{role}_hf_metrics.jsonl", role, config, pin)
        attempts = workers[role]["attempts"]
        require(
            load["load_seconds_including_hashes"] <= attempts[0]["load_seconds"],
            "native load timing containment",
        )
        require(
            measurements[role]["backend_total_seconds"]
            <= attempts[1]["generation_seconds"]
            <= attempts[1]["elapsed_seconds"]
            <= record["call_seconds"],
            "host/worker timing containment",
        )
        measurements[role].update(
            host_call_seconds=record["call_seconds"],
            hf_load=load,
            cleanup=workers[role]["lifecycle"][0],
        )
    times, residuals = [], []
    for i in range(6):
        row = read_record(root / f"recovery_{i}.json")
        fields(row, {"elapsed_seconds", "memory"}, "recovery")
        validate_memory(row["memory"])
        require(
            [m["total_bytes"] for m in row["memory"]] == totals
            and positive(row["elapsed_seconds"]),
            "recovery totals/time",
        )
        times.append(row["elapsed_seconds"])
        residuals.append(
            [baseline[d]["free_bytes"] - row["memory"][d]["free_bytes"] for d in (0, 1)]
        )
    require(
        all(b > a for a, b in zip(times, times[1:], strict=False)), "recovery observation order"
    )
    require(all(abs(n) <= TOLERANCE for row in residuals[-3:] for n in row), "VRAM recovery")
    equal(
        read_record(root / "summary.json"),
        {
            "protocol": "context_stress_pair_probe_v1",
            "status": "EXECUTION_COMPLETE",
            "valid": True,
            "phase5_accepted": False,
            "calls_completed": 2,
            "reaped": True,
            "recovery_valid": True,
            "cleanup_error": False,
            "actual_model_generation_calls": 2,
            "native_stress_verified": True,
            "scope": "Stress transport/completion/recovery; stub is not native GPU evidence; "
            "native records still require independent artifact audit",
        },
        "probe summary",
    )
    equal(inventory(root), before, "probe changed during audit")
    return {
        "protocol": "context_stress_artifact_audit_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_commit": commit,
        "raw_sha256": before,
        "measurements": measurements,
        "workers_reaped": 2,
        "graceful_workers": sum(
            w["lifecycle"][0]["method"] == "GRACEFUL" for w in workers.values()
        ),
        "model_generation_calls": 2,
        "separate_final_forwards": 2,
        "resident_bytes": [
            baseline[d]["free_bytes"] - ready_memory[d]["free_bytes"] for d in (0, 1)
        ],
        "recovery_elapsed_seconds": times,
        "signed_residual_bytes": residuals,
        "ipc_cleanup_verified": False,
        "source_authenticated": False,
        "limitations": "Receipt consistency only until remote source/bundle authenticated; "
        "no tokenizer reconstruction, quality, decode-only throughput, separated prefill, "
        "continuous global peak or IPC leak-free proof",
    }
