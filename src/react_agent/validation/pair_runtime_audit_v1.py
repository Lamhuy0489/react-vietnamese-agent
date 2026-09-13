"""Join runtime gate evidence with actual pair worker attempts and startup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import ArtifactStore, canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig
from react_agent.llm.model_pair_v1 import READY_COMMAND
from react_agent.security_v1.guard import PROMPT, GuardInput, GuardOutcome


def audit_task(output: Path) -> dict[str, Any]:
    receipt = json.loads((output / "pair_runtime.json").read_text())
    workers = receipt["snapshot"]["workers"]
    guard_enabled = receipt["security"]["llm_guard"]
    if set(workers) != ({"agent", "guard"} if guard_enabled else {"agent"}):
        raise ValueError("unexpected worker roles")
    if receipt["cleanup_error_class"] is not None or any(
        not w["closed"] or w["handle_pending"] or any(not e["reaped"] for e in w["lifecycle"])
        for w in workers.values()
    ):
        raise ValueError("worker cleanup incomplete")
    for worker in workers.values():
        attempts = worker["attempts"]
        if [a["sequence"] for a in attempts] != list(range(1, len(attempts) + 1)):
            raise ValueError("transport attempt sequence mismatch")
        if attempts:
            first = attempts[0]
            if first["request_sha256"] != text_hash(
                canonical_json([{"role": "user", "content": READY_COMMAND}])
            ) or first["generation_sha256"] != text_hash(
                canonical_json(GenerationConfig().model_dump())
            ):
                raise ValueError("readiness request binding mismatch")
        if any(a["cold_start"] or a.get("load_seconds", 0) != 0 for a in attempts[1:]):
            raise ValueError("unexpected cold reload after readiness")
    meta_path = output / "runtime/run_metadata.json"
    if not meta_path.exists():
        if receipt["error_class"] is None or receipt["terminal"] is not None:
            raise ValueError("missing runtime without recorded outer failure")
        return {"valid": True, "runtime_present": False, "guard_attempts": 0}
    metadata = json.loads(meta_path.read_text())
    if metadata.get("pair_runtime_profile") != receipt["profile"]:
        raise ValueError("runtime pair profile mismatch")
    if (
        metadata["task_hash"] != receipt["task_sha256"]
        or metadata["security_config"] != receipt["security"]
    ):
        raise ValueError("runtime task/security identity mismatch")
    if metadata["result"]["status"] != receipt["terminal"]:
        raise ValueError("runtime terminal mismatch")
    if guard_enabled:
        host_roles = receipt["host_role_attempts"]
        if len(host_roles["agent"]) != metadata["control"]["model_turn_count"]:
            raise ValueError("agent proposed generation count mismatch")
        for role in ("agent", "guard"):
            dispatched = workers[role]["attempts"][1:]
            cursor = 0
            for sequence, host in enumerate(host_roles[role], 1):
                if (
                    host["sequence"] != sequence
                    or host["role"] != role
                    or host["worker_attempts_before"] != cursor
                ):
                    raise ValueError("host role sequence mismatch")
                after = host["worker_attempts_after"]
                if after == cursor:
                    if host["status"] != "ERROR" or host["error_class"] is None:
                        raise ValueError("unexplained rejected host proposal")
                elif after == cursor + 1 and cursor < len(dispatched):
                    actual = dispatched[cursor]
                    if any(
                        host[key] != actual[key]
                        for key in ("request_sha256", "generation_sha256")
                    ):
                        raise ValueError("host/worker request mismatch")
                    if (host["status"] == "OK") != (actual["status"] == "OK") or (
                        (host["error_class"] is None) != (host["status"] == "OK")
                    ):
                        raise ValueError("host/worker result mismatch")
                else:
                    raise ValueError("host/worker attempt count mismatch")
                cursor = after
            if cursor != len(dispatched):
                raise ValueError("unaccounted worker request")
    elif len(workers["agent"]["attempts"]) - 1 != metadata["control"]["model_turn_count"]:
        raise ValueError("agent generation count mismatch")
    if not guard_enabled:
        if metadata["guard_execution_attempt_count"] or metadata["guard_execution"] is not None:
            raise ValueError("agent-only run contains guard execution")
        return {"valid": True, "runtime_present": True, "guard_attempts": 0}
    guards = [
        json.loads(line) for line in (output / "runtime/trace_guard.jsonl").read_text().splitlines()
    ]
    if metadata["guard_trace_schema"] != "guard_trace_pair_v1" or any(
        row["schema_version"] != "guard_trace_pair_v1" for row in guards
    ):
        raise ValueError("pair guard trace schema mismatch")
    if len(guards) != metadata["guard_classification_count"]:
        raise ValueError("guard classification count mismatch")
    uncached = [row for row in guards if not row["outcome"]["cache_hit"]]
    guard_hosts = receipt["host_role_attempts"]["guard"]
    if len(uncached) != len(guard_hosts):
        raise ValueError("guard proposed generation count mismatch")
    for row, host in zip(uncached, guard_hosts, strict=True):
        messages = [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": canonical_json(row["input"])},
        ]
        if host["request_sha256"] != text_hash(canonical_json(messages)) or host[
            "generation_sha256"
        ] != text_hash(canonical_json(metadata["guard_generation"])):
            raise ValueError("guard host request binding mismatch")
    attempts = [a for row in guards for a in row["execution_attempts"]]
    if (
        attempts != workers["guard"]["attempts"][1:]
        or len(attempts) != metadata["guard_execution_attempt_count"]
    ):
        raise ValueError("runtime attempts differ from worker evidence")
    store = ArtifactStore.deserialize(
        metadata["run_id"], (output / "runtime/artifacts/artifacts.jsonl").read_text()
    )
    expected = []
    for line in (output / "runtime/trace_security.jsonl").read_text().splitlines():
        event = json.loads(line)
        data = json.loads(event["data_json"])
        if event["event"] == "proposal":
            expected.append(("PRE", data["proposal_id"], data["artifact_id"]))
        elif event["event"] == "decision" and data["stage"] == "POST":
            artifact = store.get(data["artifact_id"])
            sources = [
                p.parent_id
                for p in artifact.parents
                if store.get(p.parent_id).producer == "tool_source_snapshot"
            ]
            if len(sources) != 1:
                raise ValueError("ambiguous Post source")
            expected.append(("POST", data["proposal_id"], sources[0]))
    if [(r["stage"], r["proposal_id"], r["candidate_artifact_id"]) for r in guards] != expected:
        raise ValueError("guard gate coverage mismatch")
    cache: dict[str, object] = {}
    for sequence, row in enumerate(guards, 1):
        request = GuardInput.model_validate(row["input"])
        outcome = GuardOutcome.model_validate(row["outcome"])
        if (
            row["sequence"] != sequence
            or row["run_id"] != metadata["run_id"]
            or row["task_id"] != metadata["task_id"]
        ):
            raise ValueError("guard trace sequence/identity mismatch")
        if text_hash(request.user_instruction) != metadata["task_hash"]:
            raise ValueError("guard user identity mismatch")
        source = store.get(row["candidate_artifact_id"])
        if row["stage"] == "PRE":
            if request.candidate_action_json != canonical_json(
                json.loads(str(source.content()))["action"]
            ):
                raise ValueError("guard proposed action mismatch")
        elif request.candidate_content != source.raw_json:
            raise ValueError("guard observed source mismatch")
        key = text_hash(
            canonical_json(
                {
                    "model": metadata["guard_execution"]["model_id"],
                    "revision": metadata["guard_execution"]["model_revision"],
                    "prompt": text_hash(PROMPT),
                    "generation": metadata["guard_generation"],
                    "input": row["input"],
                }
            )
        )
        if outcome.cache_key != key:
            raise ValueError("guard cache identity mismatch")
        request_hash = text_hash(
            canonical_json(
                [
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": canonical_json(row["input"])},
                ]
            )
        )
        for attempt in row["execution_attempts"]:
            if attempt["request_sha256"] != request_hash or attempt[
                "generation_sha256"
            ] != text_hash(canonical_json(metadata["guard_generation"])):
                raise ValueError("guard request/generation mismatch")
            if attempt["execution_config_sha256"] != metadata["guard_execution_hash"]:
                raise ValueError("guard deadline identity mismatch")
        if outcome.cache_hit and (
            row["execution_attempts"] or cache.get(key) != row["outcome"]["result"]
        ):
            raise ValueError("unexplained guard cache hit")
        if outcome.status == "OK":
            cache[key] = row["outcome"]["result"]
        else:
            cache.clear()
    return {"valid": True, "runtime_present": True, "guard_attempts": len(attempts)}
