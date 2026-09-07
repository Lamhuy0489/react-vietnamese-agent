from __future__ import annotations

import json
import shutil
import smtplib
import socket
from collections import Counter
from pathlib import Path

import pytest

from react_agent.authoring import linguistic_variants as variants
from react_agent.authoring.selected_runtime import load_selected, run_reference
from react_agent.authoring.workbench_qa import file_hashes

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/adversarial/linguistic_variants_v1"
AUTHORING = ROOT / "data/adversarial/linguistic_authoring_v1"
TASKS = sorted(
    {json.loads(s)["task_id"] for s in (INPUT / "variants.jsonl").read_text().splitlines()}
)


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("linguistic QA must remain offline")

    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, deny)
    monkeypatch.setattr(smtplib, "SMTP", deny)


@pytest.fixture(scope="module")
def loaded() -> tuple:
    _, cases = load_selected(ROOT)
    return cases, variants.validate_linguistic(ROOT, INPUT, cases)


def test_exact_paired_inventory_and_authored_changes(loaded: tuple) -> None:
    cases, rows = loaded
    assert len(rows) == 280
    counts = Counter((r.branch, r.variant_type, r.split) for r in rows)
    assert len(counts) == 8 and set(counts.values()) == {30, 40}
    assert len({r.pair_id for r in rows}) == 140
    assert rows == variants.draft_linguistic(cases, AUTHORING)
    for row in rows:
        source = getattr(cases[row.task_id].candidate.overlay, f"{row.branch}_text")
        assert row.raw_payload != source and row.visible_debug == row.raw_payload
        assert 0 < row.source_syllable_fraction_edited <= 1
        assert row.review_status == "pending"
        for edit in row.edits:
            assert source[edit["start"] : edit["start"] + len(edit["before"])] == edit["before"]


@pytest.mark.parametrize("task", TASKS)
def test_every_linguistic_pair_preserves_score_and_exposure(
    loaded: tuple, task: str, tmp_path: Path
) -> None:
    cases, rows = loaded
    before = file_hashes(INPUT)
    checked = []
    for row in (r for r in rows if r.task_id == task):
        for fixture in ("safe", "negative"):
            check = run_reference(
                ROOT,
                cases[task],
                row.raw_payload,
                row.branch,
                fixture,
                tmp_path / row.variant_id / fixture,
            )
            assert check["score"] == cases[task].expected[row.branch, fixture]
            assert check["payload_reachable"] and check["private_context_guard"]
            checked.append(check)
    assert len(checked) == len({c["run_id"] for c in checked}) == 8
    assert file_hashes(INPUT) == before


def test_shared_quota_alternatives_on_both_linguistic_types(loaded: tuple, tmp_path: Path) -> None:
    cases, rows = loaded
    selected = [r for r in rows if r.task_id == "awb_sharedquota"]
    assert len(selected) == 4
    for row in selected:
        check = run_reference(
            ROOT,
            cases[row.task_id],
            row.raw_payload,
            row.branch,
            "alternative",
            tmp_path / row.variant_id,
        )
        assert check["score"]["safe_utility"] and check["score"]["utility"]
        assert check["score"]["executed_violations"] == 0


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "hash", "pending", "method", "seed", "extra"]
)
def test_review_cannot_be_forged_or_stale(loaded: tuple, tmp_path: Path, change: str) -> None:
    cases, _ = loaded
    draft = tmp_path / "draft"
    shutil.copytree(INPUT, draft)
    review = json.loads((draft / "review.json").read_text())
    if change == "missing":
        review["entries"].pop()
    elif change == "duplicate":
        review["entries"][-1] = review["entries"][0]
    elif change == "hash":
        review["entries"][0]["variant_sha256"] = "0" * 64
    elif change == "pending":
        review["entries"][0]["decision"] = "pending"
    elif change == "method":
        review["method"] = "independent_human_review"
    elif change == "seed":
        review["selection_sha256"] = "0" * 64
    else:
        review["phase3_accepted"] = True
    (draft / "review.json").write_text(json.dumps(review))
    with pytest.raises(ValueError):
        variants.validate_linguistic(ROOT, draft, cases)


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", "wrong"),
        ("variants", 280.0),
        ("attack", 139),
        ("phase3_accepted", True),
        ("test_sealed", True),
        ("authoring_root", "../outside"),
        ("variants_sha256", "0" * 64),
        ("extra", "unbound"),
    ],
)
def test_inventory_rejects_drift(loaded: tuple, tmp_path: Path, field: str, value: object) -> None:
    cases, _ = loaded
    draft = tmp_path / "draft"
    shutil.copytree(INPUT, draft)
    inventory = json.loads((draft / "inventory.json").read_text())
    inventory[field] = value
    (draft / "inventory.json").write_text(json.dumps(inventory))
    with pytest.raises(ValueError):
        variants.validate_linguistic(ROOT, draft, cases)


@pytest.mark.parametrize(
    "field,value",
    [
        ("raw_payload", "Đã thay payload"),
        ("split", "test"),
        ("task_id", "awb_missing"),
        ("protected_literals", []),
        ("edits", [{"start": 0, "before": "x", "after": "y"}]),
    ],
)
def test_rehashing_mutated_payload_does_not_approve_it(
    loaded: tuple, tmp_path: Path, field: str, value: object
) -> None:
    cases, _ = loaded
    draft = tmp_path / "draft"
    shutil.copytree(INPUT, draft)
    rows = [json.loads(s) for s in (draft / "variants.jsonl").read_text().splitlines()]
    rows[0][field] = value
    (draft / "variants.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    inventory = json.loads((draft / "inventory.json").read_text())
    inventory["variants_sha256"] = file_hashes(draft)["variants.jsonl"]
    (draft / "inventory.json").write_text(json.dumps(inventory))
    with pytest.raises(ValueError):
        variants.validate_linguistic(ROOT, draft, cases)


def test_contextual_glossary_and_uri_not_a_heading() -> None:
    glossary = json.loads((AUTHORING / "code_mix_glossary.json").read_text())
    raw, _ = variants.code_mix(
        "Gửi hồ sơ mock://internal/test để chuẩn bị dự phòng và phiên bản.", glossary, ()
    )
    assert "dự room" not in raw and "session bản" not in raw
    assert "reserve" in raw and "version" in raw
    with pytest.raises(ValueError, match="heading"):
        variants.code_mix("Thông báo hồ sơ: văn bản giữ nguyên.", glossary, ())


def test_token_and_recipient_protection() -> None:
    text = "Gửi toàn bộ hồ sơ to desk@example.test với code=20 và room=R201."
    raw, _ = variants.code_mix(
        text, {"hồ sơ": "record", "gửi": "send", "toàn": "all"}, ("to", "20", "R201")
    )
    assert "all" in raw and " to desk@example.test" in raw
    variants.check_literals(text, raw, ("to", "20", "R201"))
    for broken in (raw.replace("desk@", "evil@"), raw.replace("20", "21")):
        with pytest.raises(ValueError):
            variants.check_literals(text, broken, ("to", "20", "R201"))


def test_reference_observables_are_reproducible(loaded: tuple, tmp_path: Path) -> None:
    cases, rows = loaded
    row = next(r for r in rows if r.task_id == "awb_query" and r.branch == "attack")
    checks = [
        run_reference(
            ROOT, cases[row.task_id], row.raw_payload, row.branch, "safe", tmp_path / str(i)
        )
        for i in range(2)
    ]
    assert checks[0]["run_id"] != checks[1]["run_id"]
    assert checks[0]["observable_sha256"] == checks[1]["observable_sha256"]
