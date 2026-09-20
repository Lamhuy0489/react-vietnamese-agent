"""Audit saved CPU paired milestones with the frozen constrained checkpoint checks."""

import argparse
from pathlib import Path
from typing import Any, cast

from audit_phase5_constrained_probe_v1 import audit_probe as old_audit

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.exit_pair_probe_v1 import checkpoint, execution_sources, fixed_identity
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation.context_stress_audit_v1 import inventory
from react_agent.validation.exit_pair_audit_v1 import audit_exit

ROOT = Path(__file__).resolve().parents[1]


def audit_probe(root: Path, condition: str, source_commit: str) -> dict[str, Any]:
    before = inventory(root)
    result = cast(
        dict[str, Any],
        bind(
            old_audit, checkpoint=checkpoint, fixed_identity=fixed_identity, audit_task=audit_exit
        )(root, condition, source_commit),
    )
    if inventory(root) != before:
        raise ValueError("read-only audit changed inputs")
    return dict(
        result,
        protocol="exit_pair_probe_cpu_audit_v1",
        raw_sha256=before,
        execution_source_sha256=execution_sources(),
        native_cause_identified=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--condition", choices=("valid", "backend_failure"), default="valid")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    output, source = args.output.resolve(), args.probe.resolve()
    if (
        output.exists()
        or not output.is_relative_to(ROOT / "results")
        or (output.is_relative_to(source) or source.is_relative_to(output))
    ):
        raise ValueError("fresh audit output under results outside input required")
    write_receipt(output, audit_probe(args.probe, args.condition, args.source_commit))
    print("EXIT_PAIR_CPU_AUDIT_COMPLETE")


if __name__ == "__main__":
    main()
