"""CPU controls for the structured API Dev manifest and checkpoint runner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from react_agent.adversarial_release import load_split
from react_agent.foundation.artifacts import canonical_json
from react_agent.llm.base import GenerationConfig
from react_agent.llm.structured_api_dev_v1 import (
    ApiDevManifest,
    TaskState,
    run,
    write_manifest,
)
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend
from react_agent.serving.structured_api_v1 import AGENT_SCHEMA, GUARD_SCHEMA, PROFILE, sha

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data/clean/v1_1"
RELEASE = ROOT / "data/adversarial/release_v2"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> ApiDevManifest:
    selection = json.loads((CLEAN / "dev_pilot/task_ids.json").read_text())
    rows = {
        json.loads(line)["task_id"]: json.loads(line)
        for line in (CLEAN / "splits/dev.jsonl").read_text().splitlines()
    }
    fixtures = load_split(RELEASE)
    attacks = {row.pair_id: row for row in fixtures if row.branch == "attack"}
    benign = {row.pair_id: row for row in fixtures if row.branch == "benign"}
    pair_id = sorted(set(attacks) & set(benign))[0]
    pair = (attacks[pair_id].variant_id, benign[pair_id].variant_id)
    agent_revision = "sha256:" + sha(canonical_json({"config": "agent"}).encode())
    guard_revision = "sha256:" + sha(canonical_json({"config": "guard"}).encode())
    return ApiDevManifest(
        source_commit="test-source",
        source_files={
            "src/react_agent/llm/structured_api_dev_v1.py": _digest(
                ROOT / "src/react_agent/llm/structured_api_dev_v1.py"
            )
        },
        clean_split_sha256=_digest(CLEAN / "splits/dev.jsonl"),
        clean_selection_sha256=_digest(CLEAN / "dev_pilot/task_ids.json"),
        clean_task_ids=tuple(selection["task_ids"]),
        clean_task_categories={
            task_id: rows[task_id]["category"] for task_id in selection["task_ids"]
        },
        clean_input_root=str(CLEAN),
        fault_plans_sha256=_digest(CLEAN / "dev_pilot/fault_plans.json"),
        adversarial_release_root=str(RELEASE),
        adversarial_attack_sha256=_digest(RELEASE / "dev_attack.jsonl"),
        adversarial_benign_sha256=_digest(RELEASE / "dev_benign.jsonl"),
        guard_variant_ids=pair,
        guard_pairs=(pair,),
        agent_identity={"model_id": "model-agent", "model_revision": agent_revision,
                        "session_id": "session-agent", "source_commit": "test-source",
                        "worker_sha256": "b" * 64},
        guard_identity={"model_id": "model-guard", "model_revision": guard_revision,
                        "session_id": "session-guard", "source_commit": "test-source",
                        "worker_sha256": "b" * 64},
        agent_generation=GenerationConfig(max_new_tokens=1024).model_dump(mode="json"),
        guard_generation=GenerationConfig(max_new_tokens=128).model_dump(mode="json"),
        runtime={"config_id": "A0", "max_steps": 8, "max_format_retries_per_step": 2,
                 "tool_timeout_seconds": 5.0},
    )


class _Transport:
    def __init__(self, role: str, session: str, model: str) -> None:
        self.role = role
        self.session = session
        self.model = model
        self.files = {"config": role}
        self.revision = "sha256:" + sha(canonical_json(self.files).encode())
        self.calls = 0

    def __call__(self, method: str, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        if method == "GET" and path == "/models":
            return {
                "profile": PROFILE,
                "session_id": self.session,
                "role": self.role,
                "source_commit": "test-source",
                "model_revision": self.revision,
                "worker_sha256": "b" * 64,
                "data": [{"id": self.model, "object": "model"}],
                "capabilities": {"json_schema": True},
                "model_fingerprint": {"files": self.files},
            }
        if method != "POST" or path != "/chat/completions" or payload is None:
            raise AssertionError("unexpected transport call")
        self.calls += 1
        schema = GUARD_SCHEMA if self.role == "guard" else AGENT_SCHEMA
        content = (
            '{"risk":"SAFE","labels":[],"confidence":"LOW"}'
            if self.role == "guard"
            else '{"final_answer":{"answer":"ok"}}'
        )
        return {
            "profile": PROFILE,
            "session_id": self.session,
            "model": self.model,
            "model_revision": self.revision,
            "execution": {
                "constrained_decoding": True,
                "schema_sha256": sha(canonical_json(schema).encode()),
                "seed": payload["seed"],
            },
            "choices": [
                {"finish_reason": "stop", "message": {"role": "assistant", "content": content}}
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }


def _backend(role: str) -> tuple[StructuredHTTPBackend, _Transport]:
    transport = _Transport(role, f"session-{role}", f"model-{role}")
    backend = StructuredHTTPBackend(
        transport,
        model=transport.model,
        role=role,
        session_id=transport.session,
        source_commit="test-source",
        model_revision=transport.revision,
        worker_sha256="b" * 64,
    )
    return backend, transport


def test_manifest_forbids_test_and_private_ground_truth() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        ApiDevManifest.model_validate(_manifest().model_dump() | {"test_tasks_loaded": 1})


def test_task_state_rejects_uncertain_false_interruption() -> None:
    with pytest.raises(ValueError, match="delivery uncertainty"):
        TaskState(key="x", kind="agent", status="interrupted", input_sha256="a" * 64,
                  started_at_ns=1, finished_at_ns=2)


def test_runner_checkpoints_missing_only_and_writes_receipt(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest_path, manifest)
    agent, agent_transport = _backend("agent")
    guard, guard_transport = _backend("guard")
    output = tmp_path / "run"

    first = run(output, manifest_path, agent=agent, guard=guard, max_new_tasks=2, probe=True)
    assert first["completed"] == 2
    assert first["missing"] == 21
    assert agent_transport.calls == 2
    assert guard_transport.calls == 0
    assert (output / "summary.json").is_file()

    second = run(output, manifest_path, agent=agent, guard=guard, max_new_tasks=0, probe=False,
                 resume=True)
    assert second["completed"] == 2
    assert agent_transport.calls == 2
    assert guard_transport.calls == 0

    third = run(output, manifest_path, agent=agent, guard=guard, max_new_tasks=1, probe=False,
                resume=True)
    assert third["completed"] == 3
    assert agent_transport.calls == 3
