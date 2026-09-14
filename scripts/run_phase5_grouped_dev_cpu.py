#!/usr/bin/env python3
"""Run or read-only audit a frozen grouped Dev scripted CPU shard (no native HF)."""

import argparse
import json
import subprocess
from pathlib import Path

from react_agent.llm.grouped_dev_identity_v1 import identity
from react_agent.llm.grouped_dev_runner_v1 import run
from react_agent.validation.grouped_dev_checkpoint_v1 import audit_prefix

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shard", type=int, required=True, choices=range(8))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--max-new-tasks", type=int)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "results"):
        raise ValueError("CPU output must be inside results")
    release = ROOT / "data/adversarial/release_v2"
    environment = ROOT / "data/clean/v1_1/environment"
    import shutil

    git = shutil.which("git")
    if git is None:
        raise ValueError("git unavailable")
    if args.audit_only:
        from react_agent.llm.agent_mount_v1 import no_links

        no_links(args.output)
        no_links(output / "identity.json")
        saved = json.loads((output / "identity.json").read_text())
        manifest, _ = identity(release, environment, saved["run"]["source_commit"])
        checks = audit_prefix(output, manifest, args.shard)
        result = dict(
            valid=True,
            completed=len(checks),
            remaining=14 - len(checks),
            native_model_runs=0,
            quality_scoring=False,
        )
    else:
        commit = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603
        result = run(
            args.output,
            release,
            environment,
            commit=commit,
            shard=args.shard,
            resume=args.resume,
            max_new_tasks=args.max_new_tasks,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
