"""Prompt-only candidate with task-local bindings over frozen classifier/runtime bodies."""

from __future__ import annotations

from types import FunctionType
from typing import Any, cast

from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.guard import PROMPT as BASELINE_PROMPT
from react_agent.security_v1.guard import GuardInput, GuardOutcome, ModelGuard
from react_agent.security_v1.pair_runtime_v3 import run_pair_task as original_pair
from react_agent.security_v1.processing_scope_v3 import PROFILE, ProcessingScope, describe_action
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime
from react_agent.security_v1.warm_guard import WarmModelGuard

PROMPT_VERSION = "guard_prompt_bare_json_v1"
SUFFIX = (
    " Return bare JSON only. The first character must be { and the last character "
    "must be }. Do not use Markdown, code fences, backticks, or any prefix or suffix."
)
PROMPT = BASELINE_PROMPT + SUFFIX
RUNTIME_VERSION = "security_runtime_v8_bare_json_v1"


def bind(original: Any, **dependencies: Any) -> Any:
    """Copy function globals privately; never replace a symbol in an imported module."""
    namespace = dict(original.__globals__)
    namespace.update(dependencies)
    body = FunctionType(
        original.__code__, namespace, original.__name__, original.__defaults__, original.__closure__
    )
    body.__kwdefaults__ = original.__kwdefaults__
    return body


class BareJsonModelGuard(ModelGuard):
    prompt_version = PROMPT_VERSION

    def classify(self, request: GuardInput) -> GuardOutcome:
        return cast(GuardOutcome, bind(ModelGuard.classify, PROMPT=PROMPT)(self, request))


class BareJsonWarmGuard(WarmModelGuard, BareJsonModelGuard):
    """WarmModelGuard.super() reaches the candidate classifier through this MRO."""


class SecurityRuntime(V7Runtime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        inner = bind(V5Runtime._run_task, WarmModelGuard=BareJsonWarmGuard, PROMPT=PROMPT)
        body = bind(
            V7Runtime._run_task,
            _V5_RUN_TASK=inner,
            ProcessingScope=ProcessingScope,
            describe_action=describe_action,
            SCOPE_PROFILE=PROFILE,
            RUNTIME_VERSION=RUNTIME_VERSION,
        )
        return cast(SecurityRun, body(self, task, **kwargs))


def run_pair_task(task: RuntimeTask, **kwargs: Any) -> SecurityRun:
    body = bind(original_pair, ProcessingScope=ProcessingScope, SecurityRuntime=SecurityRuntime)
    return cast(SecurityRun, body(task, **kwargs))
