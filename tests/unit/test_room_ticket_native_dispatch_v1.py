"""No-model controls for source-gated native dispatch and durable resume."""

import json
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.llm import room_control_native_dispatch_v1 as control
from react_agent.llm import room_ticket_native_dispatch_v1 as candidate
from react_agent.llm.base import GenerationConfig
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation import room_control_native_release_v1 as control_release
from react_agent.validation import room_prospective_run_manifest_v2 as prospective
from react_agent.validation import room_ticket_native_release_v1 as release
from react_agent.validation import room_ticket_run_manifest_v1 as run_manifest
from react_agent.validation.room_inventory_review_v1 import RoomInventoryReview

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "a" * 40
REVIEW = ROOT / "experiments/manifests/phase5_room_prospective_inventory_review_v1.json"
DRAFT = ROOT / "experiments/manifests/phase5_room_prospective_inventory_review_draft_v1.json"
SNAPSHOT = ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json"


def inputs(tmp_path: Path) -> dict:
    project = tmp_path / "project"
    files = {}
    for name in sorted(release.REQUIRED):
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("public synthetic source", encoding="utf-8")
        files[name] = candidate.source.digest(path)
    manifest = tmp_path / "source_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "protocol": release.SOURCE_PROTOCOL,
                "source_mode": "committed",
                "source_commit": COMMIT,
                "git_base_commit": COMMIT,
                "source_sha256": files,
                "archive_sha256": "b" * 64,
            }
        ),
        encoding="utf-8",
    )
    environment = tmp_path / "environment"
    (environment / "documents").mkdir(parents=True)
    (environment / "documents/documents.json").write_text(
        json.dumps(
            [
                {"doc_id": "AUX_FUTUREPRIVATE", "title": "Synthetic private", "content": "private"},
                {"doc_id": "AUX_FUTUREROOM", "title": "Synthetic room", "content": "room"},
            ]
        ),
        encoding="utf-8",
    )
    review = RoomInventoryReview.model_validate_json(REVIEW.read_bytes())
    draft = DRAFT.read_bytes()
    pin = review.prepare_pin(
        draft, source_commit=COMMIT, declared_at_utc=review.recorded_at_utc + timedelta(seconds=1)
    )
    agent, guard = tmp_path / "agent", tmp_path / "guard"
    agent.mkdir()
    guard.mkdir()
    model_inventory = tmp_path / "model_inventory.json"
    model_inventory.write_text(
        json.dumps(
            {
                "model_id": "Qwen/Qwen2.5-7B-Instruct",
                "upstream_revision": "d" * 40,
            }
        ),
        encoding="utf-8",
    )
    return dict(
        task=SimpleNamespace(task_id="pilot_synthetic_001", instruction="Synthetic task"),
        output=tmp_path / "output",
        project=project,
        source_manifest=manifest,
        expected_source_sha256=candidate.source.digest(manifest),
        source_commit=COMMIT,
        environment=environment,
        review=review,
        draft_bytes=draft,
        pin=pin,
        expected_pin_sha256=pin.identity,
        run_manifest_sha256="c" * 64,
        agent=agent,
        model_inventory=model_inventory,
        guard=guard,
        snapshot=GuardSnapshot.model_validate_json(SNAPSHOT.read_text(encoding="utf-8")),
        runtime_config=RuntimeConfig(),
        generation=GenerationConfig(),
    )


