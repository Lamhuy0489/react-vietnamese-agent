"""Observe ordinary per-request native policy, without changing frozen generation."""

from __future__ import annotations

import inspect
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.efficient_requests_v1 import EfficientRequestBackend, EfficientRequestFactory
from react_agent.llm.generation_policy_v1 import METHODS, VERSION, config_snapshot, json_copy


def paths(policy: Path, attention: Path) -> None:
    for path in (policy, attention):
        no_links(path)
        if path.exists():
            raise ValueError("fresh policy and attention roots required")
    if policy.resolve().is_relative_to(attention.resolve()) or attention.resolve().is_relative_to(
        policy.resolve()
    ):
        raise ValueError("separate policy and attention roots required")


class RequestPolicyBackend:
    def __init__(self, inner: EfficientRequestBackend, output: Path) -> None:
        if type(inner) is not EfficientRequestBackend or inner._index or inner._retired:
            raise ValueError("exact fresh ordinary attention backend required")
        paths(output, inner.output)
        self.inner, self.output = inner, output
        self.model_id, self.model_revision = inner.model_id, inner.model_revision
        self._owner, self._index, self._retired = os.getpid(), 0, False
        self._lock = threading.Lock()
        self._native: Any = cast(Any, inner.native)
        self._role = inner.role
        if self._native.transformers.__version__ != VERSION:
            raise ValueError("pinned native policy implementation required")
        self._model = self._native.model
        self._publisher = config_snapshot(self._model.generation_config)

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if os.getpid() != self._owner or not self._lock.acquire(blocking=False):
            raise RuntimeError("one policy owner required")
        try:
            if self._retired:
                raise RuntimeError("policy backend retired; no retries")
            self._index += 1
            try:
                if config != GenerationConfig(
                    max_new_tokens=512 if self.inner.role == "agent" else 128
                ):
                    raise ValueError("frozen ordinary generation config required")
                if self.inner._index != self._index - 1 or self.inner._retired:
                    raise ValueError("policy and attention request histories diverged")
                self._identity()
                if config_snapshot(self._model.generation_config) != self._publisher:
                    raise ValueError("publisher policy drift between requests")
                target = self.output / f"request_{self._index:06d}"
                no_links(target)
                target.mkdir(parents=True, exist_ok=False)
                return self._generate(messages, config, target)
            except BaseException:
                self._retired = True
                raise
        finally:
            self._lock.release()

    def _identity(self) -> None:
        if self.inner.role != self._role or self._native.transformers.__version__ != VERSION:
            raise ValueError("policy role or native version drift")
        expected = self.model_id, self.model_revision
        if any(
            (value.model_id, value.model_revision) != expected
            for value in (self.inner, self._native)
        ):
            raise ValueError("policy native identity drift")
        if (
            self.inner.native is not self._native
            or cast(Any, self._native).model is not self._model
        ):
            raise ValueError("policy native object replaced")

    def _generate(
        self, messages: list[dict[str, str]], config: GenerationConfig, target: Path
    ) -> ModelResponse:
        model = self._model
        if any(name in vars(model) for name in METHODS):
            raise ValueError("unmodified class-bound policy methods required")
        originals = {name: getattr(model, name) for name in METHODS}
        if any(not inspect.ismethod(m) or m.__self__ is not model for m in originals.values()):
            raise ValueError("native bound policy methods required")
        owner = os.getpid(), threading.get_ident()
        calls = dict.fromkeys(METHODS, 0)
        observed: dict[str, dict[str, Any]] = {}

        def owning() -> None:
            if owner != (os.getpid(), threading.get_ident()):
                raise RuntimeError("foreign policy hook owner")

        def save(stage: str, **values: Any) -> None:
            write_receipt(
                target / f"{stage}.json",
                dict(
                    protocol="request_policy_v1",
                    stage=stage,
                    role=self.inner.role,
                    pid=self._owner,
                    request_index=self._index,
                    model_id=self.model_id,
                    model_revision=self.model_revision,
                    **values,
                ),
            )

        def resolve(*args: Any, **kwargs: Any) -> Any:
            owning()
            calls[METHODS[0]] += 1
            if calls[METHODS[0]] != 1 or calls[METHODS[1]]:
                raise ValueError("one ordered native resolution required")
            bound = inspect.signature(originals[METHODS[0]]).bind(*args, **kwargs)
            submitted = config_snapshot(bound.arguments["generation_config"])
            if set(bound.arguments.get("kwargs", {})) != {"input_ids", "attention_mask"}:
                raise ValueError("unexpected native generation override")
            result = originals[METHODS[0]](*args, **kwargs)
            effective, model_kwargs = result
            if set(model_kwargs) != {"input_ids", "attention_mask"}:
                raise ValueError("unexpected resolved model keyword")
            observed["resolved"] = config_snapshot(effective)
            save(
                "resolved",
                submitted=submitted,
                resolved=observed["resolved"],
                model_kwargs_keys=sorted(model_kwargs),
            )
            return result

        def length(*args: Any, **kwargs: Any) -> Any:
            owning()
            calls[METHODS[1]] += 1
            if calls[METHODS[0]] != 1 or calls[METHODS[1]] != 1:
                raise ValueError("one ordered native length preparation required")
            inputs = inspect.signature(originals[METHODS[1]]).bind(*args, **kwargs).arguments
            count = inputs["input_ids_length"]
            if (
                inputs["model_input_name"] != "input_ids"
                or type(count) is not int
                or not 1 <= count <= 4096
            ):
                raise ValueError("bounded ordinary input length required")
            before = config_snapshot(inputs["generation_config"])
            result = originals[METHODS[1]](*args, **kwargs)
            observed["length"] = config_snapshot(result)
            save(
                "length",
                before=before,
                after=observed["length"],
                input_tokens=count,
                model_input_name="input_ids",
            )
            return result

        save(
            "entered",
            publisher=self._publisher,
            global_defaults=json_copy(model.generation_config._get_default_generation_params()),
            transformers_version=VERSION,
            model_generation_calls_planned=1,
            policy_changed=False,
        )
        installed = []
        try:
            for name, hook in zip(METHODS, (resolve, length), strict=True):
                setattr(model, name, hook)
                installed.append(name)
            response = self.inner.generate(messages, config)
            if any(n != 1 for n in calls.values()) or set(observed) != {"resolved", "length"}:
                raise ValueError("missing native policy observations")
            self._identity()
            if (response.model_id, response.model_revision) != (self.model_id, self.model_revision):
                raise ValueError("policy response identity drift")
            if config_snapshot(model.generation_config) != self._publisher:
                raise ValueError("publisher policy mutated during request")
        except BaseException as exc:
            save("error", error_class=type(exc).__name__, hook_calls=calls)
            raise
        finally:
            for name in reversed(installed):
                delattr(model, name)
            restored = all(
                getattr(model, n) == originals[n] and n not in vars(model) for n in METHODS
            )
            save("restored", methods_restored=restored, hook_calls=calls)
        if not restored:
            raise RuntimeError("policy methods not restored; retire worker")
        save(
            "completed",
            model_generation_calls=1,
            hook_calls=calls,
            resolved_sha256=text_hash(canonical_json(observed["resolved"])),
            length_sha256=text_hash(canonical_json(observed["length"])),
            methods_restored=True,
            policy_changed=False,
        )
        return response


@dataclass(frozen=True)
class RequestPolicyFactory:
    attention: EfficientRequestFactory
    output: Path

    def __call__(self) -> LLMBackend:
        if type(self.attention) is not EfficientRequestFactory:
            raise ValueError("exact ordinary attention factory required")
        paths(self.output, self.attention.output)
        inner = self.attention()
        if type(inner) is not EfficientRequestBackend:
            raise ValueError("exact ordinary attention backend required")
        return RequestPolicyBackend(inner, self.output)
