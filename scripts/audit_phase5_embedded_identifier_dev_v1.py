"""Reproduce the synthetic Dev v3/v4 final-sink matrix without model inference."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.runtime_hooks import derive
from react_agent.security_v1.final_entitlements_v2 import (
    extract_final_entitlement,
    release_final_with_entitlement,
)
from react_agent.security_v1.value_origin import ValueType
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex as FrozenIndex
from react_agent.security_v1.value_origin_v4 import ValueOriginIndex as CandidateIndex

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/dev/embedded_identifier_v1/cases.json"
V3 = ROOT / "src/react_agent/security_v1/value_origin_v3.py"
V4 = ROOT / "src/react_agent/security_v1/value_origin_v4.py"
COUNTS = {"leak": 6, "benign": 6, "collision": 3, "unsupported": 3}


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    group: Literal["leak", "benign", "collision", "unsupported"]
    user: str
    private: str
    private_sensitivity: Sensitivity
    private_trust: Trust
    public: str | None
    proposed_final: str
    target: str
    desired: Literal["omit_target", "exact", "observe"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(path: Path = CASES) -> tuple[Case, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"protocol", "scope", "cases"} or (
        payload["protocol"] != "phase5_embedded_identifier_dev_matrix_v1"
        or payload["scope"] != "synthetic_dev_diagnostic_not_phase3_benchmark"
    ):
        raise ValueError("unexpected Dev matrix protocol or fields")
    cases = tuple(Case.model_validate(row) for row in payload["cases"])
    if len({case.id for case in cases}) != len(cases) or Counter(
        case.group for case in cases
    ) != COUNTS:
        raise ValueError("duplicate IDs or changed predeclared group counts")
    for case in cases:
        if not case.id or not case.user or not case.private or not case.target:
            raise ValueError("empty Dev case field")
        if case.private_sensitivity == Sensitivity.PUBLIC:
            raise ValueError("private Dev source cannot be S0")
        if case.target not in case.proposed_final:
            raise ValueError("target absent from forced final")
        desired = {
            "leak": "omit_target",
            "benign": "exact",
            "collision": "exact",
            "unsupported": "observe",
        }[case.group]
        if case.desired != desired:
            raise ValueError("desired outcome conflicts with predeclared group")
        if case.group in {"leak", "collision"} and case.target not in case.private:
            raise ValueError("sensitive target absent from source")
        if case.group == "benign" and case.target in case.private:
            raise ValueError("benign target collides with private source")
        if case.group == "collision" and case.target not in (case.user + (case.public or "")):
            raise ValueError("collision target lacks user/public occurrence")
    return cases


def run_case(case: Case, arm: Literal["v3", "v4"], sequence: int) -> dict[str, object]:
    store = ArtifactStore(f"embedded_matrix_{arm}_{sequence:02d}")
    user = store.create(
        case.user,
        artifact_type=ArtifactType.USER_INPUT,
        source_type=SourceType.USER,
        source_id="synthetic_user",
        producer="host_context",
        created_step=0,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.UNTRUSTED,
    )
    private = store.create(
        {"content": case.private},
        artifact_type=ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.DOCUMENT,
        source_id="DEV_PRIVATE",
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=case.private_sensitivity,
        trust=case.private_trust,
    )
    public = None
    if case.public is not None:
        public = store.create(
            {"content": case.public},
            artifact_type=ArtifactType.DOCUMENT_CONTENT,
            source_type=SourceType.DOCUMENT,
            source_id="DEV_PUBLIC",
            producer="tool_source_snapshot",
            created_step=2,
            sensitivity=Sensitivity.PUBLIC,
            trust=Trust.UNTRUSTED,
        )
    index = (FrozenIndex if arm == "v3" else CandidateIndex)(store)
    index.add_artifact(user.artifact_id, observed_step=0)
    index.add_artifact(private.artifact_id, observed_step=1)
    parents = [user.artifact_id, private.artifact_id]
    if public is not None:
        index.add_artifact(public.artifact_id, observed_step=2)
        parents.append(public.artifact_id)
    model = derive(
        store,
        "synthetic forced Replay proposal",
        kind=ArtifactType.MODEL_OUTPUT,
        parents=tuple(parents),
        step=3,
    )
    proposed = derive(
        store,
        case.proposed_final,
        kind=ArtifactType.FINAL_RESPONSE,
        parents=(model.artifact_id,),
        step=4,
    )
    decision = release_final_with_entitlement(
        index,
        proposed.artifact_id,
        user.artifact_id,
        extract_final_entitlement(case.user),
    )
    released = str(store.get(decision.released_artifact_id).content())
    passed = (
        case.target not in released
        if case.desired == "omit_target"
        else released == case.proposed_final
        if case.desired == "exact"
        else None
    )
    return {
        "effect": decision.effect.value,
        "released": released,
        "target_present": case.target in released,
        "exact": released == case.proposed_final,
        "desired_pass": passed,
        "protected_match_count": len(decision.matches),
        "sensitive_identifier_origin_count": sum(
            record.value_type == ValueType.IDENTIFIER
            and record.sensitivity > Sensitivity.PUBLIC
            for record in index.records
        ),
    }


def audit(path: Path = CASES) -> dict[str, object]:
    cases = load_cases(path)
    rows: list[dict[str, object]] = []
    for sequence, case in enumerate(cases, start=1):
        rows.append(
            {
                "id": case.id,
                "group": case.group,
                "desired": case.desired,
                "v3": run_case(case, "v3", sequence),
                "v4": run_case(case, "v4", sequence),
            }
        )
    summary: dict[str, dict[str, dict[str, int | None]]] = {}
    for group, total in COUNTS.items():
        summary[group] = {}
        for arm in ("v3", "v4"):
            group_rows: list[dict[str, object]] = []
            for row in rows:
                if row["group"] == group:
                    item = row[arm]
                    if not isinstance(item, dict):
                        raise ValueError("invalid internal arm result")
                    group_rows.append(item)
            scored = sum(item["desired_pass"] is not None for item in group_rows)
            summary[group][arm] = {
                "total": total,
                "scored": scored,
                "desired_pass": (
                    sum(item["desired_pass"] is True for item in group_rows)
                    if scored
                    else None
                ),
                "suppressed": sum(item["exact"] is False for item in group_rows),
                "target_released": sum(item["target_present"] is True for item in group_rows),
            }
    return {
        "protocol": "phase5_embedded_identifier_dev_matrix_receipt_v1",
        "scope": "synthetic_dev_diagnostic_not_phase3_benchmark",
        "case_source_sha256": digest(path),
        "auditor_sha256": digest(Path(__file__)),
        "v3_source_sha256": digest(V3),
        "v4_source_sha256": digest(V4),
        "model_inference_runs": 0,
        "held_out_test_loaded": False,
        "private_benchmark_ground_truth_loaded": False,
        "runtime_integrated": False,
        "phase5_accepted": False,
        "summary": summary,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/evaluation"):
        raise ValueError("fresh build/evaluation output required")
    receipt = audit()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
