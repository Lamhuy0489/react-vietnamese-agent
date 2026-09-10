"""Independent JSON policy precedence checks; no native library or inference."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.generation_policy_v1 import CONFIG_FIELDS, METHODS
from react_agent.llm.model_pair_v1 import ModelIdentity, Role
from react_agent.validation.context_stress_audit_v1 import equal, fields, inventory, read_record
from react_agent.validation.guard_probe_audit_v2 import require

GLOBAL_DEFAULTS = {
    "max_length": 20,
    "min_length": 0,
    "do_sample": False,
    "use_cache": True,
    "early_stopping": False,
    "num_beams": 1,
    "temperature": 1.0,
    "top_k": 50,
    "top_p": 1.0,
    "typical_p": 1.0,
    "repetition_penalty": 1.0,
    "length_penalty": 1.0,
    "no_repeat_ngram_size": 0,
    "encoder_no_repeat_ngram_size": 0,
    "bad_words_ids": None,
    "num_return_sequences": 1,
    "output_scores": False,
    "return_dict_in_generate": False,
    "forced_bos_token_id": None,
    "forced_eos_token_id": None,
    "remove_invalid_values": False,
    "exponential_decay_length_penalty": None,
    "suppress_tokens": None,
    "begin_suppress_tokens": None,
    "epsilon_cutoff": 0.0,
    "eta_cutoff": 0.0,
    "encoder_repetition_penalty": 1.0,
    "num_assistant_tokens": 20,
    "num_assistant_tokens_schedule": "constant",
    "assistant_confidence_threshold": 0.4,
    "assistant_lookbehind": 10,
    "target_lookbehind": 10,
    "num_beam_groups": 1,
    "diversity_penalty": 0.0,
}


def resolve(submitted: dict[str, Any], publisher: dict[str, Any]) -> dict[str, Any]:
    fields(submitted, set(CONFIG_FIELDS), "submitted policy")
    fields(publisher, set(CONFIG_FIELDS), "publisher policy")
    result = dict(submitted)
    for source in (publisher, GLOBAL_DEFAULTS):
        for key, value in source.items():
            if result[key] is None:
                result[key] = value
    return result


def audit_policy(
    root: Path,
    role: Role,
    identity: ModelIdentity,
    pid: int,
    submitted: dict[str, Any],
    publisher: dict[str, Any],
) -> dict[str, Any]:
    """Caller must authenticate publisher metadata and prepared.json separately."""
    hashes = inventory(root)
    names = ("entered", "resolved", "length", "restored", "completed")
    equal(sorted(hashes), sorted(n + ".json" for n in names), "policy inventory")
    require(type(pid) is int and pid > 0, "policy PID")
    base = {
        "protocol": "generation_policy_observation_v1",
        "pid": pid,
        "role": role,
        "model_id": identity.model_id,
        "model_revision": identity.model_revision,
    }
    calls = dict.fromkeys(METHODS, 1)
    effective = resolve(submitted, publisher)
    total = 4096 + (512 if role == "agent" else 128)
    length = {**effective, "max_length": total, "min_length": total}
    expected: dict[str, dict[str, Any]] = {
        "entered": {
            "publisher": publisher,
            "global_defaults": GLOBAL_DEFAULTS,
            "transformers_version": "5.5.0",
            "model_generation_calls_planned": 1,
            "policy_changed": False,
        },
        "resolved": {
            "submitted": submitted,
            "resolved": effective,
            "model_kwargs_keys": ["attention_mask", "input_ids"],
        },
        "length": {
            "before": effective,
            "after": length,
            "input_tokens": 4096,
            "model_input_name": "input_ids",
        },
        "restored": {"methods_restored": True, "hook_calls": calls},
        "completed": {
            "model_generation_calls": 1,
            "hook_calls": calls,
            "resolved_sha256": text_hash(canonical_json(effective)),
            "length_sha256": text_hash(canonical_json(length)),
            "methods_restored": True,
            "policy_changed": False,
        },
    }
    for stage in names:
        equal(
            read_record(root / f"{stage}.json"),
            {**base, "stage": stage, **expected[stage]},
            "policy " + stage,
        )
    equal(inventory(root), hashes, "policy changed during audit")
    return {
        "protocol": "generation_policy_audit_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_authenticated": False,
        "resolved": effective,
        "length": length,
        "raw_sha256": hashes,
        "scope": "Observed resolution and length stages; not all later generation internals",
    }
