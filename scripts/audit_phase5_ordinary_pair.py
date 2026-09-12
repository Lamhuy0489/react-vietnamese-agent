"""Read-only ordinary-pair supervisor audit; never imports native model libraries."""

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.ordinary_pair_audit_v1 import audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--backend", choices=("stub", "hf"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    require(
        not args.output.exists()
        and not args.output.resolve().is_relative_to(args.probe.resolve())
        and not args.probe.resolve().is_relative_to(args.output.resolve()),
        "fresh output outside probe",
    )
    result = audit(args.probe, commit=args.source_commit, backend=args.backend)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("ORDINARY_PAIR_AUDIT_COMPLETE native_validated=False")


if __name__ == "__main__":
    main()
