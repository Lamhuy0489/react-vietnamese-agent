"""Typed-reference semantics and fail-closed host boundaries; no benchmark payloads."""

import importlib
from pathlib import Path

import pytest

from react_agent.foundation.artifacts import Sensitivity, Trust
from react_agent.logging.trace_logger import TraceLogger
from react_agent.prototypes.field_reference_v1 import LIMIT, Plan, ReferenceError, Session


@pytest.fixture
def controls(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("run_phase5_field_reference_v1")


@pytest.mark.parametrize("case", [
    "prose", "multiline", "collision", "repeat", "public_base64", "public_hex",
    "concat_public", "trusted_public", "private", "private_base64", "private_hex",
    "mixed", "ungranted", "wrong_hash", "unknown", "veto",
])
def test_matched_broker_controls(controls, tmp_path, case):
    candidate = controls.run_case(case, "selected", tmp_path / "candidate")
    baseline = controls.run_case(case, "exposure", tmp_path / "baseline")
    assert candidate["desired"] is True
    assert baseline["allowed"] is False
    assert candidate["broker_reads"] == baseline["broker_reads"]
    assert candidate["matched_input_sha256"] == baseline["matched_input_sha256"]


@pytest.mark.parametrize("sensitivity", [Sensitivity.INTERNAL, Sensitivity.CONFIDENTIAL])
@pytest.mark.parametrize("trust", list(Trust))
@pytest.mark.parametrize("transforms", [(), ("base64",), ("hex",), ("base64", "hex")])
def test_transform_never_sheds_label(controls, sensitivity, trust, transforms):
    session = controls.new_session("prose", "labels", TraceLogger())
    catalog = session.catalog.model_copy(update={"bindings": tuple(
        binding.model_copy(update={"label": binding.label.model_copy(update={
            "sensitivity": sensitivity, "trust": trust})})
        for binding in session.catalog.bindings)})
    grant = session.grant.model_copy(update={"catalog_sha256": controls.text_hash(
        controls.canonical_json(catalog.model_dump(mode="json")))})
    session = Session(session.broker, catalog, controls.USER, grant, grant.sha256)
    ref = session.read_document("REF_PRIVATE")
    result = session.finalize(Plan(refs=(ref,), transforms=transforms), upstream_allowed=True)
    assert not result.allowed and result.output is None
    assert result.effective_sensitivity == sensitivity
    rendered = session.store.get(result.rendered_artifact_id)
    assert rendered.sensitivity == sensitivity and rendered.trust == trust


@pytest.mark.parametrize("fault", ["literal", "expression", "cross_run", "grant", "path",
                                   "type", "too_many_refs", "transform", "too_many_transforms"])
def test_untrusted_proposal_cannot_forge_authority(controls, fault):
    session = controls.new_session("prose", "invalid", TraceLogger())
    ref = session.read_document("REF_PUBLIC")
    proposal = Plan(refs=(ref,)).model_dump(mode="json")
    if fault in {"literal", "expression"}:
        proposal[fault] = "synthetic private text"
    elif fault == "cross_run":
        proposal["refs"][0]["run_id"] = "elsewhere"
    elif fault == "grant":
        proposal["refs"][0]["grant_sha256"] = "0" * 64
    elif fault == "path":
        proposal["refs"][0]["path"] = "/../content"
    elif fault == "type":
        proposal["refs"][0]["value_type"] = "number"
    elif fault == "too_many_refs":
        proposal["refs"] *= 9
    elif fault == "transform":
        proposal["transforms"] = ["eval"]
    else:
        proposal["transforms"] = ["base64"] * 5
    before = session.store.serialize()
    decision = session.finalize(proposal, upstream_allowed=True)
    assert decision.allowed is False and decision.output is None
    assert session.store.serialize() == before


def test_no_veto_permission_by_default_and_independent_labels(controls):
    session = controls.new_session("trusted_public", "veto", TraceLogger())
    ref = session.read_document("REF_PUBLIC")
    session.read_document("REF_PRIVATE")
    plan = Plan(refs=(ref,))
    assert not session.finalize(plan).allowed
    assert not session.finalize(plan, upstream_allowed=1).allowed
    allowed = session.finalize(plan, upstream_allowed=True)
    assert allowed.allowed
    assert session.store.get(allowed.rendered_artifact_id).trust == Trust.TRUSTED


@pytest.mark.parametrize("fault", ["pin", "user", "catalog", "unknown_read", "read_budget"])
def test_host_admission_before_broker(controls, fault):
    logger = TraceLogger()
    session = controls.new_session("prose", "admission", logger)
    if fault in {"pin", "user", "catalog"}:
        grant = session.grant
        if fault == "catalog":
            grant = grant.model_copy(update={"catalog_sha256": "0" * 64})
        with pytest.raises(ReferenceError):
            Session(session.broker, session.catalog, "wrong" if fault == "user" else controls.USER,
                    grant, "0" * 64 if fault == "pin" else grant.sha256)
        assert not logger.events
    elif fault == "unknown_read":
        with pytest.raises(ReferenceError):
            session.read_document("NOT_GRANTED")
        assert not logger.events
    else:
        for _ in range(64):
            session.read_document("REF_PUBLIC")
        count = len(logger.events)
        with pytest.raises(ReferenceError):
            session.read_document("REF_PUBLIC")
        assert len(logger.events) == count


def test_output_expansion_limit(controls):
    session = controls.new_session("prose", "size", TraceLogger())
    tool = session.broker.registry.get("doc_read")
    tool._store.get("REF_PUBLIC").content = "ắ" * (LIMIT // 4)
    ref = session.read_document("REF_PUBLIC")
    decision = session.finalize(Plan(refs=(ref,), transforms=("hex",)), upstream_allowed=True)
    assert not decision.allowed and decision.output is None


def test_failed_tool_never_creates_reference(controls):
    session = controls.new_session("prose", "missing", TraceLogger())
    tool = session.broker.registry.get("doc_read")
    tool._store._documents.pop("REF_PUBLIC")
    with pytest.raises(ReferenceError):
        session.read_document("REF_PUBLIC")
    assert not session.store.all()
    assert session.broker.logger.events[-1].data["ok"] is False


def test_collision_keeps_value_and_exposure_lineage_separate(controls):
    session = controls.new_session("collision", "collision_labels", TraceLogger())
    public = session.read_document("REF_PUBLIC")
    private = session.read_document("REF_PRIVATE")
    before = {a.artifact_id: a.model_dump_json() for a in session.store.all()}
    decision = session.finalize(Plan(refs=(public,)), upstream_allowed=True)
    rendered = session.store.get(decision.rendered_artifact_id)
    assert decision.allowed and rendered.sensitivity == Sensitivity.PUBLIC
    assert rendered.trust == Trust.UNTRUSTED
    assert [p.parent_id for p in rendered.parents] == [public.artifact_id]
    assert private.artifact_id in controls.json.loads(rendered.metadata_json)["exposure_ids"]
    assert all(session.store.get(k).model_dump_json() == value for k, value in before.items())


def test_model_copy_is_revalidated(controls):
    session = controls.new_session("prose", "modelcopy", TraceLogger())
    ref = session.read_document("REF_PUBLIC").model_copy(update={"value_type": "code"})
    plan = Plan.model_construct(refs=(ref,), separator="", transforms=())
    assert not session.finalize(plan, upstream_allowed=True).allowed


def test_unknown_catalog_rejects_before_broker(controls):
    session = controls.new_session("prose", "no_metadata", TraceLogger())
    catalog = controls.SourceCatalog()
    grant = session.grant.model_copy(update={"catalog_sha256": controls.text_hash(
        controls.canonical_json(catalog.model_dump(mode="json")))})
    session = Session(session.broker, catalog, controls.USER, grant, grant.sha256)
    with pytest.raises(ReferenceError, match="metadata"):
        session.read_document("REF_PUBLIC")
    assert not session.broker.logger.events


@pytest.mark.parametrize("fault", ["extra_field", "non_text", "wrong_document", "source_budget"])
def test_raw_wrapper_and_budget(controls, fault, monkeypatch):
    session = controls.new_session("prose", "bad_wrapper", TraceLogger())
    tool = session.broker.registry.get("doc_read")
    document = tool._store.get("REF_PUBLIC")
    if fault == "source_budget":
        document.content = "x" * LIMIT
    elif fault == "wrong_document":
        document.doc_id = "WRONG_SOURCE"
    elif fault == "non_text":
        monkeypatch.setattr(tool, "_run", lambda *_: dict(document.model_dump(), content=12))
    else:
        monkeypatch.setattr(tool, "_run",
                            lambda *_: dict(document.model_dump(), extra="unreviewed"))
    with pytest.raises(ReferenceError):
        session.read_document("REF_PUBLIC")
    assert not session.store.all()


def test_broker_component_performs_no_network(controls, tmp_path, monkeypatch):
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError("network is forbidden")
    monkeypatch.setattr(socket, "socket", forbidden)
    assert controls.run_case("prose", "selected", tmp_path / "offline")["desired"] is True
