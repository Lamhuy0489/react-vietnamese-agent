"""Hash-bound public grouped Dev identities; never model prompt material."""

from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from react_agent.adversarial_release import ReleasedFixture
from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.model_pair_v1 import ModelIdentity
from react_agent.llm.model_pair_v2 import ShutdownPairConfig
from react_agent.llm.native_shutdown_v2 import agent_config
from react_agent.security_v1.contracts import Level, configuration
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog, selected_fixtures
from react_agent.validation.grouped_dev_plan_v1 import DEV_SHA256, SELECTION_SEED

PROTOCOL = "grouped_dev_cpu_runner_v1"
REVISION = "grouped_dev_scripted_v1"
LEVELS: tuple[Level, ...] = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")


def pair_config() -> ShutdownPairConfig:
    return ShutdownPairConfig(
        ModelIdentity("synthetic-agent", REVISION),
        ModelIdentity("synthetic-guard", REVISION),
        agent_start_seconds=10,
        guard_start_seconds=10,
        agent_call_seconds=5,
        guard_call_seconds=5,
    )


def task_key(row: ReleasedFixture, level: Level) -> str:
    return row.variant_id + "__" + level


def identity(
    release: Path, environment: Path, commit: str
) -> tuple[dict[str, Any], tuple[ReleasedFixture, ...]]:
    if re.fullmatch(r"[a-f0-9]{40}", commit) is None:
        raise ValueError("exact source commit required")
    rows = selected_fixtures(release)
    tasks = []
    for index in range(8):
        for level in LEVELS:
            for row in rows[index * 2 : index * 2 + 2]:
                tasks.append(
                    dict(
                        key=task_key(row, level),
                        shard=index,
                        level=level,
                        variant_id=row.variant_id,
                        pair_id=row.pair_id,
                        group_id=row.group_id,
                        branch=row.branch,
                        task_id=row.task.task_id,
                        task_sha256=text_hash(row.task.instruction),
                        fixture_sha256=text_hash(canonical_json(row.model_dump(mode="json"))),
                        source_catalog=fixture_catalog(row).model_dump(mode="json"),
                    )
                )
    data = dict(
        protocol=PROTOCOL,
        backend="scripted_cpu",
        source_commit=commit,
        selection_seed=SELECTION_SEED,
        dev_sha256=dict(DEV_SHA256),
        environment_sha256=inventory(environment),
        tasks=tasks,
        shards=8,
        expected_tasks=112,
        runtime_version="security_runtime_v10",
        runtime=RuntimeConfig().model_dump(),
        generation=GenerationConfig().model_dump(),
        security={level: configuration(level).model_dump(mode="json") for level in LEVELS},
        pair_config=asdict(pair_config()),
        agent_execution=asdict(agent_config(pair_config())),
        scripted_profile=REVISION,
        automatic_retry=False,
        native_dispatch_allowed=False,
        quality_scoring=False,
        test_payload_accessed=False,
    )
    return data, rows
