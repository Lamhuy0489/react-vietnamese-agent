from __future__ import annotations

import hashlib
import itertools
import json
import smtplib
import socket
from dataclasses import replace
from pathlib import Path

import pytest

from react_agent.authoring import canonical_selection as selection
from react_agent.authoring.boundary_rules import load_boundary_candidates
from react_agent.authoring.candidate_qa import load_candidates
from react_agent.schemas.agent_output import Action

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "data/adversarial/canonical_selection_v1/review.json"


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("selection must not perform network I/O")

    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, deny)
    monkeypatch.setattr(smtplib, "SMTP", deny)


@pytest.fixture(scope="module")
def report() -> dict:
    with pytest.MonkeyPatch.context() as patch:

        def deny(*args: object, **kwargs: object) -> None:
            raise AssertionError("selection must not perform network I/O")

        patch.setattr(socket, "socket", deny)
        return selection.select_canonicals(ROOT, REVIEW)


def test_full_selection_and_evidence(report: dict) -> None:
    assert report["valid"] and report["canonical_authoring_admitted"]
    assert report["canonical_split_valid"] and report["admitted_canonicals"] == 70
    assert report["stored_candidates"] == 72
    assert report["reused_stored_reference_paths"] == 288
    assert report["selected_reference_paths"] == 280
    assert report["fresh_replay_runs"] == report["real_model_runs"] == 0
    assert report["held_out_model_runs"] == report["variants_generated"] == 0
    assert not report["phase3_accepted"] and not report["test_sealed"]
    assert not report["independent_human_review"]
    assert not report["semantic_independence_certified"]


def test_exact_split_and_paired_identity(report: dict) -> None:
    dev, test = set(report["split"]["dev"]), set(report["split"]["test"])
    assert len(dev) == 40 and len(test) == 30 and not dev & test
    assert report["group_count"] == 20 and report["pair_comparisons"] == 2556
    for group in report["groups"]:
        assert set(group) <= dev or set(group) <= test
    assert max(map(len, report["groups"])) == 25
    rows = report["canonicals"]
    assert len({row["family_id"] for row in rows}) == 70
    assert len({row["attack_canonical_id"] for row in rows}) == 70
    assert len({row["benign_canonical_id"] for row in rows}) == 70
    assert not set(report["merges"]) & (dev | test)
    for row in rows:
        assert (row["task_id"] in dev) == (row["split"] == "dev")


def test_unavoidable_imbalance_is_reported(report: dict) -> None:
    split = report["split"]
    assert split["feasible_assignments"] == 17429
    assert split["objective"][:2] == [96, 156]
    assert split["distribution"]["category"]["tool_output_poisoning"] == {
        "total": 15,
        "dev": 12,
        "test": 3,
    }
    for cells in split["distribution"].values():
        assert sum(c["dev"] for c in cells.values()) == 40
        assert sum(c["test"] for c in cells.values()) == 30
        assert all(c["total"] == c["dev"] + c["test"] for c in cells.values())
    assert split["distribution"]["complexity"]["5"]["test"] == 0


def small_strata() -> dict[str, dict[str, str]]:
    return {
        str(i): {
            "category": str(i % 2),
            "source": str(i % 3),
            "sink": str(i % 2),
            "complexity": "1",
        }
        for i in range(6)
    }


def test_optimizer_matches_independent_brute_force() -> None:
    strata = small_strata()
    groups = [["0", "1"], ["2"], ["3"], ["4", "5"]]
    got = selection.optimize_split(groups, strata, 3, "audit-seed")
    candidates = []
    for bits in itertools.product((False, True), repeat=4):
        chosen = sorted(i for group, bit in zip(groups, bits, strict=True) if bit for i in group)
        if len(chosen) != 3:
            continue
        losses = {}
        for dimension in ("category", "source", "sink", "complexity"):
            losses[dimension] = sum(
                abs(
                    2 * sum(strata[i][dimension] == value for i in chosen)
                    - sum(row[dimension] == value for row in strata.values())
                )
                for value in {row[dimension] for row in strata.values()}
            )
        tie = hashlib.sha256(("audit-seed\n" + "\n".join(chosen)).encode()).hexdigest()
        candidates.append(
            (
                losses["category"] + losses["source"],
                losses["sink"] + losses["complexity"],
                tie,
                chosen,
            )
        )
    best = min(candidates)
    assert got["objective"] == list(best[:3]) and got["dev"] == best[3]
    assert got["feasible_assignments"] == len(candidates)
    assert selection.optimize_split(list(reversed(groups)), strata, 3, "audit-seed") == got


@pytest.mark.parametrize(
    "groups,target",
    [
        ([], 3),
        ([["0", "0"]], 1),
        ([["0", "1"], []], 1),
        ([["0", "1"], ["2", "3"], ["4", "5"]], 3),
        ([[str(i) for i in range(6)]], 6),
        ([["0", "1"]], 1),
    ],
)
def test_invalid_or_impossible_split_fails_closed(groups: list, target: int) -> None:
    with pytest.raises(ValueError):
        selection.optimize_split(groups, small_strata(), target, "seed")


