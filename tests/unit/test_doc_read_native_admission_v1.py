"""No-model external-pin/source/input failures and durable native dispatch controls."""

import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.llm import doc_read_native_dispatch_v1 as dispatch
from react_agent.llm.base import GenerationConfig
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1.doc_read_final_proof_v1 import DocReadApproval
from react_agent.validation import doc_read_native_admission_v1 as admission
from react_agent.validation import doc_read_native_release_v1 as release
from react_agent.validation.context_stress_audit_v1 import inventory

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "a" * 40


def inputs(tmp_path):
    project = tmp_path / "project"
    files = {}
    for name in sorted(admission.REQUIRED):
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic public source")
        files[name] = admission.source.digest(path)
    source = tmp_path / "source.json"
    source.write_text(json.dumps(dict(
        protocol=admission.SOURCE_PROTOCOL, source_mode="committed", source_commit=COMMIT,
        git_base_commit=COMMIT, source_sha256=files, archive_sha256="b" * 64,
    )))
    base = tmp_path / "inputs"
    base.mkdir()
    approved = DocReadApproval(source_id="DOC_NATIVEPUB", review_ref="synthetic-precontent-review")
    catalog = SourceCatalog(bindings=(SourceBinding(
        tool="doc_read", arguments_json=canonical_json({"doc_id": approved.source_id}),
        label=SourceLabel(source_type=SourceType.DOCUMENT, source_id=approved.source_id,
                          sensitivity=Sensitivity.PUBLIC, trust=Trust.UNTRUSTED),
    ),))
    snapshot = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_bytes()
    )
    records = {
        "task.json": dict(task_id="awb_nativeproof", instruction="Trả content từ DOC_NATIVEPUB."),
        "approval.json": approved.model_dump(mode="json"),
        "catalog.json": catalog.model_dump(mode="json"),
        "runtime.json": RuntimeConfig().model_dump(mode="json"),
        "generation.json": GenerationConfig().model_dump(mode="json"),
        "agent_inventory.json": json.loads(
            (ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json").read_text()),
        "guard_snapshot.json": snapshot.model_dump(mode="json"),
    }
    for name, value in records.items():
        (base / name).write_text(json.dumps(value))
    environment = base / "environment"
    for name in admission.ENVIRONMENT_FILES:
        destination = environment / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "data/smoke" / name, destination)
    (environment / "documents/documents.json").write_text(json.dumps([
        dict(doc_id="DOC_NATIVEPUB", title="Public label", content="NATIVELABEL1947")
    ]))
    manifest = tmp_path / "run.json"
    manifest.write_text(json.dumps(dict(
        protocol="phase5_doc_read_native_run_v1", expected_task_count=1, task_id="awb_nativeproof",
        source_commit=COMMIT, source_manifest_sha256=admission.source.digest(source),
        files={name: admission.source.digest(base / name) for name in admission.INPUT_FILES},
        environment_sha256=text_hash(canonical_json(inventory(environment))),
        approval_sha256=approved.identity, agent_model_id="Qwen/Qwen2.5-7B-Instruct",
        agent_revision=records["agent_inventory.json"]["upstream_revision"],
        agent_runtime_revision=admission.AGENT_REVISION, guard_revision=snapshot.model_revision,
        guard_snapshot_sha256=snapshot.sha256, seed=GenerationConfig().seed,
        evaluator_version="synthetic-unscored-control", native_model_authenticated=False,
        phase5_accepted=False,
    )))
    return dict(manifest_path=manifest, expected_manifest_sha256=admission.source.digest(manifest),
                project=project, source_manifest=source, inputs=base)


def test_admits_exact_external_pins(tmp_path):
    values = inputs(tmp_path)
    result = admission.admit_run(**values)
    assert result.task.task_id == "awb_nativeproof"
    assert result.approval.identity == result.manifest.approval_sha256


@pytest.mark.parametrize("fault", [
    "run_pin", "source", "untracked", "working_tree", "task", "catalog", "approval",
    "runtime", "generation", "environment", "model", "snapshot", "extra_input", "symlink",
    "hidden_environment",
])
def test_bad_inputs_reject_before_worker_creation(tmp_path, monkeypatch, fault):
    values = inputs(tmp_path)
    if fault == "run_pin":
        values["expected_manifest_sha256"] = "0" * 64
    elif fault == "source":
        (values["project"] / sorted(admission.REQUIRED)[0]).write_text("changed")
    elif fault == "untracked":
        (values["project"] / "extra.py").write_text("shadow")
    elif fault == "working_tree":
        source = json.loads(values["source_manifest"].read_text())
        source.update(source_mode="working_tree", source_commit=None)
        values["source_manifest"].write_text(json.dumps(source))
        manifest = json.loads(values["manifest_path"].read_text())
        manifest["source_manifest_sha256"] = admission.source.digest(values["source_manifest"])
        values["manifest_path"].write_text(json.dumps(manifest))
        values["expected_manifest_sha256"] = admission.source.digest(values["manifest_path"])
    elif fault == "environment":
        (values["inputs"] / "environment/documents/documents.json").write_text("[]")
    elif fault == "extra_input":
        (values["inputs"] / "oracle.json").write_text("{}")
    elif fault == "hidden_environment":
        (values["inputs"] / "environment/oracle.json").write_text("{}")
        manifest = json.loads(values["manifest_path"].read_text())
        manifest["environment_sha256"] = text_hash(canonical_json(
            inventory(values["inputs"] / "environment")))
        values["manifest_path"].write_text(json.dumps(manifest))
        values["expected_manifest_sha256"] = admission.source.digest(values["manifest_path"])
    elif fault == "symlink":
        target = values["inputs"] / "catalog.json"
        retained = values["inputs"] / "retained.json"
        target.rename(retained)
        target.symlink_to(retained)
    else:
        names = {"model": "agent_inventory", "snapshot": "guard_snapshot"}
        path = values["inputs"] / (names.get(fault, fault) + ".json")
        path.write_text(path.read_text() + "\n")
    def forbid(*args, **kwargs):
        raise AssertionError("worker must not be constructed")
    monkeypatch.setattr(dispatch, "build_pair", forbid)
    output = tmp_path / "result"
    with pytest.raises(ValueError):
        dispatch.run(**values, agent=tmp_path / "agent", guard=tmp_path / "guard", output=output)
    assert not output.exists()


def test_output_overlap_rejected(tmp_path):
    values = inputs(tmp_path)
    with pytest.raises(ValueError, match="overlaps"):
        dispatch.run(**values, agent=tmp_path / "agent", guard=tmp_path / "guard",
                     output=values["inputs"] / "output")


def test_shadow_source_does_not_authenticate_executing_code(tmp_path, monkeypatch):
    values = inputs(tmp_path)
    def forbid(*args, **kwargs):
        raise AssertionError("worker must not start")
    monkeypatch.setattr(dispatch, "build_pair", forbid)
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="outside admitted project"):
        dispatch.run(**values, agent=tmp_path / "agent", guard=tmp_path / "guard", output=output)
    assert not output.exists()