def run_inputs(tmp_path: Path) -> dict:
    values = inputs(tmp_path)
    task_path = tmp_path / "task.json"
    task_path.write_text(
        json.dumps({"task_id": "awb_pilotsynthetic", "instruction": "Synthetic task"}),
        encoding="utf-8",
    )
    pin_path = tmp_path / "pin.json"
    pin_path.write_text(values["pin"].model_dump_json(), encoding="utf-8")
    runtime_path = tmp_path / "runtime.json"
    runtime_path.write_text(values["runtime_config"].model_dump_json(), encoding="utf-8")
    generation_path = tmp_path / "generation.json"
    generation_path.write_text(values["generation"].model_dump_json(), encoding="utf-8")
    paths = dict(
        project=values["project"],
        source_manifest=values["source_manifest"],
        review_path=REVIEW,
        draft_path=DRAFT,
        pin_path=pin_path,
        task_path=task_path,
        environment=values["environment"],
        model_inventory=values["model_inventory"],
        snapshot_path=SNAPSHOT,
        runtime_config_path=runtime_path,
        generation_path=generation_path,
    )
    manifest = dict(
        protocol="phase5_room_ticket_run_manifest_v1",
        arm="ticket",
        condition="clean_public_room",
        task_id="awb_pilotsynthetic",
        expected_task_count=1,
        source_commit=COMMIT,
        source_manifest_sha256=candidate.source.digest(values["source_manifest"]),
        review_sha256=candidate.source.digest(REVIEW),
        draft_sha256=candidate.source.digest(DRAFT),
        inventory_pin_sha256=values["pin"].identity,
        inventory_pin_file_sha256=candidate.source.digest(pin_path),
        task_sha256=candidate.source.digest(task_path),
        environment_sha256=run_manifest.text_hash(
            run_manifest.canonical_json(run_manifest.inventory(values["environment"]))
        ),
        model_inventory_sha256=candidate.source.digest(values["model_inventory"]),
        agent_model_id="Qwen/Qwen2.5-7B-Instruct",
        agent_model_revision="d" * 40,
        guard_snapshot_sha256=values["snapshot"].sha256,
        guard_snapshot_file_sha256=candidate.source.digest(SNAPSHOT),
        guard_model_revision=values["snapshot"].model_revision,
        runtime_config_sha256=candidate.source.digest(runtime_path),
        generation_sha256=candidate.source.digest(generation_path),
        seed=values["generation"].seed,
        evaluator_version="prospective_cpu_specimen_v1",
        source_authenticated_by_remote_audit=False,
        phase5_accepted=False,
    )
    manifest_path = tmp_path / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return dict(
        manifest_path=manifest_path,
        expected_manifest_sha256=candidate.source.digest(manifest_path),
        **paths,
    )


def test_external_run_manifest_admission_and_byte_pins(tmp_path: Path) -> None:
    values = run_inputs(tmp_path)
    admitted = run_manifest.admit_run(**values)
    assert admitted[0].arm == "ticket"
    assert admitted[1].task_id == "awb_pilotsynthetic"
    with pytest.raises(ValueError, match="external prospective run pin"):
        run_manifest.admit_run(**{**values, "expected_manifest_sha256": "0" * 64})
    with pytest.raises(ValueError, match="inventory pin file"):
        values["pin_path"].write_text(values["pin_path"].read_text() + "\n")
        run_manifest.admit_run(**values)


def test_prospective_output_never_overlaps_any_frozen_input(tmp_path: Path) -> None:
    values = run_inputs(tmp_path)
    with pytest.raises(ValueError, match="overlaps frozen input"):
        run_manifest.admit_output(tmp_path / "environment/output", (values["environment"],))
    with pytest.raises(ValueError, match="overlaps frozen input"):
        run_manifest.admit_output(tmp_path, (values["task_path"],))
    run_manifest.admit_output(tmp_path / "result", (values["environment"], values["task_path"]))


def test_run_manifest_rejects_changed_environment_and_seed(tmp_path: Path) -> None:
    values = run_inputs(tmp_path)
    document = values["environment"] / "documents/documents.json"
    document.write_text(document.read_text() + "\n")
    with pytest.raises(ValueError, match="prospective environment"):
        run_manifest.admit_run(**values)
    values = run_inputs(tmp_path / "second")
    config = json.loads(values["generation_path"].read_text())
    config["seed"] = 999
    values["generation_path"].write_text(json.dumps(config))
    with pytest.raises(ValueError, match="generation config file"):
        run_manifest.admit_run(**values)


