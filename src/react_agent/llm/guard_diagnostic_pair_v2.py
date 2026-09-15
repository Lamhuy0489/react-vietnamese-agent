"""Host-side response hash witness over unchanged sibling-worker transport."""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Callable
from pathlib import Path

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.guard_diagnostic_backend_v2 import RecordSink
from react_agent.llm.model_pair_v1 import Role
from react_agent.llm.model_pair_v2 import ShutdownPair, ShutdownPairConfig


class DiagnosticPair(ShutdownPair):
    """Witness only responses actually returned to the host, never readiness ACKs.

    The host hashes received text independently; it does not read worker sidecars
    or diagnose/repair output. This is integrity evidence, not model authentication.
    """

    def __init__(
        self,
        agent_factory: Callable[[], LLMBackend],
        guard_factory: Callable[[], LLMBackend],
        config: ShutdownPairConfig,
        witness: Path,
    ) -> None:
        self.witness = RecordSink(witness)
        self._observer_lock = threading.Lock()
        super().__init__(agent_factory, guard_factory, config)

    def generate(
        self, role: Role, messages: list[dict[str, str]], config: GenerationConfig
    ) -> ModelResponse:
        self.witness.check()
        if not self._observer_lock.acquire(blocking=False):
            raise RuntimeError("diagnostic pair operation already in flight")
        try:
            request_hash = text_hash(canonical_json(messages))
            generation_hash = text_hash(canonical_json(config.model_dump()))
            response = super().generate(role, messages, config)
            if role == "guard":
                attempt = self.snapshot()["workers"]["guard"]["attempts"][-1]
                try:
                    self.witness.append(
                        dict(
                            protocol="guard_response_witness_v2",
                            sequence=self.witness.sequence + 1,
                            host_pid=self.witness.owner_pid,
                            worker_pid=attempt["pid"],
                            worker_sequence=attempt["sequence"],
                            request_sha256=request_hash,
                            generation_sha256=generation_hash,
                            response_sha256=hashlib.sha256(
                                response.text.encode("utf-8", errors="surrogatepass")
                            ).hexdigest(),
                            response_chars=len(response.text),
                            response_identity_matches=(response.model_id, response.model_revision)
                            == (self.config.guard.model_id, self.config.guard.model_revision),
                        )
                    )
                except RuntimeError:
                    self.close()  # A broken observer is infrastructure failure, not a retry.
                    raise
            return response
        finally:
            self._observer_lock.release()
