"""CPU-only CLI gate for observed pair integration; native package is not released."""

import argparse
import shutil
import subprocess
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.exit_pair_probe_v1 import run
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--condition", choices=("valid", "backend_failure"), default="valid")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    no_links(args.output)
    if not args.output.resolve().is_relative_to(ROOT / "results"):
        raise ValueError("CPU output must be under results")
    git = shutil.which("git")
    if not git:
        raise RuntimeError("Git base required")
    base = subprocess.check_output(  # noqa: S603 - resolved executable, fixed read-only arguments
        [git, "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    print(
        run(
            args.output,
            ROOT / "data/clean/v1_1/environment",
            backend="stub",
            commit=base,
            observer_factory=SyntheticPairObserver,
            condition=args.condition,
            resume=args.resume,
        )
    )


if __name__ == "__main__":
    main()
