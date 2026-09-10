"""Synthetic GPU-shaped records plus public metadata; never model measurements."""

from __future__ import annotations

import importlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import MODEL
from react_agent.llm.generation_policy_v1 import CONFIG_FIELDS, METHODS
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION, GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.llm.model_pair_v1 import ModelIdentity, PairConfig
from react_agent.validation.context_policy_audit_v1 import (
    PUBLISHERS,
    audit_combined,
    publisher_policy,
)
from react_agent.validation.context_stress_audit_v1 import read_record
from react_agent.validation.generation_policy_audit_v1 import GLOBAL_DEFAULTS

ROOT = Path(__file__).resolve().parents[2]
METADATA = ROOT / "docs/evaluation/publisher_policy_v1"


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


@pytest.fixture
def combined(tmp_path: Path) -> tuple[Path, Path, Path, GuardSnapshot, str]:
    fixture = importlib.import_module("test_context_stress_audit_v1")
    probe, oldpin, commit = fixture.sample.__wrapped__(tmp_path / "synthetic")
    value = oldpin.model_dump(mode="json")
    value["upstream_revision"] = CANDIDATE_REVISION
    for entry in value["files"]:
        if entry["name"] == "generation_config.json":
            entry.update(size=242, sha256=PUBLISHERS["guard"]["sha256"])
    pin = GuardSnapshot.model_validate(value)
    oldconfig = PairConfig(
        ModelIdentity(MODEL, AGENT_REVISION), ModelIdentity(oldpin.model_id, oldpin.model_revision)
    )
    config = PairConfig(
        ModelIdentity(MODEL, AGENT_REVISION), ModelIdentity(pin.model_id, pin.model_revision)
    )
    replacements = {
        oldpin.model_revision: pin.model_revision,
        oldpin.sha256: pin.sha256,
        oldconfig.sha256: config.sha256,
    }
    for cold in (True, False):
        replacements[oldconfig.execution("guard", cold=cold).identity] = config.execution(
            "guard", cold=cold
        ).identity
    for path in probe.rglob("*"):
        if path.is_file():
            data = path.read_text()
            for before, after in replacements.items():
                data = data.replace(before, after)
            path.write_text(data)
    # Reuse only published byte identities from the selected mount scan; all
    # timings/tensors/PIDs above remain synthetic, with no historical outputs.
    scan = read_record(ROOT / "experiments/manifests/phase5_agent_mount_v1_scan01.json")
    loadpath = probe / "agent_hf_metrics.jsonl"
    load = read_record(loadpath)
    load["runtime_admission"]["files"] = [
        {k: r[k] for k in ("name", "size", "sha256")} for r in scan["files"]
    ]
    write(loadpath, load)
    policy, publishers = tmp_path / "policy", tmp_path / "publishers"
    shutil.copytree(METADATA, publishers)
    workers = read_record(probe / "closed.json")["workers"]
    for role in ("agent", "guard"):
        native = read_record(publishers / f"{role}_generation_config.json")
        publisher = {**dict.fromkeys(CONFIG_FIELDS), **native, "transformers_version": "5.5.0"}
        submitted = read_record(probe / f"{role}_stress/prepared.json")["generation"]
        resolved = dict(submitted)
        for defaults in (publisher, GLOBAL_DEFAULTS):
            for k, v in defaults.items():
                if resolved[k] is None:
                    resolved[k] = v
        total = 4608 if role == "agent" else 4224
        length = {**resolved, "max_length": total, "min_length": total}
        identity = config.agent if role == "agent" else config.guard
        common = {
            "protocol": "generation_policy_observation_v1",
            "pid": workers[role]["attempts"][0]["pid"],
            "role": role,
            "model_id": identity.model_id,
            "model_revision": identity.model_revision,
        }
        records = {
            "entered": {
                "publisher": publisher,
                "global_defaults": GLOBAL_DEFAULTS,
                "transformers_version": "5.5.0",
                "model_generation_calls_planned": 1,
                "policy_changed": False,
            },
            "resolved": {
                "submitted": submitted,
                "resolved": resolved,
                "model_kwargs_keys": ["attention_mask", "input_ids"],
            },
            "length": {
                "before": resolved,
                "after": length,
                "input_tokens": 4096,
                "model_input_name": "input_ids",
            },
            "restored": {"methods_restored": True, "hook_calls": dict.fromkeys(METHODS, 1)},
            "completed": {
                "model_generation_calls": 1,
                "hook_calls": dict.fromkeys(METHODS, 1),
                "resolved_sha256": text_hash(canonical_json(resolved)),
                "length_sha256": text_hash(canonical_json(length)),
                "methods_restored": True,
                "policy_changed": False,
            },
        }
        for stage, data in records.items():
            write(policy / role / f"{stage}.json", {**common, "stage": stage, **data})
    return probe, policy, publishers, pin, commit