def test_three_arm_manifests_share_all_non_arm_inputs(tmp_path: Path) -> None:
    values = run_inputs(tmp_path)
    initial = json.loads(values["manifest_path"].read_text())
    initial["protocol"] = "phase5_room_prospective_run_manifest_v2"
    initial["comparison_id"] = "room_cpu_control_001"
    paths = {}
    for arm in ("baseline", "metadata", "ticket"):
        path = tmp_path / f"{arm}.json"
        path.write_text(json.dumps({**initial, "arm": arm}))
        paths[arm] = (path, candidate.source.digest(path))
        admitted = prospective.admit_run(
            path,
            paths[arm][1],
            **{
                key: value
                for key, value in values.items()
                if key not in {"manifest_path", "expected_manifest_sha256"}
            },
        )
        assert admitted[0].arm == arm
    assert prospective.audit_triplet(paths)["valid"] is True
    changed = json.loads(paths["metadata"][0].read_text())
    changed["seed"] = 999
    paths["metadata"][0].write_text(json.dumps(changed))
    paths["metadata"] = (paths["metadata"][0], candidate.source.digest(paths["metadata"][0]))
    with pytest.raises(ValueError, match="matched three-arm inputs"):
        prospective.audit_triplet(paths)


def test_control_native_checkpoint_resume_and_partial_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = inputs(tmp_path)
    calls = []

    class FakePair:
        def close(self):
            calls.append("close")

    def fake_pair(*args, **kwargs):
        calls.append("start")
        return FakePair()

    def execute(*args, **kwargs):
        calls.append("execute")
        metadata = kwargs["output"] / "runtime/run_metadata.json"
        metadata.parent.mkdir(parents=True)
        metadata.write_text("{}")
        return SimpleNamespace(result=SimpleNamespace(status="completed"))

    monkeypatch.setattr(control, "build_pair", fake_pair)
    monkeypatch.setattr(control, "run_pair_task", execute)
    monkeypatch.setattr(control, "audit_join", lambda *args, **kwargs: {"valid": True})
    monkeypatch.setattr(control_release, "audit_join", lambda *args, **kwargs: {"valid": True})
    result = control.run(**values, arm="baseline")
    assert result["arm"] == "baseline"
    assert calls == ["start", "execute", "close"]
    before = control.inventory(values["output"])
    assert control.run(**values, arm="baseline", resume=True)["valid"] is True
    assert control.inventory(values["output"]) == before
    assert calls == ["start", "execute", "close"]
    with pytest.raises(ValueError, match="control run identity"):
        control.run(**values, arm="metadata", resume=True)
    metadata = values["output"] / "execution/runtime/run_metadata.json"
    metadata.write_text(metadata.read_text() + "\n")
    with pytest.raises(ValueError, match="control immutable raw"):
        control.run(**values, arm="baseline", resume=True)
    (values["output"] / "checkpoint.json").unlink()
    with pytest.raises(ValueError, match="partial control task"):
        control.run(**values, arm="baseline", resume=True)


def test_control_bad_pin_stops_before_native_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = inputs(tmp_path)
    values["expected_pin_sha256"] = "0" * 64
    monkeypatch.setattr(control, "build_pair", lambda *args, **kwargs: pytest.fail("pair started"))
    with pytest.raises(ValueError, match="frozen run identity"):
        control.run(**values, arm="metadata")
    assert not values["output"].exists()


def test_native_source_rejects_working_tree_and_missing_closure(tmp_path: Path) -> None:
    values = inputs(tmp_path)
    assert candidate.admit_source(
        values["project"], values["source_manifest"], values["expected_source_sha256"], COMMIT
    )["source_mode"] == "committed"
    manifest = json.loads(values["source_manifest"].read_text())
    manifest["source_mode"] = "working_tree"
    manifest["source_commit"] = None
    values["source_manifest"].write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="native requires committed"):
        candidate.admit_source(
            values["project"],
            values["source_manifest"],
            candidate.source.digest(values["source_manifest"]),
            COMMIT,
        )
    manifest["source_mode"] = "committed"
    manifest["source_commit"] = COMMIT
    manifest["source_sha256"].pop(next(iter(release.REQUIRED)))
    values["source_manifest"].write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        candidate.admit_source(
            values["project"],
            values["source_manifest"],
            candidate.source.digest(values["source_manifest"]),
            COMMIT,
        )


def test_bad_pin_stops_before_output_or_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = inputs(tmp_path)
    values["expected_pin_sha256"] = "0" * 64
    monkeypatch.setattr(
        candidate, "build_pair", lambda *args, **kwargs: pytest.fail("pair started")
    )
    with pytest.raises(ValueError, match="frozen run identity"):
        candidate.run(**values)
    assert not values["output"].exists()


