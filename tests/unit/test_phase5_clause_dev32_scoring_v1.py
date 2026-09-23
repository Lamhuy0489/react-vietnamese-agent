"""Evaluator-only Dev32 scorer controls; no held-out payload or model run."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from pydantic import BaseModel


def scorer():  # type: ignore[no-untyped-def]
    path = Path(__file__).resolve().parents[2] / "scripts/score_phase5_clause_dev32_v1.py"
    spec = importlib.util.spec_from_file_location("dev32_scorer_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event(name: str, data: dict[str, object]) -> str:
    return json.dumps(
        {
            "event": name,
            "task_id": "awb_demo",
            "run_id": "run_demo",
            "data_json": json.dumps(data),
        }
    )


def test_security_proposals_retains_prebroker_denial(tmp_path: Path) -> None:
    path = tmp_path / "trace_security.jsonl"
    path.write_text(
        "\n".join(
            [
                event(
                    "proposal",
                    {
                        "proposal_id": "p1",
                        "action": {
                            "name": "doc_read",
                            "arguments": {"doc_id": "AUX_DEMO"},
                        },
                    },
                ),
                event("decision", {"stage": "PRE", "proposal_id": "p1", "effect": "DENY"}),
                event("released_final", {"artifact_id": "art_final"}),
            ]
        )
        + "\n"
    )
    proposals, released = scorer().security_proposals(path, "awb_demo", "run_demo")
    assert len(proposals) == 1
    assert proposals[0][0].name == "doc_read" and proposals[0][1] is True
    assert released == "art_final"


@pytest.mark.parametrize("effect", ["BLOCK", "", "TAG"])
def test_unknown_pre_effect_fails_closed(tmp_path: Path, effect: str) -> None:
    path = tmp_path / "trace_security.jsonl"
    path.write_text(
        "\n".join(
            [
                event(
                    "proposal",
                    {
                        "proposal_id": "p1",
                        "action": {
                            "name": "doc_read",
                            "arguments": {"doc_id": "AUX_DEMO"},
                        },
                    },
                ),
                event("decision", {"stage": "PRE", "proposal_id": "p1", "effect": effect}),
                event("released_final", {"artifact_id": "art_final"}),
            ]
        )
        + "\n"
    )
    with pytest.raises(ValueError, match="bounded PRE effect"):
        scorer().security_proposals(path, "awb_demo", "run_demo")


def test_selected_record_rejects_missing_or_duplicate_id(tmp_path: Path) -> None:
    class Row(BaseModel):
        task_id: str
        value: int

    path = tmp_path / "sidecar.json"
    path.write_text(
        json.dumps(
            [
                {"task_id": "awb_selected", "value": 7},
                {"task_id": "awb_unselected", "value": 9},
            ]
        )
    )
    assert scorer().selected_record(path, "awb_selected", Row).value == 7
    with pytest.raises(ValueError, match="one selected Dev oracle record"):
        scorer().selected_record(path, "awb_missing", Row)
    path.write_text(json.dumps([{"task_id": "awb_selected", "value": 7}] * 2))
    with pytest.raises(ValueError, match="one selected Dev oracle record"):
        scorer().selected_record(path, "awb_selected", Row)
