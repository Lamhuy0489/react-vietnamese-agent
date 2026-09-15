"""Run native CPU compatibility or explicitly limited metadata-only package rehearsal."""

from __future__ import annotations

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_language_native_v1 import metadata, native_probe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    no_links(args.output)
    if args.output.exists() or any(
        args.output.resolve().is_relative_to(p.resolve())
        or p.resolve().is_relative_to(args.output.resolve())
        for p in (args.bundle, Path("data"))
    ):
        raise ValueError("fresh output outside inputs required")
    if len(args.source_commit) != 40 or any(
        c not in "0123456789abcdef" for c in args.source_commit
    ):
        raise ValueError("explicit source commit required")
    args.output.mkdir(parents=True)
    admitted = metadata(args.bundle, args.output / "tokenizer")
    write_receipt(args.output / "admission.json", admitted)
    result = dict(protocol="guard_language_metadata_only_v1", valid=True, library_verified=False)
    if not args.metadata_only:
        result = native_probe(args.bundle, args.output / "tokenizer", admitted)
    result.update(
        source_commit=args.source_commit,
        test_payload_accessed=False,
        private_ground_truth_accessed=False,
        phase5_accepted=False,
    )
    write_receipt(args.output / "summary.json", result)
    print("GUARD_LANGUAGE_COMPAT_COMPLETE metadata_only=" + str(args.metadata_only), flush=True)


if __name__ == "__main__":
    main()
