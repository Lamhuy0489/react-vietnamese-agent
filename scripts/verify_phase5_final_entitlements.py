#!/usr/bin/env python3
"""Hash-bound synthetic QA for host-bound private final entitlements."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
)
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import derive
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.final_entitlements import (
    EntitlementError,
    extract_final_entitlement,
    release_final_with_entitlement,
)
from react_agent.security_v1.value_origin import ValueOriginIndex

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    paths = [
        ROOT / "src/react_agent/security_v1/final_entitlements.py",
        ROOT / "tests/unit/test_final_entitlements_v1.py",
        Path(__file__).resolve(),
        ROOT / "docs/architecture/phase5_final_entitlements_contract.md",
    ]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def prior_evidence() -> dict[str, Any]:
    receipts = {}
    count = 0
    for name in (
        "phase4_closure_v1_validation01.json",
        "phase5_components_v1_validation01.json",
        "phase5_runtime_v1_validation01.json",
        "phase5_a2_v2_validation01.json",
        "phase5_session_v1_validation01.json",
        "phase5_value_origin_v1_validation01.json",
        "phase5_value_gates_v1_validation02.json",
        "phase5_a6_runtime_v1_validation01.json",
        "phase5_warm_guard_v1_validation01.json",
        "phase5_processing_scope_v1_validation01.json",
    ):
        path = ROOT / "experiments/manifests" / name
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if receipt["valid"] is not True:
            raise ValueError("invalid prior evidence")
        for relative, expected in receipt["source_sha256"].items():
            if digest(ROOT / relative) != expected:
                raise ValueError("frozen source changed: " + relative)
            count += 1
        receipts[name] = digest(path)
    return {"receipt_sha256": receipts, "source_hash_entries_checked": count}


def fixture(
    user_text: str,
    final_text: str,
    *,
    source_id: str = "DOC_PRIVATE",
    trust: Trust = Trust.TRUSTED,
    content: object | None = None,
    admit_source: bool = True,
) -> tuple[ArtifactStore, ValueOriginIndex, str, str]:
    store = ArtifactStore("synthetic_entitlement_qa")
    user = store.create(
        user_text,
        artifact_type=ArtifactType.USER_INPUT,
        source_type=SourceType.USER,
        source_id="synthetic_user",
        producer="host_context",
        created_step=0,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.UNTRUSTED,
    )
    source = store.create(
        content if content is not None else {"gpa": 3.2},
        artifact_type=ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.DOCUMENT,
        source_id=source_id,
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=Sensitivity.CONFIDENTIAL,
        trust=trust,
    )
    index = ValueOriginIndex(store)
    index.add_artifact(user.artifact_id, observed_step=0)
    if admit_source:
        index.add_artifact(source.artifact_id, observed_step=1)
    model = derive(
        store,
        "synthetic model output",
        kind=ArtifactType.MODEL_OUTPUT,
        parents=(user.artifact_id, source.artifact_id),
        step=2,
    )
    proposal = derive(
        store,
        final_text,
        kind=ArtifactType.FINAL_RESPONSE,
        parents=(model.artifact_id,),
        step=3,
    )
    return store, index, user.artifact_id, proposal.artifact_id


def record(output: Path, name: str, check: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    destination = output / name
    destination.mkdir(parents=True, exist_ok=False)
    result = {"case": name, **check(), "valid": True}
    (destination / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def allowed() -> dict[str, Any]:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = fixture(text, "GPA: 3.2")
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    if (
        decision.effect != Effect.ALLOW
        or store.get(decision.released_artifact_id).content() != "GPA: 3.2"
    ):
        raise ValueError("authorized private value was not released")
    return {
        "effect": decision.effect.value,
        "authorized_matches": len(decision.authorized_matches),
    }


def redacted() -> dict[str, Any]:
    text = "Đọc DOC_PRIVATE và tóm tắt"
    store, index, user, proposal = fixture(text, "GPA: 3.2")
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    if (
        decision.effect != Effect.REDACT
        or store.get(decision.released_artifact_id).content() != "GPA: [REDACTED]"
    ):
        raise ValueError("missing entitlement did not redact")
    return {"effect": decision.effect.value, "redacted_spans": len(decision.redacted_spans)}


def untrusted() -> dict[str, Any]:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = fixture(text, "GPA: 3.2", trust=Trust.UNTRUSTED)
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    if decision.effect != Effect.REDACT:
        raise ValueError("untrusted origin received an entitlement")
    return {"effect": decision.effect.value}


def wrong_source() -> dict[str, Any]:
    text = "Trả GPA từ DOC_ALLOWED trong câu trả lời"
    store, index, user, proposal = fixture(text, "GPA: 3.2", source_id="DOC_OTHER")
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    if decision.effect != Effect.REDACT:
        raise ValueError("cross-source entitlement was accepted")
    return {"effect": decision.effect.value}


def mixed_types() -> dict[str, Any]:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = fixture(
        text,
        "GPA: 3.2; email: private@example.test",
        content={"gpa": 3.2, "email": "private@example.test"},
    )
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    released = store.get(decision.released_artifact_id).content()
    if decision.effect != Effect.REDACT or released != "GPA: 3.2; email: [REDACTED]":
        raise ValueError("unentitled value type was not redacted")
    return {"effect": decision.effect.value, "authorized": len(decision.authorized_matches)}


def normalized_only() -> dict[str, Any]:
    text = "Trả email từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = fixture(
        text, "private\u200b@example.test", content={"email": "private@example.test"}
    )
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    if (
        decision.effect != Effect.DENY
        or store.get(decision.released_artifact_id).content() != ""
    ):
        raise ValueError("normalized-only match did not deny")
    return {"effect": decision.effect.value}


def missing_coverage() -> dict[str, Any]:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = fixture(text, "GPA: 3.2", admit_source=False)
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    if (
        decision.effect != Effect.DENY
        or store.get(decision.released_artifact_id).content() != ""
    ):
        raise ValueError("missing source coverage did not deny")
    return {"effect": decision.effect.value, "index_complete": index.complete}


def hash_binding() -> dict[str, Any]:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = fixture(text, "GPA: 3.2")
    try:
        release_final_with_entitlement(
            index,
            proposal,
            user,
            extract_final_entitlement("Trả GPA từ DOC_OTHER trong câu trả lời"),
        )
    except EntitlementError:
        return {"mismatch_rejected": True, "artifact_count": len(store.all())}
    raise ValueError("raw-user hash mismatch was accepted")


def public_no_match() -> dict[str, Any]:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = fixture(
        text, "Không có dữ liệu riêng", content={"title": "Public"}
    )
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    if decision.effect != Effect.ALLOW:
        raise ValueError("public no-match final was blocked")
    return {"effect": decision.effect.value, "matches": len(decision.matches)}


def serializable_labels() -> dict[str, Any]:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = fixture(text, "GPA: 3.2")
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    round_trip = type(decision).model_validate_json(decision.model_dump_json())
    released = store.get(decision.released_artifact_id)
    if round_trip != decision or released.sensitivity != Sensitivity.CONFIDENTIAL:
        raise ValueError("release serialization or labels changed")
    return {"round_trip": True, "sensitivity": released.sensitivity.value}


def cue_inventory() -> dict[str, Any]:
    cues = (
        ("email", "EMAIL"),
        ("URL", "URL"),
        ("student id", "STUDENT_ID"),
        ("course code", "COURSE_CODE"),
        ("phone", "PHONE"),
        ("money", "MONEY"),
        ("date", "DATE"),
        ("identifier", "IDENTIFIER"),
    )
    for cue, expected in cues:
        entitlement = extract_final_entitlement(f"Show {cue} from DOC_PRIVATE")
        if not entitlement.explicit or entitlement.value_types != (expected,):
            raise ValueError("unsupported entitlement cue")
    return {"supported_value_cues": len(cues)}


def rejected_clauses() -> dict[str, Any]:
    values = (
        "Không trả GPA từ DOC_PRIVATE",
        "Nếu cần trả GPA từ DOC_PRIVATE",
        "Trả GPA từ 'DOC_PRIVATE'",
        "Đọc tài liệu DOC_PRIVATE",
    )
    if any(extract_final_entitlement(value).explicit for value in values):
        raise ValueError("rejected clause became an entitlement")
    return {"rejected_clauses": len(values)}


def all_cases(output: Path) -> list[dict[str, Any]]:
    if output.exists():
        raise ValueError("fresh final-entitlement QA output required")
    output.mkdir(parents=True)
    cases = (
        ("allowed", allowed),
        ("redacted", redacted),
        ("untrusted", untrusted),
        ("wrong_source", wrong_source),
        ("mixed_types", mixed_types),
        ("normalized_only", normalized_only),
        ("missing_coverage", missing_coverage),
        ("hash_binding", hash_binding),
        ("public_no_match", public_no_match),
        ("serializable_labels", serializable_labels),
        ("cue_inventory", cue_inventory),
        ("rejected_clauses", rejected_clauses),
    )
    return [record(output, name, check) for name, check in cases]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    output, report = args.output.resolve(), args.report.resolve()
    if output.exists() or report.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("fresh results output/report required")
    if not any(report.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")):
        raise ValueError("report must be under results/manifests")
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git required")
    commit = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603
    clean = not subprocess.check_output([git, "status", "--porcelain"], cwd=ROOT, text=True)  # noqa: S603
    hashes = source_hashes()
    reference = json.loads(args.reference.read_text(encoding="utf-8")) if args.reference else None
    if reference is not None and (not reference["valid"] or reference["source_sha256"] != hashes):
        raise ValueError("reference source mismatch")
    if report.is_relative_to(ROOT / "experiments/manifests") and (not clean or reference is None):
        raise ValueError("selected evidence requires clean source and matching preflight")
    prior = prior_evidence()
    checks = all_cases(output / "cases")
    if len(checks) != 12 or any(not row["valid"] for row in checks):
        raise ValueError("12 valid synthetic entitlement cases required")
    stable = text_hash(canonical_json(checks))
    if reference is not None and reference["stable_summary_sha256"] != stable:
        raise ValueError("preflight deterministic summary mismatch")
    quality: dict[str, Any] = {}
    commands = {
        "setup": [sys.executable, "scripts/verify_setup.py"],
        "ruff": [str(ROOT / ".venv/bin/ruff"), "check", "."],
        "mypy": [str(ROOT / ".venv/bin/mypy"), "src", "scripts"],
        "pytest": [sys.executable, "-m", "pytest"],
        "knowledge": [sys.executable, "scripts/validate_knowledge.py"],
    }
    for name, command in commands.items():
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603
        path = output / (name + ".log")
        path.write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode:
            raise ValueError("quality check failed: " + str(path))
        quality[name] = {"returncode": 0, "log_sha256": digest(path)}
    if source_hashes() != hashes or prior_evidence() != prior:
        raise ValueError("source/input changed during validation")
    result = {
        "schema_version": "phase5_final_entitlements_qa_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_git_commit": commit,
        "source_worktree_clean": clean,
        "source_sha256": hashes,
        "prior_evidence": prior,
        "profile": "final_entitlement_v1",
        "synthetic_conditions": len(checks),
        "checks": checks,
        "stable_summary_sha256": stable,
        "preflight_sha256": digest(args.reference) if args.reference else None,
        "preflight_matches": reference is not None,
        "quality": quality,
        "raw_output": output.relative_to(ROOT).as_posix(),
        "raw_sha256": {
            p.relative_to(output).as_posix(): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
        "real_model_runs": 0,
        "benchmark_dev_runs": 0,
        "test_payloads_parsed": 0,
        "scope": (
            "Host-bound private final entitlement component; no runtime adoption "
            "or model metrics"
        ),
        "remaining": [
            "Compose entitlement with A6 final gate in a new versioned runtime",
            "Broader origin-coverage assessment for unstructured/derived values",
            "Production guard model/revision and efficient GPU worker validation",
            "grouped Dev validation and freeze",
        ],
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("valid", "phase5_accepted", "synthetic_conditions")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
