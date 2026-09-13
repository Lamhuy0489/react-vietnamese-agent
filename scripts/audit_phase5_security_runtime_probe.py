"""Save a fresh read-only artifact audit; never rerun model inference."""

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.security_runtime_probe_audit_v1 import audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("probe", "tokenizers", "publishers", "snapshot", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    result = audit(
        args.probe,
        args.tokenizers,
        args.publishers,
        GuardSnapshot.model_validate_json(args.snapshot.read_text()),
        args.source_commit,
    )
    write_receipt(args.output, result)


if __name__ == "__main__":
    main()
