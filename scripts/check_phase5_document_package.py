"""Read-only synthetic package checkpoint audit and lazy native factory check."""

import argparse
import json
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import write_receipt
from react_agent.llm.document_runtime_probe_v1 import (
    LEVELS,
    checkpoint,
    inventory,
    validate_identity,
)
from react_agent.llm.model_pair_v2 import ShutdownPair
from react_agent.llm.native_shutdown_v2 import agent_config, native_config
from react_agent.llm.request_policy_pair_v2 import policy_pair
from react_agent.security_v1.worker_shutdown_v2 import ShutdownBackend
from react_agent.validation.document_runtime_probe_audit_v1 import path_coverage


def no_model_load() -> Any:
    raise AssertionError("package CPU check must not load a model")


def audit(probe: Path) -> dict[str, Any]:
    before = inventory(probe)
    identity = json.loads((probe / "identity.json").read_text())
    validate_identity(identity)
    if identity["backend"] != "stub":
        raise ValueError("synthetic package evidence required")
    if sorted(p.name for p in (probe / "tasks").iterdir()) != list(LEVELS):
        raise ValueError("seven synthetic levels required")
    checkpoints = [checkpoint(probe / "tasks" / level) for level in LEVELS]
    coverage = {level: path_coverage(probe / "tasks" / level) for level in LEVELS}
    if not all(c["path_covered"] for c in coverage.values()):
        raise ValueError("synthetic document/guard path coverage required")
    if any(c["terminal"] != "completed" or c["recovered"] is not True for c in checkpoints):
        raise ValueError("completed/recovered synthetic levels required")
    config = native_config()
    pair = policy_pair(
        no_model_load,
        no_model_load,
        config,
        probe / "unused_attention",
        probe / "unused_policy",
    )
    try:
        if type(pair) is not ShutdownPair or any(
            type(worker) is not ShutdownBackend or worker.attempts
            for worker in pair._workers.values()
        ):
            raise ValueError("native lazy worker topology mismatch")
        for cold in (True, False):
            if agent_config(config).execution(cold=cold) != config.execution("agent", cold=cold):
                raise ValueError("agent-only/paired execution mismatch")
    finally:
        pair.close()
    if inventory(probe) != before:
        raise ValueError("package check mutated inputs")
    return dict(
        protocol="document_package_stub_audit_v1",
        valid=True,
        levels=len(checkpoints),
        path_coverage=coverage,
        terminals=[c["terminal"] for c in checkpoints],
        native_factory_lazy_verified=True,
        native_model_loads=0,
        phase5_accepted=False,
        raw_sha256=before,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve().is_relative_to(args.probe.resolve()):
        raise ValueError("fresh output outside probe required")
    write_receipt(args.output, audit(args.probe))


if __name__ == "__main__":
    main()
