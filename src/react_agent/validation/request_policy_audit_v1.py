"""Independent ordinary-policy precedence and attention/native-metric join."""

from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.generation_policy_v1 import CONFIG_FIELDS, METHODS
from react_agent.llm.model_pair_v1 import Role
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.efficient_requests_audit_v1 import _record
from react_agent.validation.efficient_requests_audit_v1 import audit as audit_attention
from react_agent.validation.generation_policy_audit_v1 import GLOBAL_DEFAULTS, resolve
from react_agent.validation.guard_probe_audit_v2 import digest, require


def audit(
    policy: Path,
    attention: Path,
    metrics: Path,
    *,
    role: Role,
    worker_pid: int,
    expected_requests: int,
    publisher: dict[str, Any],
    pad_token_id: int,
) -> dict[str, Any]:
    """Publisher and pad ID are caller expectations, not authenticated model inputs."""
    no_links(policy)
    require(type(pad_token_id) is int and pad_token_id >= 0, "tokenizer pad ID")
    for other in (attention, metrics):
        no_links(other)
        require(
            not policy.resolve().is_relative_to(other.resolve())
            and not other.resolve().is_relative_to(policy.resolve()),
            "separate policy inputs",
        )
    hashes, attention_before, metric_before = (
        inventory(policy),
        inventory(attention),
        digest(metrics),
    )
    tree = sorted(p.relative_to(policy).as_posix() for p in policy.rglob("*"))
    joined = audit_attention(
        attention, metrics, role=role, worker_pid=worker_pid, expected_requests=expected_requests
    )
    names = [f"request_{i:06d}" for i in range(1, expected_requests + 1)]
    stages = ("entered", "resolved", "length", "restored", "completed")
    expected_tree = sorted(names + [f"{name}/{stage}.json" for name in names for stage in stages])
    equal(tree, expected_tree, "exact policy request tree")
    submitted: dict[str, Any] = dict.fromkeys(CONFIG_FIELDS)
    submitted.update(
        dict(
            max_new_tokens=512 if role == "agent" else 128,
            do_sample=False,
            num_beams=1,
            use_cache=True,
            cache_implementation="dynamic",
            return_dict_in_generate=False,
            output_scores=False,
            output_attentions=False,
            output_hidden_states=False,
            eos_token_id=publisher["eos_token_id"],
            pad_token_id=pad_token_id,
            transformers_version="5.5.0",
        )
    )
    effective = resolve(submitted, publisher)
    calls = dict.fromkeys(METHODS, 1)
    summaries = []
    for index, row in enumerate(joined["requests"], 1):
        count = row["input_tokens"]
        length = dict(effective, max_length=count + submitted["max_new_tokens"])
        if effective["min_new_tokens"] is not None:
            length["min_length"] = count + effective["min_new_tokens"]
        base = dict(
            protocol="request_policy_v1",
            role=role,
            pid=worker_pid,
            request_index=index,
            model_id=joined["model_id"],
            model_revision=joined["model_revision"],
        )
        expected: dict[str, dict[str, Any]] = {
            "entered": dict(
                publisher=publisher,
                global_defaults=GLOBAL_DEFAULTS,
                transformers_version="5.5.0",
                model_generation_calls_planned=1,
                policy_changed=False,
            ),
            "resolved": dict(
                submitted=submitted,
                resolved=effective,
                model_kwargs_keys=["attention_mask", "input_ids"],
            ),
            "length": dict(
                before=effective, after=length, input_tokens=count, model_input_name="input_ids"
            ),
            "restored": dict(methods_restored=True, hook_calls=calls),
            "completed": dict(
                model_generation_calls=1,
                hook_calls=calls,
                resolved_sha256=text_hash(canonical_json(effective)),
                length_sha256=text_hash(canonical_json(length)),
                methods_restored=True,
                policy_changed=False,
            ),
        }
        for stage in stages:
            equal(
                _record((policy / names[index - 1] / f"{stage}.json").read_text()),
                dict(base, stage=stage, **expected[stage]),
                "request policy " + stage,
            )
        summaries.append(
            dict(
                request_index=index,
                input_tokens=count,
                resolved_sha256=text_hash(canonical_json(effective)),
                length_sha256=text_hash(canonical_json(length)),
                max_length=length["max_length"],
                min_length=length["min_length"],
            )
        )
    equal(inventory(policy), hashes, "policy mutated during audit")
    equal(
        sorted(p.relative_to(policy).as_posix() for p in policy.rglob("*")),
        tree,
        "policy tree mutated",
    )
    equal(inventory(attention), attention_before, "attention changed during policy audit")
    equal(digest(metrics), metric_before, "metrics changed during policy audit")
    return dict(
        protocol="request_policy_audit_v1",
        valid=True,
        phase5_accepted=False,
        source_authenticated=False,
        publisher_metadata_authenticated=False,
        tokenizer_metadata_authenticated=False,
        supervisor_pid_authenticated=False,
        full_boundary_cache_verified=False,
        policy_requests=summaries,
        attention=joined,
        raw_sha256=hashes,
        publisher_sha256=text_hash(canonical_json(publisher)),
        pad_token_id=pad_token_id,
        scope="Observed resolution/length consistency only; caller must authenticate "
        "source/publisher/tokenizer/loader/supervisor before native adoption",
    )
