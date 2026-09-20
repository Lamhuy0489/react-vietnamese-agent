"""Real spawned CPU controls; no native weights, Test or network."""

import copy
import multiprocessing as mp
import threading
from multiprocessing import util

import pytest

from react_agent.llm.base import GenerationConfig
from react_agent.llm.exit_milestone_probe_v1 import BOUNDARY, audit_case, config, run_case
from react_agent.llm.teardown_probe_v1 import MODES
from react_agent.security_v1.exit_milestones_v1 import MilestoneBackend, runtime_identity


@pytest.mark.parametrize("mode", MODES)
def test_observed_synthetic_shutdown(mode):
    old_finalizer, old_threads = util._exit_function, threading._shutdown
    record = run_case(mode)
    assert audit_case(record, mode, runtime_identity()) == BOUNDARY[mode]
    assert record["lifecycle"][0]["pid"] not in {p.pid for p in mp.active_children()}
    assert util._exit_function is old_finalizer
    assert threading._shutdown is old_threads


class FailedFactory:
    def __call__(self):
        raise RuntimeError("not-to-be-recorded")


def test_backend_failure_keeps_partial_milestones_without_retry():
    backend = MilestoneBackend(FailedFactory(), config())
    with pytest.raises(RuntimeError):
        backend.generate([], GenerationConfig())
    backend.close()
    snapshot = backend.exit_milestones()
    assert snapshot["events"]["target_enter"] is not None
    assert len(backend.attempts) == 1
    assert backend.attempts[0]["status"] == "BACKEND_FAILURE"
    assert "not-to-be-recorded" not in repr(snapshot)
    assert backend._process is None


@pytest.fixture(scope="module")
def fast_record():
    return run_case("fast")


@pytest.mark.parametrize(
    "mutation",
    ["extra", "stop", "config", "response", "sequence", "generation", "timing", "grace", "serve"],
)
def test_control_binding_rejects_tampering(fast_record, mutation):
    value = copy.deepcopy(fast_record)
    if mutation == "extra":
        value["arbitrary_payload"] = "not-allowed"
    elif mutation == "stop":
        value["stop_received_at"] += 1.0
    elif mutation == "config":
        value["attempts"][0]["execution_config_sha256"] = "other"
    elif mutation == "response":
        value["responses"][0]["text"] = "changed"
    elif mutation == "sequence":
        value["attempts"][1]["sequence"] = 1
    elif mutation == "generation":
        value["attempts"][0]["generation_sha256"] = "other"
    elif mutation == "timing":
        value["attempts"][0]["load_seconds"] = float("nan")
    elif mutation == "grace":
        value["lifecycle"][0]["graceful_shutdown_seconds"] = 20.0
    elif mutation == "serve":
        value["serve_returned_at"] -= 0.1
    with pytest.raises((ValueError, KeyError)):
        audit_case(value, "fast", runtime_identity())
