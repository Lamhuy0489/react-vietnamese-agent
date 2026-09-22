"""Fixed 32-task public Dev identity; no output-selected cases or evaluator data."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from react_agent.adversarial_release import ReleasedFixture
from react_agent.llm.clause_pair_probe_v1 import execution_sources as pair_sources
from react_agent.llm.exit_pair_v1 import ExitPairConfig, observer_config
from react_agent.llm.grouped_dev_identity_v1 import pair_config as old_config
from react_agent.llm.grouped_dev_identity_v2 import identity as old_identity
from react_agent.llm.guard_observer_probe_v2 import PROFILE as GUARD_REVISION
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v1 import ModelIdentity
from react_agent.llm.native_shutdown_v2 import agent_config, native_config
from react_agent.security_v1.authorization_anchors_v3 import PROFILE as ANCHORS
from react_agent.security_v1.clause_pair_runtime_v1 import RUNTIME_VERSION
from react_agent.security_v1.exit_milestones_v1 import runtime_identity
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, PROMPT_VERSION
from react_agent.security_v1.processing_scope_v5 import PROFILE as SCOPE
from react_agent.security_v1.value_origin_v3 import PROFILE as ORIGIN
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY, LANGUAGE, POLICY

PROTOCOL = "clause_dev32_v1"
LEVELS = ("A2", "A6")


def pair_config() -> ExitPairConfig:
    return observer_config(
        replace(old_config(), guard=ModelIdentity("synthetic-guard", GUARD_REVISION))
    )


def execution_sources() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    names = (
        "llm/clause_dev_identity_v1.py",
        "llm/clause_dev_runner_v1.py",
        "validation/clause_dev_checkpoint_v1.py",
        "validation/clause_dev_native_audit_v1.py",
        "llm/grouped_dev_runner_v2.py",
        "llm/grouped_dev_identity_v1.py",
        "llm/grouped_dev_identity_v2.py",
        "llm/grouped_dev_runner_v1.py",
        "validation/grouped_dev_checkpoint_v2.py",
        "validation/grouped_dev_inputs_v1.py",
        "validation/grouped_dev_plan_v1.py",
        "llm/constrained_probe_stub_v1.py",
    )
    return {
        **pair_sources(),
        **{p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in names},
    }


def identity(
    release: Path,
    environment: Path,
    commit: str,
    backend: str,
    model_inventory: Path | None = None,
    snapshot: GuardSnapshot | None = None,
) -> tuple[dict[str, Any], tuple[ReleasedFixture, ...]]:
    manifest, rows = old_identity(release, environment, commit, backend, model_inventory, snapshot)
    tasks = [t for t in manifest["tasks"] if t["level"] in LEVELS]
    if len(tasks) != 32 or any(sum(t["shard"] == s for t in tasks) != 4 for s in range(8)):
        raise ValueError("exact paired Dev32 schedule required")
    config = observer_config(native_config()) if backend == "hf" else pair_config()
    manifest.update(
        protocol=PROTOCOL,
        tasks=tasks,
        expected_tasks=32,
        security={level: manifest["security"][level] for level in LEVELS},
        pair_config=asdict(config),
        agent_execution=asdict(agent_config(config)),
        runtime_version=RUNTIME_VERSION,
        execution_source_sha256=execution_sources(),
        clause_pair_profiles=dict(anchors=ANCHORS, scope=SCOPE, origin=ORIGIN),
        guard_prompt=dict(
            version=PROMPT_VERSION, sha256=hashlib.sha256(PROMPT.encode()).hexdigest()
        ),
        constrained_execution=dict(identity=IDENTITY, language=LANGUAGE, policy=POLICY),
        exit_observer=dict(protocol="exit_milestones_v1", runtime=runtime_identity()),
        historical_runtime_tasks=112,
        quality_scoring=False,
        native_release_authenticated=False,
        native_dispatch_allowed=False,
    )
    return manifest, rows
