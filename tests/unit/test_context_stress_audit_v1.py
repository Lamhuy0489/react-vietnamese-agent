"""GPU-shaped synthetic receipts, not native GPU measurements or model outputs."""

from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import MODEL
from react_agent.llm.base import GenerationConfig
from react_agent.llm.context_geometry_v1 import SEED_TEXT, build_geometry, summarize_generation
from react_agent.llm.context_stress_v1 import ACK, REQUEST
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.llm.model_pair_probe_v1 import MIN_RESIDENT, TOLERANCE, SyntheticPairObserver
from react_agent.llm.model_pair_v1 import ModelIdentity, PairConfig
from react_agent.validation.context_stress_audit_v1 import (
    NATIVE_NONE_FIELDS,
    audit_probe,
    inventory,
    read_record,
)


def write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) + "\n")


class Tokenizer:
    all_special_ids = [151643, 151645]

    def __len__(self) -> int:
        return 151665

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        assert text == SEED_TEXT and not add_special_tokens
        return [2, 3, 4]


@pytest.fixture
def sample(tmp_path: Path) -> tuple[Path, GuardSnapshot, str]:
    # Reuse only synthetic loader metrics from the earlier audit tests, never
    # local historical GPU artifacts or benchmark payloads.
    fixture = importlib.import_module("test_pair_cancellation_audit_v1")
    old, pin, commit = fixture.sample.__wrapped__(tmp_path / "old_synthetic")
    root = tmp_path / "stress"
    config = PairConfig(
        ModelIdentity(MODEL, AGENT_REVISION), ModelIdentity(pin.model_id, pin.model_revision)
    )
    memory = SyntheticPairObserver()
    baseline, resident = memory.sample("baseline"), memory.sample("resident")
    write(
        root / "manifest.json",
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
    )
    write(root / "baseline.json", {"memory": baseline})
    workers = read_record(old / "agent_busy/closed.json")["workers"]
    for index, role in enumerate(("agent", "guard")):
        identity = config.agent if role == "agent" else config.guard
        worker = workers[role]
        first = worker["attempts"][0]
        first.update(generation_seconds=0.1)
        second = {
            **first,
            "cold_start": False,
            "sequence": 2,
            "elapsed_seconds": 23.0,
            "generation_seconds": 22.0,
            "load_seconds": 0.0,
            "request_sha256": text_hash(canonical_json(REQUEST)),
            "generation_sha256": text_hash(
                canonical_json(
                    GenerationConfig(max_new_tokens=512 if role == "agent" else 128).model_dump()
                )
            ),
            "execution_config_sha256": config.execution(role, cold=False).identity,
        }
        worker["attempts"] = [first, second]
        worker["lifecycle"][0].update(method="GRACEFUL", exitcode=0)
        write(
            root / f"{role}_hf_metrics.jsonl",
            read_record(old / f"agent_busy/{role}_hf_metrics.jsonl"),
        )
        geo = build_geometry(Tokenizer(), role, identity.model_revision)
        count = geo.output_tokens
        sequence = list(geo.input_ids) + [10] * count
        common = {
            "protocol": "context_stress_v1",
            "role": role,
            "pid": first["pid"],
            "model_id": identity.model_id,
            "model_revision": identity.model_revision,
        }
        local_memory = [
            {
                "device": d,
                "global_free_bytes": resident[d]["free_bytes"],
                "global_total_bytes": baseline[d]["total_bytes"],
                "allocated_bytes": 4 * 1024**3,
                "reserved_bytes": 4 * 1024**3,
                "peak_allocated_bytes": 4 * 1024**3,
                "peak_reserved_bytes": 4 * 1024**3,
            }
            for d in ([0, 1] if role == "agent" else [1])
        ]
        write(root / f"{role}_stress/entered.json", {**common, "stage": "entered"})
        write(
            root / f"{role}_stress/prepared.json",
            {
                **common,
                "stage": "prepared",
                "geometry": geo.receipt(),
                "generation": {
                    **dict.fromkeys(NATIVE_NONE_FIELDS),
                    "transformers_version": "5.5.0",
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
                },
                "tokenize_seconds": 0.2,
                "memory": local_memory,
                "seed": 42,
                "input_device": f"cuda:{index}",
                "prefill_seconds": None,
                "timing_scope": "generation aggregate includes prefill; not separated",
            },
        )
        for final in (False, True):
            stage = "completed" if final else "generated"
            length = 4096 + count - (not final)
            by_device: dict[str, int] = {}
            layers = []
            for layer in range(28):
                device = int(layer >= 20) if role == "agent" else 1
                heads = 4 if role == "agent" else 2
                size = length * (2048 if role == "agent" else 1024)
                layers.append(
                    {
                        "layer": layer,
                        "device": device,
                        "shape": [1, heads, length, 128],
                        "bytes": size,
                    }
                )
                by_device[str(device)] = by_device.get(str(device), 0) + size
            record = {
                **common,
                "stage": stage,
                "summary": summarize_generation(
                    geo,
                    sequence,
                    cache_length_after_generation=4095 + count,
                    cache_length_after_final_forward=4096 + count if final else None,
                ),
                "cache": {
                    "sequence_length": length,
                    "layers": layers,
                    "tensor_bytes_by_device": by_device,
                },
                "memory": local_memory,
                "generation_seconds": 20.0,
            }
            if final:
                record.update(
                    final_forward_seconds=0.1,
                    total_seconds=21.0,
                    model_generation_calls=1,
                    separate_final_forwards=1,
                    memory_scope="process allocator peaks; global endpoints, not global peak",
                )
            write(root / f"{role}_stress/{stage}.json", record)
    events = []
    for role in ("agent", "guard"):
        events.append(
            {
                "sequence": len(events) + 1,
                "stage": "ready",
                "role": role,
                "pid": workers[role]["attempts"][0]["pid"],
                "cold_execution_sha256": config.execution(role, cold=True).identity,
            }
        )
        events.append(
            {
                "sequence": len(events) + 1,
                "stage": "warm_deadline",
                "role": role,
                "execution_sha256": config.execution(role, cold=False).identity,
            }
        )
    for role in ("agent", "guard"):
        events.append(
            {"sequence": len(events) + 1, "stage": "generate", "role": role, "status": "OK"}
        )
    for role in ("guard", "agent"):
        events.append(
            {"sequence": len(events) + 1, "stage": "cleanup", "role": role, "reaped": True}
        )
    base = {
        "protocol": "model_pair_v1",
        "state": "CLOSED",
        "config_sha256": config.sha256,
        "owner_pid": 99,
        "events": events,
        "workers": workers,
        "phase5_accepted": False,
    }
    write(root / "closed.json", base)
    for i, name in enumerate(("ready", "agent_call", "guard_call")):
        live = copy.deepcopy(base)
        live.update(state="READY", events=events[: 4 + i])
        for role, w in live["workers"].items():
            count = 2 if i == 2 or (i == 1 and role == "agent") else 1
            w.update(
                attempts=w["attempts"][:count], lifecycle=[], closed=False, handle_pending=True
            )
        row = {"pair": live, "memory": resident}
        if i:
            row.update(
                role="agent" if i == 1 else "guard",
                response_sha256=text_hash(ACK),
                call_seconds=24.0,
            )
        write(root / (name + ".json"), row)
    for i in range(6):
        write(root / f"recovery_{i}.json", {"elapsed_seconds": 100.0 + i, "memory": baseline})
    write(
        root / "summary.json",
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
    )
    return root, pin, commit


