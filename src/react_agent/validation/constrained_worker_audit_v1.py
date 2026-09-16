"""Bounded constraint receipt consistency; not proof of native model execution."""

from pathlib import Path
from typing import Any

from react_agent.validation.context_stress_audit_v1 import (
    equal,
    fields,
    inventory,
    read_record,
    sha,
)

IDENTITY = "a3a5b0a2695dbf68426ccbec6785118ca3a30e320ccdfaea6f2d169679b5c425"
LANGUAGE = "f8df0c2892984e8c6520a8e3bcf4e91dc793d8950165e99284c904a93f6bc3fb"
POLICY = "fbe63d97727be376a45d5b484ea70147e7724231dc625118515e5f2188c2d69f"


def complete(root: Path, binding: dict[str, Any], response_sha: str) -> dict[str, Any]:
    before = inventory(root)
    equal(
        sorted(before),
        ["admitted.json", "completed.json", "entered.json", "restored.json"],
        "complete constraint files",
    )
    equal(sorted(p.name for p in root.iterdir()), sorted(before), "no extra request directory")
    records = {}
    for stage in ("entered", "admitted", "restored", "completed"):
        record = read_record(root / (stage + ".json"))
        common = dict(protocol="constrained_policy_worker_v1", stage=stage, **binding)
        for key, value in common.items():
            equal(record.pop(key), value, "constraint " + key)
        records[stage] = record
    equal(records["entered"], dict(execution_identity=IDENTITY), "entered identity")
    admitted, done = records["admitted"], records["completed"]
    fields(
        admitted,
        {"policy_sha256", "language_sha256", "processor_types", "input_tokens"},
        "constraint admission",
    )
    count = admitted["input_tokens"]
    if type(count) is not int or not 1 <= count <= 4096:
        raise ValueError("bounded input tokens required")
    equal(admitted["policy_sha256"], POLICY, "constraint policy")
    equal(admitted["language_sha256"], LANGUAGE, "constraint language")
    equal(
        admitted["processor_types"],
        ["RepetitionPenaltyLogitsProcessor", "PrefixConstrainedLogitsProcessor"],
        "ordered constraint processors",
    )
    fields(
        done,
        {"counts", "output_tokens", "output_token_sha256", "response_sha256", "execution_identity"},
        "constraint completion",
    )
    tokens = done["output_tokens"]
    if type(tokens) is not int or not 2 <= tokens <= 36:
        raise ValueError("bounded completed token count required")
    counts = dict(generate=1, processors=1, callbacks=tokens)
    equal(done["counts"], counts, "constraint counters")
    equal(done["execution_identity"], IDENTITY, "completed identity")
    sha(done["output_token_sha256"])
    sha(response_sha)
    equal(done["response_sha256"], response_sha, "received response hash")
    equal(records["restored"], dict(methods_restored=True, counts=counts), "restored scopes")
    equal(inventory(root), before, "constraint receipts unchanged")
    return dict(
        raw_sha256=before,
        input_tokens=count,
        output_tokens=tokens,
        response_sha256=response_sha,
        execution_identity=IDENTITY,
    )
