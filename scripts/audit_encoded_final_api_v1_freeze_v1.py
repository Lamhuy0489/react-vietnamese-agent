"""Read-only source-drift audit for the encoded FINAL API evidence.

The API run, evaluations, and receipt are historical artifacts.  This audit
does not rerun inference and never writes into their directories.  It records
the parent hashes, compares every source path bound by the parent run, and
recomputes the saved evaluator result from the sealed local checkpoints.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = Path("experiments/manifests/encoded_final_api_v1.json")
RUN = Path("build/evaluation/encoded_final_api_v1/run01")
EVALUATIONS = (
    Path("build/evaluation/encoded_final_api_v1/evaluation01.json"),
    Path("build/evaluation/encoded_final_api_v1/evaluation02.json"),
)
PROTOCOL = Path("docs/evaluation/encoded_final_api_v1_protocol.md")
REPORT = Path("docs/evaluation/encoded_final_api_v1_report.md")
EVALUATOR = Path("scripts/evaluate_encoded_final_api_v1.py")
AUDIT_SCRIPT = Path(__file__).resolve().relative_to(ROOT)
VERSION = "encoded_final_api_v1_freeze_audit_v2"


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_path(root: Path, name: str | Path) -> Path:
    """Resolve a repository-relative file without following symlink components."""
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe repository path: {name}")
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"symlink in repository path: {name}")
    return cursor


def _digest(root: Path, name: str | Path) -> str | None:
    path = _safe_path(root, name)
    if not path.is_file():
        return None
    return sha(path.read_bytes())


def _relative_paths(paths: Iterable[str]) -> list[str]:
    return sorted(set(paths))


def _mismatches(root: Path, expected: dict[str, str]) -> list[dict[str, str | None]]:
    mismatches: list[dict[str, str | None]] = []
    for name in sorted(expected):
        actual = _digest(root, name)
        if actual != expected[name]:
            mismatches.append({"path": name, "expected": expected[name], "actual": actual})
    return mismatches


def _current_source(root: Path, parent_paths: Iterable[str]) -> dict[str, str]:
    """Hash the parent source scope plus newly present Python source files."""
    paths = set(parent_paths)
    source_root = _safe_path(root, "src/react_agent")
    paths.update(str(path.relative_to(root)) for path in source_root.rglob("*.py"))
    # These scripts directly define or audit the encoded FINAL evidence.
    paths.update({
        "scripts/evaluate_encoded_final_api_v1.py",
        "scripts/run_encoded_final_api_v1.py",
        "scripts/evaluate_encoded_final_api_v2.py",
        "scripts/run_encoded_final_api_v2.py",
        "scripts/evaluate_remote_gate_controls_v1.py",
    })
    result: dict[str, str] = {}
    for name in _relative_paths(paths):
        digest = _digest(root, name)
        if digest is not None:
            result[name] = digest
    return result


def _recompute_saved_evaluation(
    root: Path, run: Path, evaluation_paths: tuple[Path, ...]
) -> dict[str, Any]:
    """Re-run only the saved evaluator in-process; no endpoint is contacted."""
    evaluator_path = _safe_path(root, EVALUATOR)
    scripts_dir = str(evaluator_path.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "encoded_final_api_v1_saved_evaluator", evaluator_path
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot load saved evaluator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    recomputed = module.evaluate(_safe_path(root, run))
    saved = [json.loads(_safe_path(root, path).read_text()) for path in evaluation_paths]
    return {
        "matches_saved": all(canonical(recomputed) == canonical(item) for item in saved),
        "saved_evaluations_identical": canonical(saved[0]) == canonical(saved[1]),
        "recomputed": recomputed,
    }


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(  # noqa: S603 - fixed read-only Git query
            ["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL  # noqa: S607
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _record_hash(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "audit_record_sha256"}
    return sha(canonical(payload).encode())


def verify_record(record: dict[str, Any]) -> bool:
    """Verify the tamper-evident record field without reading any payload."""
    return record.get("audit_record_sha256") == _record_hash(record)


def build_record(root: Path = ROOT) -> dict[str, Any]:
    """Build a source-drift record using only local historical artifacts."""
    receipt_path = _safe_path(root, RECEIPT)
    receipt = json.loads(receipt_path.read_text())
    parent_run_path = _safe_path(root, RUN / "manifest.json")
    parent_run = json.loads(parent_run_path.read_text())
    parent_source = {str(name): str(value) for name, value in parent_run["source_sha256"].items()}

    parent_artifacts = {str(name): str(value) for name, value in receipt["artifact_sha256"].items()}
    parent_journal = {str(name): str(value) for name, value in receipt["journal_sha256"].items()}
    artifact_mismatches = _mismatches(root, parent_artifacts)
    journal_mismatches = _mismatches(root, parent_journal)
    source_mismatches = _mismatches(root, parent_source)
    current_source = _current_source(root, parent_source)
    parent_source_paths = set(parent_source)
    current_source_paths = set(current_source)
    source_additions = sorted(current_source_paths - parent_source_paths)
    source_missing = sorted(parent_source_paths - current_source_paths)

    parent_hashes = {
        "receipt_sha256": _digest(root, RECEIPT),
        "raw_manifest_sha256": _digest(root, RUN / "manifest.json"),
        "evaluation01_sha256": _digest(root, EVALUATIONS[0]),
        "evaluation02_sha256": _digest(root, EVALUATIONS[1]),
        "protocol_sha256": _digest(root, PROTOCOL),
        "report_sha256": _digest(root, REPORT),
        "evaluator_sha256": _digest(root, EVALUATOR),
        "runner_sha256": _digest(root, "scripts/run_encoded_final_api_v1.py"),
    }
    expected_protocol = parent_run.get("protocol_sha256")
    expected_evaluator = parent_run.get("evaluator_sha256")
    protocol_unchanged = parent_hashes["protocol_sha256"] == expected_protocol
    evaluator_unchanged = parent_hashes["evaluator_sha256"] == expected_evaluator
    evaluation_paths = tuple(EVALUATIONS)
    try:
        recomputed = _recompute_saved_evaluation(root, RUN, evaluation_paths)
        recompute_error: str | None = None
    except (ImportError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        recomputed = {"matches_saved": False, "saved_evaluations_identical": False}
        recompute_error = f"{type(exc).__name__}: {exc}"

    parent_manifest_intact = _digest(root, RUN / "manifest.json") is not None
    raw_artifacts_intact = not artifact_mismatches
    journal_intact = not journal_mismatches
    source_unchanged = not source_mismatches and not source_missing
    evaluations_identical = bool(recomputed["saved_evaluations_identical"])
    recomputed_match = bool(recomputed["matches_saved"])
    can_reaudit = all((
        parent_manifest_intact,
        raw_artifacts_intact,
        journal_intact,
        source_unchanged,
        protocol_unchanged,
        evaluator_unchanged,
        evaluations_identical,
        recomputed_match,
    ))
    record: dict[str, Any] = {
        "audit_version": VERSION,
        "date": "2026-09-29",
        "audit_script": str(AUDIT_SCRIPT),
        "audit_script_sha256": _digest(root, AUDIT_SCRIPT),
        "source_state": "working-tree; parent-bound paths are compared, not committed",
        "git_head": _git(root, "rev-parse", "HEAD"),
        "git_status_dirty": bool(_git(root, "status", "--porcelain")),
        "parent": {
            "receipt": str(RECEIPT),
            "run": str(RUN),
            "evaluations": [str(path) for path in EVALUATIONS],
            "protocol": str(PROTOCOL),
            "report": str(REPORT),
            "evaluator": str(EVALUATOR),
            "hashes": parent_hashes,
            "receipt_artifact_paths": len(parent_artifacts),
            "receipt_journal_paths": len(parent_journal),
            "raw_source_paths": len(parent_source),
            "raw_source_sha256": parent_source,
            "artifact_mismatches": artifact_mismatches,
            "journal_mismatches": journal_mismatches,
            "source_mismatches": source_mismatches,
        },
        "current_source_sha256": current_source,
        "current_source_paths": len(current_source),
        "source_additions_outside_parent_binding": source_additions,
        "source_missing_from_current_tree": source_missing,
        "protocol_unchanged": protocol_unchanged,
        "evaluator_unchanged": evaluator_unchanged,
        "evaluations_byte_identical": parent_hashes["evaluation01_sha256"]
        == parent_hashes["evaluation02_sha256"],
        "recomputed_evaluation": {
            "matches_saved": recomputed_match,
            "saved_evaluations_identical": evaluations_identical,
            "error": recompute_error,
        },
        "re_audit": {
            "raw_artifacts_intact": raw_artifacts_intact,
            "journal_intact": journal_intact,
            "parent_source_unchanged": source_unchanged,
            "recomputed_evaluation_matches_saved": recomputed_match,
            "can_reaudit_old_evidence": can_reaudit,
            "phase5_accepted": False,
            "network_or_inference_run": False,
        },
        "scope": "integrity and saved-evaluator re-audit only; no new API inference",
        "audit_record_sha256": "",
    }
    record["audit_record_sha256"] = _record_hash(record)
    return record


def write_record(root: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite audit artifact: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    record = build_record(root)
    output.write_text(canonical(record) + "\n")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = write_record(ROOT, args.output)
    print(canonical({
        "can_reaudit_old_evidence": record["re_audit"]["can_reaudit_old_evidence"],
        "artifact_mismatches": len(record["parent"]["artifact_mismatches"]),
        "journal_mismatches": len(record["parent"]["journal_mismatches"]),
        "source_mismatches": len(record["parent"]["source_mismatches"]),
        "source_additions": len(record["source_additions_outside_parent_binding"]),
    }))


if __name__ == "__main__":
    main()
