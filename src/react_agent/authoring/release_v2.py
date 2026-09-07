"""Full benchmark integration: re-score selected evidence, package, then seal separately."""

from __future__ import annotations

import gzip
import hashlib
import json
import platform
import shutil
import subprocess
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from typing import Any

from react_agent.adversarial_release import ReleasedFixture
from react_agent.authoring.admission_review import verify_hash_map
from react_agent.authoring.linguistic_variants import LinguisticVariant, validate_linguistic
from react_agent.authoring.mechanical_variants import (
    MechanicalVariant,
    digest,
    validate_inventory,
    validate_variants,
)
from react_agent.authoring.mechanism_rules import MechanismRules
from react_agent.authoring.selected_runtime import SELECTION_SHA256, SelectedCase, load_selected
from react_agent.authoring.workbench_qa import file_hashes
from react_agent.schemas.agent_output import Action
from react_agent.schemas.trace import TraceEvent

RECEIPTS = {
    "mechanical": "dbf3b9f7a69bcd0a5439713a118ee53a6d73c0328b2914ad9f1c1cf4e26df2bd",
    "linguistic": "028b102b2dd5db0b59dc1b87175650fcc02ce6f0eed32b4d14bf248aa4c53143",
}
KINDS = {"no_diacritic", "word_boundary", "zero_width", "code_mix", "paraphrase"}


def encoded(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sources(root: Path) -> dict[str, str]:
    paths = [
        *sorted((root / "src").rglob("*.py")),
        root / "scripts/assemble_adversarial_release.py",
        root / "docs/benchmark/adversarial_release_v2_contract.md",
        root / "pyproject.toml",
        root / "requirements.txt",
        root / "requirements-dev.txt",
        root / "configs/agent/A0.yaml",
        root / "configs/runtime/default.yaml",
        root / "tests/integration/conftest.py",
        root / "tests/integration/test_adversarial_release_v2.py",
        root / "tests/integration/test_adversarial_seal.py",
    ]
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
    }


def selected_rows(root: Path, cases: dict[str, SelectedCase]) -> list[ReleasedFixture]:
    mechanical = root / "data/adversarial/mechanical_variants_v1"
    rows = [
        MechanicalVariant.model_validate_json(s)
        for s in (mechanical / "variants.jsonl").read_text().splitlines()
    ]
    validate_inventory(
        json.loads((mechanical / "inventory.json").read_text()),
        file_hashes(mechanical)["variants.jsonl"],
    )
    validate_variants(rows, cases, json.loads((mechanical / "review.json").read_text()))
    linguistic = validate_linguistic(root, root / "data/adversarial/linguistic_variants_v1", cases)
    released = []
    combined: list[MechanicalVariant | LinguisticVariant] = [*rows, *linguistic]
    for row in combined:
        public = cases[row.task_id].public_inputs(row.raw_payload, row.branch)
        released.append(
            ReleasedFixture(
                **{
                    key: getattr(row, key)
                    for key in (
                        "variant_id",
                        "pair_id",
                        "family_id",
                        "canonical_id",
                        "group_id",
                        "split",
                        "branch",
                        "variant_type",
                    )
                },
                task=public.task,
                overlay=public.overlay,
                resources=public.resources,
            )
        )
    return sorted(released, key=lambda r: r.variant_id)


def validate_mapping(rows: list[ReleasedFixture], cases: dict[str, SelectedCase]) -> None:
    if len(rows) != 700 or len({r.variant_id for r in rows}) != 700:
        raise ValueError("full release needs 700 unique variants")
    groups: dict[str, set[str]] = {}
    for row in rows:
        case = cases[row.task.task_id]
        for key in ("family_id", "group_id", "split"):
            if getattr(row, key) != case.selection[key]:
                raise ValueError("family/group/split changed")
        if row.canonical_id != case.selection[f"{row.branch}_canonical_id"]:
            raise ValueError("canonical mapping changed")
        groups.setdefault(row.group_id, set()).add(row.split)
    counts = Counter((r.branch, r.split) for r in rows)
    expected_counts = {
        (branch, split): 200 if split == "dev" else 150
        for branch in ("attack", "benign")
        for split in ("dev", "test")
    }
    if counts != expected_counts or len(groups) != 20 or any(len(s) != 1 for s in groups.values()):
        raise ValueError("counts or conservative split leakage")
    for task in cases:
        family = [r for r in rows if r.task.task_id == task]
        if Counter((r.branch, r.variant_type) for r in family) != Counter(
            (b, k) for b in ("attack", "benign") for k in KINDS
        ):
            raise ValueError("missing/duplicate surface pair")
        for kind in KINDS:
            pair = [r for r in family if r.variant_type == kind]
            if pair[0].task != pair[1].task or pair[0].resources != pair[1].resources:
                raise ValueError("benign task/environment differs")
            ignore = {"attack_text", "benign_text"}
            if pair[0].overlay.model_dump(exclude=ignore) != pair[1].overlay.model_dump(
                exclude=ignore
            ):
                raise ValueError("paired source structure differs")


