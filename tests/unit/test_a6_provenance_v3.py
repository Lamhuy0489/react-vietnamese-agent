from __future__ import annotations

from pathlib import Path

import react_agent.security_v1.runtime_v14_email_origin_candidate as runtime_v14
from react_agent.adversarial_release import load_split
from react_agent.security_v1 import a6_provenance_v3
from react_agent.security_v1.a6_provenance_v3 import ClauseAnchoredScope, unquoted
from react_agent.security_v1.phase5_runtime import Phase5Runtime
from react_agent.security_v1.processing_scope_v5 import ProcessingScope as V5Scope
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.security_v1.sql_rows_v1 import RowBindings
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog

ROOT = Path(__file__).resolve().parents[2]


def test_unquoted_removes_balanced_spans_and_rejects_unbalanced() -> None:
    assert unquoted('Đọc AWB_X. Gửi {"a":"b"}.') == "Đọc AWB_X. Gửi { : }."
    assert unquoted('Đọc AWB_X "mở') is None
    assert unquoted("> Đọc AWB_X") is None


def _scopes(variant_id: str) -> tuple[V5Scope, ClauseAnchoredScope]:
    row = next(r for r in load_split(ROOT / "data/adversarial/release_v2")
               if r.variant_id == variant_id)
    catalog = fixture_catalog(row)
    kwargs = {"resources": ResourceBindings.from_catalog(catalog),
              "rows": RowBindings.from_catalog(catalog)}
    return V5Scope(row.task.instruction, **kwargs), ClauseAnchoredScope(
        row.task.instruction, **kwargs)


def test_document_named_outside_quotes_is_anchored() -> None:
    old, new = _scopes("BEN_CAND_SOURCECLAIM_CODE_MIX")
    assert old.anchors.documents == ()
    assert new.anchors.documents == ("AWB_SOURCECLAIM",) and new.anchors.explicit_scope


def test_instruction_without_quotes_is_unchanged() -> None:
    old, new = _scopes("BEN_CAND_AGGREGATE_CODE_MIX")
    assert old.anchors == new.anchors


def test_activation_swaps_scope_only_while_an_a6_run_executes() -> None:
    try:
        a6_provenance_v3.activate()
        assert Phase5Runtime._run_task is a6_provenance_v3._run_task
        assert getattr(runtime_v14, "ProcessingScope") is a6_provenance_v3._ORIGINAL_SCOPE  # noqa: B009
    finally:
        a6_provenance_v3.deactivate()
    assert Phase5Runtime._run_task is a6_provenance_v3._ORIGINAL_RUN
