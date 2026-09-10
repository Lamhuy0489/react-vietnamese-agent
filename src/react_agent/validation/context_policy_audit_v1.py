"""Authenticate publisher metadata and join stress/policy records, without inference."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.llm.agent_mount_v1 import MODEL, REVISION, no_links
from react_agent.llm.agent_runtime_input_v1 import INVENTORY_SHA256
from react_agent.llm.generation_policy_v1 import CONFIG_FIELDS
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION, GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AGENT_CONTENT, AGENT_REVISION
from react_agent.llm.model_pair_v1 import ModelIdentity, Role
from react_agent.validation.context_stress_audit_v1 import (
    audit_probe,
    equal,
    inventory,
    read_record,
)
from react_agent.validation.generation_policy_audit_v1 import audit_policy
from react_agent.validation.guard_probe_audit_v2 import require

# Previously authenticated immutable upstream inventories. No arbitrary caller
# hash is accepted as publisher authority, and no weights are read here.
PUBLISHERS: dict[Role, dict[str, Any]] = {
    "agent": {
        "model_id": MODEL,
        "revision": REVISION,
        "size": 243,
        "git_blob_sha1": "0eb3c536657dcd12626e09eca4b6198c0cbcde1e",
        "sha256": "3a8f9087e486054c8a4a08dae2e5a3ba62e23da212b5b8c08bc42cb983c3459f",
    },
    "guard": {
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "revision": CANDIDATE_REVISION,
        "size": 242,
        "git_blob_sha1": "dfc11073787daf1b0f9c0f1499487ab5f4c93738",
        "sha256": "e558847a8b4402616f1273797b015104dc266fe4b520056fca88823ba8f8ebe6",
    },
}


def publisher_policy(path: Path, role: Role) -> dict[str, Any]:
    """Reconstruct the pinned native config snapshot from authenticated JSON bytes."""
    no_links(path)
    require(role in PUBLISHERS and path.is_file(), "publisher role/file")
    expected = PUBLISHERS[role]
    with path.open("rb") as stream:
        raw = stream.read(expected["size"] + 1)
    require(len(raw) == expected["size"], "publisher metadata size")
    blob = hashlib.sha1(  # noqa: S324 - immutable upstream Git object address
        f"blob {len(raw)}\0".encode() + raw, usedforsecurity=False
    ).hexdigest()
    require(
        blob == expected["git_blob_sha1"] and hashlib.sha256(raw).hexdigest() == expected["sha256"],
        "publisher metadata hash",
    )
    value = read_record(path)
    require(set(value) < CONFIG_FIELDS, "publisher fields")
    # Pinned native constructor uses None for absent parameters. The observer
    # uses native serialization's version5.5.0, not the publisher's4.37.0 label.
    policy = {**dict.fromkeys(CONFIG_FIELDS), **value, "transformers_version": "5.5.0"}
    return {
        "identity": dict(expected),
        "publisher_json": value,
        "observed_publisher_expected": policy,
        "native_imported": False,
    }


def audit_combined(
    probe: Path, policy: Path, publishers: Path, pin: GuardSnapshot, commit: str
) -> dict[str, Any]:
    """Remote wrapper/bundle authentication is a separate release-level gate."""
    roots = (probe, policy, publishers)
    for i, root in enumerate(roots):
        no_links(root)
        for other in roots[i + 1 :]:
            require(
                not root.resolve().is_relative_to(other.resolve())
                and not other.resolve().is_relative_to(root.resolve()),
                "separate non-nested audit inputs",
            )
    before = {
        name: inventory(root)
        for name, root in zip(("probe", "policy", "publishers"), roots, strict=True)
    }
    equal(
        sorted(before["publishers"]),
        ["agent_generation_config.json", "guard_generation_config.json"],
        "publisher inventory",
    )
    equal(
        sorted(before["policy"]),
        sorted(
            f"{role}/{stage}.json"
            for role in PUBLISHERS
            for stage in ("entered", "resolved", "length", "restored", "completed")
        ),
        "combined policy inventory",
    )
    require(pin.upstream_revision == CANDIDATE_REVISION, "guard revision")
    stress = audit_probe(probe, pin, commit)
    workers = read_record(probe / "closed.json")["workers"]
    observations, metadata = {}, {}
    for role in PUBLISHERS:
        evidence = publisher_policy(publishers / f"{role}_generation_config.json", role)
        expected = PUBLISHERS[role]
        if role == "agent":
            load = read_record(probe / "agent_hf_metrics.jsonl")
            entries = load["runtime_admission"]["files"]
            equal(
                hashlib.sha256(
                    canonical_json(
                        {
                            "protocol": "agent_runtime_input_v1",
                            "inventory": INVENTORY_SHA256,
                            "files": entries,
                        }
                    ).encode()
                ).hexdigest(),
                AGENT_CONTENT,
                "full agent runtime metadata content identity",
            )
            matches = [r for r in entries if r["name"] == "generation_config.json"]
            equal(len(matches), 1, "agent generation metadata coverage")
            entry = matches[0]
            for key in ("size", "sha256"):
                equal(entry[key], expected[key], "agent admitted metadata " + key)
            identity = ModelIdentity(MODEL, AGENT_REVISION)
        else:
            matches = [r for r in pin.files if r.name == "generation_config.json"]
            require(len(matches) == 1, "guard generation metadata coverage")
            equal(matches[0].size, expected["size"], "guard admitted metadata size")
            equal(matches[0].sha256, expected["sha256"], "guard admitted metadata SHA256")
            identity = ModelIdentity(pin.model_id, pin.model_revision)
        pid = workers[role]["attempts"][0]["pid"]
        submitted = read_record(probe / f"{role}_stress/prepared.json")["generation"]
        observations[role] = audit_policy(
            policy / role, role, identity, pid, submitted, evidence["observed_publisher_expected"]
        )
        metadata[role] = evidence
    after = {
        name: inventory(root)
        for name, root in zip(("probe", "policy", "publishers"), roots, strict=True)
    }
    equal(after, before, "combined inputs changed during audit")
    return {
        "protocol": "context_policy_combined_audit_v1",
        "valid": True,
        "phase5_accepted": False,
        "publisher_metadata_authenticated": True,
        "source_authenticated": False,
        "source_commit": commit,
        "stress": stress,
        "policies": observations,
        "publishers": metadata,
        "input_sha256": before,
        "limitations": "Authenticated publisher JSON and consistent 23-probe/10-policy records; "
        "remote source/bundle still require release audit. No tokenizer reconstruction, "
        "model quality, IPC leak-free proof or native execution inferred from synthetic fixtures",
    }
