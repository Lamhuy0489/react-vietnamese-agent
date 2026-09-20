"""Audit the constrained CPU/native observer outputs without model loading."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_phase5_exit_pair_v1 import audit_probe

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.exit_native_audit_v1 import audit as native_audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--condition", choices=("valid", "backend_failure"), default="valid")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--tokenizers", type=Path)
    parser.add_argument("--publishers", type=Path)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata_paths = (args.tokenizers, args.publishers, args.snapshot)
    protected = [args.probe, Path("data"), *[p for p in metadata_paths if p is not None]]
    for path in [args.output, *protected]:
        no_links(path)
    if args.output.exists() or any(
        args.output.resolve().is_relative_to(p.resolve())
        or p.resolve().is_relative_to(args.output.resolve())
        for p in protected
    ):
        raise ValueError("fresh audit destination outside inputs required")
    identity = json.loads((args.probe / "identity.json").read_text())
    if identity.get("backend") == "hf":
        if args.tokenizers is None or args.publishers is None or args.snapshot is None:
            raise ValueError("native tokenizer/publisher/snapshot inputs required")
        if args.condition != "valid":
            raise ValueError("native injected condition forbidden")
        result = native_audit(
            args.probe,
            args.tokenizers,
            args.publishers,
            GuardSnapshot.model_validate_json(args.snapshot.read_text()),
            args.source_commit,
            Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
            Path("data/clean/v1_1/environment"),
        )
    else:
        if any(p is not None for p in metadata_paths):
            raise ValueError("native metadata forbidden for CPU audit")
        result = audit_probe(args.probe, args.condition, args.source_commit)
    write_receipt(args.output, result)
    print("EXIT_PAIR_NATIVE_AUDIT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
