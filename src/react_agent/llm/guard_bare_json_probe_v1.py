"""Separate prompt-candidate identity; preserve the four-task observer baseline."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.normalization import text_hash
from react_agent.llm import guard_observer_probe_v2 as baseline
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.security_v1.guard import PROMPT as BASELINE_PROMPT
from react_agent.security_v1.guard_bare_json_v1 import (
    PROMPT,
    PROMPT_VERSION,
    RUNTIME_VERSION,
    bind,
    run_pair_task,
)
from react_agent.validation.guard_bare_json_audit_v1 import audit_join

PROFILE = "guard_bare_json_probe_v1"
SCHEDULE = baseline.SCHEDULE


def execution_sources() -> dict[str, str]:
    source = Path(__file__).resolve().parents[1]
    names = (
        "llm/guard_bare_json_probe_v1.py",
        "security_v1/guard_bare_json_v1.py",
        "validation/guard_bare_json_audit_v1.py",
    )
    return {
        **baseline.execution_sources(),
        **{name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in names},
    }


def fixed_identity(backend: str, condition: str) -> dict[str, Any]:
    if condition not in {"valid", "trailing_comma", "fenced"} or (
        backend == "hf" and condition != "valid"
    ):
        raise ValueError("native output injection forbidden or unknown CPU condition")
    identity = baseline.fixed_identity(backend, "valid")
    identity.update(
        protocol=PROFILE,
        condition=condition,
        security_runtime_version=RUNTIME_VERSION,
        guard_prompt=dict(
            version=PROMPT_VERSION,
            sha256=text_hash(PROMPT),
            baseline_sha256=text_hash(BASELINE_PROMPT),
        ),
    )
    return identity


class StubBackend(baseline.StubBackend):
    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if self.fixture.role == "guard":
            if messages[0] != {"role": "system", "content": PROMPT}:
                raise ValueError("candidate system prompt missing")
            if self.fixture.condition == "fenced":
                return ModelResponse(
                    text="```json\n" + baseline.SAFE + "\n```",
                    model_id=self.model_id,
                    model_revision=self.model_revision,
                )
        return super().generate(messages, config)


class StubFactory(baseline.StubFactory):
    def __call__(self) -> StubBackend:
        return StubBackend(self)


def checkpoint(root: Path) -> dict[str, Any]:
    return cast(dict[str, Any], bind(baseline.checkpoint, **dependencies())(root))


def dependencies() -> dict[str, Any]:
    return dict(
        PROFILE=PROFILE,
        fixed_identity=fixed_identity,
        execution_sources=execution_sources,
        checkpoint=checkpoint,
        audit_join=audit_join,
        run_pair_task=run_pair_task,
        StubFactory=StubFactory,
    )


def run(output: Path, environment: Path, **kwargs: Any) -> dict[str, Any]:
    return cast(dict[str, Any], bind(baseline.run, **dependencies())(output, environment, **kwargs))
