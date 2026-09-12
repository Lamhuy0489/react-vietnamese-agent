"""Join completed ordinary native artifacts without launching inference or rewriting raw files."""

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.ordinary_native_audit_v1 import audit
from react_agent.validation.ordinary_pair_audit_v1 import read


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("probe", "policy", "attention", "publishers", "snapshot", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--agent-pad-token-id", type=int, required=True)
    parser.add_argument("--guard-pad-token-id", type=int, required=True)
    args = parser.parse_args()
    no_links(args.output)
    no_links(args.snapshot)
    require(not args.output.exists(), "fresh audit output")
    for root in (args.probe, args.policy, args.attention, args.publishers, args.snapshot):
        require(
            not args.output.resolve().is_relative_to(root.resolve())
            and not root.resolve().is_relative_to(args.output.resolve()),
            "audit output outside inputs",
        )
    pin = GuardSnapshot.model_validate(read(args.snapshot))
    result = audit(
        args.probe,
        args.policy,
        args.attention,
        args.publishers,
        pin=pin,
        commit=args.source_commit,
        pad_token_ids=dict(agent=args.agent_pad_token_id, guard=args.guard_pad_token_id),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("ORDINARY_NATIVE_AUDIT_COMPLETE native_validated=False source_authenticated=False")


if __name__ == "__main__":
    main()
