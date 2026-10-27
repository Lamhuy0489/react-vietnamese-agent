"""One declared synthetic Plan/guard integration; no benchmark or A6 acceptance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from run_phase5_field_reference_v1 import USER, new_session

from react_agent.llm.base import GenerationConfig
from react_agent.llm.http_diagnostic_v1 import HTTPSJSON
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend
from react_agent.llm.structured_plan_http_v1 import StructuredPlanHTTPBackend, plan_schema
from react_agent.logging.trace_logger import TraceLogger
from react_agent.prototypes.field_model_bridge_v1 import run_selection
from react_agent.prototypes.field_reference_v1 import Plan
from react_agent.security_v1.guard import GuardInput, ModelGuard
from react_agent.serving.structured_api_v1 import canonical, sha

ROOT = Path(__file__).resolve().parents[1]


def save(path: Path, value: Any) -> None:
    with path.open("x") as stream:
        stream.write(canonical(value) + "\n")


def run(agent: StructuredPlanHTTPBackend, guard_backend: StructuredHTTPBackend,
        output: Path) -> dict[str, Any]:
    logger = TraceLogger(output / "broker.jsonl")
    session = new_session("prose", "structured_plan_diagnostic_v1", logger)
    guard = ModelGuard(guard_backend)
    verdicts: list[dict[str, Any]] = []

    def veto(plan: Plan) -> bool:
        # Diagnostic guard sees the proposed typed Plan. The host renderer still
        # independently verifies source/hash/grant/sensitivity; SAFE is no grant.
        outcome = guard.classify(GuardInput(user_instruction=USER,
            source_type="model_field_plan", candidate_content=plan.model_dump_json()))
        verdicts.append(outcome.model_dump(mode="json"))
        return (outcome.status == "OK" and outcome.result is not None
                and outcome.result.risk == "SAFE")

    save(output / "started.json", {"status": "started", "no_automatic_retry": True})
    result = run_selection(session, agent, USER, GenerationConfig(max_new_tokens=1024),
        expected_model=agent.model_id, expected_revision=agent.model_revision, final_veto=veto)
    value = {"status": "completed", "bridge": result.model_dump(mode="json"),
        "guard_outcomes": verdicts, "agent_attempts": agent.attempts,
        "guard_attempts": guard_backend.attempts, "agent_calls": agent.calls,
        "guard_calls": guard_backend.calls, "broker_event_count": len(logger.events),
        "formal_benchmark": False, "phase5_accepted": False,
        "scope": "one synthetic Plan -> diagnostic guard veto -> host field rendering"}
    save(output / "result.json", value)
    save(output / "artifact_sha256.json", {p.name: sha(p.read_bytes())
        for p in output.iterdir() if p.is_file()})
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "build/evaluation") or output.exists():
        raise ValueError("fresh build/evaluation output required; no retry/resume")
    config = json.loads((args.directory / "pair_endpoints.json").read_text())
    backends: dict[str, StructuredHTTPBackend] = {}
    metadata = {}
    for record in config["models"]:
        role = record["role"]
        if role not in {"agent", "guard"} or role in backends:
            raise ValueError("exact unique agent/guard pair required")
        saved = json.loads((args.directory / f"{role}_live_metadata.json").read_text())
        cls = StructuredPlanHTTPBackend if role == "agent" else StructuredHTTPBackend
        backend = cls(HTTPSJSON(record["endpoint"], record["api_key"], timeout=150),
            model=record["id"], role=role, session_id=record["session_id"],
            source_commit=record["source_commit"], model_revision=record["model_revision"],
            worker_sha256=saved["worker_sha256"])
        metadata[role] = backend.probe()
        backends[role] = backend
    if set(backends) != {"agent", "guard"}:
        raise ValueError("exact pair required")
    agent = backends["agent"]
    if not isinstance(agent, StructuredPlanHTTPBackend):
        raise ValueError("explicit Plan backend required")
    output.mkdir(parents=True, exist_ok=False)
    sources = {str(p.relative_to(ROOT)): sha(p.read_bytes())
               for p in (ROOT / "src/react_agent").rglob("*.py")}
    for name in ("run_structured_plan_diagnostic_v1.py", "run_phase5_field_reference_v1.py"):
        path = ROOT / "scripts" / name
        sources[str(path.relative_to(ROOT))] = sha(path.read_bytes())
    save(output / "declaration.json", {"source_kind": "working-tree", "sources": sources,
        "metadata": metadata, "task_id": "field_reference_component", "fixture": "prose",
        "raw_user": USER, "schema": plan_schema(), "max_agent_calls": 1, "max_guard_calls": 1,
        "generation": GenerationConfig(max_new_tokens=1024).model_dump(),
        "guard_generation": ModelGuard(backends["guard"]).generation.model_dump(),
        "test_oracle_loaded": False, "semantic_retry": False, "acceptance_claim": False})
    result = run(agent, backends["guard"], output)
    print(canonical({"status": result["status"], "allowed": result["bridge"]["decision"]["allowed"],
        "reason": result["bridge"]["decision"]["reason"],
        "agent_attempts": result["agent_attempts"], "guard_attempts": result["guard_attempts"]}))


if __name__ == "__main__":
    main()
