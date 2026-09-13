#!/usr/bin/env python3
"""Hash-bound A6 entitlement-runtime QA; synthetic only, no benchmark inference."""

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

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import (
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
)
from react_agent.foundation.dev_validation import prerequisites
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.a2_qa import MODEL, REVISION, SyntheticGuardFactory
from react_agent.security_v1.contracts import Effect, Level, configuration
from react_agent.security_v1.final_entitlements import extract_final_entitlement
from react_agent.security_v1.runtime_v6 import SecurityRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[1]
QUERY = "SELECT 3.2 AS gpa"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    paths = [
        ROOT / "src/react_agent/security_v1/runtime_v6.py",
        ROOT / "src/react_agent/security_v1/final_entitlements.py",
        ROOT / "tests/integration/test_phase5_final_entitlement_runtime.py",
        Path(__file__).resolve(),
        ROOT / "docs/architecture/phase5_runtime_v6_entitlement_contract.md",
    ]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def prior_evidence() -> dict[str, Any]:
    receipts: dict[str, str] = {}
    count = 0
    for name in (
        "phase5_a6_runtime_v1_validation01.json",
        "phase5_warm_guard_v1_validation01.json",
        "phase5_processing_scope_v1_validation01.json",
        "phase5_final_entitlements_v1_validation01.json",
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


def catalog(*, source_id: str, trust: Trust) -> SourceCatalog:
    action = Action(name="db_query", arguments={"query": QUERY})
    return SourceCatalog(
        bindings=(
            SourceBinding(
                tool=action.name,
                arguments_json=canonical_json(action.arguments),
                label=SourceLabel(
                    source_type=SourceType.DATABASE,
                    source_id=source_id,
                    sensitivity=Sensitivity.CONFIDENTIAL,
                    trust=trust,
                ),
            ),
        )
    )


def run_runtime(
    destination: Path,
    *,
    instruction: str,
    answer: str | None,
    source_id: str = "DOC_001",
    trust: Trust = Trust.TRUSTED,
    level: Level = "A6",
    supplied_entitlement: bool = False,
    entitlement_text: str | None = None,
) -> dict[str, Any]:
    run_output = destination / "run"
    if level == "A6":
        responses = [
            action_response(Action(name="db_query", arguments={"query": QUERY})),
            *([final_response(answer)] if answer is not None else ["invalid"]),
        ]
        runtime = SecurityRuntime(
            RecordingBackend(responses),
            build_smoke_registry(ROOT / "data/smoke"),
            runtime_config=RuntimeConfig(max_steps=2, max_format_retries_per_step=0),
        )
        entitlement = (
            extract_final_entitlement(entitlement_text or instruction)
            if supplied_entitlement
            else None
        )
        run = runtime.run_instrumented(
            PublicWorkbenchTask(task_id="awb_entitlement", instruction=instruction),
            output=run_output,
            source_catalog=catalog(source_id=source_id, trust=trust),
            security_config=configuration("A6"),
            guard_factory=SyntheticGuardFactory(),
            guard_execution=WarmGuardConfig(MODEL, REVISION, 10),
            entitlement=entitlement,
        )
    else:
        if answer is None:
            raise ValueError("A0 case requires a final answer")
        runtime = SecurityRuntime(
            RecordingBackend([final_response(answer)]),
            build_smoke_registry(ROOT / "data/smoke"),
            runtime_config=RuntimeConfig(max_steps=1, max_format_retries_per_step=0),
        )
        run = runtime.run_instrumented(
            PublicWorkbenchTask(task_id="awb_entitlement", instruction=instruction),
            output=run_output,
            security_config=configuration("A0"),
        )
    metadata = json.loads((run_output / "run_metadata.json").read_text(encoding="utf-8"))
    return {
        "status": run.result.status,
        "final_answer": run.result.final_answer,
        "runtime_version": metadata["runtime_version"],
        "final_effect": (metadata["final_release"] or {}).get("effect"),
        "final_profile": (metadata["final_release"] or {}).get("profile"),
        "guard_attempts": metadata["guard_execution_attempt_count"],
    }


def case(output: Path, name: str, check: Any) -> dict[str, Any]:
    destination = output / name
    destination.mkdir(parents=True, exist_ok=False)
    result = {"case": name, **check(destination), "valid": True}
    (destination / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def allow(destination: Path) -> dict[str, Any]:
    instruction = "Trả GPA từ DOC_001 trong câu trả lời"
    result = run_runtime(
        destination,
        instruction=instruction,
        answer="GPA: 3.2",
        supplied_entitlement=True,
    )
    if result["final_effect"] != Effect.ALLOW or result["final_answer"] != "GPA: 3.2":
        raise ValueError("trusted explicit entitlement did not release")
    return result


def redact(destination: Path) -> dict[str, Any]:
    result = run_runtime(
        destination,
        instruction="Đọc DOC_001 và tóm tắt",
        answer="GPA: 3.2",
    )
    if result["final_effect"] != Effect.REDACT or result["final_answer"] != "GPA: [REDACTED]":
        raise ValueError("implicit entitlement did not redact")
    return result


def wrong_source(destination: Path) -> dict[str, Any]:
    result = run_runtime(
        destination,
        instruction="Trả GPA từ DOC_OTHER trong câu trả lời",
        answer="GPA: 3.2",
    )
    if result["final_effect"] != Effect.REDACT:
        raise ValueError("wrong source was released")
    return result


def untrusted(destination: Path) -> dict[str, Any]:
    result = run_runtime(
        destination,
        instruction="Trả GPA từ DOC_001 trong câu trả lời",
        answer="GPA: 3.2",
        trust=Trust.UNTRUSTED,
    )
    if result["final_effect"] != Effect.REDACT:
        raise ValueError("untrusted origin was released")
    return result


def normalized(destination: Path) -> dict[str, Any]:
    result = run_runtime(
        destination,
        instruction="Trả GPA từ DOC_001 trong câu trả lời",
        answer="GPA: 3.\u200b2",
        supplied_entitlement=True,
    )
    if result["final_effect"] != Effect.DENY or result["final_answer"] != "":
        raise ValueError("normalized-only final did not deny")
    return result


def public_no_match(destination: Path) -> dict[str, Any]:
    result = run_runtime(
        destination,
        instruction="Trả GPA từ DOC_001 trong câu trả lời",
        answer="Không có dữ liệu riêng",
    )
    if result["final_effect"] != Effect.ALLOW:
        raise ValueError("public no-match final was blocked")
    return result


def parse_failure(destination: Path) -> dict[str, Any]:
    result = run_runtime(
        destination,
        instruction="Trả GPA từ DOC_001 trong câu trả lời",
        answer=None,
    )
    if result["status"] != "parse_failure" or result["final_effect"] is not None:
        raise ValueError("parse terminal path changed")
    return result


def a0_passthrough(destination: Path) -> dict[str, Any]:
    result = run_runtime(
        destination,
        instruction="Trả lời công khai",
        answer="Nội dung công khai",
        level="A0",
    )
    if result["final_answer"] != "Nội dung công khai" or result["guard_attempts"] != 0:
        raise ValueError("A0 adapter parity changed")
    return result


def hash_rejection(destination: Path) -> dict[str, Any]:
    instruction = "Trả GPA từ DOC_001 trong câu trả lời"
    try:
        run_runtime(
            destination,
            instruction=instruction,
            answer="GPA: 3.2",
            supplied_entitlement=True,
            entitlement_text="Trả GPA từ DOC_OTHER trong câu trả lời",
        )
    except ValueError as exc:
        if "bound" not in str(exc):
            raise
        if (destination / "run").exists():
            raise ValueError("mismatched entitlement created runtime output") from exc
        return {"mismatch_rejected": True}
    raise ValueError("mismatched host entitlement was accepted")


def auto_extract(destination: Path) -> dict[str, Any]:
    result = run_runtime(
        destination,
        instruction="Trả GPA từ DOC_001 trong câu trả lời",
        answer="GPA: 3.2",
    )
    if result["final_effect"] != Effect.ALLOW or result["final_answer"] != "GPA: 3.2":
        raise ValueError("raw-user affirmative entitlement was not honored")
    return result


def all_cases(output: Path) -> list[dict[str, Any]]:
    if output.exists():
        raise ValueError("fresh runtime entitlement output required")
    output.mkdir(parents=True)
    checks: tuple[tuple[str, Callable[[Path], dict[str, Any]]], ...] = (
        ("allow", allow),
        ("redact", redact),
        ("wrong_source", wrong_source),
        ("untrusted", untrusted),
        ("normalized", normalized),
        ("public_no_match", public_no_match),
        ("parse_failure", parse_failure),
        ("a0_passthrough", a0_passthrough),
        ("hash_rejection", hash_rejection),
        ("auto_extract", auto_extract),
    )
    # Keep the host hash-binding assertion at the component layer; runtime
    # mismatch is covered by the integration test without inventing a second
    # raw-user channel in this runner.
    return [case(output, name, check) for name, check in checks]


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
    before, prior = prerequisites(ROOT), prior_evidence()
    smoke = {
        p.relative_to(ROOT).as_posix(): digest(p)
        for p in sorted((ROOT / "data/smoke").rglob("*"))
        if p.is_file()
    }
    checks = all_cases(output / "cases")
    if len(checks) != 10 or any(not row["valid"] for row in checks):
        raise ValueError("ten valid synthetic runtime entitlement cases required")
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
    if source_hashes() != hashes or prerequisites(ROOT) != before or prior_evidence() != prior:
        raise ValueError("source/input changed during validation")
    if any(digest(ROOT / p) != h for p, h in smoke.items()):
        raise ValueError("smoke input changed during validation")
    result = {
        "schema_version": "phase5_runtime_v6_entitlement_qa_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_git_commit": commit,
        "source_worktree_clean": clean,
        "source_sha256": hashes,
        "prior_evidence": prior,
        "smoke_input_sha256": smoke,
        "profile": "runtime_v6_entitlement_adapter",
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
        "scope": "Versioned host-only A6 final entitlement composition; no model metrics",
        "remaining": [
            "Production guard model/revision and efficient GPU worker validation",
            "General A4 scope and broader origin/semantic coverage",
            "Grouped Dev differential validation and freeze",
        ],
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("valid", "phase5_accepted", "synthetic_conditions")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
