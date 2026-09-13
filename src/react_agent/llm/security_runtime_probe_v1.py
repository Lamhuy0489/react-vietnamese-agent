"""Seven-level public synthetic runtime probe, with immutable task checkpoints."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_probe_v1 import TOLERANCE, PairObserver, validate_memory
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig
from react_agent.llm.native_agent_only_v1 import native_agent
from react_agent.llm.ordinary_pair_probe_v1 import native_config, native_pair
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.pair_runtime_v2 import run_pair_task
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.pair_runtime_audit_v2 import audit_task

LEVELS: tuple[Level, ...] = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")


class ProbeTask(BaseModel):
    """Only public runtime fields; no benchmark authoring/evaluator dependency."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    task_id: str
    instruction: str


TASK = ProbeTask(
    task_id="awb_runtimecalculator",
    instruction="Dùng công cụ calculator để tính 17 * 23, sau đó trả lời kết quả bằng tiếng Việt.",
)
RUNTIME = RuntimeConfig(max_steps=3, max_format_retries_per_step=0)
GENERATION = GenerationConfig()


def inventory(root: Path) -> dict[str, str]:
    no_links(root)
    result = {}
    for path in sorted(root.rglob("*")):
        no_links(path)
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return result


@dataclass(frozen=True)
class StubFactory:
    role: str

    def __call__(self) -> StubBackend:
        return StubBackend(self.role)


class StubBackend:
    def __init__(self, role: str) -> None:
        self.role, self.calls = role, 0
        self.model_id, self.model_revision = "synthetic-" + role, "runtime_probe_v1"

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        # Technical public fixture only, never constructed from an evaluator answer.
        self.calls += 1
        if self.role == "guard":
            text = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'
        elif self.calls == 1:
            text = '{"action":{"name":"calculator","arguments":{"expression":"17 * 23"}}}'
        else:
            text = '{"final_answer":{"answer":"Kết quả là 391."}}'
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)


def config(backend: str) -> PairConfig:
    if backend == "hf":
        return native_config()
    if backend != "stub":
        raise ValueError("known backend required")
    return PairConfig(
        ModelIdentity("synthetic-agent", "runtime_probe_v1"),
        ModelIdentity("synthetic-guard", "runtime_probe_v1"),
        agent_start_seconds=10,
        guard_start_seconds=10,
        agent_call_seconds=5,
        guard_call_seconds=5,
    )


def checkpoint(root: Path) -> dict[str, Any]:
    value: dict[str, Any] = json.loads((root / "checkpoint.json").read_text())
    actual = inventory(root)
    actual.pop("checkpoint.json")
    if actual != value["raw_sha256"]:
        raise ValueError("checkpoint raw hashes differ")
    audit_task(root / "execution")
    identity = json.loads((root.parent.parent / "identity.json").read_text())
    receipt = json.loads((root / "execution/pair_runtime.json").read_text())
    if value["level"] != root.name or any(
        receipt[key] != expected
        for key, expected in {
            "task_sha256": identity["task_sha256"],
            "generation": identity["generation"],
            "runtime_config": identity["runtime"],
            "security": identity["security"][root.name],
            "terminal": value["terminal"],
        }.items()
    ):
        raise ValueError("checkpoint input/terminal binding mismatch")
    return value


