#!/usr/bin/env python3
"""Execute the frozen structured-API Dev pilot with durable checkpoints."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from react_agent.agent.checkpoint import atomic_json
from react_agent.llm.http_diagnostic_v1 import HTTPSJSON, APIError
from react_agent.llm.structured_api_dev_v1 import run
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API = ROOT / "build/kaggle/structured_pair_release01"
DEFAULT_MANIFEST = ROOT / "build/evaluation/structured_api_dev_v1/manifest.json"


def _backend(directory: Path, role: str) -> StructuredHTTPBackend:
    pair = json.loads((directory / "pair_endpoints.json").read_text(encoding="utf-8"))
    records = [record for record in pair.get("models", []) if record.get("role") == role]
    if len(records) != 1:
        raise ValueError(f"exactly one {role} endpoint required")
    record: dict[str, Any] = records[0]
    metadata = json.loads(
        (directory / f"{role}_live_metadata.json").read_text(encoding="utf-8")
    )
    return StructuredHTTPBackend(
        HTTPSJSON(record["endpoint"], record["api_key"], timeout=150),
        model=record["id"],
        role=role,
        session_id=record["session_id"],
        source_commit=record["source_commit"],
        model_revision=record["model_revision"],
        worker_sha256=metadata["worker_sha256"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-directory", type=Path, default=DEFAULT_API)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-new-tasks", type=int)
    parser.add_argument("--no-probe", action="store_true")
    args = parser.parse_args()
    if args.max_new_tasks is not None and args.max_new_tasks < 0:
        raise ValueError("--max-new-tasks must be nonnegative")
    directory = args.api_directory.resolve()
    agent = _backend(directory, "agent")
    guard = _backend(directory, "guard")
    output = args.output.resolve()
    try:
        summary = run(
            output,
            args.manifest.resolve(),
            agent=agent,
            guard=guard,
            resume=args.resume,
            max_new_tasks=args.max_new_tasks,
            probe=not args.no_probe,
        )
    except APIError as exc:
        # Persist only a public error code. Endpoint/key details must never enter
        # an experiment artifact or terminal output.
        output.mkdir(parents=True, exist_ok=True)
        atomic_json(
            output / "startup_error.json",
            {
                "protocol": "structured_api_dev_v1",
                "stage": "probe_or_transport",
                "error_code": exc.code,
                "recorded_at": datetime.now(UTC).isoformat(),
                "inference_requests_sent": False,
            },
        )
        print(json.dumps({"status": "startup_error", "error_code": exc.code}))
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return int(summary["failed"] != 0 or summary["interrupted"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