@pytest.mark.parametrize("fault", [None, "outside", "multiple", "missing", "not_namespace"])
def test_public_validation_namespace_source(monkeypatch, tmp_path, fault):
    paths = [str(ROOT / "src/react_agent/validation")]
    if fault == "outside":
        paths = [str(tmp_path)]
    elif fault == "multiple":
        paths.append(str(tmp_path))
    elif fault == "missing":
        paths = []
    module = SimpleNamespace(__file__=None, __path__=paths,
                             __spec__=SimpleNamespace(origin="fake" if fault == "not_namespace"
                                                      else None))
    monkeypatch.setitem(sys.modules, "react_agent.validation", module)
    if fault is None:
        dispatch.execution_source(ROOT)
    else:
        with pytest.raises(ValueError, match="outside admitted project"):
            dispatch.execution_source(ROOT)


@pytest.mark.parametrize("fault", [None, "execute", "join", "agent", "guard", "resume_raw"])
def test_dispatch_and_resume_with_stubbed_native_boundary(tmp_path, monkeypatch, fault):
    values = inputs(tmp_path)
    # This unit harness simulates source/worker boundaries, never authenticates native execution.
    monkeypatch.setattr(dispatch, "execution_source", lambda *_: None)
    calls = []
    class Pair:
        def close(self):
            calls.append("closed")
    def build(*args, **kwargs):
        calls.append("built")
        return Pair()
    def execute(*args, **kwargs):
        if fault == "execute":
            raise ValueError("synthetic worker failure")
        output = kwargs["output"] / "runtime"
        output.mkdir(parents=True)
        admitted = admission.admit_run(**values)
        (output / "run_metadata.json").write_text(json.dumps(dict(
            task_hash=text_hash(admitted.task.instruction), task_id=admitted.task.task_id,
            source_catalog=admitted.catalog.model_dump(mode="json"),
            runtime_config=admitted.runtime.model_dump(mode="json"),
            generation_config=admitted.generation.model_dump(mode="json"),
            model_id=admitted.manifest.agent_model_id,
            model_revision=("wrong" if fault == "agent"
                            else admitted.manifest.agent_runtime_revision),
            guard_execution=dict(model_id=admitted.snapshot.model_id,
                                 model_revision="wrong" if fault == "guard"
                                 else admitted.manifest.guard_revision),
            result=dict(status="completed"),
        )))
        return SimpleNamespace(result=SimpleNamespace(status="completed"))
    monkeypatch.setattr(dispatch, "build_pair", build)
    monkeypatch.setattr(dispatch, "run_pair_task", execute)
    def join(*args, **kwargs):
        if fault == "join":
            raise ValueError("synthetic join failure")
        return {"valid": True}
    monkeypatch.setattr(release, "audit_join", join)
    kwargs = dict(**values, agent=tmp_path / "agent", guard=tmp_path / "guard",
                  output=tmp_path / "run")
    if fault in ("execute", "join", "agent", "guard"):
        with pytest.raises(ValueError):
            dispatch.run(**kwargs)
        assert calls == ["built", "closed"]
        assert not (kwargs["output"] / "checkpoint.json").exists()
        before = inventory(kwargs["output"])
        with pytest.raises(ValueError, match="manual triage"):
            dispatch.run(**kwargs, resume=True)
        assert inventory(kwargs["output"]) == before and calls == ["built", "closed"]
        return
    assert dispatch.run(**kwargs)["valid"] is True
    assert calls == ["built", "closed"]
    if fault == "resume_raw":
        metadata = kwargs["output"] / "execution/runtime/run_metadata.json"
        metadata.write_text(metadata.read_text() + "\n")
        before = inventory(kwargs["output"])
        with pytest.raises(ValueError, match="immutable complete raw checkpoint"):
            dispatch.run(**kwargs, resume=True)
        assert inventory(kwargs["output"]) == before and calls == ["built", "closed"]
        return
    before = inventory(kwargs["output"])
    assert dispatch.run(**kwargs, resume=True)["terminal"] == "completed"
    assert calls == ["built", "closed"] and inventory(kwargs["output"]) == before
    checkpoint = kwargs["output"] / "checkpoint.json"
    checkpoint.rename(kwargs["output"] / "saved_checkpoint.json")
    with pytest.raises(ValueError, match="manual triage"):
        dispatch.run(**kwargs, resume=True)
    assert calls == ["built", "closed"]
