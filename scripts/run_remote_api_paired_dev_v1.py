"""Pinned public Dev attack/benign differential via journaled structured APIs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from react_agent.adversarial_release import ReleasedFixture
from react_agent.agent.state import RuntimeConfig
from react_agent.llm.base import GenerationConfig
from react_agent.llm.session_journal_v1 import save_new
from react_agent.llm.structured_session_factory_v1 import StructuredSessionFactory
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.remote_api_runtime_v1 import RemoteAPIRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.serving.structured_api_v1 import canonical, sha
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog
from react_agent.validation.grouped_dev_plan_v1 import DEV_SHA256

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/adversarial/release_v2"
ENVIRONMENT = ROOT / "data/clean/v1_1/environment"
JOURNAL = ROOT / "build/evaluation/structured_api_sessions_v1"
FAMILIES = ("CAND_DATABASE", "CAND_QUOTED")
LEVELS: tuple[Level, ...] = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")


def selected() -> list[ReleasedFixture]:
    rows: dict[tuple[str, str], ReleasedFixture] = {}
    for branch in ("attack", "benign"):
        path = RELEASE / f"dev_{branch}.jsonl"
        raw = path.read_bytes()
        if sha(raw) != DEV_SHA256[path.name]:
            raise ValueError("frozen Dev hash mismatch")
        for line in raw.splitlines():
            row = ReleasedFixture.model_validate_json(line)
            if row.split != "dev" or row.branch != branch:
                raise ValueError("Dev-only branch required")
            if row.family_id in FAMILIES and row.variant_type == "paraphrase":
                key = (row.family_id, branch)
                if key in rows:
                    raise ValueError("duplicate pair")
                rows[key] = row
    result = [rows[(family, branch)] for family in FAMILIES for branch in ("attack", "benign")]
    if len(result) != 4:
        raise ValueError("exact two complete pairs required")
    for a, b in zip(result[::2], result[1::2], strict=True):
        if a.pair_id != b.pair_id or a.task != b.task or a.group_id != b.group_id:
            raise ValueError("matched pair identity mismatch")
    return result


def unresolved() -> bool:
    for started in JOURNAL.rglob("*.started.json"):
        finished = started.with_name(started.name.replace(".started.", ".finished."))
        try:
            if json.loads(finished.read_text()).get("state") != "response_received":
                return True
        except (OSError, ValueError):
            return True
    return False


def inventory(path: Path) -> dict[str, str]:
    return {str(p.relative_to(path)): sha(p.read_bytes()) for p in path.rglob("*") if p.is_file()}


def run(directory: Path, output: Path, *, resume: bool = False,
        max_new_conditions: int | None = None) -> dict[str, Any]:
    output = output.resolve()
    if not output.is_relative_to(ROOT / "build/evaluation") or output.is_symlink():
        raise ValueError("build/evaluation output required")
    if max_new_conditions is not None and max_new_conditions < 0:
        raise ValueError("nonnegative task budget required")
    rows = selected()
    schedule: list[dict[str, Any]] = [
        {"key": f"{row.variant_id}__{level}", "variant_id": row.variant_id,
        "family_id": row.family_id, "pair_id": row.pair_id, "branch": row.branch,
        "group_id": row.group_id, "level": level} for row in rows for level in LEVELS]
    factories = {role: StructuredSessionFactory.from_directory(directory, JOURNAL,
        "admission", role) for role in ("agent", "guard")}
    generation = GenerationConfig(max_new_tokens=512, temperature=0, seed=42)
    mechanics = RuntimeConfig(max_steps=4, max_format_retries_per_step=0)
    sources = {str(p.relative_to(ROOT)): sha(p.read_bytes())
               for p in (ROOT / "src/react_agent").rglob("*.py")}
    sources[str(Path(__file__).resolve().relative_to(ROOT))] = sha(Path(__file__).read_bytes())
    manifest = {"protocol": "remote_api_paired_dev_v1", "schedule": schedule,
        "source_kind": "working-tree", "source_sha256": sources,
        "public_dev_sha256": DEV_SHA256, "environment_sha256": inventory(ENVIRONMENT),
        "selected_public_sha256": {
            r.variant_id: sha(canonical(r.model_dump()).encode()) for r in rows},
        "identities": {role: factory.public_identity() for role, factory in factories.items()},
        "generation": generation.model_dump(), "runtime": mechanics.model_dump(),
        "evaluation_protocol_sha256": sha((Path(__file__).resolve().parents[1] /
            "docs/evaluation/remote_api_paired_dev_v1_protocol.md").read_bytes()),
        "evaluator_sha256": sha((Path(__file__).resolve().parent /
            "evaluate_remote_api_paired_dev_v1.py").read_bytes()),
        "guard_process_deadline_seconds": 180, "http_socket_timeout_seconds": 150,
        "test_payloads_loaded": 0, "private_ground_truth_loaded": 0,
        "phase5_accepted": False}
    if output.exists():
        if not resume or json.loads((output / "manifest.json").read_text()) != manifest:
            raise ValueError("resume requires exact source/input/session identity")
    else:
        output.mkdir(parents=True)
        save_new(output / "manifest.json", manifest)
        (output / "conditions").mkdir()
    completed = []
    pending = []
    for condition in schedule:
        root = output / "conditions" / condition["key"]
        terminal = root / "completed.json"
        if terminal.exists():
            saved = json.loads(terminal.read_text())
            if saved["condition"] != condition:
                raise ValueError("checkpoint identity mismatch")
            for name, expected in saved["artifact_sha256"].items():
                relative = Path(name)
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("unsafe checkpoint path")
                if sha((root / relative).read_bytes()) != expected:
                    raise ValueError("checkpoint artifact changed")
            completed.append(saved)
        elif root.exists():
            raise ValueError("started condition is uncertain; no automatic rerun")
        else:
            pending.append(condition)
    if not pending or max_new_conditions == 0:
        return {"completed": len(completed), "remaining": len(pending), "new_conditions": 0}
    if unresolved():
        raise ValueError("session journal has unresolved delivery")
    for factory in factories.values():
        factory()  # read-only probe; no inference
    by_variant = {r.variant_id: r for r in rows}
    new = 0
    for condition in pending:
        if unresolved() or (max_new_conditions is not None and new >= max_new_conditions):
            break
        row = by_variant[condition["variant_id"]]
        level: Level = condition["level"]
        root = output / "conditions" / condition["key"]
        root.mkdir()
        save_new(root / "started.json", {"condition": condition, "status": "started"})
        registry = row.registry(ENVIRONMENT, root / "environment")
        overlay_before = inventory(root / "environment")
        agent = StructuredSessionFactory.from_directory(directory, JOURNAL, row.task.task_id,
                                                         "agent")()
        guard = (StructuredSessionFactory.from_directory(directory, JOURNAL, row.task.task_id,
                                                        "guard") if level not in {"A0", "A1"}
                 else None)
        runtime = RemoteAPIRuntime(agent, registry, runtime_config=mechanics,
                                   generation_config=generation)
        result = runtime.run_instrumented(row.task, output=root / "execution",
            source_catalog=fixture_catalog(row), security_config=configuration(level),
            guard_factory=guard, guard_execution=WarmGuardConfig(
                guard.model_id, guard.model_revision, 180) if guard else None)
        if overlay_before != inventory(root / "environment"):
            raise ValueError("environment mutated during mock execution")
        metadata = json.loads((root / "execution/run_metadata.json").read_text())
        saved = {"condition": condition, "status": result.result.status,
            "final_answer": result.result.final_answer,
            "tool_sequence": result.result.tool_sequence,
            "agent_attempts": agent.attempts, "agent_calls": agent.calls,
            "guard_attempts": metadata["guard_execution_attempt_count"],
            "guard_classifications": metadata["guard_classification_count"],
            "artifact_sha256": inventory(root), "remote_delivery_uncertain": unresolved()}
        save_new(root / "completed.json", saved)
        completed.append(saved)
        new += 1
        print(canonical({"key": condition["key"], "status": saved["status"],
            "agent_attempts": agent.attempts, "guard_attempts": saved["guard_attempts"]}),
            flush=True)
    summary = {"completed": len(completed), "remaining": len(schedule)-len(completed),
               "new_conditions": new, "remote_delivery_uncertain": unresolved(),
               "phase5_accepted": False}
    save_new(output / f"progress_{len(completed):03d}.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-new-conditions", type=int)
    args = parser.parse_args()
    print(canonical(run(args.directory, args.output, resume=args.resume,
                        max_new_conditions=args.max_new_conditions)))


if __name__ == "__main__":
    main()
