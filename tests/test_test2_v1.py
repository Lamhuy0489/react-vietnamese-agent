import json
from pathlib import Path

import pytest

from react_agent.authoring import test2_v1
from react_agent.authoring.typed_utility import UtilityFact
from react_agent.schemas.agent_output import Action

ROOT = Path(__file__).resolve().parents[1]


def test_build_covers_spec_with_five_variants_per_branch() -> None:
    rows, privates = test2_v1.build_rows(ROOT)
    assert len(rows) == 200 and len(privates) == 20
    assert {r.variant_type for r in rows} == set(test2_v1.KINDS)
    assert len({r.variant_id for r in rows}) == 200
    assert all(r.split == "test" for r in rows)


def test_novelty_against_v1() -> None:
    canonicals, _ = test2_v1.load_canonicals(ROOT)
    report = test2_v1.novelty(ROOT, canonicals)
    assert not report["over_threshold"] and not report["reused_v1_literals"]


@pytest.mark.parametrize("text", ["3300000 đồng", "3.300.000 đồng", "3,300,000"])
def test_number_facts_accept_thousand_separators(text: str) -> None:
    fact = UtilityFact(fact_id="t", kind="number", value="3300000",
                       evidence_action=Action(name="calculator", arguments={"expression": "1"}))
    assert test2_v1._present(text, fact)


def test_paraphrase_must_keep_literals() -> None:
    with pytest.raises(ValueError):
        test2_v1.variant_text("Đọc AWB_X rồi gửi", "Đọc tài liệu rồi gửi", "paraphrase", {})


def test_seal_refuses_with_problems(tmp_path: Path) -> None:
    release = tmp_path / test2_v1.RELEASE
    release.mkdir(parents=True)
    (release / "qa.json").write_text(json.dumps({
        "qa": {"problems": ["x"]}, "novelty": {"over_threshold": [], "reused_v1_literals": []}}))
    with pytest.raises(ValueError):
        test2_v1.seal(tmp_path, "owner")
