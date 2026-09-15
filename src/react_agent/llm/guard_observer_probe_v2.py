"""Four synthetic runtime tasks with versioned observer joins and missing-only resume."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.document_runtime_probe_v1 import (
    CATALOG,
    GENERATION,
    RUNTIME,
    ProbeTask,
    inventory,
)
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_probe_v1 import TOLERANCE, PairObserver, validate_memory
from react_agent.llm.model_pair_v1 import ModelIdentity
from react_agent.llm.model_pair_v2 import ShutdownPairConfig
from react_agent.llm.native_guard_diagnostics_v2 import native_pair
from react_agent.llm.native_shutdown_v2 import native_config
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.document_pair_runtime_v1 import run_pair_task
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.guard_diagnostic_audit_v2 import audit as audit_join

PROFILE = "guard_observer_probe_v2"
SCHEDULE = ("CALC_A2", "CALC_A6", "DOC_A2", "DOC_A6")
SAFE = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'
MALFORMED = '{"risk":"SAFE","labels":[],"confidence":"HIGH",}'


def execution_sources() -> dict[str, str]:
    """Bind this rollout's code bytes even when the working tree is ahead of Git."""
    source = Path(__file__).resolve().parents[1]
    names = (
        "llm/guard_observer_probe_v2.py",
        "llm/native_guard_diagnostics_v2.py",
        "llm/guard_diagnostic_backend_v2.py",
        "llm/guard_diagnostic_pair_v2.py",
        "security_v1/guard_diagnostics_v2.py",
        "validation/guard_diagnostic_audit_v2.py",
    )
    return {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in names}


def case(key: str) -> tuple[ProbeTask, SourceCatalog, Level]:
    if key not in SCHEDULE:
        raise ValueError("known observer task required")
    level: Level = "A2" if key.endswith("A2") else "A6"
    instruction = (
        "Dùng calculator tính 17+25 rồi trả lời kết quả từ công cụ. Không đoán kết quả."
        if key.startswith("CALC")
        else "Đọc tài liệu công khai CDOC_034 bằng doc_read, rồi tóm tắt vị trí Lab Mạng. "
        "Chỉ trả lời sau khi đã đọc; không gửi email hoặc webhook."
    )
    return (
        ProbeTask(task_id="awb_observer_" + key.lower(), instruction=instruction),
        SourceCatalog() if key.startswith("CALC") else CATALOG,
        level,
    )


def config(backend: str) -> ShutdownPairConfig:
    if backend == "hf":
        return native_config()
    if backend != "stub":
        raise ValueError("known backend required")
    return ShutdownPairConfig(
        ModelIdentity("synthetic-agent", PROFILE),
        ModelIdentity("synthetic-guard", PROFILE),
        agent_start_seconds=10,
        guard_start_seconds=10,
        agent_call_seconds=5,
        guard_call_seconds=5,
    )


@dataclass(frozen=True)
class StubFactory:
    role: str
    key: str
    condition: str

    def __call__(self) -> StubBackend:
        return StubBackend(self)


class StubBackend:
    def __init__(self, factory: StubFactory) -> None:
        self.fixture, self.calls = factory, 0
        self.model_id, self.model_revision = "synthetic-" + factory.role, PROFILE

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.calls += 1
        if self.fixture.role == "guard":
            text = SAFE if self.fixture.condition == "valid" else MALFORMED
        elif self.calls == 1:
            text = (
                '{"action":{"name":"calculator","arguments":{"expression":"17+25"}}}'
                if self.fixture.key.startswith("CALC")
                else '{"action":{"name":"doc_read","arguments":{"doc_id":"CDOC_034"}}}'
            )
        else:
            # Public scripted output, not oracle-derived or a scored model answer.
            text = (
                '{"final_answer":{"answer":"42"}}'
                if self.fixture.key.startswith("CALC")
                else '{"final_answer":{"answer":"Đã đọc tài liệu công khai."}}'
            )
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)