def run(
    output: Path,
    environment: Path,
    *,
    backend: str,
    commit: str,
    observer_factory: Callable[[], PairObserver],
    resume: bool = False,
    agent: Path | None = None,
    model_inventory: Path | None = None,
    guard: Path | None = None,
    snapshot: GuardSnapshot | None = None,
) -> dict[str, Any]:
    """Never retry a terminal/partial attempt; resume only wholly missing levels."""
    no_links(output)
    no_links(environment)
    if output.resolve().is_relative_to(
        environment.resolve()
    ) or environment.resolve().is_relative_to(output.resolve()):
        raise ValueError("output/environment overlap")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("source commit required")
    native = (agent, model_inventory, guard, snapshot)
    if (backend == "hf" and any(v is None for v in native)) or (
        backend == "stub" and any(v is not None for v in native)
    ):
        raise ValueError("backend/native options mismatch")
    pair_config = config(backend)
    # Agent-only v2 currently has one deadline. Name this limitation in the identity.
    agent_execution = pair_config.execution("agent", cold=True)
    identity = dict(
        protocol="security_runtime_probe_v1",
        backend=backend,
        source_commit=commit,
        levels=list(LEVELS),
        task=TASK.model_dump(mode="json"),
        task_sha256=text_hash(TASK.instruction),
        runtime=RUNTIME.model_dump(),
        generation=GENERATION.model_dump(),
        pair_config=asdict(pair_config),
        agent_only_execution=asdict(agent_execution),
        source_catalog=SourceCatalog().model_dump(mode="json"),
        security={level: configuration(level).model_dump(mode="json") for level in LEVELS},
        environment_sha256=inventory(environment),
        snapshot_sha256=snapshot.sha256 if snapshot else None,
        model_inventory_sha256=hashlib.sha256(model_inventory.read_bytes()).hexdigest()
        if model_inventory
        else None,
        automatic_retry=False,
        benchmark_tasks=0,
        test_tasks=0,
    )
    if output.exists():
        if not resume or json.loads((output / "identity.json").read_text()) != identity:
            raise ValueError("resume identity mismatch or fresh output required")
    else:
        output.mkdir(parents=True)
        write_receipt(output / "identity.json", identity)
    tasks = output / "tasks"
    tasks.mkdir(exist_ok=True)
    if set(p.name for p in tasks.iterdir()) - set(LEVELS):
        raise ValueError("unexpected task checkpoint")
    results = []
    for level in LEVELS:
        root = tasks / level
        if root.exists():
            if not (root / "checkpoint.json").is_file():
                raise ValueError("partial attempt retained; no automatic retry")
            saved = checkpoint(root)
            if saved["level"] != level:
                raise ValueError("checkpoint level mismatch")
            if not saved["recovered"]:
                raise ValueError("unrecovered completed task; no automatic continuation")
            results.append(saved["terminal"])
            continue
        root.mkdir()
        observer = observer_factory()
        baseline = observer.sample("baseline")
        validate_memory(baseline)
        write_receipt(root / "baseline.json", {"memory": baseline})
        arguments: dict[str, Any]
        if backend == "hf":
            if agent is None or model_inventory is None or guard is None or snapshot is None:
                raise ValueError("native inputs missing")
            if int(level[1:]) >= 2:
                arguments = {
                    "pair": native_pair(
                        agent,
                        model_inventory,
                        guard,
                        snapshot,
                        root / "native",
                        root / "attention",
                        root / "policy",
                    )
                }
            else:
                arguments = dict(
                    agent_factory=native_agent(
                        agent,
                        model_inventory,
                        root / "native/agent_hf_metrics.jsonl",
                        root / "attention/agent",
                        root / "policy/agent",
                    ),
                    agent_execution=agent_execution,
                )
        elif int(level[1:]) >= 2:
            arguments = {"pair": ModelPair(StubFactory("agent"), StubFactory("guard"), pair_config)}
        else:
            arguments = dict(agent_factory=StubFactory("agent"), agent_execution=agent_execution)
        try:
            if backend == "hf":
                # Frozen native loaders require an existing metrics parent.
                # Create it only after native_pair has validated fresh roots.
                (root / "native").mkdir()
            result = run_pair_task(
                TASK,
                output=root / "execution",
                registry_factory=lambda: build_clean_registry(environment),
                security=configuration(level),
                runtime_config=RUNTIME,
                generation=GENERATION,
                source_catalog=SourceCatalog(),
                **arguments,
            )
        finally:
            # run_pair_task owns worker cleanup; always retain subsequent memory observations.
            if "pair" in arguments:
                arguments["pair"].close()
            samples = []
            for _ in range(6):
                if observer.interval:
                    time.sleep(observer.interval)
                sample = observer.sample("recovery")
                validate_memory(sample)
                samples.append(sample)
            write_receipt(root / "recovery.json", {"memory": samples})
        audit_task(root / "execution")
        recovered = all(
            last["total_bytes"] == initial["total_bytes"]
            and last["free_bytes"] >= initial["free_bytes"] - TOLERANCE
            for last, initial in zip(samples[-1], baseline, strict=True)
        )
        write_receipt(
            root / "checkpoint.json",
            dict(
                level=level,
                terminal=result.result.status,
                recovered=recovered,
                raw_sha256=inventory(root),
            ),
        )
        results.append(result.result.status)
        print(f"{level}: {result.result.status}; recovered={recovered}", flush=True)
        if not recovered:
            raise RuntimeError("GPU memory did not recover; stop before next model load")
    if inventory(environment) != identity["environment_sha256"]:
        raise ValueError("environment changed")
    return dict(
        protocol="security_runtime_probe_v1",
        levels=7,
        terminals=results,
        phase5_accepted=False,
        native_quality_validated=False,
    )
