"""Six ordinary synthetic requests through one task-owned pair; no stress decoding."""

from __future__ import annotations

import math
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import MODEL, no_links, write_receipt
from react_agent.llm.base import GenerationConfig
from react_agent.llm.efficient_requests_v1 import GUARD_REVISION
from react_agent.llm.guard_hf_v1 import GuardHFConfig, GuardHFFactory
from react_agent.llm.guard_snapshot_v1 import MODEL_ID, GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION, AgentFactoryV2, GuardFactory
from react_agent.llm.model_pair_probe_v1 import (
    MIN_RESIDENT,
    TOLERANCE,
    PairObserver,
    technical_inputs,
    validate_memory,
)
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig, Role
from react_agent.llm.request_policy_pair_v1 import policy_pair
from react_agent.security_v1.guard import PROMPT, GuardInput

ROLES: tuple[Role, ...] = ("agent", "guard")
PROTOCOL = "ordinary_pair_probe_v1"


def fresh_roots(*roots: Path) -> None:
    for root in roots:
        no_links(root)
        if root.exists():
            raise ValueError("fresh output roots required")
    resolved = [root.resolve() for root in roots]
    for index, root in enumerate(resolved):
        if any(root.is_relative_to(p) or p.is_relative_to(root) for p in resolved[index + 1 :]):
            raise ValueError("separate non-nested output roots required")


def native_config() -> PairConfig:
    return PairConfig(ModelIdentity(MODEL, AGENT_REVISION), ModelIdentity(MODEL_ID, GUARD_REVISION))


def native_pair(
    agent: Path,
    inventory: Path,
    guard: Path,
    snapshot: GuardSnapshot,
    output: Path,
    attention: Path,
    policy: Path,
) -> ModelPair:
    """Original immutable native factories, no private factory replacement or eager load."""
    fresh_roots(output, attention, policy)
    if not isinstance(snapshot, GuardSnapshot) or (snapshot.model_id, snapshot.model_revision) != (
        MODEL_ID,
        GUARD_REVISION,
    ):
        raise ValueError("exact content-bound guard snapshot required")
    for source in (agent, inventory, guard):
        no_links(source)
        if any(
            root.resolve().is_relative_to(source.resolve())
            or source.resolve().is_relative_to(root.resolve())
            for root in (output, attention, policy)
        ):
            raise ValueError("outputs must not overlap model inputs")
    return policy_pair(
        AgentFactoryV2(agent, inventory, output / "agent_hf_metrics.jsonl"),
        GuardFactory(
            GuardHFFactory(guard, snapshot, GuardHFConfig(), output / "guard_hf_metrics.jsonl")
        ),
        native_config(),
        attention,
        policy,
    )


def inputs() -> dict[str, dict[str, list[dict[str, str]]]]:
    """Public synthetic A/B fixtures, not benchmark tasks or exact-token stress inputs."""
    public = "Thông báo giả lập: thư viện mở cửa lúc 8 giờ và đóng cửa lúc 17 giờ. " * 32
    guard = GuardInput(
        user_instruction="Tóm tắt giờ mở cửa thư viện trong thông báo công khai giả lập.",
        source_type="document",
        candidate_content=public,
    )
    return {
        "A": technical_inputs(),
        "B": {
            "agent": [{"role": "user", "content": "Tóm tắt ngắn thông báo công khai: " + public}],
            "guard": [
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": canonical_json(guard.model_dump(mode="json"))},
            ],
        },
    }


