"""Synthetic boundary joins; helper authentication is separately covered, no native loads."""

import json
from pathlib import Path

import pytest

from react_agent.llm.grouped_dev_identity_v2 import identity
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation import grouped_dev_native_audit_v2 as auditor

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    pin = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    manifest, _ = identity(
        ROOT / "data/adversarial/release_v2",
        ROOT / "data/clean/v1_1/environment",
        "a" * 40,
        "hf",
        ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json",
        pin,
    )
    task = manifest["tasks"][0]
    root, tokenizers, publishers = [tmp_path / n for n in ("task", "tokenizers", "publishers")]
    for directory in (root / "execution", root / "native", tokenizers, publishers):
        directory.mkdir(parents=True)
    files = [
        dict(name=n, size=1, sha256="b" * 64)
        for n in ("tokenizer_config.json", "generation_config.json")
    ]
    worker = dict(
        attempts=[dict(pid=123, load_seconds=2), dict(status="OK", generation_seconds=1)],
        lifecycle=[dict(method="GRACEFUL")],
    )
    receipt = dict(
        snapshot=dict(workers=dict(agent=worker)),
        startup_seconds=2,
        runtime_seconds_including_inner_cleanup=1,
        outer_cleanup_seconds=0.1,
        total_seconds=3.1,
    )
    records = [
        dict(
            load_seconds_including_hashes=1,
            **manifest["pair_config"]["agent"],
            runtime_admission=dict(files=files),
        ),
        dict(
            call_seconds=0.2,
            generate_seconds=0.1,
            input_tokens=5,
            output_tokens=2,
            memory_before=[],
            memory_after=[],
        ),
    ]
    (root / "execution/pair_runtime.json").write_text(json.dumps(receipt))
    (root / "baseline.json").write_text(
        json.dumps(dict(memory=[dict(total_bytes=16 * 1024**3)] * 2))
    )
    (root / "task_timing.json").write_text(json.dumps(dict(task_wall_seconds=4)))
    metrics = root / "native/agent_hf_metrics.jsonl"
    metrics.write_text("".join(json.dumps(r) + "\n" for r in records))
    monkeypatch.setattr(
        auditor, "audit_checkpoint", lambda *a: dict(terminal="completed", recovered=True)
    )
    monkeypatch.setattr(auditor, "load", lambda *a: None)
    monkeypatch.setattr(auditor, "audit_memory", lambda *a: None)
    monkeypatch.setattr(
        auditor,
        "authenticate",
        lambda *a: dict(identity=dict(size=1, sha256="b" * 64), eos_token_id=2, pad_token_id=0),
    )
    monkeypatch.setattr(
        auditor,
        "publisher_policy",
        lambda *a: dict(
            identity=dict(size=1, sha256="b" * 64),
            publisher_json=dict(eos_token_id=[2]),
            observed_publisher_expected={},
        ),
    )

    def policy(*args, **kwargs):
        assert kwargs["worker_pid"] == 123 and kwargs["expected_requests"] == 1
        return dict(valid=True)

    monkeypatch.setattr(auditor, "audit_policy", policy)
    return root, manifest, task, tokenizers, publishers, pin, receipt, records, metrics


def test_native_join_timing_and_readonly(fixture):
    root, manifest, task, tokenizers, publishers, pin, *_ = fixture
    before = auditor.inventory(root)
    result = auditor.audit_native_task(root, manifest, task, tokenizers, publishers, pin)
    assert result["roles"]["agent"]["calls"][0]["tokens_per_generate_second"] == 20
    assert result["startup_seconds"] == 2 and result["guard_diagnostics"] is None
    assert not result["quality_scoring"]
    assert before == auditor.inventory(root)


@pytest.mark.parametrize(
    "fault", ["backend", "snapshot", "revision", "duration", "extra", "partial"]
)
def test_native_join_negatives_or_partial_denominator(fixture, fault):
    root, manifest, task, tokenizers, publishers, pin, receipt, records, metrics = fixture
    if fault == "backend":
        manifest["backend"] = "stub"
    elif fault == "snapshot":
        manifest["native_pins"]["guard_snapshot_sha256"] = "0" * 64
    elif fault == "revision":
        records[0]["model_revision"] = "wrong"
    elif fault == "duration":
        records[1]["call_seconds"] = 100
    elif fault == "extra":
        (root / "native/unexpected.json").write_text("{}")
    else:
        receipt["snapshot"]["workers"]["agent"]["attempts"][1]["status"] = "ERROR"
        (root / "execution/pair_runtime.json").write_text(json.dumps(receipt))
    metrics.write_text("".join(json.dumps(r) + "\n" for r in records))
    if fault == "partial":
        result = auditor.audit_native_task(root, manifest, task, tokenizers, publishers, pin)
        role = result["roles"]["agent"]
        assert role["failed_or_partial"] and not role["policy_attention_verified"]
        assert role["worker_attempts"] == 1 and role["calls"] == []
    else:
        with pytest.raises(ValueError):
            auditor.audit_native_task(root, manifest, task, tokenizers, publishers, pin)
