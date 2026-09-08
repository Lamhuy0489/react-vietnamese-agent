"""Spawned-process probe QA with synthetic transport, not real HF or CUDA."""

import json
from pathlib import Path

import pytest

from react_agent.llm.guard_probe_v1 import StubProbeTrials, messages, run_probe
from react_agent.security_v1.warm_guard import WarmGuardConfig


@pytest.mark.parametrize(
    "failure,valid,attempts,structured",
    [
        ("", True, 4, 4),
        ("history", False, 4, 4),
        ("invalid", False, 2, 0),
        ("backend", False, 2, 0),
    ],
)
def test_probe_matrix(
    tmp_path: Path,
    failure: str,
    valid: bool,
    attempts: int,
    structured: int,
) -> None:
    output = tmp_path / "probe"
    summary = run_probe(
        output,
        StubProbeTrials(failure),
        WarmGuardConfig(
            "synthetic-probe-stub",
            "v1",
            timeout_seconds=15,
        ),
        {"backend": "stub", "source_commit": "synthetic"},
    )
    assert summary["valid"] is valid
    assert summary["attempted_calls"] == attempts
    assert summary["structured_valid_calls"] == structured
    assert summary["phase5_accepted"] is False
    assert len(summary["rows"]) == 4
    for trial in ("warm", "fresh"):
        trace = json.loads((output / trial / "trial.json").read_text())
        assert trace["closed"]
        assert len({row["pid"] for row in trace["attempts"]}) == 1
        assert trace["lifecycle"][-1]["reaped"]
    warm = json.loads((output / "warm/trial.json").read_text())
    if valid:
        assert [a["cold_start"] for a in warm["attempts"]] == [True, False, False]
        assert summary["same_A_response_sha256"]
    if failure in {"invalid", "backend"}:
        assert [r["status"] for r in warm["records"]][1:] == [
            "SKIPPED_AFTER_FAILURE",
            "SKIPPED_AFTER_FAILURE",
        ]
    if failure == "history":
        assert not summary["same_A_response_sha256"]
    manifest = json.loads((output / "probe_manifest.json").read_text())
    assert manifest["classification_cache"] == "bypassed"
    assert manifest["automatic_retry"] is False
    assert manifest["test_payloads_parsed"] == 0
    with pytest.raises(FileExistsError):
        run_probe(output, StubProbeTrials(), WarmGuardConfig("synthetic-probe-stub", "v1"), {})


def test_messages_are_fresh_and_different() -> None:
    first = messages("A")
    second = messages("A")
    first[0]["content"] = "changed by synthetic test"
    assert first != second and second == messages("A")
    assert messages("A") != messages("B")
    with pytest.raises(KeyError):
        messages("unknown")
