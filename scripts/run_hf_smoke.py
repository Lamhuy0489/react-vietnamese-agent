#!/usr/bin/env python3
"""Run the Phase 1 smoke suite with a local Hugging Face causal LM."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from run_smoke import DATA_ROOT, ROOT, data_hash, git_commit, load_tasks, task_succeeded

from react_agent.agent import AgentRuntime
from react_agent.config import load_generation_config, load_runtime_config
from react_agent.llm import HFBackend
from react_agent.schemas.task import SmokeTask
from react_agent.tools.factory import build_smoke_registry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--model-id", default="qwen-lm/qwen2.5")
    parser.add_argument("--model-revision", default="transformers/3b-instruct/1")
    parser.add_argument("--task-id")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_tasks(all_tasks: list[SmokeTask], task_id: str | None) -> list[SmokeTask]:
    if task_id is None:
        return all_tasks
    selected = [task for task in all_tasks if task.task_id == task_id]
    if not selected:
        raise ValueError(f"unknown smoke task: {task_id}")
    return selected


def load_backend(
    model_path: Path, model_id: str, model_revision: str, *, chat_adapter: str = "native"
) -> HFBackend:
    import torch  # type: ignore[import-not-found]
    from transformers import (  # type: ignore[import-not-found]
        AutoModelForCausalLM,
        AutoTokenizer,
        pipeline,
    )

    if not model_path.is_dir():
        raise FileNotFoundError(f"model directory not found: {model_path}")
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    from react_agent.llm.pilot_profiles import adapt_messages

    # Compile a context with a correction before allocating model weights.
    probe = [
        {"role": "system", "content": "System"},
        {"role": "user", "content": "Task"},
        {"role": "assistant", "content": "Action"},
        {"role": "user", "content": "Observation"},
        {"role": "user", "content": "Correction"},
    ]
    tokenizer.apply_chat_template(
        adapt_messages(probe, chat_adapter), tokenize=False, add_generation_prompt=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        local_files_only=True,
    )
    generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    def adapted_generator(messages: list[dict[str, str]], **kwargs: Any) -> Any:
        return generator(adapt_messages(messages, chat_adapter), **kwargs)

    return HFBackend(adapted_generator, model_id=model_id, model_revision=model_revision)


def run_suite(
    tasks: list[SmokeTask],
    backend: HFBackend,
    output_dir: Path,
    *,
    model_path: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    combined_trace = output_dir / "traces.jsonl"
    combined_trace.write_text("", encoding="utf-8")
    runtime_config_path = ROOT / "configs" / "agent" / "A0.yaml"
    generation_config_path = ROOT / "configs" / "runtime" / "default.yaml"
    runtime_config = load_runtime_config(runtime_config_path)
    generation_config = load_generation_config(generation_config_path)
    results: list[dict[str, Any]] = []
    total_model_outputs = 0
    total_parse_errors = 0

    with tempfile.TemporaryDirectory(prefix="react-hf-smoke-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        for task in tasks:
            runtime = AgentRuntime(
                backend,
                build_smoke_registry(DATA_ROOT),
                runtime_config=runtime_config,
                generation_config=generation_config,
            )
            task_trace = temporary_root / f"{task.task_id}.jsonl"
            result = runtime.run(task, trace_path=task_trace)
            trace_lines = task_trace.read_text(encoding="utf-8").splitlines()
            with combined_trace.open("a", encoding="utf-8") as stream:
                for line in trace_lines:
                    stream.write(line + "\n")
                    event = json.loads(line)
                    total_model_outputs += event["event"] == "model_output"
                    total_parse_errors += event["event"] == "parse_error"
            answer = result.final_answer or ""
            success = task_succeeded(task, result.status, result.tool_sequence, answer)
            results.append({**result.model_dump(), "success": success})
            print(
                f"{task.task_id}: status={result.status} "
                f"success={success} tools={result.tool_sequence}",
                flush=True,
            )

    terminal_statuses = {"completed", "parse_failure", "max_steps", "model_error"}
    failures = [result for result in results if not result["success"]]
    covered = sorted({tool for result in results for tool in result["tool_sequence"]})
    summary: dict[str, Any] = {
        "total_tasks": len(tasks),
        "terminal_runs": sum(result["status"] in terminal_statuses for result in results),
        "completed_runs": sum(result["status"] == "completed" for result in results),
        "crashed_runs": sum(result["status"] == "model_error" for result in results),
        "task_successes": sum(bool(result["success"]) for result in results),
        "schema_validity_rate": (
            (total_model_outputs - total_parse_errors) / total_model_outputs
            if total_model_outputs
            else None
        ),
        "tools_covered": covered,
        "backend": "huggingface",
    }
    metadata = {
        "suite_id": datetime.now(UTC).strftime("phase1_hf_%Y%m%dT%H%M%SZ"),
        "git_commit": git_commit(),
        "config_id": runtime_config.config_id,
        "config_hashes": {
            "agent": file_sha256(runtime_config_path),
            "generation": file_sha256(generation_config_path),
        },
        "model_id": backend.model_id,
        "model_revision": backend.model_revision,
        "model_path": str(model_path),
        "temperature": generation_config.temperature,
        "max_new_tokens": generation_config.max_new_tokens,
        "seed": generation_config.seed,
        "task_set": "smoke_v1",
        "selected_task_ids": [task.task_id for task in tasks],
        "data_hash": data_hash(),
        "started_at": datetime.now(UTC).isoformat(),
        "runtime_version": "0.1.0",
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "failures.json").write_text(
        json.dumps(failures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return summary


def main() -> int:
    args = parse_args()
    tasks = select_tasks(load_tasks(), args.task_id)
    backend = load_backend(args.model_path, args.model_id, args.model_revision)
    summary = run_suite(tasks, backend, args.output.resolve(), model_path=args.model_path)
    return int(
        summary["terminal_runs"] != len(tasks) or summary["crashed_runs"] != 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
