#!/usr/bin/env python3
"""Run the 20 A0 smoke tasks against a vLLM endpoint with per-task checkpoint/resume.

Endpoint URL and key come from VLLM_BASE_URL / VLLM_API_KEY, never from arguments.
Tasks that end with an infrastructure error are not checkpointed and rerun on resume.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from react_agent.agent import AgentRuntime
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.llm.http_diagnostic_v1 import HTTPSJSON
from react_agent.llm.openai_compat_v1 import OpenAICompatBackend
from react_agent.schemas.task import SmokeTask
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "smoke"
MAX_CONSECUTIVE_INFRA = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--revision", help="override the pinned revision in the config")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=150)
    return parser.parse_args()


def task_succeeded(task: SmokeTask, status: str, sequence: list[str], answer: str) -> bool:
    facts = all(f.casefold() in answer.casefold() for f in task.expected.required_answer_facts)
    return status == "completed" and sequence in task.expected.acceptable_tool_sequences and facts


def load_done(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return {row["task_id"]: row for row in rows}


def main() -> int:
    args = parse_args()
    spec = yaml.safe_load((ROOT / "configs/models/backbones_v2.yaml").read_text())[args.model_key]
    revision = args.revision or spec["revision"]
    if not revision:
        raise SystemExit("Pin the revision in configs/models/backbones_v2.yaml or pass --revision")
    base_url, api_key = os.environ.get("VLLM_BASE_URL"), os.environ.get("VLLM_API_KEY")
    if not base_url or not api_key:
        raise SystemExit("Set VLLM_BASE_URL (https://.../v1) and VLLM_API_KEY")
    if not (DATA_ROOT / "database" / "university.db").is_file():
        raise SystemExit("Run scripts/build_smoke_environment.py first.")

    backend = OpenAICompatBackend(HTTPSJSON(base_url, api_key, timeout=args.timeout),
                                  repo=spec["repo"], revision=revision,
                                  chat_template_kwargs=spec.get("chat_template_kwargs"))
    backend.probe()
    output = (args.output or ROOT / "results" / "rebuild_a" / f"smoke_{args.model_key}").resolve()
    output.mkdir(parents=True, exist_ok=True)
    identity = {"model_key": args.model_key, "repo": spec["repo"], "revision": revision}
    identity_path = output / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise SystemExit("Output directory belongs to another model identity")
    identity_path.write_text(json.dumps(identity, indent=2) + "\n")

    results_path, calls_path = output / "results.jsonl", output / "calls.jsonl"
    done = load_done(results_path)
    tasks = [SmokeTask.model_validate_json(line) for line in
             (DATA_ROOT / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    runtime_config = load_runtime_config(ROOT / "configs" / "agent" / "A0.yaml")
    generation_config = load_generation_config(ROOT / "configs" / "runtime" / "default.yaml")
    consecutive_infra = 0
    with tempfile.TemporaryDirectory(prefix="react-api-smoke-") as temporary:
        for task in tasks:
            if task.task_id in done:
                continue
            first_call, infra_before = len(backend.calls), backend.infra_failures
            runtime = AgentRuntime(backend, build_smoke_registry(DATA_ROOT),
                                   runtime_config=runtime_config,
                                   generation_config=generation_config)
            trace = Path(temporary) / f"{task.task_id}.jsonl"
            result = runtime.run(task, trace_path=trace)
            with calls_path.open("a", encoding="utf-8") as stream:
                for call in backend.calls[first_call:]:
                    stream.write(json.dumps({"task_id": task.task_id, **call}) + "\n")
            if result.status == "model_error" and backend.infra_failures > infra_before:
                consecutive_infra += 1
                print(f"{task.task_id}: infrastructure error, will rerun on resume")
                if consecutive_infra >= MAX_CONSECUTIVE_INFRA:
                    print("Endpoint looks down; stopping. Rerun the same command to resume.")
                    return 2
                continue
            consecutive_infra = 0
            answer = result.final_answer or ""
            row = {**result.model_dump(), "success": task_succeeded(
                task, result.status, result.tool_sequence, answer),
                "finished_at": datetime.now(UTC).isoformat()}
            with (output / "traces.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(trace.read_text(encoding="utf-8"))
            with results_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"{task.task_id}: {result.status} success={row['success']}")

    rows = list(load_done(results_path).values())
    summary = {**identity, "tasks": len(tasks), "finished": len(rows),
               "success": sum(r["success"] for r in rows),
               "statuses": {s: sum(r["status"] == s for r in rows)
                            for s in sorted({r["status"] for r in rows})}}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if len(rows) == len(tasks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
