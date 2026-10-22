"""Independent saved-data checks, including corrupted receipts with no model rerun."""

import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def saved(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    controls = importlib.import_module("run_phase5_field_reference_v1")
    auditor = importlib.import_module("audit_phase5_field_reference_v1")
    path = tmp_path / "saved"
    controls.run_case("prose", "selected", path)
    documents, catalog = controls.fixture("prose")
    fixture = dict(documents=[d.model_dump(mode="json") for d in documents],
                   catalog=catalog.model_dump(mode="json"))
    return auditor, path, fixture


def test_repeated_audit_does_not_write(saved):
    audit, root, fixture = saved
    before = audit.inventory(root)
    first = audit.audit_case(root, fixture, "prose", "selected")
    assert first == audit.audit_case(root, fixture, "prose", "selected")
    assert first["valid"] and audit.inventory(root) == before


@pytest.mark.parametrize("fault", ["output", "allowed", "label", "plan", "broker", "fixture"])
def test_saved_evidence_corruption_rejected(saved, fault):
    audit, root, fixture = saved
    if fault in {"output", "allowed", "label"}:
        path = root / "decision.json"
        value = json.loads(path.read_text())
        key, replacement = {"output": ("output", "changed"), "allowed": ("allowed", False),
                            "label": ("effective_sensitivity", "S2")}[fault]
        value[key] = replacement
        path.write_text(json.dumps(value))
    elif fault == "plan":
        path = root / "plan.json"
        value = json.loads(path.read_text())
        value["transforms"] = ["hex"]
        path.write_text(json.dumps(value))
    elif fault == "broker":
        path = root / "broker.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[2]["data"]["content"]["content"] = "changed"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    else:
        fixture["documents"][0]["content"] = "changed"
    with pytest.raises(ValueError):
        audit.audit_case(root, fixture, "prose", "selected")
