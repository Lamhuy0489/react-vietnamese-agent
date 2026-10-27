"""Versioned native closure runner; immutable inputs and missing-only resume."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

from run_encoded_final_api_v2 import (
    checked_artifact,
    checkpoint_sha256,
    reject_symlink_components,
)
from run_phase5_native_closure_cpu_admission_v1 import inventory
from run_phase5_native_closure_v1 import ALL_CASES, environment, fixture

from react_agent.agent.state import RuntimeConfig
from react_agent.llm.base import GenerationConfig
from react_agent.llm.request_worker_runtime_v1 import RequestWorkerSessionFactory
from react_agent.llm.session_journal_v1 import save_new
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.phase5_closure_runtime_v1 import (
    RUNTIME_FAMILY,
    RUNTIME_VERSION,
    Phase5ClosureRuntime,
)
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.serving.structured_api_v1 import canonical, sha
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "build/evaluation/request_worker_sessions_closure_v2"
CASES = ALL_CASES
LEVELS: tuple[Level, ...] = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")
PROTOCOL = "docs/evaluation/phase5_native_closure_protocol_v2.md"
EVALUATOR = "scripts/evaluate_phase5_native_observations_v2.py"


def environment_identity() -> dict[str, str]:
    """Freeze actual constructed synthetic inputs, not only the smoke seed files."""
    with tempfile.TemporaryDirectory(prefix="closure-environment-") as tmp:
        folder = Path(tmp) / "environment"
        environment(folder)
        return inventory(folder)


def unresolved() -> bool:
    """Any missing/uncertain v3 receipt blocks later work; never repair it here."""
    for started in JOURNAL.rglob("*.started.json"):
        finished = started.with_name(started.name.replace(".started.", ".finished."))
        recovered = started.with_name(started.name.replace(".started.", ".recovered."))
        try:
            reject_symlink_components(started)
            reject_symlink_components(finished)
            initial = json.loads(started.read_text())
            terminal = json.loads(finished.read_text())
            if terminal.get("state") == "uncertain" and recovered.exists():
                reject_symlink_components(recovered)
                terminal = json.loads(recovered.read_text())
            if terminal.get("state") not in {"response_received", "recovered"} or any(
                terminal.get(k) != initial.get(k)
                for k in ("identity", "request_id", "request_sha256", "task_id")
            ):
                return True
        except (OSError, ValueError):
            return True
    return False


def run(
    directory: Path, output: Path, *, resume: bool = False, max_new_conditions: int | None = None
) -> dict[str, Any]:
    reject_symlink_components(output)
    output = output.resolve()
    if not output.is_relative_to(ROOT / "build/evaluation"):
        raise ValueError("build/evaluation output required")
    if max_new_conditions is not None and max_new_conditions < 0:
        raise ValueError("nonnegative condition budget required")
    schedule = [
        {"key": f"{case}__{level}", "case": case, "level": level}
        for case in CASES
        for level in LEVELS
    ]
    factories = {
        role: RequestWorkerSessionFactory.from_directory(
            directory, JOURNAL, "admission", role, timeout_seconds=150
        )
        for role in ("agent", "guard")
    }
    generation = GenerationConfig(max_new_tokens=512, temperature=0, seed=42)
    mechanics = RuntimeConfig(max_steps=4, max_format_retries_per_step=0)
    paths = sorted((ROOT / "src/react_agent").rglob("*.py")) + [
        ROOT / name
        for name in (
            "scripts/run_phase5_native_closure_v2.py",
            EVALUATOR,
            "scripts/run_phase5_native_closure_v1.py",
            "scripts/run_phase5_native_closure_cpu_admission_v1.py",
            "scripts/run_phase5_mainline.py",
            "scripts/evaluate_phase5_acceptance_v1.py",
            "scripts/evaluate_phase5_native_closure_controls_v1.py",
            "scripts/run_encoded_final_api_v2.py",
            "scripts/run_remote_gate_controls_v1.py",
            "scripts/evaluate_remote_gate_controls_v1.py",
        )
    ]
    sources = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}
    manifest: dict[str, Any] = {
        "protocol": "phase5_native_closure_v2",
        "closure_runtime_family": RUNTIME_FAMILY,
        "closure_runtime_version": RUNTIME_VERSION,
        "schedule": schedule,
        "source_kind": "working-tree",
        "source_sha256": sources,
        "git_base": subprocess.check_output(  # noqa: S603 - fixed read-only command
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=ROOT,
            text=True,
        ).strip(),
        "environment_sha256": inventory(ROOT / "data/smoke"),
        "identities": {role: f.public_identity() for role, f in factories.items()},
        "connection_sha256": {role: f.connection_sha256 for role, f in factories.items()},
        "metadata_sha256": {role: f.metadata_sha256 for role, f in factories.items()},
        "fixtures": {
            case: {"task": task.model_dump(), "catalog": catalog.model_dump(mode="json")}
            for case in CASES
            for task, catalog, _ in (fixture(case),)
        },
        "generation": generation.model_dump(),
        "runtime": mechanics.model_dump(),
        "configurations": {level: configuration(level).model_dump(mode="json") for level in LEVELS},
        "guard_generation": {"max_new_tokens": 128, "temperature": 0, "seed": 42},
        "agent_backend": "native_qwen_api",
        "guard_backend": "native_llama_api",
        "protocol_sha256": sha((ROOT / PROTOCOL).read_bytes()),
        "evaluator_sha256": sha((ROOT / EVALUATOR).read_bytes()),
        "http_timeout_seconds": 150,
        "guard_process_deadline_seconds": 180,
        "test_payloads_loaded": 0,
        "private_ground_truth_loaded": 0,
        "phase5_accepted": False,
    }
    environment_digest = environment_identity()
    manifest["prepared_environment_sha256"] = environment_digest
    if output.exists():
        if not resume or json.loads((output / "manifest.json").read_text()) != manifest:
            raise ValueError("resume requires exact source/input/session identity")
    else:
        output.mkdir(parents=True)
        save_new(output / "manifest.json", manifest)
        (output / "conditions").mkdir()
        # Retain the exact source bytes so later code changes do not erase evidence.
        for name in sources:
            destination = output / "source_snapshot" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / name).read_bytes())
        destination = output / "source_snapshot" / PROTOCOL
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / PROTOCOL).read_bytes())
    for name, expected in sources.items():
        checked_artifact(output / "source_snapshot", name, expected)
    checked_artifact(output / "source_snapshot", PROTOCOL, manifest["protocol_sha256"])
    complete, pending = [], []
    for condition in schedule:
        folder = output / "conditions" / condition["key"]
        reject_symlink_components(folder)
        terminal = folder / "completed.json"
        if terminal.exists():
            saved = json.loads(terminal.read_text())
            if saved["condition"] != condition or saved.get(
                "checkpoint_sha256"
            ) != checkpoint_sha256(saved):
                raise ValueError("checkpoint identity/hash mismatch")
            for name, digest in saved["artifact_sha256"].items():
                checked_artifact(folder, name, digest)
            complete.append(saved)
        elif folder.exists():
            raise ValueError("started-only condition; no automatic retry")
        else:
            pending.append(condition)
    if not pending or max_new_conditions == 0:
        return {"completed": len(complete), "remaining": len(pending), "new_conditions": 0}
    if unresolved():
        raise ValueError("shared journal has unresolved delivery")
    for factory in factories.values():
        factory()  # Authenticated read-only health and exact identity check.
    new = 0
    for condition in pending:
        if unresolved() or (max_new_conditions is not None and new >= max_new_conditions):
            break
        level = cast(Level, condition["level"])
        task, catalog, _ = fixture(condition["case"])
        bound = {
            role: RequestWorkerSessionFactory.from_directory(
                directory, JOURNAL, task.task_id, role, timeout_seconds=150
            )
            for role in factories
        }
        for role, factory in bound.items():
            if (
                factory.public_identity() != factories[role].public_identity()
                or factory.connection_sha256 != factories[role].connection_sha256
                or factory.metadata_sha256 != factories[role].metadata_sha256
            ):
                raise ValueError("worker identity changed during run")
        folder = output / "conditions" / condition["key"]
        folder.mkdir()
        save_new(
            folder / "started.json",
            {
                "condition": condition,
                "status": "started",
                "manifest_sha256": sha((output / "manifest.json").read_bytes()),
            },
        )
        environment(folder / "environment")
        before = inventory(folder / "environment")
        if before != environment_digest:
            raise ValueError("prepared environment differs from pre-request manifest")
        agent = bound["agent"]()
        guard = bound["guard"] if configuration(level).llm_guard else None
        runtime = Phase5ClosureRuntime(
            agent,
            build_smoke_registry(folder / "environment"),
            runtime_config=mechanics,
            generation_config=generation,
        )
        result = runtime.run_instrumented(
            task,
            output=folder / "execution",
            source_catalog=catalog,
            security_config=configuration(level),
            guard_factory=guard,
            guard_execution=WarmGuardConfig(guard.model_id, guard.model_revision, 180)
            if guard
            else None,
        )
        if before != inventory(folder / "environment"):
            raise ValueError("environment mutated")
        metadata_path = folder / "execution/run_metadata.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["native_transport"] = {
            "profile": "react-vn-request-lifecycle-v3-candidate",
            "identities": manifest["identities"],
            "guard_lifecycle_scope": "host_http_process_only",
            "remote_shutdown_proven": False,
        }
        metadata_path.write_text(canonical(metadata) + "\n")
        saved = {
            "condition": condition,
            "status": result.result.status,
            "final_answer": result.result.final_answer,
            "agent_api_attempts": agent.attempts,
            "agent_calls": agent.calls,
            "guard_attempts": metadata["guard_execution_attempt_count"],
            "local_cleanup": metadata["guard_lifecycle_events"],
            "worker_identities": manifest["identities"],
            "remote_delivery_uncertain": unresolved(),
            "artifact_sha256": inventory(folder),
        }
        saved["checkpoint_sha256"] = checkpoint_sha256(saved)
        save_new(folder / "completed.json", saved)
        complete.append(saved)
        new += 1
        print(
            canonical(
                {
                    "condition": condition,
                    "status": saved["status"],
                    "agent_attempts": agent.attempts,
                    "guard_attempts": saved["guard_attempts"],
                }
            ),
            flush=True,
        )
    summary = {
        "completed": len(complete),
        "remaining": len(schedule) - len(complete),
        "new_conditions": new,
        "remote_delivery_uncertain": unresolved(),
        "phase5_accepted": False,
    }
    if new:
        save_new(output / f"progress_{len(complete):03d}.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-new-conditions", type=int)
    args = parser.parse_args()
    print(
        canonical(
            run(
                args.directory,
                args.output,
                resume=args.resume,
                max_new_conditions=args.max_new_conditions,
            )
        )
    )
