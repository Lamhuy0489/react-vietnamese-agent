#!/usr/bin/env python3
"""Hash-bound synthetic QA for the bounded A4 processing-scope component."""

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

from react_agent.foundation.artifacts import SourceType, Trust, canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.processing_scope import (
    PROFILE,
    ProcessingScope,
    ScopeError,
    extract_scope_anchors,
)

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    paths = [
        ROOT / "src/react_agent/security_v1/processing_scope.py",
        ROOT / "tests/unit/test_processing_scope_v1.py",
        Path(__file__).resolve(),
        ROOT / "docs/architecture/phase5_processing_scope_contract.md",
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


def doc(identity: str) -> Action:
    return Action(name="doc_read", arguments={"doc_id": identity})


def page(identity: str) -> Action:
    return Action(name="cached_fetch", arguments={"page_id": identity})


def query(value: str) -> Action:
    return Action(name="db_query", arguments={"query": value})


def observe(
    scope: ProcessingScope,
    action: Action,
    artifact_id: str,
    trust: Trust,
    source_type: SourceType = SourceType.DOCUMENT,
    source_id: str | None = None,
) -> None:
    action_source_id = action.arguments.get("doc_id") if action.name == "doc_read" else None
    if not isinstance(action_source_id, str):
        action_source_id = None
    scope.observe(
        action,
        artifact_id=artifact_id,
        source_type=source_type,
        source_id=source_id if source_id is not None else action_source_id,
        trust=trust,
    )


def write_case(output: Path, name: str, check: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    destination = output / name
    destination.mkdir(parents=True, exist_ok=False)
    result = {"case": name, **check(), "valid": True}
    (destination / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def case_explicit_document() -> dict[str, Any]:
    scope = ProcessingScope("Đọc tài liệu DOC_001")
    allowed = scope.pre(doc("DOC_001"))
    denied = scope.pre(doc("DOC_002"))
    if allowed.effect != Effect.ALLOW or denied.effect != Effect.DENY:
        raise ValueError("explicit document scope expectation failed")
    return {"allowed_by": allowed.authorized_by, "denied_by": denied.authorized_by}


def case_explicit_cache() -> dict[str, Any]:
    scope = ProcessingScope("Xem trang CACHE_002")
    allowed = scope.pre(page("CACHE_002"))
    denied = scope.pre(page("CACHE_003"))
    if allowed.effect != Effect.ALLOW or denied.effect != Effect.DENY:
        raise ValueError("explicit cached-page scope expectation failed")
    return {"allowed_by": allowed.authorized_by, "denied_by": denied.authorized_by}


def case_explicit_database() -> dict[str, Any]:
    scope = ProcessingScope("Truy vấn table courses với column course_id và column gpa")
    allowed = scope.pre(query("SELECT course_id, gpa FROM courses"))
    wrong_table = scope.pre(query("SELECT course_id FROM students"))
    wrong_column = scope.pre(query("SELECT name FROM courses"))
    if any(d.effect != Effect.ALLOW for d in (allowed,)) or any(
        d.effect != Effect.DENY for d in (wrong_table, wrong_column)
    ):
        raise ValueError("explicit database scope expectation failed")
    return {"allowed_by": allowed.authorized_by, "denied": 2}


def case_untrusted_expansion() -> dict[str, Any]:
    scope = ProcessingScope("Tóm tắt tài liệu công khai")
    before = scope.pre(doc("DOC_001"))
    observe(scope, doc("DOC_001"), "ART_DOC_001", Trust.UNTRUSTED)
    repeat = scope.pre(doc("DOC_001"))
    expansion = scope.pre(doc("DOC_002"))
    if (
        before.effect != Effect.ALLOW
        or repeat.effect != Effect.ALLOW
        or expansion.effect != Effect.DENY
    ):
        raise ValueError("untrusted scope expansion was not blocked")
    return {
        "before": before.authorized_by,
        "repeat": repeat.authorized_by,
        "expansion": expansion.authorized_by,
    }


def case_untrusted_search() -> dict[str, Any]:
    scope = ProcessingScope("Tóm tắt")
    observe(scope, doc("DOC_001"), "ART_DOC_001", Trust.UNTRUSTED)
    decision = scope.pre(Action(name="doc_search", arguments={"query": "học phí"}))
    if decision.effect != Effect.DENY or decision.authorized_by != "unassessed_scope":
        raise ValueError("untrusted search must fail closed")
    return {"effect": decision.effect.value, "authorized_by": decision.authorized_by}


def case_trusted_no_trigger() -> dict[str, Any]:
    scope = ProcessingScope("Tóm tắt")
    observe(scope, doc("DOC_001"), "ART_DOC_001", Trust.TRUSTED)
    decision = scope.pre(doc("DOC_002"))
    if decision.effect != Effect.ALLOW or scope.state.untrusted_seen:
        raise ValueError("trusted observation triggered scope veto")
    return {"effect": decision.effect.value, "authorized_by": decision.authorized_by}


def case_malformed_database() -> dict[str, Any]:
    scope = ProcessingScope("Tóm tắt")
    observe(scope, doc("DOC_001"), "ART_DOC_001", Trust.UNTRUSTED)
    decision = scope.pre(query("SELECT * FROM courses"))
    if decision.effect != Effect.DENY or decision.authorized_by != "unassessed_scope":
        raise ValueError("malformed database scope must fail closed")
    return {"effect": decision.effect.value, "authorized_by": decision.authorized_by}


def case_delegated_actions() -> dict[str, Any]:
    scope = ProcessingScope("Tóm tắt")
    observe(scope, doc("DOC_001"), "ART_DOC_001", Trust.UNTRUSTED)
    actions = (
        Action(name="calculator", arguments={"expression": "1+1"}),
        Action(
            name="send_email_mock",
            arguments={"to": "demo@example.test", "subject": "s", "body": "b"},
        ),
        Action(
            name="post_webhook_mock",
            arguments={"endpoint": "mock://report", "payload": {"message": "b"}},
        ),
    )
    decisions = tuple(scope.pre(action) for action in actions)
    if any(d.effect != Effect.ALLOW or d.authorized_by != "delegated" for d in decisions):
        raise ValueError("delegated action gate changed")
    return {"delegated_actions": len(decisions)}


def case_disabled() -> dict[str, Any]:
    scope = ProcessingScope("Đọc tài liệu DOC_001", enforce=False)
    decision = scope.pre(doc("DOC_002"))
    if decision.effect != Effect.ALLOW or decision.authorized_by != "not_enforced":
        raise ValueError("disabled scope was not pass-through")
    return {"effect": decision.effect.value, "authorized_by": decision.authorized_by}


def case_anchor_rejection() -> dict[str, Any]:
    anchors = extract_scope_anchors(
        "Không đọc DOC_001; nếu cần xem DOC_002; đọc tài liệu 'DOC_003'; Đọc DOC_004"
    )
    if anchors.documents != ("DOC_004",):
        raise ValueError("rejected/quoted scope anchor was admitted")
    return {"document_anchor_count": len(anchors.documents)}


def case_database_prior_shape() -> dict[str, Any]:
    scope = ProcessingScope("Tóm tắt")
    first = query("SELECT course_id, gpa FROM courses")
    observe(
        scope,
        first,
        "ART_DB",
        Trust.UNTRUSTED,
        source_type=SourceType.DATABASE,
        source_id="database:courses",
    )
    subset = scope.pre(query("SELECT course_id FROM courses"))
    expansion = scope.pre(query("SELECT name FROM courses"))
    if subset.effect != Effect.ALLOW or expansion.effect != Effect.DENY:
        raise ValueError("database prior-shape boundary failed")
    return {"subset": subset.authorized_by, "expansion": expansion.authorized_by}


def case_unknown_action() -> dict[str, Any]:
    decision = ProcessingScope("Tóm tắt").pre(Action(name="shell", arguments={}))
    if decision.effect != Effect.DENY:
        raise ValueError("unknown action did not fail closed")
    return {"scope_kind": decision.scope_kind.value, "effect": decision.effect.value}


def case_state_integrity() -> dict[str, Any]:
    scope = ProcessingScope("Tóm tắt")
    before = scope.snapshot()
    try:
        scope.observe(
            doc("DOC_001"),
            artifact_id="ART_BAD",
            source_type=SourceType.DOCUMENT,
            source_id="DOC_002",
            trust=Trust.UNTRUSTED,
        )
    except ScopeError:
        pass
    else:
        raise ValueError("source identity mismatch accepted")
    if scope.snapshot() != before:
        raise ValueError("failed observation mutated state")
    return {"observation_count": scope.state.observation_count}


def case_limits() -> dict[str, Any]:
    many = "Đọc " + " ".join(f"DOC_{i:03d}" for i in range(300))
    try:
        ProcessingScope(many)
    except ScopeError:
        pass
    else:
        raise ValueError("anchor limit was not enforced")
    return {"anchor_limit": 256}


def all_cases(output: Path) -> list[dict[str, Any]]:
    if output.exists():
        raise ValueError("fresh processing-scope QA output required")
    output.mkdir(parents=True)
    functions = (
        ("explicit_document", case_explicit_document),
        ("explicit_cache", case_explicit_cache),
        ("explicit_database", case_explicit_database),
        ("untrusted_expansion", case_untrusted_expansion),
        ("untrusted_search", case_untrusted_search),
        ("trusted_no_trigger", case_trusted_no_trigger),
        ("malformed_database", case_malformed_database),
        ("delegated_actions", case_delegated_actions),
        ("disabled", case_disabled),
        ("anchor_rejection", case_anchor_rejection),
        ("database_prior_shape", case_database_prior_shape),
        ("unknown_action", case_unknown_action),
        ("state_integrity", case_state_integrity),
        ("limits", case_limits),
    )
    return [write_case(output, name, function) for name, function in functions]


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
    if len(checks) != 14 or any(not row["valid"] for row in checks):
        raise ValueError("14 valid synthetic processing-scope cases required")
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
        "schema_version": "phase5_processing_scope_qa_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_git_commit": commit,
        "source_worktree_clean": clean,
        "source_sha256": hashes,
        "prior_evidence": prior,
        "profile": PROFILE,
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
        "scope": "Bounded host-only A4 processing scope; no runtime adoption or model metrics",
        "remaining": [
            "Compose this component into a versioned A0–A6 runtime without changing frozen v5",
            "General private-record final entitlements and broader origin coverage",
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
