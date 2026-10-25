from __future__ import annotations

import pytest

from react_agent.schemas.clean_task import AnswerFact
from react_agent.validation import clean_comparators, clean_rebuild_v1


def fact(value: float) -> AnswerFact:
    return AnswerFact.model_validate(
        {"fact_id": "fact_num", "type": "number", "comparator": "numeric_equal", "value": value}
    )


@pytest.mark.parametrize("answer", ["8.0", "GPA là 8.0.", "GPA: 8.0!", "(8.0)", "8.0, còn lại"])
def test_sentence_final_number_matches(answer: str) -> None:
    assert clean_rebuild_v1.fact_in_text(answer, fact(8.0))


@pytest.mark.parametrize("answer", ["8.05", "18.0", "8.0kg", "phòng A8.0.1"])
def test_other_numbers_still_do_not_match(answer: str) -> None:
    assert not clean_rebuild_v1.fact_in_text(answer, fact(8.0))


def test_original_bug_and_activation_round_trip() -> None:
    assert not clean_comparators.fact_in_text("bằng 876.", fact(876))
    clean_rebuild_v1.activate()
    try:
        assert clean_comparators.fact_in_text("bằng 876.", fact(876))
    finally:
        clean_rebuild_v1.deactivate()
    assert not clean_comparators.fact_in_text("bằng 876.", fact(876))
