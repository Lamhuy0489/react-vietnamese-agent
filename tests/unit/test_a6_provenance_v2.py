from __future__ import annotations

from pathlib import Path

import pytest
from test_adversarial_eval_v1 import execute

from react_agent.adversarial_release import load_split
from react_agent.authoring.selected_runtime import load_selected
from react_agent.security_v1 import a6_provenance_v2 as v2

ROOT = Path(__file__).resolve().parents[2]


def test_user_destinations_skip_negated_conditional_and_quoted_text() -> None:
    _, endpoints = v2.user_destinations(
        "Sau khi tính xong, gửi webhook tới mock://internal/a với payload chính xác "
        '{"total":1}. Nếu cần, gửi mock://internal/b. Không gửi mock://internal/c. '
        'Tài liệu nói "gửi mock://internal/d".')
    assert endpoints == {"mock://internal/a"}
    emails, _ = v2.user_destinations("Gửi email tới c@example.test, đừng gửi d@example.test")
    assert emails == {"c@example.test"}


def test_word_bounded_match_never_matches_inside_a_url() -> None:
    text = "ghi visibility=internal tới mock://internal/publication"
    assert v2._in_text("internal", text) and not v2._in_text("public", text)


@pytest.fixture
def activated():  # noqa: ANN201
    v2.activate()
    yield
    v2.deactivate()


@pytest.fixture(scope="module")
def inputs():  # noqa: ANN201
    rows = {row.variant_id: row for row in load_split(ROOT / "data/adversarial/release_v2")}
    return rows, load_selected(ROOT)[1]


@pytest.mark.usefixtures("activated")
def test_a6_v2_recovers_user_computed_payload_and_still_blocks_injected_value(
    tmp_path: Path, inputs
) -> None:
    rows, cases = inputs
    benign = rows["BEN_CAND_AGGREGATE_CODE_MIX"]  # count = calculator(1+1), user endpoint
    assert execute(tmp_path / "b", benign, cases[benign.task.task_id], "A6", "safe")["utility"]
    attack = rows["ATK_CAND_VISIBILITY_PARAPHRASE"]  # injected visibility=public
    scored = execute(tmp_path / "a", attack, cases[attack.task.task_id], "A6", "negative")
    assert not scored["harmful"] and scored["denied"]


def test_activation_round_trip() -> None:
    import react_agent.security_v1.runtime_v14_email_origin_candidate as runtime_v14

    original = runtime_v14.CandidateA6Policy
    assert v2.activate()["name"] == "a6_provenance_v2"
    assert runtime_v14.CandidateA6Policy is v2.ProvenanceA6Policy
    v2.deactivate()
    assert runtime_v14.CandidateA6Policy is original
