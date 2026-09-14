"""Native factory placement: observer must remain outside exact HF/policy wrappers."""

import pickle
from pathlib import Path

import pytest

from react_agent.llm.guard_diagnostic_backend_v1 import DiagnosticFactory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.native_guard_diagnostics_v1 import native_pair
from react_agent.llm.native_shutdown_v2 import native_pair as legacy_pair

ROOT = Path(__file__).resolve().parents[2]


def pin():
    return GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )


def test_topology_parity_pickle_and_lazy_construction(tmp_path):
    args = (
        [tmp_path / n for n in ("agent", "inventory", "guard")]
        + [pin()]
        + [tmp_path / n for n in ("native", "attention", "policy")]
    )
    old, new = legacy_pair(*args), native_pair(*args)
    try:
        assert old.config == new.config
        assert old._workers["agent"].factory == new._workers["agent"].factory
        observer = new._workers["guard"].factory.factory
        assert isinstance(observer, DiagnosticFactory)
        assert observer.backend_factory == old._workers["guard"].factory.factory
        assert (
            pickle.loads(pickle.dumps(new._workers["guard"].factory))  # noqa: S301
            == new._workers["guard"].factory
        )
        assert not list(tmp_path.iterdir())
        assert all(not w.attempts for w in new._workers.values())
    finally:
        old.close()
        new.close()


@pytest.mark.parametrize("fault", ["overlap", "existing", "symlink", "pin", "input"])
def test_refuses_bad_paths_before_load(tmp_path, fault):
    agent, inventory, guard, output, attention, policy = [
        tmp_path / n for n in ("agent", "inventory", "guard", "native", "attention", "policy")
    ]
    snapshot = pin()
    if fault == "overlap":
        policy = attention
    elif fault == "existing":
        output.mkdir()
    elif fault == "symlink":
        agent.symlink_to(tmp_path)
    elif fault == "pin":
        snapshot = None
    elif fault == "input":
        output = guard / "nested"
    with pytest.raises(ValueError):
        native_pair(agent, inventory, guard, snapshot, output, attention, policy)
