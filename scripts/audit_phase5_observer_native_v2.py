"""Audit four-task native observer artifacts without model loading."""

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.observer_native_audit_v2 import audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("probe", "tokenizers", "publishers", "snapshot", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    paths = [args.probe, args.tokenizers, args.publishers, args.snapshot, Path("data")]
    for path in [*paths, args.output]:
        no_links(path)
    if args.output.exists() or any(
        args.output.resolve().is_relative_to(p.resolve())
        or p.resolve().is_relative_to(args.output.resolve())
        for p in paths
    ):
        raise ValueError("fresh audit destination outside inputs required")
    result = audit(
        args.probe,
        args.tokenizers,
        args.publishers,
        GuardSnapshot.model_validate_json(args.snapshot.read_text()),
        args.source_commit,
        Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
        Path("data/clean/v1_1/environment"),
    )
    write_receipt(args.output, result)
    print("OBSERVER_NATIVE_AUDIT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
