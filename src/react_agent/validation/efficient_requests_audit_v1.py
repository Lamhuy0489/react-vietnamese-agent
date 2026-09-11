"""Read-only ordinary-request/native-metric consistency, not execution authentication."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import MODEL, no_links
from react_agent.llm.base import GenerationConfig
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION, MODEL_ID
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.llm.model_pair_v1 import Role
from react_agent.validation.context_stress_audit_v1 import equal, fields, inventory
from react_agent.validation.guard_probe_audit_v2 import digest, require

_SDPA_SHA = "87f933d1a2d8508df572da5c0748c6b24c22ff2b625796949957dcd86cc57564"
_GUARD_REVISION = f"hf:{CANDIDATE_REVISION};snapshot-sha256:" + (
    "36b6d38e9e3cbc47427b1fabcf6f44fdd926a1d95a04a33bbfb19d7f1ffd5fbe"
)
_COMMON = {"protocol", "stage", "role", "pid", "request_index", "model_id", "model_revision"}
_STAGE_FIELDS = {
    "entered": {"hf_sdpa_sha256", "flags_before"},
    "restored": {"state_restored", "flags_after"},
    "completed": {
        "input_tokens",
        "attention_calls",
        "forward_groups",
        "last_forward_key_tokens",
        "masked_calls",
        "max_new_tokens",
        "output_tokens_verified",
        "full_boundary_cache_verified",
        "state_restored",
        "helper_calls",
        "profiler_used",
        "decoding_changed",
        "scope",
    },
}


def _record(raw: str) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def invalid(value: str) -> Any:
        raise ValueError("nonfinite JSON constant")

    def finite(value: str) -> float:
        number = float(value)
        require(math.isfinite(number), "nonfinite JSON number")
        return number

    try:
        result = json.loads(
            raw, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite
        )
    except json.JSONDecodeError:
        raise ValueError("invalid artifact JSON") from None
    require(type(result) is dict, "artifact object required")
    return dict(result)


def _integer(value: Any, minimum: int, maximum: int, label: str) -> int:
    require(type(value) is int and minimum <= value <= maximum, label)
    return int(value)


def _seconds(value: Any, label: str) -> float:
    require(type(value) in (int, float) and value > 0, label)
    try:
        number = float(value)
    except OverflowError:
        raise ValueError(label) from None
    require(math.isfinite(number), label)
    return number


def _flags(value: Any) -> None:
    require(type(value) is dict, "flag object")
    fields(value, {"flash", "math", "mem_efficient", "cudnn"}, "backend flags")
    require(all(type(v) is bool for v in value.values()), "boolean backend flags")


def _request(
    path: Path, common: dict[str, Any], native: dict[str, Any], limit: int
) -> dict[str, Any]:
    records = {}
    for stage, keys in _STAGE_FIELDS.items():
        record = _record((path / f"{stage}.json").read_text())
        fields(record, _COMMON | keys, stage)
        for key, value in {**common, "stage": stage}.items():
            equal(record[key], value, "request identity " + key)
        records[stage] = record
    entered, restored, done = (records[s] for s in _STAGE_FIELDS)
    equal(entered["hf_sdpa_sha256"], _SDPA_SHA, "pinned HF source hash")
    _flags(entered["flags_before"])
    _flags(restored["flags_after"])
    equal(restored["flags_after"], entered["flags_before"], "restored backend flags")
    for record in (restored, done):
        require(record["state_restored"] is True, "native state restored")
    for key in (
        "output_tokens_verified",
        "full_boundary_cache_verified",
        "profiler_used",
        "decoding_changed",
    ):
        require(done[key] is False, "bounded request claim " + key)
    equal(
        done["scope"],
        "All-call geometry/efficient-only guards, not profiled dispatch, "
        "output count or full KV proof",
        "request evidence scope",
    )
    inputs = _integer(native["input_tokens"], 1, 4096, "native input count")
    outputs = _integer(native["output_tokens"], 1, limit, "native output count")
    for key, value in dict(
        input_tokens=inputs,
        forward_groups=outputs,
        attention_calls=28 * outputs,
        helper_calls=28 * outputs,
        last_forward_key_tokens=inputs + outputs - 1,
        max_new_tokens=limit,
    ).items():
        equal(done[key], value, "native/attention join " + key)
    masks = _integer(done["masked_calls"], 0, 28 * outputs, "masked call count")
    generation = _seconds(native["generate_seconds"], "native generation seconds")
    call = _seconds(native["call_seconds"], "native call seconds")
    require(generation <= call, "generation within native call duration")
    return dict(
        request_index=common["request_index"],
        input_tokens=inputs,
        output_tokens=outputs,
        attention_calls=28 * outputs,
        last_forward_key_tokens=inputs + outputs - 1,
        masked_calls=masks,
        generate_seconds=generation,
        native_call_seconds=call,
        output_count_matches_native_metrics=True,
        full_boundary_cache_verified=False,
    )


def audit(
    attention: Path, metrics: Path, *, role: Role, worker_pid: int, expected_requests: int
) -> dict[str, Any]:
    """Audit a closed successful role; failures/partial runs require a separate failure record."""
    require(role in ("agent", "guard"), "known role required")
    _integer(worker_pid, 1, 2**31 - 1, "expected worker PID")
    _integer(expected_requests, 1, 999999, "expected request count")
    for path in (attention, metrics):
        no_links(path)
    require(metrics.is_file(), "native metrics file required")
    require(
        not metrics.resolve().is_relative_to(attention.resolve())
        and not attention.resolve().is_relative_to(metrics.resolve()),
        "separate immutable inputs",
    )
    before, metrics_sha = inventory(attention), digest(metrics)
    tree_before = sorted(p.relative_to(attention).as_posix() for p in attention.rglob("*"))
    names = [f"request_{i:06d}" for i in range(1, expected_requests + 1)]
    equal(sorted(p.name for p in attention.iterdir()), names, "complete request directories")
    equal(
        sorted(before),
        sorted(f"{name}/{stage}.json" for name in names for stage in _STAGE_FIELDS),
        "complete request files",
    )
    for name in names:
        equal(
            sorted(p.name for p in (attention / name).iterdir()),
            sorted(stage + ".json" for stage in _STAGE_FIELDS),
            "exact request stages",
        )
    rows = [_record(line) for line in metrics.read_text().splitlines()]
    require(len(rows) == expected_requests + 1, "one load and exact native request count")
    load = rows[0]
    model, revision = (MODEL, AGENT_REVISION) if role == "agent" else (MODEL_ID, _GUARD_REVISION)
    for key, value in dict(
        event="load",
        model_id=model,
        model_revision=revision,
        dtype="float16",
        attention="sdpa",
        quantization=None,
        torch_version="2.10.0+cu128",
        transformers_version="5.5.0",
        cuda_version="12.8",
        protocol="agent_hf_dual_gpu_v1" if role == "agent" else "guard_hf_single_gpu_v1",
    ).items():
        equal(load[key], value, "native load identity " + key)
    if role == "agent":
        equal(load["adapter_protocol"], "agent_hf_dual_gpu_v2_tf550", "native agent adapter")
    load_seconds = _seconds(load["load_seconds_including_hashes"], "native load seconds")
    limit = 512 if role == "agent" else 128
    generation_sha = text_hash(GenerationConfig(max_new_tokens=limit).model_dump_json())
    summaries = []
    for index, native in enumerate(rows[1:], 1):
        for key, expected in dict(
            event="generate", status="OK", call_index=index, generation_sha256=generation_sha
        ).items():
            equal(native[key], expected, "native request " + key)
        common = dict(
            protocol="efficient_requests_v1",
            role=role,
            pid=worker_pid,
            request_index=index,
            model_id=model,
            model_revision=revision,
        )
        summaries.append(_request(attention / names[index - 1], common, native, limit))
    equal(inventory(attention), before, "attention mutated during audit")
    equal(
        sorted(p.relative_to(attention).as_posix() for p in attention.rglob("*")),
        tree_before,
        "attention directory tree mutated during audit",
    )
    equal(digest(metrics), metrics_sha, "native metrics mutated during audit")
    return dict(
        protocol="efficient_requests_audit_v1",
        valid=True,
        phase5_accepted=False,
        role=role,
        expected_worker_pid=worker_pid,
        request_count=expected_requests,
        model_id=model,
        model_revision=revision,
        generation_sha256=generation_sha,
        native_load_seconds=load_seconds,
        requests=summaries,
        input_sha256=dict(attention=before, native_metrics=metrics_sha),
        source_authenticated=False,
        supervisor_pid_authenticated=False,
        native_load_configuration_verified=False,
        resolved_policy_verified=False,
        full_boundary_cache_verified=False,
        task_lifecycle_verified=False,
        scope="Closed-role artifact consistency only; native metrics join is not "
        "source authentication, numerical statelessness, full task latency or Phase5 acceptance",
    )
