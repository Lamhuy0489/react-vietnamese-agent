#!/usr/bin/env python3
"""Public-only runtime/parser smoke including every tool and a recovery adapter."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from react_agent.agent import AgentRuntime
from react_agent.llm import ReplayBackend
from react_agent.schemas.clean_task import CleanPublicTask, FaultSpec
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.clean_environment import validate_environment

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"


def main() -> int:
    failures = validate_environment(CLEAN_ROOT)
    if failures:
        raise RuntimeError(failures)
    task = CleanPublicTask.model_validate_json(
        (CLEAN_ROOT / "splits/dev.jsonl").read_text().splitlines()[0]
    )
    inputs = {
        "doc_search": {"query": "học phí"},
        "doc_read": {"doc_id": "CDOC_001"},
        "cached_search": {"query": "lịch"},
        "cached_fetch": {"page_id": "CPAGE_001"},
        "db_query": {"query": "SELECT 1 AS preflight"},
        "calculator": {"expression": "6*7"},
        "send_email_mock": {
            "to": "preflight@example.invalid",
            "subject": "Synthetic",
            "body": "Preflight",
        },
        "post_webhook_mock": {"endpoint": "mock://preflight", "payload": {"synthetic": True}},
    }
    for name, arguments in inputs.items():
        action = json.dumps({"action": {"name": name, "arguments": arguments}})
        with tempfile.TemporaryDirectory(prefix="tool-preflight-") as temporary:
            trace = Path(temporary) / "trace.jsonl"
            result = AgentRuntime(
                ReplayBackend([action, '{"final_answer":{"answer":"preflight"}}']),
                build_clean_registry(CLEAN_ROOT / "environment"),
            ).run(task, trace_path=trace)
            events = [json.loads(line) for line in trace.read_text().splitlines()]
            observations = [event["data"] for event in events if event["event"] == "tool_result"]
            if len(observations) != 1 or observations[0]["ok"] is not True:
                raise RuntimeError(f"preflight tool execution failure: {name}")
        if result.status != "completed" or result.tool_sequence != [name] or result.parse_errors:
            raise RuntimeError(f"preflight runtime/parser failure: {name}")
    action = json.dumps({"action": {"name": "doc_search", "arguments": inputs["doc_search"]}})
    result = AgentRuntime(
        ReplayBackend([action, action, '{"final_answer":{"answer":"recovered"}}']),
        build_clean_registry(
            CLEAN_ROOT / "environment",
            fault_plan=[
                FaultSpec(
                    tool="doc_search",
                    occurrence=1,
                    error_code="TEMPORARY_UNAVAILABLE",
                    retryable=True,
                )
            ],
        ),
    ).run(task)
    if (
        result.status != "completed"
        or result.parse_errors
        or result.tool_sequence != ["doc_search", "doc_search"]
    ):
        raise RuntimeError("fault adapter parser/retry preflight failed")
    print("PASS: frozen public environment, eight runtime tool schemas and recovery adapter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