def test_complete_synthetic_receipts_reproduce_without_native_claim(sample: Any) -> None:
    root, _, _ = sample
    before = inventory(root)
    result = audit_probe(*sample)
    assert result == audit_probe(*sample) and before == inventory(root)
    assert len(before) == 23 and result["workers_reaped"] == result["graceful_workers"] == 2
    assert result["valid"] and not result["phase5_accepted"] and not result["source_authenticated"]
    assert not result["ipc_cleanup_verified"]
    assert result["measurements"]["agent"]["full_kv_bytes_by_device"] == {
        "0": 188743680,
        "1": 75497472,
    }
    assert result["measurements"]["guard"]["full_kv_bytes_by_device"] == {"1": 121110528}
    assert result["measurements"]["agent"]["aggregate_output_tokens_per_second"] == 25.6


MUTATIONS = [
    ("agent_stress/entered.json", ("pid",), 101),
    ("agent_stress/entered.json", ("model_revision",), "unbound"),
    ("guard_stress/completed.json", ("summary", "new_tokens"), 512),
    ("guard_stress/completed.json", ("summary", "full_boundary_cache_observed"), 1),
    ("agent_stress/completed.json", ("summary", "sequence_ids_sha256"), "0" * 64),
    ("agent_stress/generated.json", ("summary", "cache_length_after_final_forward"), 4608),
    ("agent_stress/completed.json", ("cache", "layers", 20, "device"), 0),
    ("agent_stress/completed.json", ("cache", "layers", 0, "bytes"), 1),
    ("agent_stress/completed.json", ("cache", "layers", 0, "shape", 2), 4607),
    ("agent_stress/completed.json", ("cache", "tensor_bytes_by_device", "0"), 1),
    ("guard_stress/completed.json", ("cache", "sequence_length"), 4223),
    ("agent_stress/prepared.json", ("geometry", "seed_text_sha256"), "0" * 64),
    ("agent_stress/prepared.json", ("geometry", "input_tokens"), 4095),
    ("agent_stress/prepared.json", ("geometry", "seed_token_count"), True),
    ("agent_stress/prepared.json", ("geometry", "input_ids_sha256"), "not-a-hash"),
    ("agent_stress/prepared.json", ("generation", "min_new_tokens"), 1),
    ("agent_stress/prepared.json", ("generation", "do_sample"), True),
    ("agent_stress/prepared.json", ("generation", "eos_token_id"), []),
    ("agent_stress/prepared.json", ("generation", "output_logits"), True),
    ("agent_stress/prepared.json", ("generation", "max_time"), 1.0),
    ("agent_stress/prepared.json", ("generation", "repetition_penalty"), 1.1),
    ("agent_stress/prepared.json", ("generation", "transformers_version"), "4.43.1"),
    ("agent_stress/prepared.json", ("input_device",), "cuda:1"),
    ("agent_stress/prepared.json", ("prefill_seconds",), 1.0),
    ("agent_stress/prepared.json", ("seed",), 43),
    ("agent_stress/completed.json", ("generation_seconds",), float("nan")),
    ("agent_stress/completed.json", ("generation_seconds",), 19.0),
    ("agent_stress/completed.json", ("final_forward_seconds",), -1.0),
    ("agent_stress/completed.json", ("total_seconds",), 20.0),
    ("agent_stress/completed.json", ("model_generation_calls",), True),
    ("agent_stress/completed.json", ("memory", 0, "peak_reserved_bytes"), 13 * 1024**3),
    ("agent_stress/completed.json", ("memory", 0, "allocated_bytes"), 1),
    ("agent_stress/completed.json", ("memory", 0, "global_free_bytes"), 15 * 1024**3),
    ("agent_stress/completed.json", ("memory", 0, "global_total_bytes"), 17 * 1024**3),
    ("agent_stress/completed.json", ("memory", 0, "allocated_bytes"), True),
    ("manifest.json", ("automatic_retry",), True),
    ("manifest.json", ("identity", "backend"), "stub"),
    ("manifest.json", ("identity", "source_commit"), "a" * 40),
    ("manifest.json", ("sample_interval_seconds",), 0.0),
    ("closed.json", ("workers", "agent", "attempts", 1, "request_sha256"), "a" * 64),
    ("closed.json", ("workers", "agent", "attempts", 1, "elapsed_seconds"), 200.0),
    ("closed.json", ("workers", "guard", "attempts", 1, "load_seconds"), 1.0),
    ("closed.json", ("workers", "agent", "handle_pending"), True),
    ("closed.json", ("workers", "agent", "lifecycle", 0, "exitcode"), -9),
    ("closed.json", ("events", 7, "role"), "guard"),
    ("closed.json", ("owner_pid",), 100),
    ("ready.json", ("pair", "workers", "agent", "attempts", 0, "pid"), 101),
    ("guard_call.json", ("pair", "state"), "FAILED"),
    ("agent_call.json", ("call_seconds",), 22.0),
    ("agent_call.json", ("response_sha256",), "0" * 64),
    ("agent_call.json", ("memory", 0, "free_bytes"), 14 * 1024**3),
    ("agent_hf_metrics.jsonl", ("load_seconds_including_hashes",), 30.0),
    ("agent_hf_metrics.jsonl", ("runtime_admission", "full_inventory_match"), True),
    ("guard_hf_metrics.jsonl", ("model_revision",), "wrong"),
    ("recovery_5.json", ("memory", 1, "free_bytes"), 12 * 1024**3),
    ("recovery_0.json", ("memory", 1, "total_bytes"), 17 * 1024**3),
    ("recovery_5.json", ("elapsed_seconds",), 101.0),
    ("summary.json", ("valid",), False),
    ("summary.json", ("actual_model_generation_calls",), 0),
]


