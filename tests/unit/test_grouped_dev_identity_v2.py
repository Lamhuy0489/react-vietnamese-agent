from pathlib import Path

import pytest

from react_agent.llm.grouped_dev_identity_v2 import identity
from react_agent.llm.grouped_dev_runner_v2 import run

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "data/adversarial/release_v2"
ENV = ROOT / "data/clean/v1_1/environment"
COMMIT = "a" * 40


def test_geometry_pair_order_distinct_keys_and_shared_task_id():
    manifest, rows = identity(RELEASE, ENV, COMMIT, "stub")
    tasks = manifest["tasks"]
    assert len(tasks) == len({t["key"] for t in tasks}) == 112
    assert len(rows) == 16
    for shard in range(8):
        group = [t for t in tasks if t["shard"] == shard]
        assert len(group) == 14
        for attack, benign in zip(group[::2], group[1::2], strict=True):
            assert attack["task_id"] == benign["task_id"]
            assert attack["key"] != benign["key"]
            assert attack["level"] == benign["level"]
            assert (attack["branch"], benign["branch"]) == ("attack", "benign")
            assert attack["fixture_sha256"] != benign["fixture_sha256"]
    assert manifest == identity(RELEASE, ENV, COMMIT, "stub")[0]
    assert manifest["native_dispatch_allowed"] is False


def test_native_pins_backend_and_schedule(tmp_path):
    from react_agent.llm.guard_snapshot_v1 import GuardSnapshot

    pin = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    native, _ = identity(
        RELEASE, ENV, COMMIT, "hf", ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json", pin
    )
    stub, _ = identity(RELEASE, ENV, COMMIT, "stub")
    assert native["tasks"] == stub["tasks"]
    assert native["generation"] == stub["generation"]
    assert native["native_pins"]["guard_snapshot_sha256"] == pin.sha256
    assert native["pair_config"] != stub["pair_config"]
    assert native["scripted_profile"] is None
    assert native["recovery"]["stable_tail"] == 3
    for mode, inventory, snapshot in [
        ("hf", None, None),
        ("stub", None, pin),
        ("bogus", None, None),
    ]:
        with pytest.raises(ValueError):
            identity(RELEASE, ENV, COMMIT, mode, inventory, snapshot)


@pytest.mark.parametrize(
    "options",
    [
        {"shard": True},
        {"shard": 8},
        {"shard": -1},
        {"shard": 0, "resume": 1},
        {"shard": 0, "max_new_tasks": True},
        {"shard": 0, "max_new_tasks": -1},
        {"shard": 0, "commit": "wrong"},
    ],
)
def test_bad_options_create_no_output(tmp_path, options):
    with pytest.raises(ValueError):
        run(tmp_path / "run", RELEASE, ENV, **{"commit": COMMIT, **options})
    assert not (tmp_path / "run").exists()


def test_frozen_input_overlap_and_symlink_rejected(tmp_path):
    with pytest.raises(ValueError):
        run(RELEASE / "must_not_create", RELEASE, ENV, commit=COMMIT, shard=0)
    link = tmp_path / "link"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        run(link / "run", RELEASE, ENV, commit=COMMIT, shard=0)