def test_combined_repeatable_and_publisher_difference(combined: Any) -> None:
    result = audit_combined(*combined)
    assert result == audit_combined(*combined)
    assert result["publisher_metadata_authenticated"] and not result["source_authenticated"]
    assert not result["phase5_accepted"]
    assert [len(v) for v in result["input_sha256"].values()] == [23, 10, 2]
    for role, penalty in (("agent", 1.05), ("guard", 1.1)):
        assert result["policies"][role]["resolved"]["repetition_penalty"] == penalty
        assert result["policies"][role]["resolved"]["do_sample"] is False
        assert result["publishers"][role]["publisher_json"]["transformers_version"] == "4.37.0"


@pytest.mark.parametrize(
    "case",
    [
        "publisher_bytes",
        "publisher_swapped",
        "publisher_extra",
        "publisher_link",
        "policy_missing",
        "policy_extra",
        "policy_pid",
        "policy_penalty",
        "policy_version",
        "submitted",
        "restore",
        "calls",
        "cache",
        "agent_admission",
        "agent_file_order",
        "guard_pin",
        "revision",
        "nested",
    ],
)
def test_combined_rejects_corruption(combined: Any, case: str) -> None:
    probe, policy, publishers, pin, commit = combined
    path = policy / "agent/entered.json"
    if case == "publisher_bytes":
        path = publishers / "agent_generation_config.json"
        path.write_bytes(path.read_bytes().replace(b"1.05", b"1.06"))
    elif case == "publisher_swapped":
        shutil.copyfile(
            publishers / "guard_generation_config.json", publishers / "agent_generation_config.json"
        )
    elif case == "publisher_extra":
        write(publishers / "extra.json", {})
    elif case == "publisher_link":
        target = publishers / "agent_generation_config.json"
        target.unlink()
        target.symlink_to(METADATA / target.name)
    elif case == "policy_missing":
        path.unlink()
    elif case == "policy_extra":
        write(policy / "extra.json", {})
    elif case == "guard_pin":
        value = pin.model_dump(mode="json")
        next(r for r in value["files"] if r["name"] == "generation_config.json")["sha256"] = (
            "e" * 64
        )
        pin = GuardSnapshot.model_validate(value)
    elif case == "revision":
        commit = "d" * 40
    elif case == "nested":
        publishers = policy
    else:
        paths = {
            "submitted": probe / "agent_stress/prepared.json",
            "cache": probe / "agent_stress/completed.json",
            "restore": policy / "agent/restored.json",
            "calls": policy / "agent/completed.json",
            "agent_admission": probe / "agent_hf_metrics.jsonl",
            "agent_file_order": probe / "agent_hf_metrics.jsonl",
        }
        path = paths.get(case, path)
        value = read_record(path)
        if case == "policy_pid":
            value["pid"] += 1
        elif case == "policy_penalty":
            value["publisher"]["repetition_penalty"] = 1.1
        elif case == "policy_version":
            value["publisher"]["transformers_version"] = "4.37.0"
        elif case == "submitted":
            value["generation"]["do_sample"] = True
        elif case == "restore":
            value["methods_restored"] = False
        elif case == "calls":
            value["model_generation_calls"] = 2
        elif case == "cache":
            value["cache"]["sequence_length"] -= 1
        elif case == "agent_file_order":
            value["runtime_admission"]["files"].reverse()
        elif case == "agent_admission":
            next(
                r
                for r in value["runtime_admission"]["files"]
                if r["name"] == "generation_config.json"
            )["sha256"] = "e" * 64
        write(path, value)
    with pytest.raises((ValueError, FileNotFoundError)):
        audit_combined(probe, policy, publishers, pin, commit)


@pytest.mark.parametrize("role", ["agent", "guard"])
def test_publisher_bytes_match_frozen_inventory(role: Any) -> None:
    result = publisher_policy(METADATA / f"{role}_generation_config.json", role)
    path = ROOT / (
        "docs/evaluation/qwen7b_upstream_inventory_v1.json"
        if role == "agent"
        else "configs/guard_hf_v1/qwen_1_5b_upstream.json"
    )
    entry = next(r for r in read_record(path)["files"] if r["name"] == "generation_config.json")
    for key in ("size", "git_blob_sha1"):
        assert result["identity"][key] == entry[key]
    assert not result["native_imported"]
