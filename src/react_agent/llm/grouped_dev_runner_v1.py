"""CPU-only real-spawn grouped runner; preserve all terminal outcomes on resume."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.grouped_dev_identity_v1 import REVISION, identity, pair_config
from react_agent.llm.guard_diagnostic_backend_v1 import DiagnosticFactory
from react_agent.llm.model_pair_v2 import ShutdownPair
from react_agent.llm.native_shutdown_v2 import agent_config
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.sql_pair_runtime_v1 import run_pair_task
from react_agent.validation.grouped_dev_checkpoint_v1 import audit_checkpoint, audit_prefix
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog


@dataclass(frozen=True)
class ScriptedFactory:
    role: str
    trigger: str = ""

    def __call__(self) -> ScriptedBackend:
        return ScriptedBackend(self.role, self.trigger)


class ScriptedBackend:
    def __init__(self, role: str, trigger: str) -> None:
        self.model_id, self.model_revision = "synthetic-" + role, REVISION
        self.role, self.trigger, self.calls = role, trigger, 0

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.calls += 1
        text = (
            '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'
            if self.role == "guard"
            else self.trigger
            if self.calls == 1
            else '{"final_answer":{"answer":"Kiểm tra đường đi công cụ đã kết thúc."}}'
        )
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)


def run(
    output: Path,
    release: Path,
    environment: Path,
    *,
    commit: str,
    shard: int,
    resume: bool = False,
    max_new_tasks: int | None = None,
) -> dict[str, Any]:
    if type(shard) is not int or not 0 <= shard < 8 or type(resume) is not bool:
        raise ValueError("known shard and boolean resume required")
    if max_new_tasks is not None and (type(max_new_tasks) is not int or max_new_tasks < 0):
        raise ValueError("nonnegative controlled task budget required")
    for path in (output, release, environment):
        no_links(path)
    frozen = Path(__file__).resolve().parents[3] / "data"
    for source in (release, environment, frozen):
        if output.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(
            output.resolve()
        ):
            raise ValueError("output overlaps input or frozen data")
    manifest, rows = identity(release, environment, commit)
    if output.exists():
        if not resume:
            raise ValueError("fresh output required unless resuming exact identity")
        saved = audit_prefix(output, manifest, shard)
    else:
        output.mkdir(parents=True, exist_ok=False)
        write_receipt(output / "identity.json", {"run": manifest, "shard": shard})
        (output / "tasks").mkdir()
        saved = []
    tasks = [t for t in manifest["tasks"] if t["shard"] == shard]
    by_variant = {row.variant_id: row for row in rows}
    remaining = tasks[len(saved) :]
    if max_new_tasks is not None:
        remaining = remaining[:max_new_tasks]
    for task in remaining:
        row = by_variant[task["variant_id"]]
        root = output / "tasks" / task["key"]
        root.mkdir(exist_ok=False)
        registry = row.registry(environment, root / "environment")
        overlay_before = inventory(root / "environment")
        agent = ScriptedFactory(
            "agent", canonical_json({"action": row.overlay.trigger.model_dump()})
        )
        pair = None
        arguments: dict[str, Any]
        if task["level"] in {"A0", "A1"}:
            arguments = dict(agent_factory=agent, agent_execution=agent_config(pair_config()))
        else:
            pair = ShutdownPair(
                agent,
                cast(
                    Callable[[], LLMBackend],
                    DiagnosticFactory(ScriptedFactory("guard"), root / "guard_diagnostics.jsonl"),
                ),
                pair_config(),
            )
            arguments = {"pair": pair}
        try:
            result = run_pair_task(
                PublicWorkbenchTask.model_validate(row.task.model_dump()),
                output=root / "execution",
                registry_factory=lambda registry=registry: registry,
                security=configuration(task["level"]),
                runtime_config=RuntimeConfig(),
                generation=GenerationConfig(),
                source_catalog=fixture_catalog(row),
                **arguments,
            )
        finally:
            if pair is not None:
                pair.close()
        if inventory(root / "environment") != overlay_before:
            raise ValueError("task environment changed")
        write_receipt(
            root / "checkpoint.json",
            dict(
                protocol="grouped_dev_checkpoint_v1",
                identity_sha256=text_hash(canonical_json(manifest)),
                key=task["key"],
                terminal=result.result.status,
                raw_sha256=inventory(root),
            ),
        )
        saved.append(audit_checkpoint(root, manifest, task))
        print(f"{task['key']}: {result.result.status}", flush=True)
    current, _ = identity(release, environment, commit)
    if current != manifest:
        raise ValueError("grouped input changed during run")
    return dict(
        protocol=manifest["protocol"],
        shard=shard,
        completed=len(saved),
        expected=14,
        remaining=14 - len(saved),
        terminal_statuses=[r["terminal"] for r in saved],
        identity_sha256=text_hash(canonical_json(manifest)),
        native_model_runs=0,
        phase5_accepted=False,
        quality_scoring=False,
    )