def audit_record(
    case: SelectedCase, payload: str, check: dict[str, Any], trace: bytes, database: Path
) -> list[dict[str, Any]]:
    if hashlib.sha256(trace).hexdigest() != check["trace_sha256"]:
        raise ValueError("reference trace hash changed")
    events = [TraceEvent.model_validate_json(s) for s in trace.splitlines()]
    if (
        not events
        or {e.run_id for e in events} != {check["run_id"]}
        or {e.task_id for e in events} != {case.candidate.public.task_id}
    ):
        raise ValueError("reference runtime identity mismatch")
    normalized = [e.model_dump(mode="json", exclude={"timestamp", "run_id"}) for e in events]
    if digest(encoded(normalized)) != check["observable_sha256"]:
        raise ValueError("reference observable hash mismatch")
    proposed = {
        e.call_id: Action(name=e.data["name"], arguments=e.data["arguments"])
        for e in events
        if e.event == "tool_call_proposed"
    }
    results = [e for e in events if e.event == "tool_result"]
    if any(not e.data["ok"] for e in results):
        raise ValueError("failed reference tool")
    for action in case.exposures():
        if not any(proposed[e.call_id] == action for e in results):
            raise ValueError("reference exposure missing")
    exposures = [case.candidate.overlay.trigger]
    if isinstance(case.rule, MechanismRules):
        exposures.append(case.rule.exposure_action)
    for action in exposures:
        content = "\n".join(
            json.dumps(e.data["content"], ensure_ascii=False)
            for e in results
            if proposed[e.call_id] == action
        )
        if payload not in content or case.candidate.overlay.base_content not in content:
            raise ValueError("complete released payload not exposed")
    score = case.score(events, database)
    if score != check["score"]:
        raise ValueError("re-scoring changed reference result")
    fixture = check["fixture"]
    if fixture != "alternative" and score != case.expected[check["branch"], fixture]:
        raise ValueError("canonical score parity failed")
    if fixture == "alternative" and (
        not score["safe_utility"] or not score["utility"] or score["unassessed_actions"]
    ):
        raise ValueError("safe alternative failed")
    return [e.model_dump(mode="json") for e in events]


def dependencies(root: Path, cases: dict[str, SelectedCase]) -> dict[str, str]:
    folders = {
        "data/clean/v1_1",
        "data/adversarial/candidate_review_v1",
        "data/adversarial/canonical_selection_v1",
        "data/adversarial/mechanical_variants_v1",
        "data/adversarial/linguistic_authoring_v1",
        "data/adversarial/linguistic_variants_v1",
    }
    folders.update("data/adversarial/" + c.selection["batch"] for c in cases.values())
    hashes = {
        folder + "/" + name: value
        for folder in sorted(folders)
        for name, value in file_hashes(root / folder).items()
    }
    # Preserve the complete authoring receipt chain as metadata, without copying old payloads.
    hashes.update(
        {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / "experiments/manifests").glob("phase3_*validation*.json"))
        }
    )
    return hashes


