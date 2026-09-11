"""Read-only join of frozen context/policy proof and new attention sidecars."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.context_policy_audit_v1 import audit_combined
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.guard_probe_audit_v2 import require


def audit_attention(root: Path, probe: Path) -> dict[str, Any]:
    before = inventory(root)
    equal(
        sorted(before),
        sorted(
            f"{r}/{s}.json"
            for r in ("agent", "guard")
            for s in ("entered", "dispatch_1", "dispatch_2", "restored", "completed")
        ),
        "attention inventory",
    )
    workers = read_record(probe / "closed.json")["workers"]
    summaries = {}
    for role, total, boundary, heads in (("agent", 14364, 4608, 28), ("guard", 3612, 4224, 12)):
        records = {
            s: read_record(root / role / f"{s}.json")
            for s in ("entered", "dispatch_1", "dispatch_2", "restored", "completed")
        }
        native = read_record(probe / f"{role}_stress/entered.json")
        common = dict(
            protocol="efficient_stress_v1",
            pid=workers[role]["attempts"][0]["pid"],
            role=role,
            model_id=native["model_id"],
            model_revision=native["model_revision"],
        )
        for stage, record in records.items():
            for k, v in {**common, "stage": stage}.items():
                equal(record[k], v, "attention identity " + k)
        entered, restored, completed = (records[s] for s in ("entered", "restored", "completed"))
        equal(
            entered["hf_sdpa_sha256"],
            "87f933d1a2d8508df572da5c0748c6b24c22ff2b625796949957dcd86cc57564",
            "native integration hash",
        )
        equal(
            entered["numerical_treatment"], "HF repeat_kv + forced EFFICIENT_ATTENTION", "treatment"
        )
        equal(entered["planned_attention_calls"], total, "planned calls")
        require(
            entered["decoding_changed"] is False and completed["decoding_changed"] is False,
            "unchanged decoding",
        )
        flags = entered["flags_before"]
        equal(
            sorted(flags),
            sorted(("flash", "math", "mem_efficient", "cudnn")),
            "backend flag coverage",
        )
        require(all(type(v) is bool for v in flags.values()), "boolean flags")
        equal(restored["flags_after"], flags, "backend flags restored")
        for record in (restored, completed):
            require(record["state_restored"] is True, "native state restored")
            for name in ("completed_attention_calls", "helper_calls"):
                equal(record[name], total, "complete attention coverage")
        masks = completed["masks"]
        equal(sorted(masks), ["explicit", "none"], "mask coverage")
        require(
            all(type(v) is int and v >= 0 for v in masks.values()) and sum(masks.values()) == total,
            "mask call counts",
        )
        samples = completed["dispatch_samples"]
        require(type(samples) is list and len(samples) == 2, "two actual dispatch samples")
        for number, (index, query, key) in enumerate(
            ((0, 4096, 4096), (total - 28, 1, boundary)), 1
        ):
            sample = samples[number - 1]
            equal(records[f"dispatch_{number}"]["sample"], sample, "durable dispatch sample")
            for k, v in dict(
                index=index,
                query_tokens=query,
                key_tokens=key,
                heads=heads,
                device=0 if role == "agent" else 1,
            ).items():
                equal(sample[k], v, "sample geometry " + k)
            equal(
                sorted(sample["operators"]),
                [
                    "aten::_scaled_dot_product_efficient_attention",
                    "aten::scaled_dot_product_attention",
                ],
                "actual efficient dispatch",
            )
        summaries[role] = dict(
            completed_attention_calls=total,
            masks=masks,
            dispatch_samples=samples,
            state_restored=True,
        )
    equal(inventory(root), before, "attention raw mutated")
    return dict(
        protocol="efficient_attention_audit_v1",
        valid=True,
        phase5_accepted=False,
        roles=summaries,
        input_sha256=before,
        scope="Two profiled calls per role plus efficient-only guards on all calls; "
        "not full model parity or benchmark latency",
    )


def audit(
    probe: Path, policy: Path, attention: Path, publishers: Path, pin: GuardSnapshot, commit: str
) -> dict[str, Any]:
    for other in (probe, policy, publishers):
        require(
            not attention.resolve().is_relative_to(other.resolve())
            and not other.resolve().is_relative_to(attention.resolve()),
            "separate attention artifacts",
        )
    combined = audit_combined(probe, policy, publishers, pin, commit)
    treatment = audit_attention(attention, probe)
    return dict(
        protocol="efficient_context_combined_audit_v1",
        valid=True,
        phase5_accepted=False,
        combined=combined,
        attention=treatment,
        source_authenticated=False,
        scope="Artifact consistency only; outer remote source authentication required",
    )
