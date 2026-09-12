"""Real spawn/native tqdm with explicitly synthetic policy/model/tensor objects."""

from __future__ import annotations

import argparse
import copy
import os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import check_phase5_request_pair as base

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.generation_policy_v1 import CONFIG_FIELDS, config_snapshot
from react_agent.llm.model_pair_v1 import ModelPair, PairConfig, Role
from react_agent.llm.request_policy_pair_v1 import policy_pair
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.generation_policy_audit_v1 import GLOBAL_DEFAULTS
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.request_policy_audit_v1 import audit


class Config:
    def __init__(self, **values: Any) -> None:
        vars(self).update(dict.fromkeys(CONFIG_FIELDS))
        vars(self).update(values)

    def _get_default_generation_params(self) -> dict[str, Any]:
        return copy.deepcopy(GLOBAL_DEFAULTS)


def publisher(role: Role) -> dict[str, Any]:
    return config_snapshot(
        Config(
            eos_token_id=[151645, 151643],
            bos_token_id=151643,
            pad_token_id=151643,
            do_sample=True,
            repetition_penalty=1.05 if role == "agent" else 1.1,
            temperature=0.7,
            top_k=20,
            top_p=0.8,
        )
    )


class Model:
    """Fake resolution/length only; never imports native generation implementations."""

    def __init__(self, role: Role) -> None:
        self.generation_config = Config(**publisher(role))

    def _prepare_generation_config(self, generation_config: Any, **kwargs: Any) -> Any:
        result = copy.deepcopy(generation_config)
        for source in (vars(self.generation_config), GLOBAL_DEFAULTS):
            for key, value in source.items():
                if getattr(result, key) is None:
                    setattr(result, key, copy.deepcopy(value))
        return result, kwargs

    def _prepare_generated_length(
        self,
        generation_config: Any,
        has_default_max_length: bool,
        has_default_min_length: bool,
        model_input_name: str,
        input_ids_length: int,
        inputs_tensor: Any,
    ) -> Any:
        generation_config.max_length = input_ids_length + generation_config.max_new_tokens
        if generation_config.min_new_tokens is not None:
            generation_config.min_length = input_ids_length + generation_config.min_new_tokens
        return generation_config


@dataclass(frozen=True)
class SyntheticPolicyFactory:
    native: base.SyntheticNativeFactory

    def __call__(self) -> LLMBackend:
        # Base factory verifies real daemon spawn and native progress installation;
        # exact native-shaped objects bypass constructors and delegate fake SDPA.
        native: Any = self.native()
        native.model = Model(self.native.role)
        native.transformers = SimpleNamespace(__version__="5.5.0")
        original = native.generate
        calls = 0

        def generate(messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
            nonlocal calls
            count, _ = base.REQUESTS[calls]
            calls += 1
            generation = Config(
                max_new_tokens=config.max_new_tokens,
                do_sample=False,
                num_beams=1,
                use_cache=True,
                cache_implementation="dynamic",
                return_dict_in_generate=False,
                output_scores=False,
                output_attentions=False,
                output_hidden_states=False,
                eos_token_id=native.model.generation_config.eos_token_id,
                pad_token_id=151643,
            )
            # Shape only; no token/tensor values. The original messages/config are
            # forwarded unchanged to the old synthetic generation/metric writer.
            ids = SimpleNamespace(shape=(1, count))
            resolved, inputs = native.model._prepare_generation_config(
                generation, input_ids=ids, attention_mask=ids
            )
            require(
                inputs["input_ids"] is ids and inputs["attention_mask"] is ids, "input identity"
            )
            native.model._prepare_generated_length(resolved, True, True, "input_ids", count, ids)
            return cast(ModelResponse, original(messages, config))

        native.generate = generate
        return cast(LLMBackend, native)


def composed(
    agent: base.SyntheticNativeFactory,
    guard: base.SyntheticNativeFactory,
    config: PairConfig,
    attention: Path,
) -> ModelPair:
    return policy_pair(
        SyntheticPolicyFactory(agent),
        SyntheticPolicyFactory(guard),
        config,
        attention,
        attention.parent / "policy",
    )


def run(root: Path) -> dict[str, Any]:
    no_links(root)
    if root.exists():
        raise ValueError("fresh rehearsal output required")
    # Substitute only the builder in this host-side CPU harness; restore it even
    # on failure. Spawned factories are explicit top-level picklable objects.
    # The frozen source itself and its reversed-order control remain unchanged.
    harness = cast(Any, base)
    original = harness.request_pair
    harness.request_pair = composed
    try:
        transport = base.run(root / "transport")
    finally:
        harness.request_pair = original
    rows = []
    for case in base.CASES:
        trial = root / "transport" / case
        policy, attention = trial / "policy", trial / "attention"
        closed = read_record(trial / "closed.json")
        if case == "reversed":
            require(not policy.exists(), "reversed control did not enter ordinary policy")
            continue
        joined = {}
        for role in base.ROLES:
            attempts = closed["workers"][role]["attempts"]
            pid = attempts[0]["pid"]
            if case == "success":
                joined[role] = audit(
                    policy / role,
                    attention / role,
                    trial / f"{role}_metrics.jsonl",
                    role=role,
                    worker_pid=pid,
                    expected_requests=3,
                    publisher=publisher(role),
                    pad_token_id=151643,
                )
            elif case == role + "_error":
                request = policy / role / "request_000001"
                equal(
                    sorted(inventory(policy / role)),
                    sorted(
                        f"request_000001/{stage}.json"
                        for stage in ("entered", "resolved", "length", "error", "restored")
                    ),
                    "failed policy partials",
                )
                equal(
                    read_record(request / "error.json")["error_class"],
                    "RuntimeError",
                    "injected error",
                )
                require(
                    read_record(request / "restored.json")["methods_restored"] is True,
                    "failed policy methods restored",
                )
                equal(read_record(request / "entered.json")["pid"], pid, "failed policy worker PID")
            else:
                require(
                    not (policy / role).exists(),
                    "idle sibling READY did not consume policy request",
                )
        rows.append(dict(case=case, audits=joined))
    result = dict(
        protocol="request_policy_pair_cpu_v1",
        valid=True,
        phase5_accepted=False,
        synthetic=True,
        native_model_calls=0,
        model_loads=0,
        gpu_runs=0,
        owner_pid=os.getpid(),
        worker_pids=transport["worker_pids"],
        control_rows=[
            {
                k: row[k]
                for k in ("case", "statuses", "error", "all_handles_reaped", "no_retry_attempt")
            }
            for row in transport["rows"]
        ],
        policy_rows=rows,
        raw_sha256=inventory(root / "transport"),
        scope="Real spawned policy/attention factory composition with native tqdm; "
        "synthetic model/policy/tensor/metric values, not GPU or native numerical evidence",
    )
    write_receipt(root / "summary.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
    print("REQUEST_POLICY_PAIR_CPU_COMPLETE synthetic=True native_model_calls=0")
