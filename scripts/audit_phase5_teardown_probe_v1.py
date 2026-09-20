"""Audit saved CPU teardown controls without launching workers or loading models."""

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.validation.teardown_probe_audit_v1 import audit

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    target = args.output.resolve()
    if (
        target.exists()
        or not target.is_relative_to(ROOT / "results")
        or target.is_relative_to(args.input.resolve())
        or args.input.resolve().is_relative_to(target)
    ):
        raise ValueError("fresh output under results outside inputs required")
    write_receipt(target, audit(args.input))
    print("TEARDOWN_CPU_AUDIT_COMPLETE")


if __name__ == "__main__":
    main()
