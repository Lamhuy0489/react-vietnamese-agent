from __future__ import annotations

from typing import Any

from react_agent.evaluation.test2_eval_v1 import summarize_test2


def _rec(config: str, branch: str, fam: str, harm: bool, utility: bool,
         v1_harm: bool | None = None, denied: bool = False) -> dict[str, Any]:
    prefix = "ATK_" if branch == "attack" else "BEN_"
    return {"config": config, "variant_id": f"{prefix}{fam}", "branch": branch,
            "family_id": fam, "variant_type": "x",
            "score": {"status": "completed", "utility": utility, "denied": denied,
                      "side_effect_harm": harm,
                      "harmful": harm if v1_harm is None else v1_harm}}


def test_paired_asr_discounts_harm_shared_with_benign_pair() -> None:
    records = [_rec("A0", "attack", "F1", True, False), _rec("A0", "benign", "F1", False, True),
               _rec("A0", "attack", "F2", True, False), _rec("A0", "benign", "F2", True, True),
               _rec("D2", "attack", "F1", False, True), _rec("D2", "benign", "F1", False, True),
               _rec("D2", "attack", "F2", False, True),
               _rec("D2", "benign", "F2", False, False, denied=True)]
    out = summarize_test2(records)
    a0 = out["configs"]["A0"]["side_effect"]
    assert a0["paired_asr"]["k"] == 1 and a0["asr"]["k"] == 2 and a0["benign_harm"] == 1
    d2 = out["configs"]["D2"]["side_effect"]
    assert d2["paired_asr"]["k"] == 0 and d2["false_block"]["k"] == 1
    primary = out["primary"]["A0->D2"]
    assert primary["paired_asr_side_effect"] == {"b": 1, "c": 0, "p_value": 1.0, "n": 2}
    assert primary["benign_utility"]["b"] == 1
    assert set(out["primary"]["A6->D2"].values()) == {None}
    assert set(out["configs"]) == {"A0", "D2"}


def test_v1_and_side_effect_harm_are_scored_separately() -> None:
    records = [_rec("A1", "attack", "F1", False, False, v1_harm=True),
               _rec("A1", "benign", "F1", False, True)]
    out = summarize_test2(records)["configs"]["A1"]
    assert out["v1"]["paired_asr"]["k"] == 1 and out["side_effect"]["paired_asr"]["k"] == 0
