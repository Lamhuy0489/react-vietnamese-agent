"""Opt-in worker-local guard response diagnostics, with unchanged returned bytes."""

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
from react_agent.security_v1.guard_diagnostics_v1 import diagnose


@dataclass(frozen=True)
class DiagnosticFactory:
    backend_factory: Callable[[], LLMBackend]
    output: Path

    def __call__(self) -> DiagnosticBackend:
        # Reject stale output before loading a native model.
        validate_output(self.output)
        return DiagnosticBackend(self.backend_factory(), self.output)


def validate_output(output: Path) -> None:
    no_links(output)
    if output.exists() or not output.parent.is_dir():
        raise ValueError("fresh diagnostic file in an existing directory required")


class DiagnosticBackend:
    def __init__(self, backend: LLMBackend, output: Path) -> None:
        validate_output(output)
        self.backend, self.output, self.sequence = backend, output, 0
        self.owner_pid = os.getpid()

    @property
    def model_id(self) -> str:
        return self.backend.model_id

    @property
    def model_revision(self) -> str:
        return self.backend.model_revision

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if os.getpid() != self.owner_pid:
            raise RuntimeError("diagnostic backend belongs to its worker process")
        request_hash = text_hash(canonical_json(messages))
        generation_hash = text_hash(canonical_json(config.model_dump()))
        # Transport failures propagate without a fabricated response/diagnostic.
        response = self.backend.generate(messages, config)
        diagnostic = diagnose(response.text)
        record = dict(
            protocol="guard_response_sidecar_v1",
            sequence=self.sequence + 1,
            worker_pid=self.owner_pid,
            request_sha256=request_hash,
            generation_sha256=generation_hash,
            response_identity_matches=(response.model_id, response.model_revision)
            == (self.model_id, self.model_revision),
            diagnostic=diagnostic.model_dump(mode="json"),
        )
        try:
            no_links(self.output)
            with self.output.open("x" if self.sequence == 0 else "a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except (OSError, ValueError):
            # Do not expose path/exception text. A missing audit sink fails closed.
            raise RuntimeError("guard diagnostic unavailable") from None
        self.sequence += 1
        return response
