"""Real stub writer plus explicitly synthetic HF-shaped fixtures; no native libraries."""

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from test_request_policy_v1 import run as policy_run
from test_request_policy_v1 import setup as policy_setup

from react_agent.llm.generation_policy_v1 import config_snapshot
from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v1 import ModelIdentity, PairConfig
from react_agent.llm.ordinary_pair_probe_v1 import native_config
from react_agent.validation import ordinary_native_audit_v1 as joined
from react_agent.validation import ordinary_pair_audit_v1 as impl
from react_agent.validation.context_policy_audit_v1 import publisher_policy

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "a" * 40


def write(path: Path, row: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row))


@pytest.fixture(scope="module")
def template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("ordinary_audit") / "raw"
    subprocess.run(  # noqa: S603 - fixed repository runner and self-created temporary output
        [sys.executable, str(ROOT / "scripts/run_phase5_ordinary_pair.py"), "--output", str(root)],
        cwd=ROOT,
        env=dict(os.environ, PAIR_SOURCE_COMMIT=COMMIT, PYTHONPATH=str(ROOT / "src")),
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return root


@pytest.fixture
def sample(template: Path, tmp_path: Path) -> Path:
    return Path(shutil.copytree(template, tmp_path / "probe"))


def audit(root: Path) -> dict[str, Any]:
    return impl.audit(root, commit=COMMIT, backend="stub")


def test_real_writer_repeatable_readonly(sample: Path) -> None:
    before = impl.inventory(sample)
    result = audit(sample)
    assert result == audit(sample) and impl.inventory(sample) == before
    assert len(result["calls"]) == 6 and result["worker_handles_reaped"] == 2
    assert result["native_model_calls"] == 0 and not result["native_validated"]
    assert not result["source_authenticated"] and not result["phase5_accepted"]


@pytest.mark.parametrize(
    "case",
    [
        "commit",
        "backend",
        "config",
        "inputs",
        "generation",
        "plan",
        "duplicate_attempt",
        "request_hash",
        "pid",
        "owner",
        "bool_pid",
        "attempt_time",
        "deadline",
        "load_twice",
        "cleanup",
        "pending",
        "closed_events",
        "ready_prefix",
        "submitted_prefix",
        "returned_prefix",
        "returned_role",
        "host_time",
        "response_sha",
        "missing",
        "extra",
        "empty_directory",
        "duplicate_json",
        "infinite",
        "symlink",
        "totals",
        "resident",
        "recovery",
        "recovery_order",
        "summary_count",
        "summary_repeat",
        "stub_load",
    ],
)
def test_mutation_rejected(sample: Path, case: str) -> None:
    file = "closed.json"
    row = impl.read(sample / file)
    worker = row["workers"]["agent"]
    if case in ("commit", "backend", "config", "generation", "plan"):
        file = "manifest.json"
        row = impl.read(sample / file)
        if case in ("commit", "backend"):
            row["identity"]["source_commit" if case == "commit" else "backend"] = (
                "b" * 40 if case == "commit" else "hf"
            )
        elif case == "config":
            row["pair_config"]["agent_call_seconds"] = 181
        elif case == "generation":
            row["generation"]["agent"]["seed"] = 43
        else:
            row["order"].reverse()
    elif case == "inputs":
        file = "inputs.json"
        row = {}
    elif case == "duplicate_attempt":
        worker["attempts"].append(worker["attempts"][-1])
    elif case == "request_hash":
        worker["attempts"][2]["request_sha256"] = "0" * 64
    elif case in ("pid", "bool_pid"):
        worker["attempts"][1]["pid"] = (
            True if case == "bool_pid" else row["workers"]["guard"]["attempts"][0]["pid"]
        )
    elif case == "owner":
        row["owner_pid"] = worker["attempts"][0]["pid"]
    elif case == "attempt_time":
        worker["attempts"][1]["generation_seconds"] = 999
    elif case == "deadline":
        worker["attempts"][1]["elapsed_seconds"] = 181
    elif case == "load_twice":
        worker["attempts"][1]["load_seconds"] = 0.1
    elif case == "cleanup":
        worker["lifecycle"][0]["exitcode"] = True
    elif case == "pending":
        worker["handle_pending"] = True
    elif case == "closed_events":
        row["events"].pop()
    elif case == "ready_prefix":
        file = "ready.json"
        row = impl.read(sample / file)
        row["pair"]["workers"]["agent"]["attempts"].append(worker["attempts"][1])
    elif case in (
        "submitted_prefix",
        "returned_prefix",
        "returned_role",
        "host_time",
        "response_sha",
    ):
        file = "call_03_submitted.json" if case == "submitted_prefix" else "call_03_returned.json"
        row = impl.read(sample / file)
        if case.endswith("prefix"):
            row["pair"]["events"].pop()
        elif case == "returned_role":
            row["role"] = "guard"
        elif case == "host_time":
            row["call_seconds"] = 1e-9
        else:
            row["response_sha256"] = "x" * 64
    elif case in ("missing", "extra", "empty_directory", "duplicate_json", "infinite", "symlink"):
        target = sample / "call_03_returned.json"
        if case == "missing":
            target.unlink()
        elif case == "extra":
            write(sample / "error.json", {})
        elif case == "empty_directory":
            (sample / "empty").mkdir()
        elif case == "duplicate_json":
            target.write_text('{"index": 1,"index": 3}')
        elif case == "infinite":
            target.write_text('{"index": 1e999}')
        else:
            moved = sample.parent / "moved"
            target.rename(moved)
            target.symlink_to(moved)
        with pytest.raises((ValueError, KeyError)):
            audit(sample)
        return
    elif case in ("totals", "resident"):
        file = "call_03_memory.json"
        row = impl.read(sample / file)
        row["memory"][0]["total_bytes" if case == "totals" else "free_bytes"] += 10 * 1024**3
    elif case in ("recovery", "recovery_order"):
        file = "recovery_5.json"
        row = impl.read(sample / file)
        if case == "recovery":
            row["memory"][1]["free_bytes"] -= 1024**3
        else:
            row["elapsed_seconds"] = 1e-9
    elif case in ("summary_count", "summary_repeat"):
        file = "summary.json"
        row = impl.read(sample / file)
        if case == "summary_count":
            row["calls_submitted"] = True
        else:
            row["repeated_a_equal"]["agent"] = False
    elif case == "stub_load":
        file = "agent_synthetic_load.json"
        row = impl.read(sample / file)
        row["actual_model_load"] = True
    write(sample / file, row)
    with pytest.raises((ValueError, KeyError)):
        audit(sample)


def test_a_mismatch_is_reported_not_filtered(sample: Path) -> None:
    row = impl.read(sample / "call_05_returned.json")
    row["response_sha256"] = "0" * 64
    write(sample / "call_05_returned.json", row)
    summary = impl.read(sample / "summary.json")
    summary["repeated_a_equal"]["agent"] = False
    write(sample / "summary.json", summary)
    result = audit(sample)
    assert result["valid"] and result["repeated_a_equal"]["agent"] is False


@pytest.mark.parametrize("method,exitcode", [("TERMINATE", -15), ("KILL", -9)])
def test_forced_reap_is_reported(sample: Path, method: str, exitcode: int) -> None:
    closed = impl.read(sample / "closed.json")
    for worker in closed["workers"].values():
        worker["lifecycle"][0].update(method=method, exitcode=exitcode)
    write(sample / "closed.json", closed)
    assert audit(sample)["graceful_workers"] == 0


@pytest.fixture
def native(sample: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Explicit synthetic HF records, never treat rewritten CPU artifacts as native evidence."""
    config = native_config()
    pin = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    oldconfig = PairConfig(
        ModelIdentity("synthetic-agent", "v1"), ModelIdentity("synthetic-guard", "v1")
    )
    replacements = {oldconfig.sha256: config.sha256}
    for role in impl.ROLES:
        for cold in (True, False):
            replacements[oldconfig.execution(role, cold=cold).identity] = config.execution(
                role, cold=cold
            ).identity

    def adjust(value: Any) -> Any:
        if isinstance(value, list):
            return [adjust(v) for v in value]
        if isinstance(value, dict):
            row = {k: adjust(v) for k, v in value.items()}
            if "cold_start" in row:
                row.update(
                    load_seconds=10.0 if row["cold_start"] else 0.0,
                    generation_seconds=1.0,
                    elapsed_seconds=12.0 if row["cold_start"] else 2.0,
                )
            if "call_seconds" in row:
                row["call_seconds"] = 3.0
            return row
        return replacements.get(value, value) if isinstance(value, str) else value

    for path in sample.glob("*.json"):
        write(path, adjust(impl.read(path)))
    manifest = impl.read(sample / "manifest.json")
    from dataclasses import asdict

    manifest.update(pair_config=asdict(config), sample_interval_seconds=1.0)
    manifest["identity"].update(
        backend="hf",
        snapshot_sha256=pin.sha256,
        environment=dict(torch="2.10.0+cu128", cuda="12.8", transformers="5.5.0"),
        progress_policy="worker_thread_progress_v1",
    )
    write(sample / "manifest.json", manifest)
    summary = impl.read(sample / "summary.json")
    summary.update(independent_audit_pending=True, actual_model_generation_calls=None)
    write(sample / "summary.json", summary)
    policy, attention, publishers = (
        tmp_path / name for name in ("policy", "attention", "publishers")
    )
    shutil.copytree(ROOT / "docs/evaluation/publisher_policy_v1", publishers)
    plan = joined.PlacementPlan()
    scan = impl.read(ROOT / "experiments/manifests/phase5_agent_mount_v1_scan01.json")
    closed = impl.read(sample / "closed.json")
    totals = [16 * 1024**3] * 2
    for role in impl.ROLES:
        (sample / f"{role}_synthetic_load.json").unlink()
        own = tmp_path / (role + "_fake")
        own.mkdir()
        value = policy_setup(own, monkeypatch, role)
        publisher = publisher_policy(publishers / f"{role}_generation_config.json", role)[
            "observed_publisher_expected"
        ]
        for key, val in publisher.items():
            if key != "transformers_version":
                setattr(value.model.generation_config, key, val)
        value.wrapped._publisher = config_snapshot(value.model.generation_config)
        for inputs, outputs in ((1, 1), (512, 3), (1, 1)):
            policy_run(value, inputs, outputs)
        for kind, destination in (("policy", policy), ("attention", attention)):
            shutil.copytree(own / kind, destination / role)
            for path in (destination / role).rglob("*.json"):
                row = impl.read(path)
                row["pid"] = closed["workers"][role]["attempts"][0]["pid"]
                write(path, row)
        rows = [json.loads(line) for line in value.metrics.read_text().splitlines()]
        mem = [
            dict(
                device=device,
                global_free_bytes=4 * 1024**3,
                global_total_bytes=totals[device],
                allocated_bytes=2 * 1024**3,
                reserved_bytes=2 * 1024**3,
                peak_allocated_bytes=2 * 1024**3,
                peak_reserved_bytes=2 * 1024**3,
            )
            for device in (0, 1)
        ]
        if role == "agent":
            rows[0].update(
                placement_sha256=plan.sha256,
                device_map=plan.device_map(),
                agent_caps=list(plan.agent_caps),
                memory=mem,
                runtime_admission=dict(
                    content_sha256=joined.AGENT_CONTENT,
                    inventory_sha256=joined.INVENTORY_SHA256,
                    full_inventory_match=False,
                    documentation_mismatches=["README.md"],
                    runtime_files_match=True,
                    runtime_files=11,
                    parameter_tensors=339,
                    serialized_parameter_bytes=15231233024,
                    files=[{k: r[k] for k in ("name", "size", "sha256")} for r in scan["files"]],
                ),
            )
            for row in rows[1:]:
                row.update(memory_before=copy.deepcopy(mem), memory_after=copy.deepcopy(mem))
        else:
            guard = GuardHFConfig()
            rows[0].update(
                snapshot_sha256=pin.sha256,
                adapter_config_sha256=guard.sha256,
                device=1,
                device_map={"": 1},
                device_name="Tesla T4",
                allocator_limit_bytes=guard.allocator_limit_bytes,
                free_headroom_bytes=guard.free_headroom_bytes,
                max_input_tokens=guard.max_input_tokens,
            )
            for row in rows:
                row.update(
                    global_free_bytes=4 * 1024**3,
                    global_total_bytes=totals[1],
                    **{
                        "process_" + key: val
                        for key, val in mem[1].items()
                        if key
                        in (
                            "allocated_bytes",
                            "reserved_bytes",
                            "peak_allocated_bytes",
                            "peak_reserved_bytes",
                        )
                    },
                )
        (sample / f"{role}_hf_metrics.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows)
        )
    return dict(
        probe=sample,
        policy=policy,
        attention=attention,
        publishers=publishers,
        pin=pin,
        commit=COMMIT,
        pad_token_ids={"agent": 151643, "guard": 151643},
    )


def test_native_join_repeatable_and_bounded(native: dict[str, Any]) -> None:
    result = joined.audit(**native)
    assert result == joined.audit(**native)
    assert result["valid"] and result["publisher_metadata_authenticated"]
    assert result["supervisor_records_consistent"] and result["allocator_records_within_caps"]
    assert not result["native_validated"] and not result["source_authenticated"]
    assert not result["tokenizer_metadata_authenticated"] and not result["phase5_accepted"]
    assert len(result["calls"]) == 6
    assert [call["tokens_per_generate_second"] for call in result["calls"]] == [
        10,
        10,
        30,
        30,
        10,
        10,
    ]


@pytest.mark.parametrize(
    "case",
    [
        "policy_pid",
        "attention_pid",
        "publisher",
        "placement",
        "admission",
        "load_time",
        "call_time",
        "overflow_throughput",
        "agent_memory",
        "guard_memory",
        "pin",
        "pad",
        "extra_role",
        "mutated_tree",
    ],
)
def test_native_join_mutations(
    native: dict[str, Any], case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if case in ("policy_pid", "attention_pid"):
        path = native[case.split("_")[0]] / "agent/request_000001/entered.json"
        row = impl.read(path)
        row["pid"] += 1
        write(path, row)
    elif case == "publisher":
        path = native["publishers"] / "agent_generation_config.json"
        path.write_text(path.read_text() + " ")
    elif case == "pin":
        native["pin"] = native["pin"].model_copy(update={"upstream_revision": "b" * 40})
    elif case == "pad":
        native["pad_token_ids"]["agent"] = 0
    elif case == "extra_role":
        (native["policy"] / "extra").mkdir()
    elif case == "mutated_tree":
        original = joined.audit_policy

        def changed(*args: Any, **kw: Any) -> Any:
            result = original(*args, **kw)
            (native["publishers"] / "empty").mkdir(exist_ok=True)
            return result

        monkeypatch.setattr(joined, "audit_policy", changed)
    else:
        path = native["probe"] / (
            "guard_hf_metrics.jsonl" if case == "guard_memory" else "agent_hf_metrics.jsonl"
        )
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if case == "placement":
            rows[0]["agent_caps"][0] += 1
        elif case == "admission":
            rows[0]["runtime_admission"]["files"].reverse()
        elif case == "load_time":
            rows[0]["load_seconds_including_hashes"] = 11
        elif case == "call_time":
            rows[1]["call_seconds"] = 1.5
        elif case == "overflow_throughput":
            rows[1]["generate_seconds"] = 1e-320
        elif case == "agent_memory":
            rows[1]["memory_after"][0]["peak_reserved_bytes"] = 20 * 1024**3
        else:
            rows[1]["process_peak_reserved_bytes"] = 6 * 1024**3
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises((ValueError, KeyError)):
        joined.audit(**native)


def test_supervisor_detects_raw_change_during_audit(
    sample: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = impl.read

    def changed(path: Path) -> dict[str, Any]:
        value = original(path)
        if path.name == "summary.json":
            target = sample / "baseline.json"
            target.write_text(target.read_text() + " ")
        return value

    monkeypatch.setattr(impl, "read", changed)
    with pytest.raises(ValueError, match="changed"):
        audit(sample)


@pytest.mark.parametrize(
    "commit,backend", [("bad", "stub"), ("a" * 40, "other"), ("b" * 40, "stub")]
)
def test_caller_expectations_refused(sample: Path, commit: str, backend: Any) -> None:
    with pytest.raises(ValueError):
        impl.audit(sample, commit=commit, backend=backend)


def cli(script: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed repository CLI and test-owned paths
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        env=dict(os.environ, PYTHONPATH=str(ROOT / "src")),
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.parametrize("target", ["fresh", "existing", "inside", "wrong_commit"])
def test_supervisor_cli(sample: Path, tmp_path: Path, target: str) -> None:
    output = sample / "audit.json" if target == "inside" else tmp_path / "audit.json"
    if target == "existing":
        output.write_text("preserve-existing")
    before = impl.inventory(sample)
    result = cli(
        "audit_phase5_ordinary_pair.py",
        [
            "--probe",
            str(sample),
            "--output",
            str(output),
            "--backend",
            "stub",
            "--source-commit",
            "b" * 40 if target == "wrong_commit" else COMMIT,
        ],
    )
    assert result.returncode == 0 if target == "fresh" else result.returncode != 0
    assert impl.inventory(sample) == before
    if target == "fresh":
        assert impl.read(output) == audit(sample)
    elif target == "existing":
        assert output.read_text() == "preserve-existing"
    else:
        assert not output.exists()


def test_native_cli_and_fresh_output(native: dict[str, Any], tmp_path: Path) -> None:
    pin = tmp_path / "snapshot.json"
    write(pin, native["pin"].model_dump(mode="json"))
    output = tmp_path / "native_audit.json"
    args = [
        value
        for name in ("probe", "policy", "attention", "publishers")
        for value in ("--" + name, str(native[name]))
    ]
    args.extend(
        [
            "--snapshot",
            str(pin),
            "--source-commit",
            COMMIT,
            "--agent-pad-token-id",
            "151643",
            "--guard-pad-token-id",
            "151643",
            "--output",
            str(output),
        ]
    )
    result = cli("audit_phase5_ordinary_native.py", args)
    assert result.returncode == 0, result.stderr
    assert impl.read(output) == joined.audit(**native)
    saved = output.read_bytes()
    assert cli("audit_phase5_ordinary_native.py", args).returncode != 0
    assert output.read_bytes() == saved
