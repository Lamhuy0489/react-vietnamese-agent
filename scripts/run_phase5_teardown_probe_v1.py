"""Run the fixed 18-worker CPU teardown diagnostic; no models or benchmark inputs."""

import argparse
import subprocess
from pathlib import Path

from react_agent.llm.teardown_probe_v1 import run

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / "results"):
        raise ValueError("output must be under results")
    base = subprocess.check_output(  # noqa: S603 - fixed read-only Git query
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=ROOT,
        text=True,
    ).strip()
    run(args.output, base)


if __name__ == "__main__":
    main()
