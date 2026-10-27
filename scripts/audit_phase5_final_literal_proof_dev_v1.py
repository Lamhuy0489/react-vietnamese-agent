"""Fresh synthetic three-arm final-proof diagnostics; no benchmark/model input."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.normalization import normalize
from react_agent.foundation.runtime_hooks import derive
from react_agent.security_v1.final_entitlements_v2 import (
    extract_final_entitlement,
    release_final_with_entitlement,
)
from react_agent.security_v1.final_literal_proof_v1 import (
    LiteralProofError,
    PublicFieldApproval,
    issue_literal_proof,
    release_final_with_literal_proof,
)
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex as BaselineIndex
from react_agent.security_v1.value_origin_v4 import ValueOriginIndex

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/dev/final_literal_proof_v1/cases.json"
COUNTS = dict(user_collision=6, public_collision=4, leak=6, invalid_proof=6, unsupported=2)
ARMS = ("v3", "v4", "proof")


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    group: Literal["user_collision", "public_collision", "leak", "invalid_proof", "unsupported"]
    route: Literal["none", "user", "public"]
    user: str
    private: str
    private_sensitivity: Sensitivity
    private_trust: Trust
    public: dict[str, str] | None
    public_sensitivity: Sensitivity
    public_source: str
    proposed_final: str
    target: str
    fault: Literal[
        "none", "wrong_pin", "wrong_field", "s2_public", "wrong_source", "extra_key", "forged_hash"
    ]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(path: Path = CASES) -> tuple[Case, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"protocol", "scope", "cases"} or (
        payload["protocol"] != "phase5_final_literal_proof_dev_v1"
        or payload["scope"] != "synthetic_dev_diagnostic_not_phase3_benchmark"
    ):
        raise ValueError("unexpected matrix scope or fields")
    cases = tuple(Case.model_validate(row) for row in payload["cases"])
    if Counter(c.group for c in cases) != COUNTS or len({c.id for c in cases}) != len(cases):
        raise ValueError("changed matrix counts or duplicate IDs")
    for case in cases:
        if not case.id or not case.target or case.target not in case.private:
            raise ValueError("missing private target")
        if case.private_sensitivity == Sensitivity.PUBLIC:
            raise ValueError("sensitive source cannot be public")
        if case.target not in normalize(case.proposed_final, "security_v1").normalized_text:
            raise ValueError("forced final lacks target even after normalization")
        if (case.group == "invalid_proof") != (case.fault != "none"):
            raise ValueError("invalid proof group/fault mismatch")
        if case.group == "user_collision" and case.target not in case.user:
            raise ValueError("user collision lacks raw authorization")
        if case.group == "public_collision" and case.target not in (case.public or {}).values():
            raise ValueError("public collision lacks public literal")
    return cases


def run_case(case: Case, arm: str, sequence: int) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError("unknown arm")
    store = ArtifactStore(f"proof_matrix_{arm}_{sequence:02d}")
    user = store.create(
        case.user, artifact_type=ArtifactType.USER_INPUT, source_type=SourceType.USER,
        source_id="synthetic_user", producer="host_context", created_step=0,
        sensitivity=Sensitivity.PUBLIC, trust=Trust.UNTRUSTED,
    )
    private = store.create(
        {"content": case.private}, artifact_type=ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.DOCUMENT, source_id="MATRIX_PRIVATE",
        producer="tool_source_snapshot", created_step=1,
        sensitivity=case.private_sensitivity, trust=case.private_trust,
    )
    public = None
    if case.public is not None:
        content = dict(case.public)
        if case.fault == "wrong_field":
            content = {"other_field": case.target}
        elif case.fault == "extra_key":
            content["extra"] = "unreviewed text"
        public = store.create(
            content, artifact_type=ArtifactType.DOCUMENT_CONTENT,
            source_type=SourceType.DOCUMENT,
            source_id="OTHER_PUBLIC" if case.fault == "wrong_source" else case.public_source,
            producer="tool_source_snapshot", created_step=2,
            sensitivity=Sensitivity.CONFIDENTIAL
            if case.fault == "s2_public" else case.public_sensitivity,
            trust=Trust.UNTRUSTED,
        )
    index = (BaselineIndex if arm == "v3" else ValueOriginIndex)(store)
    roots = [user, private] + ([public] if public else [])
    for root in roots:
        index.add_artifact(root.artifact_id, observed_step=root.created_step)
    model = derive(
        store, "synthetic forced proposal", kind=ArtifactType.MODEL_OUTPUT,
        parents=tuple(root.artifact_id for root in roots), step=3,
    )
    proposal = derive(
        store, case.proposed_final, kind=ArtifactType.FINAL_RESPONSE,
        parents=(model.artifact_id,), step=4,
    )
    grant = extract_final_entitlement(case.user)
    proof_hash = None
    count_before = len(store.all())
    try:
        if arm == "proof" and case.route != "none":
            if not isinstance(index, ValueOriginIndex):
                raise TypeError("candidate index required")
            approval = PublicFieldApproval(
                source_id="MATRIX_PUBLIC",
                field_name="content" if case.id == "actual_doc_read_shape" else "room_code",
                review_ref="synthetic-assistant-self-review-not-owner-attestation",
            ) if case.route == "public" else None
            expected = approval.identity if approval is not None else None
            if case.fault == "wrong_pin":
                expected = "0" * 64
            proof = issue_literal_proof(
                index, user.artifact_id,
                public.artifact_id if public is not None else user.artifact_id,
                approval=approval, expected_approval_sha256=expected,
            )
            if case.fault == "forged_hash":
                proof = proof.model_copy(update={"source_sha256": "0" * 64})
            proof_hash = proof.identity
            release = release_final_with_literal_proof(
                index, proposal.artifact_id, user.artifact_id, grant, proof,
                approval=approval, expected_approval_sha256=expected,
            )
        else:
            release = release_final_with_entitlement(
                index, proposal.artifact_id, user.artifact_id, grant
            )
    except LiteralProofError:
        if len(store.all()) != count_before:
            raise ValueError("failed proof created an artifact") from None
        released, effect, rejected = "", "ADMISSION_REJECTED", True
    else:
        released = str(store.get(release.released_artifact_id).content())
        effect, rejected = release.effect.value, False
    present = case.target in normalize(released, "security_v1").normalized_text
    passed = (
        None if case.group == "unsupported" or (
            case.group == "invalid_proof" and arm != "proof"
        ) else
        released == case.proposed_final if case.group.endswith("collision") else
        rejected if case.group == "invalid_proof" else not present
    )
    return dict(
        released=released, effect=effect, admission_rejected=rejected,
        target_present_after_normalization=present, exact=released == case.proposed_final,
        desired_pass=passed, proof_sha256=proof_hash,
    )


def audit(path: Path = CASES) -> dict[str, Any]:
    rows: list[dict[str, Any]] = [
        dict(id=c.id, group=c.group, **{a: run_case(c, a, i) for a in ARMS})
        for i, c in enumerate(load_cases(path), 1)
    ]
    summary = {
        group: {arm: dict(
            total=count,
            scored=0 if group == "unsupported" or (
                group == "invalid_proof" and arm != "proof"
            ) else count,
            desired_pass=None if group == "unsupported" or (
                group == "invalid_proof" and arm != "proof"
            ) else sum(
                row[arm]["desired_pass"] is True for row in rows if row["group"] == group
            ),
        ) for arm in ARMS} for group, count in COUNTS.items()
    }
    return dict(
        protocol="phase5_final_literal_proof_dev_receipt_v1", summary=summary, rows=rows,
        input_sha256=digest(path), auditor_sha256=digest(Path(__file__)),
        sources={name: digest(ROOT / f"src/react_agent/security_v1/{name}.py") for name in (
            "value_origin_v3", "value_origin_v4", "final_entitlements_v2", "final_literal_proof_v1"
        )},
        cpu_adapter_admitted=all(r["proof"]["desired_pass"] is not False for r in rows),
        native_model_runs=0, held_out_test_loaded=False, phase5_accepted=False,
        public_field_runtime_admitted=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/evaluation"):
        raise ValueError("fresh build/evaluation output required")
    receipt = audit()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(
        summary=receipt["summary"], cpu_adapter_admitted=receipt["cpu_adapter_admitted"]
    )))


if __name__ == "__main__":
    main()
