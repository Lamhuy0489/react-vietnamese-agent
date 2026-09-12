"""Audit saved ordinary requests with authenticated tokenizer-derived pad IDs."""

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.ordinary_pair_audit_v1 import read
from react_agent.validation.ordinary_tokenizer_audit_v1 import audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    names = ("probe", "policy", "attention", "publishers", "tokenizers", "snapshot", "output")
    for name in names:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    no_links(args.output)
    no_links(args.snapshot)
    require(not args.output.exists(), "fresh audit output")
    for name in names[:-1]:
        root = getattr(args, name)
        require(
            not args.output.resolve().is_relative_to(root.resolve())
            and not root.resolve().is_relative_to(args.output.resolve()),
            "audit output outside inputs",
        )
    result = audit(
        args.probe,
        args.policy,
        args.attention,
        args.publishers,
        args.tokenizers,
        pin=GuardSnapshot.model_validate(read(args.snapshot)),
        commit=args.source_commit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("ORDINARY_TOKENIZER_AUDIT_COMPLETE native_validated=False source_authenticated=False")


if __name__ == "__main__":
    main()
