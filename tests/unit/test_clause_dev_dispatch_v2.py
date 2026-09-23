"""Native route exercises the actual source-admission path without model weights."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from react_agent.llm.clause_dev_runner_v1 import native_pair
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1 import clause_pair_runtime_v1 as clause
from react_agent.security_v1 import constrained_runtime_v1 as constrained
from react_agent.security_v1.guard_bare_json_v1 import bind


def test_native_route_derives_one_constraint_root_from_admitted_pair(tmp_path):
    from react_agent.llm import clause_dev_dispatch_v1 as old
    from react_agent.llm import clause_dev_dispatch_v2 as current

    fixture = (
        Path(__file__).resolve().parents[2] / "tests/fixtures/ordinary_pair_guard_snapshot.json"
    )
    snapshot = GuardSnapshot.model_validate_json(fixture.read_text())
    pair = native_pair(
        tmp_path / "agent",
        tmp_path / "inventory",
        tmp_path / "guard",
        snapshot,
        tmp_path / "native",
        tmp_path / "attention",
        tmp_path / "policy",
    )
    try:
        seen = []

        def capture(task, *, pair, constrained, **kwargs):
            seen.append((constrained, kwargs["output"], pair.state))
            return "no model started"

        constrained_shim = SimpleNamespace(
            _run=capture,
            run_pair_task=constrained.run_pair_task,
            run_synthetic_pair_task=constrained.run_synthetic_pair_task,
        )
        clause_run = bind(clause._run, constrained=constrained_shim)
        public = bind(clause.run_pair_task, _run=clause_run)
        repaired = bind(current.native_runtime, run_pair_task=public)
        previous = bind(old.native_runtime, run_pair_task=public)

        with pytest.raises(TypeError, match="multiple values.*constrained"):
            previous(object(), pair=pair, output=tmp_path / "execution")
        assert not seen
        assert repaired(object(), pair=pair, output=tmp_path / "execution") == "no model started"
        assert seen == [(tmp_path / "constraints", tmp_path / "execution", "NEW")]
        assert not (tmp_path / "execution").exists()
        assert not (tmp_path / "constraints").exists()
    finally:
        pair.close()


def test_explicit_constraint_override_rejected_before_runtime(tmp_path):
    from react_agent.llm.clause_dev_dispatch_v2 import native_runtime

    with pytest.raises(ValueError, match="owned by the admitted factory"):
        native_runtime(object(), constrained=tmp_path / "other")
    assert not list(tmp_path.iterdir())