def fixed_identity(backend: str, condition: str) -> dict[str, Any]:
    if condition not in {"valid", "trailing_comma"} or (backend == "hf" and condition != "valid"):
        raise ValueError("native output injection forbidden or unknown CPU condition")
    return dict(
        protocol=PROFILE,
        backend=backend,
        condition=condition,
        security_runtime_version="security_runtime_v8",
        schedule=list(SCHEDULE),
        cases={
            key: dict(
                task=case(key)[0].model_dump(mode="json"),
                catalog=case(key)[1].model_dump(mode="json"),
                security=configuration(case(key)[2]).model_dump(mode="json"),
            )
            for key in SCHEDULE
        },
        runtime=RUNTIME.model_dump(mode="json"),
        generation=GENERATION.model_dump(mode="json"),
        pair_config=asdict(config(backend)),
        automatic_retry=False,
        benchmark_tasks=0,
        test_tasks=0,
    )


def recovered(root: Path) -> bool:
    baseline = json.loads((root / "baseline.json").read_text())["memory"]
    samples = json.loads((root / "recovery.json").read_text())["memory"]
    if len(samples) != 6:
        raise ValueError("six recovery observations required")
    for sample in [baseline, *samples]:
        validate_memory(sample)
    return all(
        last["total_bytes"] == initial["total_bytes"]
        and last["free_bytes"] >= initial["free_bytes"] - TOLERANCE
        for last, initial in zip(samples[-1], baseline, strict=True)
    )


def checkpoint(root: Path) -> dict[str, Any]:
    before = inventory(root)
    value: dict[str, Any] = json.loads((root / "checkpoint.json").read_text())
    raw = dict(before)
    raw.pop("checkpoint.json")
    if value["raw_sha256"] != raw or value["key"] != root.name:
        raise ValueError("checkpoint hash/key mismatch")
    identity = json.loads((root.parent.parent / "identity.json").read_text())
    if (
        "execution_source_sha256" in identity
        and identity["execution_source_sha256"] != execution_sources()
    ):
        raise ValueError("checkpoint execution source changed")
    if any(
        identity.get(k) != v
        for k, v in fixed_identity(identity["backend"], identity["condition"]).items()
    ):
        raise ValueError("checkpoint protocol/input mismatch")
    task, catalog, level = case(root.name)
    receipt = json.loads((root / "execution/pair_runtime.json").read_text())
    metadata = json.loads((root / "execution/runtime/run_metadata.json").read_text())
    if (
        any(
            receipt[k] != v
            for k, v in dict(
                task_id=task.task_id,
                task_sha256=text_hash(task.instruction),
                pair_config=identity["pair_config"],
                security=configuration(level).model_dump(mode="json"),
                runtime_config=identity["runtime"],
                generation=identity["generation"],
                terminal=value["terminal"],
            ).items()
        )
        or metadata["source_catalog"] != catalog.model_dump(mode="json")
        or metadata["runtime_version"] != identity["security_runtime_version"]
    ):
        raise ValueError("checkpoint runtime binding mismatch")
    joined = audit_join(
        root / "execution", root / "native/guard_response_diagnostics.jsonl", root / "witness.jsonl"
    )
    if joined != json.loads((root / "join.json").read_text()) or value["recovered"] != recovered(
        root
    ):
        raise ValueError("checkpoint join/recovery mismatch")
    if inventory(root) != before:
        raise ValueError("checkpoint changed during audit")
    return value


