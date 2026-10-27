"""Fourteen predeclared mainline Dev conditions with real agent/guard APIs."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, cast

from run_encoded_final_api_v2 import (
    checked_artifact,
    checkpoint_sha256,
    reject_symlink_components,
)
from run_remote_gate_controls_v1 import environment, fixture, inventory, unresolved

from react_agent.agent.state import RuntimeConfig
from react_agent.llm.base import GenerationConfig
from react_agent.llm.session_journal_v1 import save_new
from react_agent.llm.structured_session_factory_v1 import StructuredSessionFactory
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.phase5_runtime import Phase5Runtime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.serving.structured_api_v1 import canonical, sha
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "build/evaluation/structured_api_sessions_v1"
CASES = ("literal_safe", "email_safe")
LEVELS: tuple[Level, ...] = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")
PROTOCOL = "docs/evaluation/phase5_mainline_protocol.md"
EVALUATOR = "scripts/evaluate_phase5_mainline.py"


def run(directory: Path, output: Path, *, resume: bool = False,
        max_new_conditions: int | None = None) -> dict[str, Any]:
    reject_symlink_components(output)
    output = output.resolve()
    if not output.is_relative_to(ROOT / "build/evaluation"):
        raise ValueError("build/evaluation output required")
    if max_new_conditions is not None and max_new_conditions < 0:
        raise ValueError("nonnegative condition budget required")
    schedule = [{"key": f"{case}__{level}", "case": case, "level": level}
                for case in CASES for level in LEVELS]
    factories = {role: StructuredSessionFactory.from_directory(directory, JOURNAL,
        "admission", role) for role in ("agent", "guard")}
    generation = GenerationConfig(max_new_tokens=512, temperature=0, seed=42)
    mechanics = RuntimeConfig(max_steps=4, max_format_retries_per_step=0)
    paths = sorted((ROOT / "src/react_agent").rglob("*.py")) + [ROOT / name for name in (
        "scripts/run_phase5_mainline.py", EVALUATOR, "scripts/run_encoded_final_api_v2.py",
        "scripts/run_remote_gate_controls_v1.py", "scripts/evaluate_remote_gate_controls_v1.py")]
    sources = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}
    manifest = {"protocol": "phase5_mainline_dev", "schedule": schedule,
        "source_kind": "working-tree", "source_sha256": sources,
        "git_base": subprocess.check_output(  # noqa: S603 - fixed read-only command
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "environment_sha256": inventory(ROOT / "data/smoke"),
        "identities": {role: f.public_identity() for role, f in factories.items()},
        "connection_sha256": {role: f.connection_sha256 for role, f in factories.items()},
        "metadata_sha256": {role: f.metadata_sha256 for role, f in factories.items()},
        "fixtures": {case: {"task": task.model_dump(), "catalog": catalog.model_dump(mode="json")}
                     for case in CASES for task, catalog, _ in (fixture(case),)},
        "generation": generation.model_dump(), "runtime": mechanics.model_dump(),
        "configurations": {level: configuration(level).model_dump(mode="json") for level in LEVELS},
        "guard_generation": {"max_new_tokens": 128, "temperature": 0, "seed": 42},
        "agent_backend": "native_qwen_api", "guard_backend": "native_llama_api",
        "protocol_sha256": sha((ROOT / PROTOCOL).read_bytes()),
        "evaluator_sha256": sha((ROOT / EVALUATOR).read_bytes()),
        "http_timeout_seconds": 150, "guard_process_deadline_seconds": 180,
        "test_payloads_loaded": 0, "private_ground_truth_loaded": 0,
        "phase5_accepted": False}
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
    complete, pending = [], []
    for condition in schedule:
        folder = output / "conditions" / condition["key"]
        reject_symlink_components(folder)
        terminal = folder / "completed.json"
        if terminal.exists():
            saved = json.loads(terminal.read_text())
            if (saved["condition"] != condition
                    or saved.get("checkpoint_sha256") != checkpoint_sha256(saved)):
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
        bound = {role: StructuredSessionFactory.from_directory(directory, JOURNAL,
                 task.task_id, role) for role in factories}
        for role, factory in bound.items():
            if (factory.public_identity() != factories[role].public_identity()
                    or factory.connection_sha256 != factories[role].connection_sha256
                    or factory.metadata_sha256 != factories[role].metadata_sha256):
                raise ValueError("worker identity changed during run")
        folder = output / "conditions" / condition["key"]
        folder.mkdir()
        save_new(folder / "started.json", {"condition": condition, "status": "started"})
        environment(folder / "environment")
        before = inventory(folder / "environment")
        agent = bound["agent"]()
        guard = bound["guard"] if configuration(level).llm_guard else None
        runtime = Phase5Runtime(agent, build_smoke_registry(folder / "environment"),
                                 runtime_config=mechanics, generation_config=generation)
        result = runtime.run_instrumented(task, output=folder / "execution",
            source_catalog=catalog, security_config=configuration(level), guard_factory=guard,
            guard_execution=WarmGuardConfig(guard.model_id, guard.model_revision, 180)
            if guard else None)
        if before != inventory(folder / "environment"):
            raise ValueError("environment mutated")
        metadata = json.loads((folder / "execution/run_metadata.json").read_text())
        saved = {"condition": condition, "status": result.result.status,
            "final_answer": result.result.final_answer, "agent_api_attempts": agent.attempts,
            "agent_calls": agent.calls, "guard_attempts": metadata["guard_execution_attempt_count"],
            "local_cleanup": metadata["guard_lifecycle_events"],
            "remote_delivery_uncertain": unresolved(), "artifact_sha256": inventory(folder)}
        saved["checkpoint_sha256"] = checkpoint_sha256(saved)
        save_new(folder / "completed.json", saved)
        complete.append(saved)
        new += 1
        print(canonical({"condition": condition, "status": saved["status"],
                         "agent_attempts": agent.attempts,
                         "guard_attempts": saved["guard_attempts"]}), flush=True)
    summary = {"completed": len(complete), "remaining": len(schedule) - len(complete),
               "new_conditions": new, "remote_delivery_uncertain": unresolved(),
               "phase5_accepted": False}
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
    print(canonical(run(args.directory, args.output, resume=args.resume,
                        max_new_conditions=args.max_new_conditions)))