def assemble(root: Path, destination: Path) -> dict[str, Any]:
    root, destination = root.resolve(), destination.resolve()
    if destination.exists() or not destination.is_relative_to(root / "data/adversarial"):
        raise ValueError("release must be fresh under data/adversarial")
    selection, cases = load_selected(root)
    rows = selected_rows(root, cases)
    validate_mapping(rows, cases)
    before = dependencies(root, cases)
    source_before = sources(root)
    index = {r.variant_id: r for r in rows}
    baselines = {
        c.selection[f"{b}_canonical_id"]: (c, b)
        for c in cases.values()
        for b in ("attack", "benign")
    }
    seen: set[str] = set()
    runs: set[str] = set()
    archive = []
    summary = []
    receipt_hashes = {}
    for kind, expected_hash in RECEIPTS.items():
        name = f"experiments/manifests/phase3_{kind}_v1_validation01.json"
        verify_hash_map(root, {name: expected_hash})
        receipt_hashes[name] = expected_hash
        receipt = json.loads((root / name).read_text())
        verify_hash_map(root, receipt["source_sha256"])
        if (
            receipt.get(kind + "_variants_accepted") is not True
            or receipt["selection_sha256"] != SELECTION_SHA256
            or receipt["real_model_runs"] != 0
            or receipt["held_out_model_runs"] != 0
        ):
            raise ValueError("unexpected evidence scope")
        inputs = root / f"data/adversarial/{kind}_variants_v1"
        if file_hashes(inputs) != receipt["input_sha256"]:
            raise ValueError("stale accepted variant snapshot")
        raw_root = Path(receipt["raw_output"]).resolve()
        if not raw_root.is_relative_to(root / "results"):
            raise ValueError("raw evidence must be inside results")
        for check in receipt["checks"]:
            identity, fixture = check["variant_id"], check["fixture"]
            if identity in index:
                row = index[identity]
                case = cases[row.task.task_id]
                branch: str = row.branch
                payload = getattr(row.overlay, branch + "_text")
            elif identity in baselines:
                case, branch = baselines[identity]
                payload = getattr(case.candidate.overlay, branch + "_text")
            else:
                raise ValueError("unknown reference variant")
            invocation = identity + "/" + fixture
            if (
                invocation in seen
                or check["run_id"] in runs
                or invocation != check["invocation_id"]
                or check["branch"] != branch
                or check["task_id"] != case.candidate.public.task_id
                or check["split"] != case.selection["split"]
            ):
                raise ValueError("duplicate/misbound evidence invocation")
            path = (raw_root / check["trace_path"]).resolve()
            if not path.is_relative_to(raw_root):
                raise ValueError("reference path escapes")
            events = audit_record(
                case,
                payload,
                check,
                path.read_bytes(),
                path.parent / "environment/database/university.db",
            )
            seen.add(invocation)
            runs.add(check["run_id"])
            archive.append({"invocation_id": invocation, "events": events})
            summary.append(
                {
                    "invocation_id": invocation,
                    "receipt": kind,
                    "trace_sha256": check["trace_sha256"],
                    "observable_sha256": check["observable_sha256"],
                }
            )
    expected = {
        identity + "/" + f for identity in [*index, *baselines] for f in ("safe", "negative")
    }
    expected.update(
        identity + "/alternative"
        for identity in [*index, *baselines]
        if (
            index[identity].task.task_id
            if identity in index
            else baselines[identity][0].candidate.public.task_id
        )
        == "awb_sharedquota"
    )
    if seen != expected or len(seen) != 1692:
        raise ValueError("incomplete full-release reference coverage")
    verify_hash_map(root, before)
    verify_hash_map(root, source_before)
    destination.mkdir(parents=True)
    for split in ("dev", "test"):
        for branch in ("attack", "benign"):
            with (destination / f"{split}_{branch}.jsonl").open("x", encoding="utf-8") as stream:
                for row in rows:
                    if row.split == split and row.branch == branch:
                        stream.write(row.model_dump_json() + "\n")
    write_json(destination / "schema.json", ReleasedFixture.model_json_schema())
    write_json(
        destination / "mapping.json",
        {
            "selection_sha256": SELECTION_SHA256,
            "canonicals": selection["canonicals"],
            "variants": [
                {
                    key: getattr(r, key)
                    for key in (
                        "variant_id",
                        "pair_id",
                        "family_id",
                        "canonical_id",
                        "group_id",
                        "split",
                        "branch",
                        "variant_type",
                    )
                }
                | {"runtime_task_id": r.task.task_id}
                for r in rows
            ],
        },
    )
    archive_bytes = ("\n".join(encoded(a) for a in archive) + "\n").encode()
    with (destination / "reference_traces.jsonl.gz").open("xb") as stream:
        stream.write(gzip.compress(archive_bytes, mtime=0))
    qa = {
        "schema_version": "adversarial_release_integration_v2",
        "software": {"python": platform.python_version(), "pydantic": version("pydantic")},
        "valid": True,
        "release_integration_accepted": True,
        "phase3_accepted": False,
        "test_sealed": False,
        "variants": 700,
        "attack": 350,
        "benign": 350,
        "dev_per_branch": 200,
        "test_per_branch": 150,
        "families": 70,
        "dev_families": 40,
        "test_families": 30,
        "conservative_groups": 20,
        "variant_types": sorted(KINDS),
        "reused_reference_paths": 1692,
        "canonical_standard_paths": 280,
        "variant_standard_paths": 1400,
        "alternative_paths": 12,
        "test_assigned_reference_paths": 732,
        "fresh_replay_runs": 0,
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "independent_human_review": False,
        "reference_archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "receipt_sha256": receipt_hashes,
        "dependency_sha256": before,
        "source_sha256": source_before,
        "checks": summary,
    }
    write_json(destination / "qa.json", qa)
    return qa


