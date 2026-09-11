"""Synthetic sidecars and deliberate corruptions; not native performance data."""

import json
from pathlib import Path
from typing import Any

import pytest
from test_context_policy_audit_v1 import combined as combined
from test_context_policy_audit_v1 import write

from react_agent.validation.context_stress_audit_v1 import read_record
from react_agent.validation.efficient_stress_audit_v1 import audit, audit_attention


def sidecars(root: Path, probe: Path) -> None:
    workers = read_record(probe / "closed.json")["workers"]
    for role, total, end, heads in (("agent", 14364, 4608, 28), ("guard", 3612, 4224, 12)):
        native = read_record(probe / f"{role}_stress/entered.json")
        common = dict(
            protocol="efficient_stress_v1",
            role=role,
            pid=workers[role]["attempts"][0]["pid"],
            model_id=native["model_id"],
            model_revision=native["model_revision"],
        )
        flags = dict(flash=True, math=True, mem_efficient=True, cudnn=True)
        samples = [
            dict(
                index=i,
                query_tokens=q,
                key_tokens=k,
                heads=heads,
                device=0 if role == "agent" else 1,
                operators=[
                    "aten::_scaled_dot_product_efficient_attention",
                    "aten::scaled_dot_product_attention",
                ],
            )
            for i, q, k in ((0, 4096, 4096), (total - 28, 1, end))
        ]
        records = {
            "entered": dict(
                hf_sdpa_sha256="87f933d1a2d8508df572da5c0748c6b24c22ff2b625796949957dcd86cc57564",
                flags_before=flags,
                planned_attention_calls=total,
                numerical_treatment="HF repeat_kv + forced EFFICIENT_ATTENTION",
                decoding_changed=False,
            ),
            "dispatch_1": dict(sample=samples[0]),
            "dispatch_2": dict(sample=samples[1]),
            "restored": dict(
                state_restored=True,
                flags_after=flags,
                completed_attention_calls=total,
                helper_calls=total,
            ),
            "completed": dict(
                state_restored=True,
                completed_attention_calls=total,
                helper_calls=total,
                masks=dict(none=total, explicit=0),
                dispatch_samples=samples,
                decoding_changed=False,
            ),
        }
        for stage, values in records.items():
            write(root / role / f"{stage}.json", {**common, "stage": stage, **values})


def test_join_repeatable_readonly(combined: Any, tmp_path: Path) -> None:
    probe, policy, publishers, pin, commit = combined
    root = tmp_path / "attention"
    sidecars(root, probe)
    result = audit(probe, policy, root, publishers, pin, commit)
    assert result == audit(probe, policy, root, publishers, pin, commit)
    assert result["valid"] and not result["source_authenticated"]
    assert len(result["attention"]["input_sha256"]) == 10


@pytest.mark.parametrize(
    "fault",
    [
        "pid",
        "model",
        "helper",
        "count",
        "bool_count",
        "restore",
        "flags",
        "hash",
        "decode",
        "mask",
        "mask_bool",
        "operator",
        "sample",
        "shape",
        "device",
        "extra",
        "missing",
        "duplicate_json",
    ],
)
def test_bad_sidecars_refused(combined: Any, tmp_path: Path, fault: str) -> None:
    probe = combined[0]
    root = tmp_path / "attention"
    sidecars(root, probe)
    name = "completed"
    if fault in ("flags", "restore"):
        name = "restored"
    if fault == "hash":
        name = "entered"
    p = root / "agent" / (name + ".json")
    value = json.loads(p.read_text())
    if fault == "pid":
        value["pid"] += 1
    elif fault == "model":
        value["model_id"] = "different"
    elif fault == "helper":
        value["helper_calls"] -= 1
    elif fault == "count":
        value["completed_attention_calls"] -= 1
    elif fault == "bool_count":
        value["completed_attention_calls"] = True
    elif fault == "restore":
        value["state_restored"] = False
    elif fault == "flags":
        value["flags_after"]["math"] = False
    elif fault == "hash":
        value["hf_sdpa_sha256"] = "0" * 64
    elif fault == "decode":
        value["decoding_changed"] = True
    elif fault == "mask":
        value["masks"]["none"] -= 1
    elif fault == "mask_bool":
        value["masks"]["explicit"] = False
    elif fault == "operator":
        value["dispatch_samples"][0]["operators"] = ["aten::_scaled_dot_product_attention_math"]
    elif fault == "sample":
        value["dispatch_samples"] = value["dispatch_samples"][:1]
    elif fault == "shape":
        value["dispatch_samples"][1]["key_tokens"] -= 1
    elif fault == "device":
        value["dispatch_samples"][0]["device"] = 1
    elif fault == "extra":
        write(root / "extra.json", {})
    elif fault == "missing":
        (root / "guard/dispatch_2.json").unlink()
    if fault == "duplicate_json":
        p.write_text('{"pid":1,"pid":2}')
    else:
        write(p, value)
    with pytest.raises((ValueError, KeyError)):
        audit_attention(root, probe)
