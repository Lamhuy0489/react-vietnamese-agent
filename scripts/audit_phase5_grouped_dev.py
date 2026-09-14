"""Read-only grouped CPU/native shard audit; no inference or checkpoint repair."""

import argparse
import json
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.grouped_dev_identity_v2 import identity
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.grouped_dev_checkpoint_v2 import audit_prefix
from react_agent.validation.grouped_dev_native_audit_v2 import audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--shard", type=int, choices=range(8), required=True)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--tokenizers", type=Path)
    parser.add_argument("--publishers", type=Path)
    args = parser.parse_args()
    for path in (args.probe, args.output, args.snapshot, args.tokenizers, args.publishers):
        if path is not None:
            no_links(path)
    protected = [args.probe, Path("data"), args.tokenizers, args.publishers, args.snapshot]
    if args.output.exists() or any(
        p is not None
        and (
            args.output.resolve().is_relative_to(p.resolve())
            or p.resolve().is_relative_to(args.output.resolve())
        )
        for p in protected
    ):
        raise ValueError("fresh audit output outside immutable probe required")
    saved = json.loads((args.probe / "identity.json").read_text())["run"]
    native = saved["backend"] == "hf"
    if native != all(p is not None for p in (args.snapshot, args.tokenizers, args.publishers)) or (
        not native and any(p is not None for p in (args.snapshot, args.tokenizers, args.publishers))
    ):
        raise ValueError("native audit metadata must agree with backend")
    snapshot = (
        GuardSnapshot.model_validate_json(args.snapshot.read_text()) if args.snapshot else None
    )
    manifest, _ = identity(
        Path("data/adversarial/release_v2"),
        Path("data/clean/v1_1/environment"),
        args.source_commit,
        saved["backend"],
        Path("docs/evaluation/qwen7b_upstream_inventory_v1.json") if native else None,
        snapshot,
    )
    if native:
        if snapshot is None:
            raise ValueError("native snapshot required")
        result = audit(args.probe, manifest, args.shard, args.tokenizers, args.publishers, snapshot)
    else:
        checks = audit_prefix(args.probe, manifest, args.shard)
        result = dict(
            valid=True,
            completed=len(checks),
            expected=14,
            complete=len(checks) == 14,
            backend="stub",
            native_artifacts_authenticated=False,
            phase5_accepted=False,
        )
    write_receipt(args.output, result)
    print(json.dumps(dict(valid=True, completed=result["completed"], native=native)))


if __name__ == "__main__":
    main()