def validate_integration(root: Path, release: Path) -> dict[str, Any]:
    qa: dict[str, Any] = json.loads((release / "qa.json").read_text())
    verify_hash_map(root, qa["source_sha256"])
    verify_hash_map(root, qa["dependency_sha256"])
    selection, cases = load_selected(root)
    if qa["source_sha256"] != sources(root) or qa["dependency_sha256"] != dependencies(root, cases):
        raise ValueError("incomplete source/dependency binding")
    rows = []
    for split in ("dev", "test"):
        for branch in ("attack", "benign"):
            items = [
                ReleasedFixture.model_validate_json(s)
                for s in (release / f"{split}_{branch}.jsonl").read_text().splitlines()
            ]
            if len(items) != (200 if split == "dev" else 150) or any(
                r.split != split or r.branch != branch for r in items
            ):
                raise ValueError("file split/branch placement mismatch")
            rows.extend(items)
    validate_mapping(rows, cases)
    if sorted(rows, key=lambda r: r.variant_id) != selected_rows(root, cases):
        raise ValueError("released fixtures differ from accepted snapshots")
    mapping = json.loads((release / "mapping.json").read_text())
    expected_mapping = {
        "selection_sha256": SELECTION_SHA256,
        "canonicals": selection["canonicals"],
        "variants": [
            {
                key: getattr(r, key)
                for key in (
                    "variant_id",
                    "pair_id",
                    "family_id",
                    "canonical_id",
                    "group_id",
                    "split",
                    "branch",
                    "variant_type",
                )
            }
            | {"runtime_task_id": r.task.task_id}
            for r in sorted(rows, key=lambda r: r.variant_id)
        ],
    }
    if (
        mapping != expected_mapping
        or json.loads((release / "schema.json").read_text()) != ReleasedFixture.model_json_schema()
    ):
        raise ValueError("mapping/schema drift")
    fixed = {
        "schema_version": "adversarial_release_integration_v2",
        "software": {"python": platform.python_version(), "pydantic": version("pydantic")},
        "valid": True,
        "release_integration_accepted": True,
        "phase3_accepted": False,
        "test_sealed": False,
        "variants": 700,
        "attack": 350,
        "benign": 350,
        "dev_per_branch": 200,
        "test_per_branch": 150,
        "families": 70,
        "dev_families": 40,
        "test_families": 30,
        "conservative_groups": 20,
        "variant_types": sorted(KINDS),
        "reused_reference_paths": 1692,
        "canonical_standard_paths": 280,
        "variant_standard_paths": 1400,
        "alternative_paths": 12,
        "test_assigned_reference_paths": 732,
        "fresh_replay_runs": 0,
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "independent_human_review": False,
    }
    variable = {
        "reference_archive_sha256",
        "receipt_sha256",
        "dependency_sha256",
        "source_sha256",
        "checks",
    }
    if set(qa) != set(fixed) | variable or encoded({k: qa[k] for k in fixed}) != encoded(fixed):
        raise ValueError("integration acceptance metadata drift")
    expected_receipts = {
        f"experiments/manifests/phase3_{k}_v1_validation01.json": v for k, v in RECEIPTS.items()
    }
    if qa["receipt_sha256"] != expected_receipts:
        raise ValueError("unapproved replacement evidence")
    checks = {}
    summaries = []
    for kind in RECEIPTS:
        path = f"experiments/manifests/phase3_{kind}_v1_validation01.json"
        verify_hash_map(root, {path: RECEIPTS[kind]})
        for check in json.loads((root / path).read_text())["checks"]:
            checks[check["invocation_id"]] = check
            summaries.append(
                {
                    "invocation_id": check["invocation_id"],
                    "receipt": kind,
                    "trace_sha256": check["trace_sha256"],
                    "observable_sha256": check["observable_sha256"],
                }
            )
    if qa["checks"] != summaries or len(checks) != 1692:
        raise ValueError("reference summary drift")
    raw = gzip.decompress((release / "reference_traces.jsonl.gz").read_bytes())
    if hashlib.sha256(raw).hexdigest() != qa["reference_archive_sha256"]:
        raise ValueError("archived reference trace drift")
    records = [json.loads(s) for s in raw.splitlines()]
    if len(records) != 1692 or len({r["invocation_id"] for r in records}) != 1692:
        raise ValueError("archived reference coverage drift")
    for record in records:
        if set(record) != {"invocation_id", "events"} or record["invocation_id"] not in checks:
            raise ValueError("unexpected archive record")
        check = checks[record["invocation_id"]]
        events = [TraceEvent.model_validate(e) for e in record["events"]]
        normalized = [e.model_dump(mode="json", exclude={"timestamp", "run_id"}) for e in events]
        if (
            digest(encoded(normalized)) != check["observable_sha256"]
            or {e.run_id for e in events} != {check["run_id"]}
            or {e.task_id for e in events} != {check["task_id"]}
        ):
            raise ValueError("archived events differ from accepted reference")
    return qa


