"""Candidate classifier with decoding-bound cache keys; no paired runtime adoption."""

from __future__ import annotations

import threading
from typing import Literal, Protocol

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, LLMBackend
from react_agent.security_v1.guard import GuardInput, GuardOutcome, GuardResult, parse_guard
from react_agent.security_v1.guard_bare_json_v1 import PROMPT


class ConstrainedBackend(LLMBackend, Protocol):
    constraint_identity: str

    @property
    def retired(self) -> bool: ...

    def retire(self) -> None: ...

    def verify_identity(self) -> None: ...


class ConstrainedClassifier:
    def __init__(self, backend: ConstrainedBackend) -> None:
        identity = backend.constraint_identity
        if len(identity) != 64 or any(c not in "0123456789abcdef" for c in identity):
            raise ValueError("explicit constrained execution identity required")
        if not backend.model_id or not backend.model_revision:
            raise ValueError("explicit model identity required")
        self.backend = backend
        self._identity = backend.model_id, backend.model_revision, identity
        self._cache: dict[str, GuardResult] = {}
        self._lock = threading.Lock()

    def classify(self, request: GuardInput) -> GuardOutcome:
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("single classifier owner required")
        try:
            generation = GenerationConfig(max_new_tokens=128)
            key = text_hash(
                canonical_json(
                    dict(
                        protocol="constrained_classifier_v1",
                        model=self._identity[0],
                        revision=self._identity[1],
                        decoding=self._identity[2],
                        prompt=text_hash(PROMPT),
                        generation=generation.model_dump(),
                        input=request.model_dump(mode="json"),
                    )
                )
            )

            def stable() -> bool:
                try:
                    self.backend.verify_identity()
                except Exception:  # Fail closed; do not retain diagnostic text.
                    return False
                except BaseException:
                    self._cache.clear()
                    self.backend.retire()
                    raise
                return (
                    self.backend.model_id,
                    self.backend.model_revision,
                    self.backend.constraint_identity,
                ) == self._identity

            def error(
                code: Literal["BACKEND_FAILURE", "INVALID_OUTPUT", "IDENTITY_CHANGED"],
            ) -> GuardOutcome:
                self._cache.clear()
                self.backend.retire()
                return GuardOutcome(status="ERROR", error_code=code, cache_key=key)

            if self.backend.retired:
                return error("BACKEND_FAILURE")
            if not stable():
                return error("IDENTITY_CHANGED")
            if key in self._cache:
                return GuardOutcome(
                    status="OK", result=self._cache[key], cache_key=key, cache_hit=True
                )
            try:
                response = self.backend.generate(
                    [
                        dict(role="system", content=PROMPT),
                        dict(role="user", content=canonical_json(request.model_dump(mode="json"))),
                    ],
                    generation,
                )
            except Exception:  # Backend boundary: never retain exception text or candidate text.
                return error("BACKEND_FAILURE")
            except BaseException:
                self._cache.clear()
                self.backend.retire()
                raise
            if self.backend.retired:
                return error("BACKEND_FAILURE")
            if not stable() or (response.model_id, response.model_revision) != self._identity[:2]:
                return error("IDENTITY_CHANGED")
            try:
                result = parse_guard(response.text)
            except ValueError:
                return error("INVALID_OUTPUT")
            self._cache[key] = result
            return GuardOutcome(status="OK", result=result, cache_key=key)
        finally:
            self._lock.release()
