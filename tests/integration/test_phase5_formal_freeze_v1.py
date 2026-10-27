from __future__ import annotations

from pathlib import Path

from react_agent.validation.phase5_formal_freeze_v1 import build_freeze

ROOT = Path(__file__).resolve().parents[2]


def test_formal_freeze_maps_all_dod_and_keeps_no_go():
    result = build_freeze(ROOT)
    assert result["decision"] == "NO_GO"
    assert result["phase5_accepted"] is False
    assert result["dod_count"] == 20
    assert result["open_dod"] == list(range(1, 21))
    assert result["test_payloads_read"] == 0
    assert result["private_ground_truth_read"] == 0
    assert result["inference_performed"] is False
    assert result["uncertain_delivery_in_current_receipts"] is False
    assert set(result["dod_disposition"]) == {str(i) for i in range(1, 21)}