@pytest.mark.parametrize("name,keys,value", MUTATIONS)
def test_reject_mutated_receipt(sample: Any, name: str, keys: tuple[Any, ...], value: Any) -> None:
    root, _, _ = sample
    path = root / name
    record = read_record(path)
    parent = record
    for key in keys[:-1]:
        parent = parent[key]
    parent[keys[-1]] = value
    write(path, record)
    before = inventory(root)
    with pytest.raises(ValueError):
        audit_probe(*sample)
    assert before == inventory(root)


@pytest.mark.parametrize(
    "case", ["missing", "extra", "raw_text", "duplicate", "linked", "infinity"]
)
def test_malformed_inventory_rejected(sample: Any, case: str) -> None:
    root, _, _ = sample
    path = root / "agent_stress/entered.json"
    if case == "missing":
        path.unlink()
    elif case == "extra":
        write(root / "error.json", {"error_class": "RuntimeError"})
    elif case == "raw_text":
        write(path, {**read_record(path), "generated_text": "synthetic forbidden field"})
    elif case == "duplicate":
        path.write_text(path.read_text().replace('"pid": 100', '"pid": 101, "pid": 100'))
    elif case == "linked":
        path.rename(root / "elsewhere.json")
        path.symlink_to(root / "elsewhere.json")
    else:
        path.write_text(path.read_text().replace('"pid": 100', '"pid": 1e999'))
    with pytest.raises(ValueError):
        audit_probe(*sample)


