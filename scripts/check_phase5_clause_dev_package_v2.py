"""Exercise all declared Dev32 tasks in the exact isolated package, without models."""

from __future__ import annotations

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import write_receipt
from react_agent.llm.clause_dev_dispatch_v1 import release_identity
from react_agent.llm.clause_dev_dispatch_v2 import run
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.validation.clause_dev_checkpoint_v1 import audit_prefix
from react_agent.validation.clause_dev_release_v1 import admit
from react_agent.validation.context_stress_audit_v1 import equal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("fresh package evidence required")
    project = Path(__file__).resolve().parents[1]
    source = admit(
        project, args.source_manifest, args.source_sha256, args.source_commit, native=False
    )
    release, environment = (
        project / "data/adversarial/release_v2",
        project / "data/clean/v1_1/environment",
    )
    manifest, _ = release_identity(release, environment, args.source_commit, "stub", release=source)
    shards = []
    for shard in range(8):
        output = args.output / f"shard{shard}"
        options = dict(
            project=project,
            source_manifest=args.source_manifest,
            source_sha256=args.source_sha256,
            commit=args.source_commit,
            shard=shard,
        )
        first = run(output, release, environment, max_new_tasks=1, **options)
        equal(first["completed"], 1, "controlled prefix")
        retained = inventory(output)
        result = run(output, release, environment, resume=True, **options)
        equal(result["completed"], 4, "complete shard")
        after = inventory(output)
        equal({p: after.get(p) for p in retained}, retained, "prefix retained")
        equal(run(output, release, environment, resume=True, **options), result, "complete resume")
        equal(len(audit_prefix(output, manifest, shard)), 4, "independent shard audit")
        equal(inventory(output), after, "raw immutable")
        shards.append(result)
    write_receipt(
        args.output / "check.json",
        dict(
            valid=True,
            runtime_tasks=32,
            shards=shards,
            missing_only_resume=True,
            complete_resume=True,
            source_bytes_verified=True,
            model_inference_runs=0,
            quality_scored=False,
            phase5_accepted=False,
        ),
    )
    print("CLAUSE_DEV32_PACKAGE_CHECK_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
