"""CPU transport controls for the structured API Dev runner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.llm.structured_api_dev_v1 import (
    ApiDevManifest,
    TaskState,
    run,
    write_manifest,
)
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend
from react_agent.serving.structured_api_v1 import AGENT_SCHEMA, GUARD_SCHEMA, sha

ROOT = Path(__file__).resolve().parents[2]


class FakeTransport:
    def __init__(self, role: str) -> None:
        self.role = role
        self.calls: list[tuple[str, str]] = []
        self.files = {
            "config.json": {"size": 1, "sha256": "a"},
            "model.safetensors": {"size": 1, "sha256": "b"},
        }
        self.model = f"fake-{role}"
        self.revision = "sha256:" + sha(canonical_json(self.files).encode())

    def __call__(self, method: str, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        self.calls.append((method, path))
        if method == "GET":
            return {
                "profile": "react-vn-structured-api-v1",
                "session_id": "test-session",
                "role": self.role,
                "source_commit": "test-source",
                "model_revision": self.revision,
                "worker_sha256": "worker-sha",
                "data": [{"id": self.model, "object": "model"}],
                "capabilities": {"json_schema": True},
                "model_fingerprint": {"files": self.files},
            }
        if self.role == "agent":
            text = '{"final_answer":{"answer":"synthetic"}}'
            schema_hash = sha(canonical_json(AGENT_SCHEMA).encode())
        else:
            text = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'
            schema_hash = sha(canonical_json(GUARD_SCHEMA).encode())
        return {
            "profile": "react-vn-structured-api-v1",
            "session_id": "test-session",
            "model": self.model,
            "model_revision": self.revision,
            "execution": {
                "constrained_decoding": True,
                "schema_sha256": schema_hash,
                "seed": 42,
            },
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": text},
                }
            ],
        }


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(path: Path) -> ApiDevManifest:
    clean = ROOT / "data/clean/v1_1"
    release = ROOT / "data/adversarial/release_v2"
    selection = json.loads((clean / "dev_pilot/task_ids.json").read_text())
    public = {
        json.loads(line)["task_id"]: json.loads(line)
        for line in (clean / "splits/dev.jsonl").read_text().splitlines()
        if line
    }
    attacks = [json.loads(line) for line in (release / "dev_attack.jsonl").read_text().splitlines()]
    benign = [json.loads(line) for line in (release / "dev_benign.jsonl").read_text().splitlines()]
    attack, good = attacks[0], benign[0]
    fake_revision = "sha256:" + sha(
        canonical_json(
            {
                "config.json": {"size": 1, "sha256": "a"},
                "model.safetensors": {"size": 1, "sha256": "b"},
            }
        ).encode()
    )
    manifest = ApiDevManifest(
        source_commit="test-source",
        source_files={
            str(Path(__file__).relative_to(ROOT)): _sha(Path(__file__)),
        },
        clean_split_sha256=_sha(clean / "splits/dev.jsonl"),
        clean_selection_sha256=_sha(clean / "dev_pilot/task_ids.json"),
        clean_task_ids=tuple(selection["task_ids"]),
        clean_task_categories={
            task_id: public[task_id]["category"] for task_id in selection["task_ids"]
        },
        clean_input_root=str(clean),
        fault_plans_sha256=_sha(clean / "dev_pilot/fault_plans.json"),
        adversarial_release_root=str(release),
        adversarial_attack_sha256=_sha(release / "dev_attack.jsonl"),
        adversarial_benign_sha256=_sha(release / "dev_benign.jsonl"),
        guard_variant_ids=(attack["variant_id"], good["variant_id"]),
        guard_pairs=((attack["variant_id"], good["variant_id"]),),
        agent_identity={
            "model_id": "fake-agent",
            "model_revision": fake_revision,
            "session_id": "test-session",
            "source_commit": "test-source",
            "worker_sha256": "worker-sha",
        },
        guard_identity={
            "model_id": "fake-guard",
            "model_revision": fake_revision,
            "session_id": "test-session",
            "source_commit": "test-source",
            "worker_sha256": "worker-sha",
        },
        agent_generation={"temperature": 0.0, "max_new_tokens": 512, "seed": 42},
        guard_generation={"temperature": 0.0, "max_new_tokens": 128, "seed": 42},
        runtime={
            "config_id": "A0",
            "max_steps": 8,
            "max_format_retries_per_step": 2,
            "tool_timeout_seconds": 5.0,
        },
    )
    write_manifest(path, manifest)
    return manifest


def _backends() -> tuple[
    StructuredHTTPBackend, StructuredHTTPBackend, FakeTransport, FakeTransport
]:
    at, gt = FakeTransport("agent"), FakeTransport("guard")
    agent = StructuredHTTPBackend(
        at,
        model=at.model,
        role="agent",
        session_id="test-session",
        source_commit="test-source",
        model_revision=at.revision,
        worker_sha256="worker-sha",
    )
    guard = StructuredHTTPBackend(
        gt,
        model=gt.model,
        role="guard",
        session_id="test-session",
        source_commit="test-source",
        model_revision=gt.revision,
        worker_sha256="worker-sha",
    )
    return agent, guard, at, gt


def test_completed_resume_does_not_call_model_again(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    _manifest(manifest_path)
    output = tmp_path / "run"
    agent, guard, at, gt = _backends()
    first = run(output, manifest_path, agent=agent, guard=guard, max_new_tasks=1)
    posts = (
        sum(method == "POST" for method, _ in at.calls),
        sum(method == "POST" for method, _ in gt.calls),
    )
    second = run(output, manifest_path, agent=agent, guard=guard, resume=True, max_new_tasks=0)
    assert first["completed"] == second["completed"] == 1
    assert posts == (
        sum(method == "POST" for method, _ in at.calls),
        sum(method == "POST" for method, _ in gt.calls),
    )
    assert json.loads((output / "summary.json").read_text())["state_sha256"]


def test_started_checkpoint_is_retained_as_interrupted(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    _manifest(manifest_path)
    output = tmp_path / "run"
    agent, guard, at, gt = _backends()
    run(output, manifest_path, agent=agent, guard=guard, max_new_tasks=1)
    first_task = json.loads((ROOT / "data/clean/v1_1/dev_pilot/task_ids.json").read_text())[
        "task_ids"
    ][0]
    task_root = output / "tasks" / first_task
    state = TaskState.model_validate(json.loads((task_root / "state.json").read_text()))
    state = state.model_copy(
        update={"status": "started", "finished_at_ns": None, "result": None, "error_code": None}
    )
    (task_root / "state.json").write_text(json.dumps(state.model_dump()), encoding="utf-8")
    posts_before = sum(method == "POST" for method, _ in at.calls)
    result = run(output, manifest_path, agent=agent, guard=guard, resume=True, max_new_tasks=0)
    assert result["interrupted"] == 1
    assert sum(method == "POST" for method, _ in at.calls) == posts_before
