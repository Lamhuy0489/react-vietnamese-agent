"""Separate backend-bound identity for grouped native execution and CPU rehearsal."""

from dataclasses import asdict
from pathlib import Path
from typing import Any

from react_agent.adversarial_release import ReleasedFixture
from react_agent.llm.agent_mount_v1 import no_links, validate_inventory
from react_agent.llm.grouped_dev_identity_v1 import identity as cpu_identity
from react_agent.llm.grouped_dev_identity_v1 import pair_config
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_probe_v1 import TOLERANCE
from react_agent.llm.native_shutdown_v2 import agent_config, native_config


def identity(
    release: Path,
    environment: Path,
    commit: str,
    backend: str,
    model_inventory: Path | None = None,
    snapshot: GuardSnapshot | None = None,
) -> tuple[dict[str, Any], tuple[ReleasedFixture, ...]]:
    if (
        backend not in {"stub", "hf"}
        or ((backend == "hf") != (model_inventory is not None and snapshot is not None))
        or (backend == "stub" and (model_inventory is not None or snapshot is not None))
    ):
        raise ValueError("backend and native pins must agree")
    manifest, rows = cpu_identity(release, environment, commit)
    config = native_config() if backend == "hf" else pair_config()
    pins = None
    if model_inventory is not None and snapshot is not None:
        import hashlib
        import json

        no_links(model_inventory)
        payload = model_inventory.read_bytes()
        validate_inventory(json.loads(payload))
        if snapshot.model_revision != config.guard.model_revision:
            raise ValueError("fixed native guard snapshot required")
        pins = dict(
            model_inventory_sha256=hashlib.sha256(payload).hexdigest(),
            guard_snapshot_sha256=snapshot.sha256,
        )
    manifest.update(
        protocol="grouped_dev_runner_v2",
        backend=backend,
        pair_config=asdict(config),
        agent_execution=asdict(agent_config(config)),
        scripted_profile=manifest["scripted_profile"] if backend == "stub" else None,
        native_dispatch_allowed=backend == "hf",
        native_pins=pins,
        recovery=dict(
            samples=6,
            stable_tail=3,
            tolerance_bytes=TOLERANCE,
            sample_interval_seconds=1.0 if backend == "hf" else 0.0,
        ),
    )
    return manifest, rows
