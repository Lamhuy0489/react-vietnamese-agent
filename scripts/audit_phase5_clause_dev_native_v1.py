"""Read-only source-admitted Dev32 shard audit; no model loading."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.clause_dev_dispatch_v1 import release_identity
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.clause_dev_checkpoint_v1 import audit_prefix
from react_agent.validation.clause_dev_native_audit_v1 import audit
from react_agent.validation.clause_dev_release_v1 import admit
from react_agent.validation.context_stress_audit_v1 import inventory
from react_agent.validation.exit_pair_audit_v1 import checked_runtime


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("probe", "output", "source-manifest"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--shard", type=int, choices=range(8), required=True)
    for name in ("snapshot", "tokenizers", "publishers"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    protected = [
        project,
        args.probe,
        args.source_manifest,
        args.snapshot,
        args.tokenizers,
        args.publishers,
    ]
    for path in [args.output, *protected]:
        if path is not None:
            no_links(path)
    if args.output.exists() or any(
        p is not None
        and (
            args.output.resolve().is_relative_to(p.resolve())
            or p.resolve().is_relative_to(args.output.resolve())
        )
        for p in protected
    ):
        raise ValueError("fresh audit output outside inputs required")
    before = inventory(args.probe)
    saved = json.loads((args.probe / "identity.json").read_text())["run"]
    native = saved["backend"] == "hf"
    paths = (args.snapshot, args.tokenizers, args.publishers)
    if (native and not all(p is not None for p in paths)) or (
        not native and any(p is not None for p in paths)
    ):
        raise ValueError("native metadata must agree with backend")
    source = admit(
        project, args.source_manifest, args.source_sha256, args.source_commit, native=native
    )
    snapshot = (
        GuardSnapshot.model_validate_json(args.snapshot.read_text()) if args.snapshot else None
    )
    manifest, _ = release_identity(
        project / "data/adversarial/release_v2",
        project / "data/clean/v1_1/environment",
        args.source_commit,
        saved["backend"],
        project / "docs/evaluation/qwen7b_upstream_inventory_v1.json" if native else None,
        snapshot,
        release=source,
    )
    manifest["exit_observer"]["runtime"] = checked_runtime(saved["exit_observer"]["runtime"])
    if native:
        if snapshot is None:
            raise ValueError("native snapshot required")
        result = audit(args.probe, manifest, args.shard, args.tokenizers, args.publishers, snapshot)
    else:
        checks = audit_prefix(args.probe, manifest, args.shard)
        result = dict(completed=len(checks), expected=4, complete=len(checks) == 4, backend="stub")
    if inventory(args.probe) != before:
        raise ValueError("audit mutated raw")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(
        args.output,
        {
            **result,
            "source_bytes_verified": True,
            "remote_release_authenticated": False,
            "phase5_accepted": False,
        },
    )
    print("CLAUSE_DEV32_AUDIT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
