"""Write a fresh metadata-only Phase 5 Dev schedule; no inference or private oracle."""

import argparse
import subprocess
from pathlib import Path

from react_agent.llm.agent_mount_v1 import write_receipt
from react_agent.validation.grouped_dev_plan_v1 import plan

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "experiments/manifests"):
        raise ValueError("fresh experiments/manifests output required")
    result = plan(ROOT / "data/adversarial/release_v2")
    result["source_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True  # noqa: S607 - fixed Git query
    ).strip()  # noqa: S603 - fixed read-only Git query
    write_receipt(output, result)
    print("GROUPED_DEV_PLAN_PREPARED cases=16 runtime_tasks=112 dispatch_allowed=False")


if __name__ == "__main__":
    main()
