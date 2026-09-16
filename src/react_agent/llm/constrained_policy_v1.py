"""Opt-in worker composition: constraints outside unchanged policy/attention scopes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.constrained_guard_v1 import (
    ConstrainedGuardBackend,
    constrained_scope,
    language_for_guard,
)
from react_agent.llm.efficient_requests_v1 import (
    GUARD_REVISION,
    EfficientRequestBackend,
    EfficientRequestFactory,
)
from react_agent.llm.guard_hf_v1 import GuardHFConfig, GuardHFFactory
from react_agent.llm.guard_language_native_v1 import FILES
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.guard_token_language_v1 import TokenLanguage
from react_agent.llm.model_pair_hf_v1 import GuardFactory
from react_agent.llm.ordinary_pair_probe_v1 import fresh_roots
from react_agent.llm.request_policy_v1 import RequestPolicyBackend, RequestPolicyFactory
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory

PROFILE = "constrained_policy_worker_v1"


class ConstrainedPolicyBackend(ConstrainedGuardBackend):
    def __init__(self, policy: RequestPolicyBackend, language: TokenLanguage, output: Path) -> None:
        if type(policy) is not RequestPolicyBackend or policy._index or policy._retired:
            raise ValueError("fresh exact policy backend required")
        attention = policy.inner
        if (
            type(attention) is not EfficientRequestBackend
            or attention.role != "guard"
            or attention._index
            or attention._retired
        ):
            raise ValueError("fresh exact guard attention backend required")
        fresh_roots(output, policy.output, attention.output)
        # The unchanged constructor authenticates the native class, limits and source.
        super().__init__(attention.native, language, output)  # type: ignore[arg-type]
        self.policy, self.attention = policy, attention

    @property
    def retired(self) -> bool:
        return super().retired or self.policy._retired or self.attention._retired

    def retire(self) -> None:
        super().retire()
        self.policy._retired = self.attention._retired = True

    def verify_identity(self) -> None:
        super().verify_identity()
        self.policy._identity()
        if (
            self.policy.inner is not self.attention
            or cast(Any, self.attention.native) is not self.native
            or self.attention.role != "guard"
            or self.policy._index != self._index
            or self.attention._index != self._index
            or self.native.call_index != self._index
        ):
            raise ValueError("constrained/policy/attention/native histories diverged")

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if os.getpid() != self._owner or not self._lock.acquire(blocking=False):
            raise RuntimeError("single constrained worker owner required")
        try:
            if self.retired:
                raise RuntimeError("constrained worker retired; no retry")
            try:
                self.verify_identity()
                if config != GenerationConfig(max_new_tokens=128):
                    raise ValueError("frozen guard generation required")
                self._index += 1
                target = self.output / f"request_{self._index:06d}"
                no_links(target)
                target.mkdir(parents=True, exist_ok=False)

                def save(stage: str, **values: Any) -> None:
                    write_receipt(
                        target / f"{stage}.json",
                        dict(
                            protocol=PROFILE,
                            stage=stage,
                            pid=self._owner,
                            model_id=self.model_id,
                            model_revision=self.model_revision,
                            request_index=self._index,
                            request_sha256=text_hash(canonical_json(messages)),
                            generation_sha256=text_hash(canonical_json(config.model_dump())),
                            **values,
                        ),
                    )

                def invoke() -> ModelResponse:
                    # Crucially, do not call native.generate directly: preserve both observers.
                    response = self.policy.generate(messages, config)
                    self.verify_identity()
                    if (response.model_id, response.model_revision) != (
                        self.model_id,
                        self.model_revision,
                    ):
                        raise ValueError("constrained response identity changed")
                    return response

                return constrained_scope(self._model, self.language, *self._types, invoke, save)
            except BaseException:
                self.retire()
                raise
        finally:
            self._lock.release()


@dataclass(frozen=True)
class ConstrainedPolicyFactory:
    inner: ThreadProgressFactory
    output: Path
    snapshot: GuardSnapshot

    def __call__(self) -> ConstrainedPolicyBackend:
        if (
            type(self.inner) is not ThreadProgressFactory
            or type(self.inner.factory) is not RequestPolicyFactory
        ):
            raise ValueError("exact progress/policy topology required")
        policy_factory = self.inner.factory
        attention_factory = policy_factory.attention
        if (
            type(attention_factory) is not EfficientRequestFactory
            or attention_factory.role != "guard"
        ):
            raise ValueError("exact guard attention factory required")
        fresh_roots(self.output, policy_factory.output, attention_factory.output)
        guard_factory = attention_factory.native_factory
        if type(guard_factory) is not GuardFactory or type(guard_factory.hf) is not GuardHFFactory:
            raise ValueError("exact guard loader required before model loading")
        hf = guard_factory.hf
        if (
            not isinstance(self.snapshot, GuardSnapshot)
            or hf.snapshot != self.snapshot
            or self.snapshot.model_revision != GUARD_REVISION
            or hf.config != GuardHFConfig()
        ):
            raise ValueError("pinned guard snapshot and limits required before loading")
        for source in (hf.model_path, hf.metrics_path):
            no_links(source)
            for root in (self.output, policy_factory.output, attention_factory.output):
                if root.resolve().is_relative_to(
                    source.resolve()
                ) or source.resolve().is_relative_to(root.resolve()):
                    raise ValueError("worker evidence must not overlap native inputs or metrics")
        hashes = {f.name: f.sha256 for f in self.snapshot.files if f.name in FILES}
        if set(hashes) != FILES:
            raise ValueError("complete tokenizer metadata required")
        policy = self.inner()
        if type(policy) is not RequestPolicyBackend:
            raise ValueError("exact worker policy backend required")
        native = policy.inner.native
        if (native.model_id, native.model_revision) != (
            self.snapshot.model_id,
            self.snapshot.model_revision,
        ):
            raise ValueError("worker/tokenizer snapshot identity mismatch")
        language = language_for_guard(native, hashes)  # type: ignore[arg-type]
        return ConstrainedPolicyBackend(policy, language, self.output)