def seal(root: Path, release: Path) -> dict[str, Any]:
    root, release = root.resolve(), release.resolve()
    if not release.is_relative_to(root / "data/adversarial") or (release / "seal.json").exists():
        raise ValueError("seal target must be an unsealed in-repository release")
    qa = validate_integration(root, release)
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git source identity required")
    commit = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=root, text=True).strip()  # noqa: S603
    # Every bound code/data byte must already exist in the source commit.
    bound = {
        **qa["source_sha256"],
        **qa["dependency_sha256"],
        **{
            release.relative_to(root).as_posix() + "/" + k: v
            for k, v in file_hashes(release).items()
        },
    }
    for path, expected_hash in bound.items():
        payload = subprocess.check_output([git, "show", commit + ":" + path], cwd=root)  # noqa: S603
        if hashlib.sha256(payload).hexdigest() != expected_hash:
            raise ValueError("commit does not contain exact release dependency")
    sealed = {
        "schema_version": "adversarial_test_seal_v2",
        "benchmark": "adversarial_v2",
        "phase3_accepted": True,
        "test_sealed": True,
        "source_git_commit": commit,
        "release_sha256": file_hashes(release),
        "source_sha256": qa["source_sha256"],
        "dependency_sha256": qa["dependency_sha256"],
        "variants": 700,
        "attack": 350,
        "benign": 350,
        "dev_per_branch": 200,
        "test_per_branch": 150,
        "review_method": "assistant_self_review_owner_waiver",
        "test_access": "hash-only integrity; payload loading requires explicit evaluation scope",
    }
    write_json(release / "seal.json", sealed)
    return sealed


def verify_seal(root: Path, release: Path) -> dict[str, Any]:
    """Read only hashes of Test data; no held-out payload parsing or reference execution."""
    sealed = json.loads((release / "seal.json").read_text())
    if sealed.get("phase3_accepted") is not True or sealed.get("test_sealed") is not True:
        raise ValueError("invalid release seal")
    required = {f"{s}_{b}.jsonl" for s in ("dev", "test") for b in ("attack", "benign")}
    required.update({"schema.json", "mapping.json", "qa.json", "reference_traces.jsonl.gz"})
    if (
        not required.issubset(sealed["release_sha256"])
        or sealed.get("schema_version") != "adversarial_test_seal_v2"
        or sealed.get("variants") != 700
        or any(
            sealed["dependency_sha256"].get(
                f"experiments/manifests/phase3_{k}_v1_validation01.json"
            )
            != v
            for k, v in RECEIPTS.items()
        )
    ):
        raise ValueError("incomplete seal binding")
    for base, key in (
        (release, "release_sha256"),
        (root, "source_sha256"),
        (root, "dependency_sha256"),
    ):
        verify_hash_map(base, sealed[key])
    return {
        "valid": True,
        "mode": "sealed_read_only",
        "phase3_accepted": True,
        "test_sealed": True,
        "variants": sealed["variants"],
    }
