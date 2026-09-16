"""Read-only runtime/cache/witness/constraint join; native release admission is separate."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.constrained_runtime_v1 import RUNTIME_VERSION
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, bind
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY, complete
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.guard_diagnostic_audit_v2 import Witness, _records
from react_agent.validation.guard_diagnostic_audit_v2 import audit as original_join
from react_agent.validation.pair_runtime_audit_v3 import audit_task as original_task


def cache_encoding(value: Any) -> str:
    """Extend only the exact cache-key object; leave every other canonical hash intact."""
    if type(value) is dict and set(value) == {"model", "revision", "prompt", "generation", "input"}:
        value = dict(value, protocol="constrained_classifier_v1", decoding=IDENTITY)
    return canonical_json(value)


def audit_task(output: Path) -> dict[str, Any]:
    result = cast(
        dict[str, Any], bind(original_task, PROMPT=PROMPT, canonical_json=cache_encoding)(output)
    )
    if result["runtime_present"]:
        meta = read_record(output / "runtime/run_metadata.json")
        for key, expected in dict(
            runtime_version=RUNTIME_VERSION,
            constrained_execution_identity=IDENTITY,
            guard_cache_protocol="constrained_classifier_v1",
            guard_prompt_hash=text_hash(PROMPT),
        ).items():
            equal(meta[key], expected, "constrained runtime " + key)
    return result


def audit_join(execution: Path, sidecar: Path, witness: Path, constrained: Path) -> dict[str, Any]:
    before = inventory(constrained) if constrained.exists() else {}
    result = cast(
        dict[str, Any], bind(original_join, audit_task=audit_task)(execution, sidecar, witness)
    )
    receipt = read_record(execution / "pair_runtime.json")
    attempts = receipt["snapshot"]["workers"]["guard"]["attempts"][1:]
    witnesses = _records(witness.read_bytes() if witness.exists() else b"", Witness)
    by_sequence = {r.worker_sequence: r for r in witnesses}
    identity = receipt["pair_config"]["guard"]
    joined = []
    expected: set[str] = set()
    incomplete = []
    for index, attempt in enumerate(attempts, 1):
        name = f"request_{index:06d}"
        binding = dict(
            pid=attempt["pid"],
            model_id=identity["model_id"],
            model_revision=identity["model_revision"],
            request_index=index,
            request_sha256=attempt["request_sha256"],
            generation_sha256=attempt["generation_sha256"],
        )
        if attempt["status"] == "OK":
            checked = complete(
                constrained / name, binding, by_sequence[attempt["sequence"]].response_sha256
            )
            expected.update(name + "/" + p for p in checked["raw_sha256"])
            joined.append(dict(request_index=index, **checked))
        else:
            # Preserve missing/partial failure evidence, never promote it to completion.
            partial = inventory(constrained / name) if (constrained / name).exists() else {}
            if "completed.json" in partial:
                raise ValueError("failed transport with completed constraint evidence needs review")
            for filename in partial:
                if filename not in {"entered.json", "admitted.json", "error.json", "restored.json"}:
                    raise ValueError("unknown failed constraint stage")
                row = read_record(constrained / name / filename)
                for key, value in dict(
                    protocol="constrained_policy_worker_v1", stage=filename[:-5], **binding
                ).items():
                    equal(row[key], value, "failed constraint binding")
            expected.update(name + "/" + p for p in partial)
            incomplete.append(dict(request_index=index, raw_sha256=partial))
    equal(sorted(before), sorted(expected), "no unreported constrained requests")
    if constrained.exists():
        expected_tree = set(expected) | {p.split("/")[0] for p in expected}
        equal(
            sorted(p.relative_to(constrained).as_posix() for p in constrained.rglob("*")),
            sorted(expected_tree),
            "exact constrained evidence tree",
        )
    equal(inventory(constrained) if constrained.exists() else {}, before, "constraint unchanged")
    return dict(
        protocol="constrained_runtime_join_v1",
        valid=True,
        observer=result,
        completed=joined,
        incomplete=incomplete,
        failed_constraint_completion_validated=False,
        raw_sha256=before,
        native_model_authenticated=False,
        guard_quality_validated=False,
        phase5_accepted=False,
    )