@pytest.mark.parametrize("mutation", ["missing", "extra", "short", "merges", "hash", "seed"])
def test_review_rejects_incomplete_or_changed_protocol(tmp_path: Path, mutation: str) -> None:
    review = json.loads(REVIEW.read_text())
    if mutation == "missing":
        review["scenario_review"].pop("awb_mail")
    elif mutation == "extra":
        review["scenario_review"]["awb_unknown"] = "x" * 100
    elif mutation == "short":
        review["scenario_review"]["awb_mail"] = "approved"
    elif mutation == "merges":
        review["merges"]["awb_rowretry"] = "awb_mail"
    elif mutation == "hash":
        review["receipt_sha256"] = "0" * 64
    else:
        review["seed"] = "changed-after-split"
    path = tmp_path / "review.json"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError):
        selection.select_canonicals(ROOT, path)


def test_changed_input_inventory_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(selection, "file_hashes", lambda path: {})
    with pytest.raises(ValueError, match="inventory"):
        selection.select_canonicals(ROOT, REVIEW)


def test_shared_artifact_and_destination_links_do_not_disclose_values() -> None:
    cases = load_candidates(ROOT / "data/adversarial/candidates_v2_2")
    by = {c.public.task_id: c for c in cases}
    a, b = by["awb_database"], by["awb_quoted"]
    modified = replace(
        b,
        oracle=b.oracle.model_copy(
            update={
                "sensitive_artifacts": a.oracle.sensitive_artifacts,
                "safe_actions": [
                    Action(
                        name="send_email_mock",
                        arguments={
                            "to": "desk@example.test",
                            "subject": "status",
                            "body": "public",
                        },
                    )
                ],
            }
        ),
    )
    groups, overlaps = selection.connected_groups([a, modified, by["awb_mail"]])
    assert len(groups) == 1  # Transitive artifact/destination chain joins different templates.
    serialized = json.dumps(overlaps)
    assert "artifact" in serialized and "destination" in serialized
    assert "desk@example.test" not in serialized
    assert all(artifact.value not in serialized for artifact in a.oracle.sensitive_artifacts)


def test_transitive_old_group_edges_remain() -> None:
    cases = load_candidates(ROOT / "data/adversarial/candidates_v2_2")
    a, b, c = cases[:3]
    b = replace(
        b, metadata=b.metadata.model_copy(update={"template_group": a.metadata.template_group})
    )
    c = replace(
        c, metadata=c.metadata.model_copy(update={"semantic_group": b.metadata.semantic_group})
    )
    groups, _ = selection.connected_groups([a, b, c])
    assert groups == [sorted([a.public.task_id, b.public.task_id, c.public.task_id])]


@pytest.mark.parametrize(
    "task,sink",
    [
        ("awb_solicit", "final"),
        ("awb_membership", "final"),
        ("awb_relative", "email"),
        ("awb_threshold", "webhook"),
    ],
)
def test_boundary_outcomes_are_not_fictitious_tool_sinks(task: str, sink: str) -> None:
    candidates = load_boundary_candidates(ROOT / "data/adversarial/boundary_batch_v1")
    candidate = next(c for c in candidates if c.public.task_id == task)
    assert selection.target_sink(candidate) == sink


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "hash", "safe", "negative"])
def test_reference_coverage_and_outcome_rejections(mutation: str) -> None:
    candidates = load_boundary_candidates(ROOT / "data/adversarial/boundary_batch_v1")
    receipt = json.loads(
        (ROOT / "experiments/manifests/phase3_boundary_v1_validation01.json").read_text()
    )
    checks = receipt["checks"]
    if mutation == "missing":
        checks.pop()
    elif mutation == "duplicate":
        checks.append(checks[0])
    elif mutation == "hash":
        checks[0]["trace_sha256"] = "invalid"
    elif mutation == "safe":
        next(c for c in checks if c["fixture"] == "safe")["score"]["utility"] = False
    else:
        check = next(c for c in checks if c["fixture"] == "negative")
        for key in (
            "executed_violations",
            "final_leaked_artifacts",
            "derived_final_disclosures",
            "final_policy_violations",
        ):
            check["score"][key] = 0
    with pytest.raises(ValueError):
        selection.check_references(candidates, checks)


def test_manifest_is_deterministic_and_private_values_absent(report: dict) -> None:
    assert selection.select_canonicals(ROOT, REVIEW) == report
    serialized = json.dumps(report, ensure_ascii=False)
    for batch in report["input_sha256"]:
        loader = load_boundary_candidates if batch == "boundary_batch_v1" else load_candidates
        for candidate in loader(ROOT / "data/adversarial" / batch):
            assert all(a.value not in serialized for a in candidate.oracle.sensitive_artifacts)
