"""Opt-in v2 observer; preserve responses and keep raw text out of audit sinks."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.guard_diagnostic_backend_v1 import validate_output
from react_agent.security_v1.guard_diagnostics_v2 import diagnose


class RecordSink:
    """One process, append-only, fresh file; a failed sink cannot be retried."""

    def __init__(self, output: Path) -> None:
        validate_output(output)
        self.output, self.owner_pid, self.sequence = output, os.getpid(), 0
        self.failed = False
        self._identity: tuple[int, int, int] | None = None

    def check(self) -> None:
        if os.getpid() != self.owner_pid or self.failed:
            raise RuntimeError("diagnostic sink unavailable or wrong process")

    def append(self, record: dict[str, object]) -> None:
        self.check()
        try:
            no_links(self.output)
            if self._identity is not None:
                stat = self.output.stat()
                if (stat.st_dev, stat.st_ino, stat.st_size) != self._identity:
                    raise ValueError("sink changed")
            with self.output.open("x" if self.sequence == 0 else "a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
                stat = os.fstat(stream.fileno())
                self._identity = (stat.st_dev, stat.st_ino, stat.st_size)
        except (OSError, ValueError):
            self.failed = True
            raise RuntimeError("guard diagnostic unavailable") from None
        self.sequence += 1


@dataclass(frozen=True)
class DiagnosticFactory:
    backend_factory: Callable[[], LLMBackend]
    output: Path

    def __call__(self) -> DiagnosticBackend:
        validate_output(self.output)  # Reject stale output before model loading.
        return DiagnosticBackend(self.backend_factory(), self.output)


class DiagnosticBackend:
    def __init__(self, backend: LLMBackend, output: Path) -> None:
        self.sink, self.backend = RecordSink(output), backend

    @property
    def model_id(self) -> str:
        return self.backend.model_id

    @property
    def model_revision(self) -> str:
        return self.backend.model_revision

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.sink.check()
        request_hash = text_hash(canonical_json(messages))
        generation_hash = text_hash(canonical_json(config.model_dump()))
        response = self.backend.generate(messages, config)
        self.sink.append(
            dict(
                protocol="guard_response_sidecar_v2",
                sequence=self.sink.sequence + 1,
                worker_pid=self.sink.owner_pid,
                request_sha256=request_hash,
                generation_sha256=generation_hash,
                response_identity_matches=(response.model_id, response.model_revision)
                == (self.model_id, self.model_revision),
                diagnostic=diagnose(response.text).model_dump(mode="json"),
            )
        )
        return response