def test_source_drift_and_authoring_stop_before_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = inputs(tmp_path)
    monkeypatch.setattr(
        candidate, "build_pair", lambda *args, **kwargs: pytest.fail("pair started")
    )
    target = values["project"] / next(iter(release.REQUIRED))
    target.write_text("source changed", encoding="utf-8")
    with pytest.raises(ValueError):
        candidate.run(**values)
    assert not values["output"].exists()

    second = inputs(tmp_path / "second")
    authoring = second["project"] / "src/react_agent/authoring/forbidden.py"
    authoring.parent.mkdir(parents=True)
    authoring.write_text("not worker code", encoding="utf-8")
    manifest = json.loads(second["source_manifest"].read_text())
    manifest["source_sha256"][authoring.relative_to(second["project"]).as_posix()] = (
        candidate.source.digest(authoring)
    )
    second["source_manifest"].write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="non-public"):
        candidate.admit_source(
            second["project"],
            second["source_manifest"],
            candidate.source.digest(second["source_manifest"]),
            COMMIT,
        )


def test_complete_resume_is_read_only_and_partial_run_is_not_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = inputs(tmp_path)
    calls = []

    class FakePair:
        def close(self):
            calls.append("close")

    def pair(*args, **kwargs):
        calls.append("start")
        return FakePair()

    def execute(*args, **kwargs):
        calls.append("execute")
        metadata = kwargs["output"] / "runtime/run_metadata.json"
        metadata.parent.mkdir(parents=True)
        metadata.write_text(json.dumps({"prospective_inventory": {"source_commit": COMMIT}}))
        return SimpleNamespace(result=SimpleNamespace(status="completed"))

    monkeypatch.setattr(candidate, "build_pair", pair)
    monkeypatch.setattr(candidate, "run_pair_task", execute)
    monkeypatch.setattr(candidate, "audit_join", lambda *args, **kwargs: {"valid": True})
    monkeypatch.setattr(release, "audit_join", lambda *args, **kwargs: {"valid": True})
    result = candidate.run(**values)
    assert result["valid"] is True
    assert calls == ["start", "execute", "close"]
    before = candidate.inventory(values["output"])
    assert candidate.run(**values, resume=True)["valid"] is True
    assert candidate.inventory(values["output"]) == before
    assert calls == ["start", "execute", "close"]
    changed = {
        **values,
        "task": SimpleNamespace(task_id="pilot_synthetic_001", instruction="changed"),
    }
    with pytest.raises(ValueError, match="room-ticket run identity"):
        candidate.run(**changed, resume=True)
    with pytest.raises(ValueError, match="room-ticket run identity"):
        candidate.run(**{**values, "run_manifest_sha256": "0" * 64}, resume=True)
    metadata = values["output"] / "execution/runtime/run_metadata.json"
    metadata.write_text("{}")
    with pytest.raises(ValueError):
        candidate.run(**values, resume=True)

    broken = inputs(tmp_path / "broken")

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic infrastructure failure")

    monkeypatch.setattr(candidate, "run_pair_task", fail)
    with pytest.raises(RuntimeError, match="infrastructure failure"):
        candidate.run(**broken)
    assert not (broken["output"] / "checkpoint.json").exists()
    with pytest.raises(ValueError):
        candidate.run(**broken, resume=True)


def test_failed_pair_join_retains_raw_without_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = inputs(tmp_path)

    class FakePair:
        def close(self):
            pass

    def execute(*args, **kwargs):
        return SimpleNamespace(result=SimpleNamespace(status="completed"))

    monkeypatch.setattr(candidate, "build_pair", lambda *args, **kwargs: FakePair())
    monkeypatch.setattr(candidate, "run_pair_task", execute)
    monkeypatch.setattr(candidate, "audit_join", lambda *args, **kwargs: {"valid": False})
    with pytest.raises(ValueError):
        candidate.run(**values)
    assert (values["output"] / "identity.json").is_file()
    assert not (values["output"] / "checkpoint.json").exists()
