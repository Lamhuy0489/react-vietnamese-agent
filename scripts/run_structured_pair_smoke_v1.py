"""One fresh synthetic task through Qwen, Llama guard and the local Tool Broker."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.agent.context import ContextBuilder
from react_agent.broker.tool_broker import ToolBroker
from react_agent.llm.base import GenerationConfig
from react_agent.llm.http_diagnostic_v1 import HTTPSJSON, APIError
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend
from react_agent.logging.trace_logger import TraceLogger
from react_agent.parser.structured_parser import ParseError, StructuredParser
from react_agent.schemas.agent_output import FinalTurn
from react_agent.security_v1.guard import GuardInput, ModelGuard
from react_agent.serving.structured_api_v1 import canonical, sha
from react_agent.tools.calculator import CalculatorTool
from react_agent.tools.registry import ToolRegistry

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Task:
    task_id: str = "structured_pair_calc_v1"
    instruction: str = "Dùng calculator tính 23*7+5. Sau khi nhận kết quả, trả lời chỉ bằng số."


def save(path: Path, value: Any) -> None:
    with path.open("x") as stream:
        stream.write(canonical(value) + "\n")


def run(agent: StructuredHTTPBackend, guard_backend: StructuredHTTPBackend,
        output: Path) -> dict[str, Any]:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    logger = TraceLogger(output / "broker.jsonl")
    broker = ToolBroker(registry, logger)
    parser = StructuredParser(registry)
    context = ContextBuilder(registry.definitions())
    guard = ModelGuard(guard_backend)
    task = Task()
    history: list[tuple[str, str]] = []
    observations: list[dict[str, Any]] = []
    terminal, final, error = "max_steps", None, None
    for step in range(1, 4):
        try:
            response = agent.generate(context.build(task, history), GenerationConfig())
            turn = parser.parse(response.text)
            request = GuardInput(user_instruction=task.instruction,
                source_type="model_final" if isinstance(turn, FinalTurn) else "model_action",
                candidate_content=turn.final_answer.answer if isinstance(turn, FinalTurn) else None,
                candidate_action_json=None if isinstance(turn, FinalTurn)
                else canonical(turn.action.model_dump(mode="json")))
            verdict = guard.classify(request)
            observations.append({"turn": turn.model_dump(mode="json"),
                                 "guard": verdict.model_dump(mode="json")})
            # Diagnostic gate, not an A0/A2/A6 policy claim.
            if verdict.status != "OK" or verdict.result is None or verdict.result.risk != "SAFE":
                terminal = "guard_rejected"
                break
            if isinstance(turn, FinalTurn):
                terminal, final = "completed", turn.final_answer.answer
                break
            tool_result = broker.execute(turn.action.name, turn.action.arguments,
                                    run_id=output.name, task_id=task.task_id, step=step)
            history.append((turn.model_dump_json(), tool_result.model_dump_json()))
        except (APIError, ParseError) as exc:
            terminal, error = "error", exc.code
            break
    result = {"status": terminal, "error_code": error, "final_answer": final,
        "observations": observations, "agent_attempts": agent.attempts,
        "guard_attempts": guard_backend.attempts, "agent_calls": agent.calls,
        "guard_calls": guard_backend.calls, "broker_events": logger.as_dicts(),
        "diagnostic_pass": terminal == "completed" and final == "166" and len(history) == 1,
        "formal_benchmark": False, "phase5_accepted": False}
    save(output / "result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads((args.directory / "pair_endpoints.json").read_text())
    backends = {}
    metadata = {}
    for record in config["models"]:
        role = record["role"]
        saved = json.loads((args.directory / f"{role}_live_metadata.json").read_text())
        backend = StructuredHTTPBackend(HTTPSJSON(record["endpoint"], record["api_key"],
            timeout=150), model=record["id"], role=role, session_id=record["session_id"],
            source_commit=record["source_commit"], model_revision=record["model_revision"],
            worker_sha256=saved["worker_sha256"])
        metadata[role] = backend.probe()
        backends[role] = backend
    if set(backends) != {"agent", "guard"}:
        raise ValueError("exact agent/guard pair required")
    args.output.mkdir(parents=True, exist_ok=False)
    sources = {str(p.relative_to(ROOT)): sha(p.read_bytes())
               for p in (ROOT / "src/react_agent").rglob("*.py")}
    sources["scripts/run_structured_pair_smoke_v1.py"] = sha(Path(__file__).read_bytes())
    save(args.output / "declaration.json", {"task": vars(Task()), "sources": sources,
        "metadata": metadata, "agent_generation": GenerationConfig().model_dump(),
        "guard_generation": ModelGuard(backends["guard"]).generation.model_dump(),
        "held_out_test_loaded": False, "max_agent_calls": 3, "max_guard_calls": 3,
        "scope": "single integration diagnostic; no formal security/quality scores"})
    result = run(backends["agent"], backends["guard"], args.output)
    print(json.dumps({k: result[k] for k in ("status", "diagnostic_pass", "final_answer",
                                            "agent_attempts", "guard_attempts")}))


if __name__ == "__main__":
    main()
