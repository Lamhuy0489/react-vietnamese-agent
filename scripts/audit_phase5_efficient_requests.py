"""Audit closed ordinary-request sidecars and native metrics without inference."""

from __future__ import annotations

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.validation.efficient_requests_audit_v1 import audit
from react_agent.validation.guard_probe_audit_v2 import require


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attention", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--role", choices=("agent", "guard"), required=True)
    parser.add_argument("--worker-pid", type=int, required=True)
    parser.add_argument("--expected-requests", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    require(
        not args.output.exists()
        and not any(
            args.output.resolve().is_relative_to(p.resolve())
            for p in (args.attention, args.metrics)
        ),
        "fresh output outside immutable inputs",
    )
    result = audit(
        args.attention,
        args.metrics,
        role=args.role,
        worker_pid=args.worker_pid,
        expected_requests=args.expected_requests,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("EFFICIENT_REQUESTS_AUDIT_COMPLETE phase5_accepted=False source_authenticated=False")


if __name__ == "__main__":
    main()
