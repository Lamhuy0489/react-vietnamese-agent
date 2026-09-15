"""Synthetic native evidence boundaries; never assert actual weights authentication."""

import hashlib
import json
from pathlib import Path

import pytest
from test_grouped_native_audit_v2 import fixture as prior_fixture  # noqa: F401

from react_agent.llm.guard_observer_probe_v2 import SCHEDULE, execution_sources, fixed_identity
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation import grouped_dev_native_audit_v2 as prior
from react_agent.validation import observer_native_audit_v2 as module

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def role_case(request, monkeypatch):
    value = request.getfixturevalue("prior_fixture")
    for name in ("load", "audit_memory", "authenticate", "publisher_policy", "audit_policy"):
        monkeypatch.setattr(module, name, getattr(prior, name))
    root, identity, _, tokenizers, publishers, pin, receipt, records, metrics = value
    worker = receipt["snapshot"]["workers"]["agent"]
    return (
        (root, "agent", worker, identity, tokenizers, publishers, pin, [16 * 1024**3] * 2),
        records,
        metrics,
    )


def test_role_timing_and_immutability(role_case):
    args, _, _ = role_case
    before = module.inventory(args[0])
    result = module.role_evidence(*args)
    assert result["policy_attention_verified"]
    assert result["calls"][0]["tokens_per_generate_second"] == 20
    assert module.inventory(args[0]) == before


@pytest.mark.parametrize(
    "fault",
    ["revision", "time", "load_time", "zero_time", "extra_call", "metadata", "partial", "no_calls"],
)
def test_role_failures_and_denominators(role_case, fault):
    args, records, metrics = role_case
    if fault == "revision":
        records[0]["model_revision"] = "changed"
    elif fault == "time":
        records[1]["call_seconds"] = 999
    elif fault == "load_time":
        records[0]["load_seconds_including_hashes"] = 999
    elif fault == "zero_time":
        records[1]["generate_seconds"] = 0
    elif fault == "extra_call":
        records.append(records[1])
    elif fault == "metadata":
        records[0]["runtime_admission"]["files"][0]["sha256"] = "0" * 64
    elif fault == "partial":
        args[2]["attempts"][1]["status"] = "ERROR"
    else:
        args[2]["attempts"].pop()
        records.pop()
    metrics.write_text("".join(json.dumps(r) + "\n" for r in records))
    if fault in {"partial", "no_calls"}:
        result = module.role_evidence(*args)
        assert not result["policy_attention_verified"] and result["calls"] == []
        assert result["failed_or_partial"] == (fault == "partial")
    else:
        with pytest.raises(ValueError):
            module.role_evidence(*args)


@pytest.fixture
def full_case(tmp_path, monkeypatch):
    probe, tokenizers, publishers, env = [
        tmp_path / n for n in ("probe", "tokenizers", "publishers", "environment")
    ]
    for path in (probe, tokenizers, publishers, env):
        path.mkdir()
    pin = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    inv = tmp_path / "inventory.json"
    inv.write_text("{}")
    identity = fixed_identity("hf", "valid")
    identity.update(
        source_commit="a" * 40,
        snapshot_sha256=pin.sha256,
        execution_source_sha256=execution_sources(),
        environment_sha256={},
        model_inventory_sha256=hashlib.sha256(inv.read_bytes()).hexdigest(),
    )
    (probe / "identity.json").write_text(json.dumps(identity))
    for key in SCHEDULE:
        root = probe / "tasks" / key
        (root / "execution/runtime").mkdir(parents=True)
        (root / "native").mkdir()
        for role in ("agent", "guard"):
            (root / "native" / f"{role}_hf_metrics.jsonl").write_text("{}\n")
        (root / "baseline.json").write_text(
            json.dumps(dict(memory=[dict(total_bytes=16 * 1024**3)] * 2))
        )
        (root / "execution/pair_runtime.json").write_text(
            json.dumps(
                dict(
                    snapshot=dict(
                        workers={
                            r: dict(lifecycle=[dict(method="GRACEFUL")]) for r in ("agent", "guard")
                        }
                    ),
                    startup_seconds=2,
                    total_seconds=3,
                )
            )
        )
        (root / "execution/runtime/trace_legacy.jsonl").write_text("")
    monkeypatch.setattr(
        module, "checkpoint", lambda root: dict(terminal="model_error", recovered=True)
    )
    monkeypatch.setattr(module, "role_evidence", lambda *args: dict(load_verified=True, calls=[]))

    def join(execution, sidecar, witness):
        assert witness == execution.parent / "witness.jsonl"
        return dict(response_records=0, joined=[])

    monkeypatch.setattr(module, "audit_guard", join)
    return probe, tokenizers, publishers, pin, "a" * 40, inv, env


def test_full_join_keeps_terminal_errors_and_zero_coverage(full_case):
    before = module.inventory(full_case[0])
    result = module.audit(*full_case)
    assert result["complete"] and len(result["tasks"]) == 4
    assert all(
        t["terminal"] == "model_error" and t["executed_tool_calls"] == 0 for t in result["tasks"]
    )
    assert not result["guard_quality_validated"] and not result["source_authenticated"]
    assert module.inventory(full_case[0]) == before


@pytest.mark.parametrize(
    "fault",
    [
        "backend",
        "commit",
        "snapshot",
        "sources",
        "environment",
        "inventory",
        "extra_task",
        "missing_task",
        "extra_metrics",
    ],
)
def test_full_input_mutations_rejected(full_case, fault):
    probe, _, _, _, _, inv, env = full_case
    path = probe / "identity.json"
    identity = json.loads(path.read_text())
    if fault in {"backend", "commit", "snapshot", "sources"}:
        field = dict(
            backend="backend",
            commit="source_commit",
            snapshot="snapshot_sha256",
            sources="execution_source_sha256",
        )[fault]
        identity[field] = "bad"
        path.write_text(json.dumps(identity))
    elif fault == "environment":
        (env / "changed").write_text("changed")
    elif fault == "inventory":
        inv.write_text("changed")
    elif fault == "extra_task":
        (probe / "tasks/extra").mkdir()
    elif fault == "missing_task":
        (probe / "tasks" / SCHEDULE[-1]).rename(probe / "retained_missing")
    else:
        (probe / "tasks" / SCHEDULE[0] / "native/extra").write_text("{}")
    with pytest.raises(ValueError):
        module.audit(*full_case)
