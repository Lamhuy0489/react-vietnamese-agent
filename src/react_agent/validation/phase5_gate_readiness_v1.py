"""Read-only Phase 5 DoD readiness audit.

The Phase 5 evidence map intentionally distinguishes mechanical/CPU evidence
from native semantic and lifecycle acceptance.  This module makes that
distinction machine-readable without treating a passing unit test, a complete
checkpoint set, or a valid JSON response as a phase acceptance decision.

The audit only reads source files, configuration files, and explicitly supplied
run metadata.  It does not open benchmark Test payloads, private ground truth,
model prompts, or raw model outputs.  It never repairs, rewrites, or hashes
frozen evidence as a side effect.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Final, Literal, TypedDict

GateStatus = Literal["cpu_evidence", "diagnostic_only", "missing"]


class GateDefinition(TypedDict):
    title: str
    evidence: tuple[str, ...]
    cpu_status: GateStatus
    native_blocker: str


class ApiPilotSummary(TypedDict):
    path: str
    expected: int
    completed: int
    failed: int
    interrupted: int
    missing: int
    test_tasks_loaded: int
    private_ground_truth_loaded: int
    agent_tasks: int
    guard_controls: int
    evaluation_path: str | None


class GateAuditError(ValueError):
    """Raised when the supplied evidence is malformed or unsafe to audit."""


ROOT_FILES: Final[dict[int, GateDefinition]] = {
    1: {
        "title": "seven security configurations",
        "evidence": ("configs/security_v1", "tests/integration/test_phase5_components.py"),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native rollout must bind the same seven levels to one run identity",
    },
    2: {
        "title": "configuration isolation",
        "evidence": (
            "src/react_agent/llm/grouped_dev_identity_v1.py",
            "src/react_agent/llm/grouped_dev_runner_v2.py",
        ),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native source/settings/raw artifacts still need prospective parity",
    },
    3: {
        "title": "A0 purity",
        "evidence": ("tests/integration/test_phase5_runtime.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "the API agent has not been dispatched through the candidate A0 runtime",
    },
    4: {
        "title": "A1 controls",
        "evidence": ("tests/integration/test_phase5_runtime.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native A1 differential and authorization evidence is still required",
    },
    5: {
        "title": "A2 guard integration",
        "evidence": (
            "tests/integration/test_phase5_a2.py",
            "docs/evaluation/structured_api_dev_v1_report.md",
        ),
        "cpu_status": "diagnostic_only",
        "native_blocker": "guard quality, coverage, and paired semantic outcomes are not accepted",
    },
    6: {
        "title": "A3 session sensitivity",
        "evidence": ("tests/integration/test_phase5_session.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native A3 session veto and lifecycle evidence is missing",
    },
    7: {
        "title": "A4 resource scope",
        "evidence": ("tests/unit/test_resource_scope_v4.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native A4 bounded-scope dispatch has not been measured",
    },
    8: {
        "title": "A5 session contrast",
        "evidence": ("tests/integration/test_phase5_session.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native unrelated-secret A5 contrast remains unproven",
    },
    9: {
        "title": "A6 provenance artifact",
        "evidence": ("tests/integration/test_phase5_a6_runtime.py",),
        "cpu_status": "diagnostic_only",
        "native_blocker": "representative native public-after-secret provenance proof is open",
    },
    10: {
        "title": "Pre gate",
        "evidence": ("tests/integration/test_phase5_value_gates.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native broker dispatch and guard decision joins are not complete",
    },
    11: {
        "title": "Post gate",
        "evidence": ("tests/integration/test_phase5_a6_runtime.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native post-view, raw provenance, and verdict joins are open",
    },
    12: {
        "title": "Final gate",
        "evidence": ("tests/integration/test_phase5_final_entitlement_runtime.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "all native terminal paths still need final entitlement proof",
    },
    13: {
        "title": "S2 egress",
        "evidence": ("tests/integration/test_phase5_components.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native recognized-destination sensitive egress coverage remains open",
    },
    14: {
        "title": "final leakage",
        "evidence": ("tests/integration/test_phase5_final_entitlement_runtime.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native semantic leakage coverage is not established by JSON validity",
    },
    15: {
        "title": "benign utility",
        "evidence": (
            "docs/evaluation/structured_api_dev_v1_report.md",
            "tests/integration/test_phase5_value_gates.py",
        ),
        "cpu_status": "diagnostic_only",
        "native_blocker": (
            "agent utility and benign false-block rates remain diagnostic (not acceptance)"
        ),
    },
    16: {
        "title": "unknown lineage",
        "evidence": ("tests/integration/test_phase5_value_origin.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native unknown-origin cases have not been scored end to end",
    },
    17: {
        "title": "ground-truth separation",
        "evidence": ("tests/integration/test_phase5_components.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": (
            "final package freeze must re-audit that evaluator-only fields stay host-side"
        ),
    },
    18: {
        "title": "Test integrity",
        "evidence": (
            "docs/project/invariants.md",
            "data/clean/v1_1/manifests/split_manifest.json",
        ),
        "cpu_status": "cpu_evidence",
        "native_blocker": (
            "formal freeze must rerun seal/hash validation before any acceptance claim"
        ),
    },
    19: {
        "title": "mock sinks only",
        "evidence": ("tests/integration/test_phase5_components.py",),
        "cpu_status": "cpu_evidence",
        "native_blocker": "native package and API integration must retain network interdiction",
    },
    20: {
        "title": "formal freeze",
        "evidence": ("docs/evaluation/phase5_dod_evidence_map.md",),
        "cpu_status": "missing",
        "native_blocker": (
            "source, model, artifacts, lifecycle, quality, and DoD receipt are not frozen"
        ),
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GateAuditError(f"invalid JSON evidence: {path}") from exc
    if not isinstance(value, dict):
        raise GateAuditError(f"JSON object required: {path}")
    return value


def _safe_relative(root: Path, path: Path) -> str:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise GateAuditError(f"evidence path outside repository: {path}") from exc
    return relative.as_posix()


def _validate_evidence(root: Path, relative: str) -> dict[str, Any]:
    raw_path = root / relative
    if raw_path.is_symlink():
        raise GateAuditError(f"symlink evidence is forbidden: {relative}")
    path = raw_path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise GateAuditError(f"evidence path escapes repository: {relative}")
    if path.name.lower() in {"test.jsonl", "test_ground_truth.jsonl"} or (
        "heldout" in path.name.lower()
    ):
        raise GateAuditError(f"held-out evidence is forbidden: {relative}")
    if path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.is_file() and not p.is_symlink())
        if not files:
            raise GateAuditError(f"evidence directory is empty: {relative}")
        return {"path": relative, "kind": "directory", "file_count": len(files)}
    if not path.is_file() or path.is_symlink():
        raise GateAuditError(f"evidence file missing: {relative}")
    return {"path": relative, "kind": "file", "sha256": _sha256(path)}


def validate_api_pilot(path: Path, root: Path) -> ApiPilotSummary:
    """Validate only public run metadata; no task payloads or private GT are read."""

    path = path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise GateAuditError("API pilot path must be inside repository")
    relative_parts = {part.lower() for part in path.relative_to(root.resolve()).parts}
    if relative_parts & {"private", "test", "heldout", "ground_truth"}:
        raise GateAuditError("API pilot path may not contain Test or private-ground-truth data")
    summary_path = path / "summary.json"
    manifest_path = path / "manifest.json"
    if not summary_path.is_file() or not manifest_path.is_file():
        raise GateAuditError("API pilot requires summary.json and manifest.json")
    summary = _read_object(summary_path)
    manifest = _read_object(manifest_path)
    integer_fields = (
        "expected",
        "completed",
        "failed",
        "interrupted",
        "missing",
        "test_tasks_loaded",
        "private_ground_truth_loaded",
        "agent_tasks",
        "guard_controls",
    )
    values: dict[str, int] = {}
    for field in integer_fields:
        value = summary.get(field, manifest.get(field))
        if type(value) is not int or value < 0:
            raise GateAuditError(f"API pilot field must be a nonnegative integer: {field}")
        values[field] = value
    forbidden_manifest = (
        manifest.get("test_tasks_loaded", 0),
        manifest.get("private_ground_truth_loaded", 0),
    )
    if values["test_tasks_loaded"] or values["private_ground_truth_loaded"] or any(
        value != 0 for value in forbidden_manifest
    ):
        raise GateAuditError("API pilot metadata claims Test/private ground truth was loaded")
    if values["expected"] != (
        values["completed"]
        + values["failed"]
        + values["interrupted"]
        + values["missing"]
    ):
        raise GateAuditError("API pilot terminal counts do not add to expected")
    if values["missing"] != 0 or values["failed"] != 0 or values["interrupted"] != 0:
        raise GateAuditError("API pilot is incomplete; diagnostic evidence cannot be promoted")
    if values["agent_tasks"] <= 0 or values["guard_controls"] <= 0:
        raise GateAuditError("API pilot has no agent or guard denominator")
    evaluation_path = path.parent / f"{path.name}_evaluation.json"
    if not evaluation_path.is_file():
        evaluation_path = path / "evaluation.json"
    if evaluation_path.is_file():
        evaluation = _read_object(evaluation_path)
        for block, denominator in (("agent", "tasks"), ("guard", "attack_tasks")):
            section = evaluation.get(block)
            if not isinstance(section, dict) or type(section.get(denominator)) is not int:
                raise GateAuditError(f"API evaluation denominator missing: {block}.{denominator}")
            for name in ("success_rate", "attack_detection_rate", "benign_flag_rate"):
                if name in section and (
                    type(section[name]) not in (int, float)
                    or not math.isfinite(float(section[name]))
                    or not 0 <= float(section[name]) <= 1
                ):
                    raise GateAuditError(f"API evaluation metric outside [0,1]: {block}.{name}")
    return ApiPilotSummary(
        path=_safe_relative(root, path),
        expected=values["expected"],
        completed=values["completed"],
        failed=values["failed"],
        interrupted=values["interrupted"],
        missing=values["missing"],
        test_tasks_loaded=values["test_tasks_loaded"],
        private_ground_truth_loaded=values["private_ground_truth_loaded"],
        agent_tasks=values["agent_tasks"],
        guard_controls=values["guard_controls"],
        evaluation_path=(
            _safe_relative(root, evaluation_path) if evaluation_path.is_file() else None
        ),
    )


def audit(root: Path, *, api_pilot: Path | None = None) -> dict[str, Any]:
    """Return a deterministic, non-accepting readiness report for all 20 DoD items."""

    root = root.resolve()
    if not root.is_dir():
        raise GateAuditError("repository root must be a directory")
    gates: list[dict[str, Any]] = []
    for number in range(1, 21):
        definition = ROOT_FILES[number]
        evidence = [_validate_evidence(root, relative) for relative in definition["evidence"]]
        gates.append(
            {
                "id": number,
                "title": definition["title"],
                "cpu_status": definition["cpu_status"],
                "overall_status": "open",
                "evidence": evidence,
                "native_blocker": definition["native_blocker"],
            }
        )
    pilot = validate_api_pilot(api_pilot, root) if api_pilot is not None else None
    return {
        "schema_version": "phase5_gate_readiness_v1",
        "protocol": "phase5_dod_readiness_audit",
        "phase5_accepted": False,
        "test_payloads_read": 0,
        "private_ground_truth_read": 0,
        "cpu_evidence_count": sum(g["cpu_status"] == "cpu_evidence" for g in gates),
        "diagnostic_only_count": sum(g["cpu_status"] == "diagnostic_only" for g in gates),
        "missing_cpu_evidence_count": sum(g["cpu_status"] == "missing" for g in gates),
        "api_pilot": pilot,
        "gates": gates,
    }