def test_forced_close_is_reported_not_graceful(sample: Any) -> None:
    root, _, _ = sample
    closed = read_record(root / "closed.json")
    closed["workers"]["guard"]["lifecycle"][0].update(method="KILL", exitcode=-9)
    write(root / "closed.json", closed)
    result = audit_probe(*sample)
    assert (
        result["valid"] and result["graceful_workers"] == 1 and not result["ipc_cleanup_verified"]
    )


def test_cli_writes_reproducible_audit_outside_raw(
    sample: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, pin, commit = sample
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    cli = importlib.import_module("audit_phase5_context_stress")
    snapshot = root.parent / "synthetic_snapshot.json"
    write(snapshot, pin.model_dump(mode="json"))
    before = inventory(root)
    for i in (1, 2):
        output = root.parent / f"audit{i}.json"
        monkeypatch.setattr(
            "sys.argv",
            [
                "audit",
                "--probe",
                str(root),
                "--snapshot",
                str(snapshot),
                "--source-commit",
                commit,
                "--output",
                str(output),
            ],
        )
        cli.main()
        assert not read_record(output)["source_authenticated"]
        with pytest.raises(ValueError, match="fresh"):
            cli.main()
    assert (root.parent / "audit1.json").read_bytes() == (root.parent / "audit2.json").read_bytes()
    assert inventory(root) == before


def test_cli_cannot_write_inside_raw(sample: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    root, pin, commit = sample
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    cli = importlib.import_module("audit_phase5_context_stress")
    snapshot = root.parent / "snapshot.json"
    write(snapshot, pin.model_dump(mode="json"))
    monkeypatch.setattr(
        "sys.argv",
        [
            "audit",
            "--probe",
            str(root),
            "--snapshot",
            str(snapshot),
            "--source-commit",
            commit,
            "--output",
            str(root / "audit.json"),
        ],
    )
    with pytest.raises(ValueError, match="outside immutable"):
        cli.main()
    assert not (root / "audit.json").exists()


def test_raw_change_during_read_is_rejected(sample: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    from react_agent.validation import context_stress_audit_v1 as mod

    root, _, _ = sample
    original = mod.read_record

    def read_and_change(path: Path) -> Any:
        result = original(path)
        if path == root / "summary.json":
            write(root / "baseline.json", {"changed_during_audit": True})
        return result

    monkeypatch.setattr(mod, "read_record", read_and_change)
    with pytest.raises(ValueError, match="changed during audit"):
        mod.audit_probe(*sample)
