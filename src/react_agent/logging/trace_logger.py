"""Append-only JSONL trace logger."""

from __future__ import annotations

import json
from pathlib import Path

from react_agent.schemas.trace import TraceEvent


class TraceLogger:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.events: list[TraceEvent] = []
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")

    def log(self, event: TraceEvent) -> None:
        self.events.append(event)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(event.model_dump_json() + "\n")

    def as_dicts(self) -> list[dict[str, object]]:
        return [json.loads(event.model_dump_json()) for event in self.events]