def run(
    output: Path,
    environment: Path,
    *,
    backend: str,
    commit: str,
    observer_factory: Callable[[], PairObserver],
    condition: str = "valid",
    resume: bool = False,
    agent: Path | None = None,
    model_inventory: Path | None = None,
    guard: Path | None = None,
    snapshot: GuardSnapshot | None = None,
) -> dict[str, Any]:
    """A terminal semantic error is retained; partial attempts require explicit disposition."""
    for path in (output, environment):
        no_links(path)
    if output.resolve().is_relative_to(
        environment.resolve()
    ) or environment.resolve().is_relative_to(output.resolve()):
        raise ValueError("output/environment overlap")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("source commit required")
    identity = fixed_identity(backend, condition)
    native = (agent, model_inventory, guard, snapshot)
    if (backend == "hf" and any(v is None for v in native)) or (
        backend == "stub" and any(v is not None for v in native)
    ):
        raise ValueError("backend/native options mismatch")
    identity.update(
        source_commit=commit,
        execution_source_sha256=execution_sources(),
        environment_sha256=inventory(environment),
        snapshot_sha256=snapshot.sha256 if snapshot else None,
        model_inventory_sha256=hashlib.sha256(model_inventory.read_bytes()).hexdigest()
        if model_inventory
        else None,
    )
    if output.exists():
        if not resume or json.loads((output / "identity.json").read_text()) != identity:
            raise ValueError("fresh output or identical resume required")
    else:
        output.mkdir(parents=True)
        write_receipt(output / "identity.json", identity)
    tasks = output / "tasks"
    tasks.mkdir(exist_ok=True)
    if set(p.name for p in tasks.iterdir()) - set(SCHEDULE):
        raise ValueError("unexpected task checkpoint")
    # Check all existing records before launching any missing task, even when a
    # corrupt/partial directory is later in the schedule.
    for key in SCHEDULE:
        saved_root = tasks / key
        if saved_root.exists():
            if not (saved_root / "checkpoint.json").is_file():
                raise ValueError("partial attempt retained; no automatic retry")
            if not checkpoint(saved_root)["recovered"]:
                raise ValueError("unrecovered task; no automatic continuation")
    results = []
    for key in SCHEDULE:
        root = tasks / key
        if root.exists():
            if not (root / "checkpoint.json").is_file():
                raise ValueError("partial attempt retained; no automatic retry")
            saved = checkpoint(root)
            if not saved["recovered"]:
                raise ValueError("unrecovered task; no automatic continuation")
            results.append(saved)
            continue
        root.mkdir()
        observer = observer_factory()
        baseline = observer.sample("baseline")
        validate_memory(baseline)
        write_receipt(root / "baseline.json", {"memory": baseline})
        if backend == "hf":
            if agent is None or model_inventory is None or guard is None or snapshot is None:
                raise ValueError("native inputs missing")
            pair = native_pair(
                agent,
                model_inventory,
                guard,
                snapshot,
                root / "native",
                root / "attention",
                root / "policy",
                witness=root / "witness.jsonl",
            )
        else:
            pair = DiagnosticPair(
                StubFactory("agent", key, condition),
                cast(
                    Callable[[], LLMBackend],
                    DiagnosticFactory(
                        StubFactory("guard", key, condition),
                        root / "native/guard_response_diagnostics.jsonl",
                    ),
                ),
                config(backend),
                root / "witness.jsonl",
            )
        # Both factories are lazy. Native validation must see fresh roots; the
        # metrics directory must exist only when the workers actually start.
        (root / "native").mkdir()
        task, catalog, level = case(key)
        try:
            result = run_pair_task(
                task,
                output=root / "execution",
                registry_factory=lambda: build_clean_registry(environment),
                security=configuration(level),
                runtime_config=RUNTIME,
                generation=GENERATION,
                source_catalog=catalog,
                pair=pair,
            )
        finally:
            pair.close()
            samples = []
            for _ in range(6):
                if observer.interval:
                    time.sleep(observer.interval)
                sample = observer.sample("recovery")
                validate_memory(sample)
                samples.append(sample)
            write_receipt(root / "recovery.json", {"memory": samples})
        write_receipt(
            root / "join.json",
            audit_join(
                root / "execution",
                root / "native/guard_response_diagnostics.jsonl",
                root / "witness.jsonl",
            ),
        )
        write_receipt(
            root / "checkpoint.json",
            dict(
                key=key,
                terminal=result.result.status,
                recovered=recovered(root),
                raw_sha256=inventory(root),
            ),
        )
        saved = checkpoint(root)
        results.append(saved)
        if not saved["recovered"]:
            raise ValueError("unrecovered task; stop before starting next pair")
        print(f"{key}: {saved['terminal']}; recovered=True", flush=True)
    if (
        inventory(environment) != identity["environment_sha256"]
        or execution_sources() != identity["execution_source_sha256"]
    ):
        raise ValueError("environment or execution source changed during run")
    return dict(
        protocol=PROFILE,
        tasks=len(results),
        completed=sum(r["terminal"] == "completed" for r in results),
        model_errors=sum(r["terminal"] == "model_error" for r in results),
        guard_quality_validated=False,
        phase5_accepted=False,
    )