def run(
    output: Path, pair: ModelPair, observer: PairObserver, identity: dict[str, Any]
) -> dict[str, Any]:
    """Record every submission/return; stop at first error and always close siblings."""
    fresh_roots(output)
    backend = identity.get("backend")
    if backend not in ("stub", "hf") or pair.state != "NEW":
        raise ValueError("explicit backend and fresh pair required")
    expected = (
        native_config()
        if backend == "hf"
        else PairConfig(
            ModelIdentity("synthetic-agent", "v1"), ModelIdentity("synthetic-guard", "v1")
        )
    )
    if (pair.config.agent, pair.config.guard) != (expected.agent, expected.guard):
        raise ValueError("backend identity mismatch")
    if backend == "hf" and pair.config != expected:
        raise ValueError("frozen native deadlines required")
    if (
        type(observer.interval) not in (int, float)
        or not math.isfinite(observer.interval)
        or observer.interval < 0
    ):
        raise ValueError("finite nonnegative observation interval required")
    fixtures = inputs()
    order = [(label, role) for label in ("A", "B", "A") for role in ROLES]
    generation = {
        role: GenerationConfig(max_new_tokens=512 if role == "agent" else 128) for role in ROLES
    }
    output.mkdir(parents=True, exist_ok=False)
    write_receipt(output / "inputs.json", fixtures)
    write_receipt(
        output / "manifest.json",
        dict(
            protocol=PROTOCOL,
            identity=identity,
            pair_config=asdict(pair.config),
            pair_config_sha256=pair.config.sha256,
            inputs_sha256=text_hash(canonical_json(fixtures)),
            generation={role: config.model_dump() for role, config in generation.items()},
            generation_sha256={
                role: text_hash(canonical_json(config.model_dump()))
                for role, config in generation.items()
            },
            order=order,
            automatic_retry=False,
            benchmark_tasks=0,
            test_payloads_parsed=0,
            min_resident_bytes=MIN_RESIDENT,
            recovery_tolerance_bytes=TOLERANCE,
            recovery_samples=6,
            sample_interval_seconds=observer.interval,
        ),
    )
    submitted = returned = 0
    responses: dict[str, list[str]] = {role: [] for role in ROLES}
    baseline: list[dict[str, int]] = []
    samples: list[list[dict[str, int]]] = []
    status, cleanup_error = "NOT_COMPLETED", False
    started = time.monotonic()
    try:
        observed = observer.sample("baseline")
        validate_memory(observed)
        baseline = observed
        write_receipt(output / "baseline.json", {"memory": baseline})
        pair.start()
        resident = observer.sample("resident")
        validate_memory(resident)
        write_receipt(output / "ready.json", {"pair": pair.snapshot(), "memory": resident})
        if any(
            resident[i]["total_bytes"] != baseline[i]["total_bytes"]
            or baseline[i]["free_bytes"] - resident[i]["free_bytes"] < MIN_RESIDENT[i]
            for i in (0, 1)
        ):
            raise RuntimeError("combined residency not observable")
        for index, (label, role) in enumerate(order, 1):
            messages = [dict(message) for message in fixtures[label][role]]
            config = generation[role].model_copy(deep=True)
            write_receipt(
                output / f"call_{index:02d}_submitted.json",
                dict(
                    index=index,
                    label=label,
                    role=role,
                    request_index=(index + 1) // 2,
                    messages_sha256=text_hash(canonical_json(messages)),
                    pair=pair.snapshot(),
                ),
            )
            submitted += 1
            call_started = time.monotonic()
            response = pair.generate(role, messages, config)
            call_seconds = time.monotonic() - call_started
            returned += 1
            digest = text_hash(response.text)
            responses[role].append(digest)
            write_receipt(
                output / f"call_{index:02d}_returned.json",
                dict(
                    index=index,
                    label=label,
                    role=role,
                    response_sha256=digest,
                    call_seconds=call_seconds,
                    pair=pair.snapshot(),
                ),
            )
            memory = observer.sample("after_call")
            validate_memory(memory)
            write_receipt(output / f"call_{index:02d}_memory.json", {"memory": memory})
        status = "EXECUTION_COMPLETE"
    except BaseException as exc:  # Durable failure class; interrupts propagate after cleanup.
        status = "ERROR" if isinstance(exc, Exception) else "INTERRUPTED"
        write_receipt(output / "error.json", {"error_class": type(exc).__name__})
        if not isinstance(exc, Exception):
            raise
    finally:
        try:
            pair.close()
        except BaseException as exc:
            cleanup_error = True
            write_receipt(output / "cleanup_error.json", {"error_class": type(exc).__name__})
        closed = pair.snapshot()
        write_receipt(output / "closed.json", closed)
        reaped = not any(worker["handle_pending"] for worker in closed["workers"].values())
        if baseline and reaped and not cleanup_error:
            try:
                for index in range(6):
                    if index:
                        time.sleep(observer.interval)
                    memory = observer.sample("recovery")
                    validate_memory(memory)
                    write_receipt(
                        output / f"recovery_{index}.json",
                        dict(
                            memory=memory,
                            elapsed_seconds=time.monotonic() - started,
                        ),
                    )
                    samples.append(memory)
            except Exception as exc:
                status = "OBSERVER_ERROR"
                write_receipt(output / "observer_error.json", {"error_class": type(exc).__name__})
        recovered = len(samples) == 6 and all(
            row[i]["total_bytes"] == baseline[i]["total_bytes"]
            and abs(row[i]["free_bytes"] - baseline[i]["free_bytes"]) <= TOLERANCE
            for row in samples[-3:]
            for i in (0, 1)
        )
        result = dict(
            protocol=PROTOCOL,
            status=status,
            execution_valid=status == "EXECUTION_COMPLETE"
            and reaped
            and recovered
            and not cleanup_error,
            phase5_accepted=False,
            native_validated=False,
            independent_audit_pending=backend == "hf",
            calls_submitted=submitted,
            responses_returned=returned,
            actual_model_generation_calls=0 if backend == "stub" else None,
            reaped=reaped,
            recovery_valid=recovered,
            cleanup_error=cleanup_error,
            repeated_a_equal={
                role: hashes[0] == hashes[2] if len(hashes) == 3 else None
                for role, hashes in responses.items()
            },
            scope="Transport/residency observations only. A equality is descriptive, "
            "not an acceptance filter; native policy/source/memory audit and "
            "runtime/quality gates remain.",
        )
        write_receipt(output / "summary.json", result)
    return result
