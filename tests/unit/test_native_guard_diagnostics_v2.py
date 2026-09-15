"""Native observer stays lazy, picklable and outside exact attention/policy loaders."""

import pickle

import pytest
from test_native_guard_diagnostics_v1 import pin

from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.native_guard_diagnostics_v1 import native_pair as old_pair
from react_agent.llm.native_guard_diagnostics_v2 import native_pair


def test_lazy_topology_and_host_sink(tmp_path):
    args = (
        [tmp_path / n for n in ("agent", "inventory", "guard")]
        + [pin()]
        + [tmp_path / n for n in ("native", "attention", "policy")]
    )
    old = old_pair(*args)
    new = native_pair(*args, witness=tmp_path / "witness.jsonl")
    try:
        assert isinstance(new, DiagnosticPair)
        assert old.config == new.config
        assert old._workers["agent"].factory == new._workers["agent"].factory
        observer = new._workers["guard"].factory.factory
        assert isinstance(observer, DiagnosticFactory)
        assert observer.backend_factory == old._workers["guard"].factory.factory.backend_factory
        assert pickle.loads(pickle.dumps(observer)) == observer  # noqa: S301
        assert not list(tmp_path.iterdir())
        assert all(not w.attempts for w in new._workers.values())
    finally:
        old.close()
        new.close()


@pytest.mark.parametrize(
    "fault", ["existing", "parent", "link", "model", "native", "overlap", "snapshot"]
)
def test_invalid_witness_and_roots_rejected(tmp_path, fault):
    agent, inventory, guard, output, attention, policy = [
        tmp_path / n for n in ("agent", "inventory", "guard", "native", "attention", "policy")
    ]
    witness = tmp_path / "witness"
    snapshot = pin()
    if fault == "existing":
        witness.write_text("preserve")
    elif fault == "parent":
        witness = output / "witness"
    elif fault == "link":
        witness.symlink_to(tmp_path / "target")
    elif fault == "model":
        witness = guard
    elif fault == "native":
        witness = output
    elif fault == "overlap":
        attention = output
    else:
        snapshot = None
    with pytest.raises(ValueError):
        native_pair(agent, inventory, guard, snapshot, output, attention, policy, witness=witness)
