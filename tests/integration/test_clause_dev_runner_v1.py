"""Paired Dev32 CPU coverage, immutable resume and tamper checks; no Test or HF."""

import json
from pathlib import Path

import pytest

from react_agent.llm.clause_dev_identity_v1 import identity
from react_agent.llm.clause_dev_runner_v1 import run
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation.clause_dev_checkpoint_v1 import audit_checkpoint

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "data/adversarial/release_v2"
ENV = ROOT / "data/clean/v1_1/environment"
COMMIT = "1" * 40


@pytest.fixture(scope="module")
def source(tmp_path_factory):
    output = tmp_path_factory.mktemp("dev32")
    results = []
    for shard in range(8):
        results.append(run(output / str(shard), RELEASE, ENV, commit=COMMIT, shard=shard))
    return output, results


def test_all32_and_complete_resume_without_rewriting(source):
    output, results = source
    assert sum(r["completed"] for r in results) == 32
    before = inventory(output)
    for shard, result in enumerate(results):
        assert result["expected"] == 4 and result["remaining"] == 0
        assert (
            run(output / str(shard), RELEASE, ENV, commit=COMMIT, shard=shard, resume=True)
            == result
        )
    assert inventory(output) == before


def test_partial_prefix_then_missing_only(tmp_path):
    root = tmp_path / "prefix"
    value = run(root, RELEASE, ENV, commit=COMMIT, shard=0, max_new_tasks=1)
    assert value["completed"] == 1 and value["remaining"] == 3
    before = inventory(root)
    assert run(root, RELEASE, ENV, commit=COMMIT, shard=0, resume=True)["completed"] == 4
    after = inventory(root)
    assert all(after[k] == v for k, v in before.items())


@pytest.mark.parametrize("fault", ["source", "guard_prompt", "tasks", "runtime", "config"])
def test_manifest_change_cannot_resume(source, tmp_path, fault):
    import shutil

    output, _ = source
    root = tmp_path / "modified"
    shutil.copytree(output / "0", root)
    path = root / "identity.json"
    saved = json.loads(path.read_text())
    manifest = saved["run"]
    if fault == "source":
        manifest["execution_source_sha256"] = {}
    elif fault == "tasks":
        manifest["tasks"] = manifest["tasks"][:-1]
    elif fault == "runtime":
        manifest["runtime_version"] = "security_runtime_v10"
    elif fault == "config":
        manifest["runtime"]["max_steps"] += 1
    else:
        manifest["guard_prompt"]["sha256"] = "0" * 64
    path.write_text(json.dumps(saved))
    before = inventory(root)
    with pytest.raises(ValueError):
        run(root, RELEASE, ENV, commit=COMMIT, shard=0, resume=True)
    assert inventory(root) == before


@pytest.mark.parametrize("fault", ["missing_checkpoint", "raw", "extra_task"])
def test_partial_or_corrupt_attempt_never_automatically_rerun(source, tmp_path, fault):
    import shutil

    output, _ = source
    root = tmp_path / "bad"
    shutil.copytree(output / "0", root)
    task = next((root / "tasks").iterdir())
    if fault == "missing_checkpoint":
        (task / "checkpoint.json").unlink()
    elif fault == "raw":
        (task / "task_timing.json").write_text("{}")
    else:
        (root / "tasks/extra").mkdir()
    before = inventory(root)
    with pytest.raises(ValueError):
        run(root, RELEASE, ENV, commit=COMMIT, shard=0, resume=True)
    assert inventory(root) == before


def test_checkpoint_uses_recorded_interpreter(source, monkeypatch):
    from react_agent.validation import exit_pair_audit_v1

    output, _ = source
    value = json.loads((output / "0/identity.json").read_text())["run"]
    monkeypatch.setattr(exit_pair_audit_v1, "runtime_identity", lambda: {"bad": "host"})
    task = value["tasks"][0]
    assert audit_checkpoint(output / "0/tasks" / task["key"], value, task)["recovered"]


def test_native_gate_and_linked_output(tmp_path):
    with pytest.raises(ValueError, match="native release gate"):
        run(tmp_path / "native", RELEASE, ENV, commit=COMMIT, shard=0, backend="hf")
    assert not (tmp_path / "native").exists()
    (tmp_path / "linked").symlink_to(tmp_path / "absent")
    with pytest.raises(ValueError):
        run(tmp_path / "linked", RELEASE, ENV, commit=COMMIT, shard=0)


def test_predeclared_family_pairs_levels_and_settings():
    from react_agent.llm.grouped_dev_identity_v2 import identity as old_identity

    new, rows = identity(RELEASE, ENV, COMMIT, "stub")
    old, old_rows = old_identity(RELEASE, ENV, COMMIT, "stub")
    assert rows == old_rows and len(rows) == 16
    assert new["tasks"] == [t for t in old["tasks"] if t["level"] in {"A2", "A6"}]
    assert len(new["tasks"]) == len({t["key"] for t in new["tasks"]}) == 32
    assert new["generation"] == old["generation"] and new["runtime"] == old["runtime"]
    assert new["dev_sha256"] == old["dev_sha256"]
    assert not new["native_dispatch_allowed"] and not new["quality_scoring"]


def test_failure_terminal_is_preserved(tmp_path):
    from react_agent.llm import clause_dev_runner_v1 as runner
    from react_agent.llm.constrained_probe_stub_v1 import SyntheticConstraintFactory

    def failed_factory(output, condition):
        return SyntheticConstraintFactory(output, "backend_failure")

    failing_pair = bind(runner.synthetic_pair, SyntheticConstraintFactory=failed_factory)
    invoke = bind(runner.run, synthetic_pair=failing_pair)
    root = tmp_path / "failure"
    result = invoke(root, RELEASE, ENV, commit=COMMIT, shard=0)
    assert result["terminal_statuses"] == ["model_error"] * 4
    before = inventory(root)
    assert invoke(root, RELEASE, ENV, commit=COMMIT, shard=0, resume=True) == result
    assert inventory(root) == before
