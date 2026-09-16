"""Explicit synthetic receipt producer for packaging tests, never native evidence."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import write_receipt
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.guard_observer_probe_v2 import PROFILE, SAFE
from react_agent.security_v1.guard_bare_json_v1 import PROMPT
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY, LANGUAGE, POLICY


@dataclass(frozen=True)
class SyntheticConstraintFactory:
    output: Path
    condition: str

    def __call__(self) -> SyntheticConstraintBackend:
        if self.condition not in {"valid", "backend_failure"} or self.output.exists():
            raise ValueError("fresh explicit synthetic condition required")
        return SyntheticConstraintBackend(self)


class SyntheticConstraintBackend:
    model_id = "synthetic-guard"
    model_revision = PROFILE

    def __init__(self, factory: SyntheticConstraintFactory) -> None:
        self.factory, self.index = factory, 0

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if config != GenerationConfig(max_new_tokens=128) or messages[0] != dict(
            role="system", content=PROMPT
        ):
            raise ValueError("synthetic guard request mismatch")
        self.index += 1
        root = self.factory.output / f"request_{self.index:06d}"
        root.mkdir(parents=True, exist_ok=False)
        base = dict(
            protocol="constrained_policy_worker_v1",
            pid=os.getpid(),
            model_id=self.model_id,
            model_revision=self.model_revision,
            request_index=self.index,
            request_sha256=text_hash(canonical_json(messages)),
            generation_sha256=text_hash(canonical_json(config.model_dump())),
        )
        counts = dict(generate=1, processors=1, callbacks=28)
        records: dict[str, dict[str, Any]] = dict(
            entered=dict(execution_identity=IDENTITY),
            admitted=dict(
                input_tokens=7,
                policy_sha256=POLICY,
                language_sha256=LANGUAGE,
                processor_types=[
                    "RepetitionPenaltyLogitsProcessor",
                    "PrefixConstrainedLogitsProcessor",
                ],
            ),
            restored=dict(methods_restored=True, counts=counts),
        )
        if self.factory.condition == "backend_failure":
            records["error"] = dict(error_class="RuntimeError", counts=counts)
        else:
            records["completed"] = dict(
                counts=counts,
                output_tokens=28,
                output_token_sha256=text_hash("synthetic-only-token-count-fixture"),
                response_sha256=text_hash(SAFE),
                execution_identity=IDENTITY,
            )
        for stage, value in records.items():
            write_receipt(root / (stage + ".json"), dict(base, stage=stage, **value))
        if self.factory.condition == "backend_failure":
            raise RuntimeError("synthetic backend control")
        return ModelResponse(text=SAFE, model_id=self.model_id, model_revision=self.model_revision)
